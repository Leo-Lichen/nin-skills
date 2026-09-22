"""Build and verify an allowlisted, source-only Ninther Skills ZIP.

Only reviewed root files and UTF-8 text beneath skills/docs/scripts/.github
are candidates. Symlinks and Windows junctions in candidate trees are rejected.
Generated files, environments, hidden files and credential names are excluded.
Existing different artifacts are never overwritten. Standard library only.
"""
import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT_FILES = (
    "README.md", "README.en.md", "LICENSE", "NOTICE", "CHANGELOG.md",
    "VERSION", "manifest.json", "requirements-dev.txt", ".gitignore",
)
SOURCE_DIRS = ("skills", "docs", "scripts", ".github")
TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".ps1", ".sh", ".bat", ".cmd", ".ini", ".cfg", ".csv", ".tsv"}
TEXT_NAMES = {"LICENSE", "NOTICE", "VERSION"}
EXCLUDED_DIRS = {"__pycache__", "env", "venv", "virtualenv", "node_modules", "dist", "build", "artifacts"}
CREDENTIAL_STEMS = {"credential", "credentials", "secret", "secrets", "token", "tokens", "private-key", "private_key", "service-account", "service_account", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
VERSION_PATTERN = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?")


def reject_link(path):
    if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
        raise ValueError(f"Links are not allowed in a release: {path}")


def excluded_name(path):
    name = path.name.lower()
    return (
        name.startswith(".") or name in EXCLUDED_DIRS
        or name == "env" or name.startswith("env.") or name.endswith(".env")
        or path.stem.lower() in CREDENTIAL_STEMS
        or any(name.startswith(stem + ".") for stem in CREDENTIAL_STEMS)
    )


def text_bytes(path):
    reject_link(path)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError(f"Only regular files may be packaged: {path}")
    data = path.read_bytes()
    try:
        data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Release text must be UTF-8: {path}") from exc
    if any(byte < 32 and byte not in (9, 10, 13) or byte == 127 for byte in data):
        raise ValueError(f"Binary/control bytes found in release text: {path}")
    return data


def source_files(root):
    """Return only allowlisted files; never traverse excluded directories."""
    candidates = []
    for name in ROOT_FILES:
        path = root / name
        reject_link(path)
        if not path.is_file():
            raise ValueError(f"Required release file is missing: {name}")
        candidates.append(path)

    def visit(folder):
        for path in sorted(folder.iterdir(), key=lambda item: item.name):
            # Check links before exclusions, so a hidden link cannot silently
            # change the release's traversal boundary.
            reject_link(path)
            if excluded_name(path):
                continue
            mode = path.stat().st_mode
            if stat.S_ISDIR(mode):
                visit(path)
            elif stat.S_ISREG(mode):
                if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES:
                    candidates.append(path)
            else:
                raise ValueError(f"Nonregular source entry: {path}")

    for name in SOURCE_DIRS:
        folder = root / name
        reject_link(folder)
        if not folder.is_dir():
            raise ValueError(f"Required source directory is missing: {name}")
        visit(folder)
    return sorted(candidates, key=lambda path: path.relative_to(root).as_posix())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_archive(path, expected):
    """Check every ZIP member against captured bytes and current source bytes."""
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError("ZIP members do not exactly match the release allowlist")
        for entry in entries:
            source, data = expected[entry.filename]
            if entry.is_dir() or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError(f"Unexpected ZIP directory or link: {entry.filename}")
            archived = archive.read(entry)
            if len(archived) != len(data) or digest(archived) != digest(data):
                raise ValueError(f"ZIP/source hash mismatch: {entry.filename}")
            if digest(text_bytes(source)) != digest(data):
                raise ValueError(f"Source changed while building release: {source}")


def build_release(root):
    root = Path(root)
    reject_link(root)
    root = root.resolve()
    paths = source_files(root)
    contents = {path: text_bytes(path) for path in paths}
    version = contents[root / "VERSION"].decode("utf-8-sig").strip()
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("VERSION must be a safe major.minor.patch version, optionally with a prerelease")
    manifest = json.loads(contents[root / "manifest.json"].decode("utf-8-sig"))
    if manifest.get("version") != version:
        raise ValueError("VERSION and manifest.json version differ")
    prefix = f"nin-skills-v{version}"
    expected = {
        f"{prefix}/{path.relative_to(root).as_posix()}": (path, data)
        for path, data in contents.items()
    }
    folder = root / "dist"
    reject_link(folder)
    folder.mkdir(exist_ok=True)
    destination = folder / (prefix + ".zip")
    reject_link(destination)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{prefix}-", suffix=".tmp", dir=folder)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for name, (_, data) in expected.items():
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        verify_archive(temporary, expected)
        artifact_hash = digest(temporary.read_bytes())
        unchanged = False
        try:
            # Same-filesystem hard linking publishes a fully verified file
            # atomically and refuses an existing name on Windows and POSIX.
            # Never fall back to replacement if linking is unsupported.
            os.link(temporary, destination)
        except FileExistsError:
            reject_link(destination)
            if not destination.is_file() or digest(destination.read_bytes()) != artifact_hash:
                raise ValueError(f"A different artifact already exists; refusing to overwrite: {destination}")
            verify_archive(destination, expected)
            unchanged = True
        return {
            "artifact": destination.relative_to(root).as_posix(),
            "version": version,
            "file_count": len(expected),
            "sha256": artifact_hash,
            "verified": True,
            "unchanged": unchanged,
        }
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Source repository root")
    args = parser.parse_args()
    print(json.dumps(build_release(args.root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
