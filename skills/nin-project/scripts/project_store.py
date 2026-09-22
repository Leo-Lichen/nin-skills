"""Local, append-only project records. Python standard library only."""
import argparse
import errno
import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

KINDS = {"user_statement", "material_record", "external_verified", "inference", "hypothesis"}


@contextmanager
def project_lock(root, timeout=30.0):
    """Serialize cooperating writers; the OS releases the lock on process exit.

    Keep this file permanently: unlinking it could give waiting and new writers
    different lock objects. All writers lock byte zero on Windows, or the whole
    file on POSIX. The file is only coordination state, never project evidence.
    """
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".project-store.lock").open("a+b") as handle:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        if os.name == "nt":
            import msvcrt

            def acquire():
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)

            def release():
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            def acquire():
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            def release():
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

        deadline = time.monotonic() + timeout
        while True:
            try:
                acquire()
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                    raise
                if time.monotonic() >= deadline:
                    raise TimeoutError("Project is busy; retry after the current save finishes") from exc
                time.sleep(0.05)
        try:
            yield
        finally:
            release()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def validate_payload(data):
    if not isinstance(data, dict):
        raise ValueError("Record must be a JSON object")
    for key in ("project_id", "title", "summary"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"{key} must be a nonempty string")
    for key in ("source_skills", "decisions", "rejected_directions", "open_questions"):
        values = data.get(key, [])
        if not isinstance(values, list) or any(not isinstance(x, str) for x in values):
            raise ValueError(f"{key} must be a list of strings")
    claims = data.get("claims", [])
    if not isinstance(claims, list):
        raise ValueError("claims must be a list")
    seen = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise ValueError("Each claim must be an object")
        for key in ("id", "text", "source"):
            if not isinstance(claim.get(key), str) or not claim[key].strip():
                raise ValueError(f"Claim {key} must be a nonempty string")
        if claim["id"] in seen:
            raise ValueError("Duplicate claim ID in one record")
        seen.add(claim["id"])
        if claim.get("kind") not in KINDS:
            raise ValueError("Unknown claim evidence kind")
        if not isinstance(claim.get("observed_at", ""), str):
            raise ValueError("observed_at must be a string")
        supersedes = claim.get("supersedes", [])
        if not isinstance(supersedes, list) or any(not isinstance(x, str) for x in supersedes):
            raise ValueError("supersedes must be a list of IDs")
        if claim["id"] in supersedes:
            raise ValueError("A claim cannot supersede itself")
    if not isinstance(data.get("next_action", {}), dict):
        raise ValueError("next_action must be an object")


def project_meta(root):
    path = root / "project.json"
    if not path.exists():
        return None
    value = read_json(path)
    if not isinstance(value, dict) or value.get("schema_version") != 1 or not isinstance(value.get("project_id"), str):
        raise ValueError("Invalid project.json; refusing to guess project identity")
    return value


def records(root):
    result, errors = [], []
    meta = project_meta(root)
    for path in sorted((root / "snapshots").glob("*.json")):
        try:
            row = read_json(path)
            validate_payload(row)
            if not meta or row["project_id"] != meta["project_id"]:
                raise ValueError("Project identity mismatch")
            if row.get("schema_version") != 1:
                raise ValueError("Unsupported schema version")
            if not isinstance(row.get("id"), str) or len(row["id"]) != 32:
                raise ValueError("Invalid record ID")
            uuid.UUID(hex=row["id"])
            moment = datetime.fromisoformat(row["created_at"])
            if moment.tzinfo is None:
                raise ValueError("Record timestamp must include timezone")
            result.append((moment, row["id"], path, row))
        except (ValueError, TypeError, KeyError, OSError) as exc:
            errors.append({"path": str(path), "error": str(exc)})
    result.sort(key=lambda x: (x[0], x[1]))
    known = {}
    for _, _, path, row in result:
        for claim in row.get("claims", []):
            prior = known.get(claim["id"])
            if prior and prior[0] != claim:
                errors.append({
                    "path": str(path), "conflicting_path": str(prior[1]),
                    "claim_id": claim["id"], "error": "Existing claim ID has conflicting content",
                })
            else:
                known.setdefault(claim["id"], (claim, path))
    return result, errors


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def save(root, input_path):
    data = read_json(input_path)
    validate_payload(data)
    # An absent project cannot contain a prior claim. Reject this invalid first
    # save without creating even an empty project directory.
    if not root.exists() and any(claim.get("supersedes") for claim in data.get("claims", [])):
        raise ValueError("supersedes refers to an unknown prior claim")
    with project_lock(root):
        return _save_locked(root, data)


def _save_locked(root, data):
    """Read, validate and append while the caller holds the project lock."""
    old, errors = records(root)
    if errors:
        raise ValueError("Existing malformed or conflicting records require review before saving: " + json.dumps(errors, ensure_ascii=False))
    meta = project_meta(root)
    if meta and meta["project_id"] != data["project_id"]:
        raise ValueError("Input project_id differs from existing project")
    known = {}
    for _, _, _, row in old:
        for claim in row.get("claims", []):
            known[claim["id"]] = claim
    for claim in data.get("claims", []):
        if claim["id"] in known and known[claim["id"]] != claim:
            raise ValueError("Changed claim must use a new ID and preserve the old record")
        if any(key not in known for key in claim.get("supersedes", [])):
            raise ValueError("supersedes refers to an unknown prior claim")
    now = datetime.now(timezone.utc)
    record = dict(data, schema_version=1, id=uuid.uuid4().hex, created_at=now.isoformat(timespec="microseconds"))
    if not meta:
        write_new(root / "project.json", {"schema_version": 1, "project_id": data["project_id"]})
    folder = root / "snapshots"
    folder.mkdir(exist_ok=True)
    path = folder / (now.strftime("%Y%m%dT%H%M%S%fZ") + "-" + record["id"] + ".json")
    write_new(path, record)
    if read_json(path) != record:
        raise ValueError("Saved record failed read-back")
    return {"saved": str(path), "id": record["id"], "project_id": record["project_id"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["save", "list", "show"])
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--id", default="latest")
    args = parser.parse_args()
    root = args.project_dir.resolve()
    skill_root = Path(__file__).resolve().parents[1]
    if root == skill_root or skill_root in root.parents:
        parser.error("Business records must be outside the skill installation")
    if args.command == "save":
        if not args.input:
            parser.error("save requires --input")
        output = save(root, args.input)
    else:
        rows, errors = records(root)
        if args.command == "list":
            output = {"records": [{"id": row["id"], "created_at": row["created_at"], "title": row["title"], "path": str(path)} for _, _, path, row in rows], "errors": errors}
        else:
            matches = rows[-1:] if args.id == "latest" else [entry for entry in rows if entry[1] == args.id]
            if len(matches) > 1:
                raise ValueError("Duplicate record IDs; cannot choose reliably")
            output = {"record": matches[0][3] if matches else None, "path": str(matches[0][2]) if matches else None, "errors": errors}
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
