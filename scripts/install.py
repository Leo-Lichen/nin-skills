"""Install all Ninther Skills without overwriting existing skills. Python 3.10+."""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def default_destination(target):
    if target == "codex":
        return Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "skills"
    return Path.home() / {"claude": ".claude", "agents": ".agents"}[target] / "skills"


def plan_install(destination, root=ROOT):
    destination = Path(destination).expanduser().resolve()
    source = (root / "skills").resolve()
    if destination == source or destination.is_relative_to(source):
        raise ValueError("Install destination must be outside the source skills directory")
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    names = [entry["name"] for entry in manifest["skills"]]
    if len(names) != 18 or len(set(names)) != 18:
        raise ValueError("Manifest must contain 18 distinct skills")
    files = []
    for name in names:
        if not re.fullmatch(r"nin(?:-[a-z0-9]+)*", name):
            raise ValueError("Invalid skill name in manifest")
        skill = source / name
        if skill.is_symlink() or not (skill / "SKILL.md").is_file():
            raise ValueError(f"Missing or linked source skill: {name}")
        if os.path.lexists(destination / name):
            raise ValueError(f"Existing skill will not be overwritten: {destination / name}")
        for path in skill.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Linked source file is not supported: {path}")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                files.append((path, path.relative_to(source)))
    return destination, names, files


def install(destination, dry_run=False, root=ROOT):
    destination, names, files = plan_install(destination, root)
    if dry_run:
        return {"dry_run": True, "destination": str(destination), "skills": names, "file_count": len(files)}
    destination.mkdir(parents=True, exist_ok=True)
    installed = []
    for name in names:
        target = destination / name
        target.mkdir(exist_ok=False)
        for source_file, relative in files:
            if relative.parts[0] != name:
                continue
            target_file = destination / relative
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with source_file.open("rb") as source_handle, target_file.open("xb") as target_handle:
                shutil.copyfileobj(source_handle, target_handle)
            if hashlib.sha256(source_file.read_bytes()).digest() != hashlib.sha256(target_file.read_bytes()).digest():
                raise ValueError(f"Copy verification failed: {relative}")
        installed.append(name)
    return {"installed": installed, "destination": str(destination), "verified_files": len(files)}


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", choices=["codex", "claude", "agents"])
    group.add_argument("--destination", type=Path, help="Explicit skill directory")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = install(args.destination if args.destination else default_destination(args.target), args.dry_run)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as exc:
        print(f"Installation stopped: {exc}. Existing entries were not replaced; a failed copy may leave newly created directories.", file=sys.stderr)
        sys.exit(1)
