"""Validate the distributable skills, metadata and relative resource links."""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import yaml


def validate(root, official_path=None):
    errors, results = [], []
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    declared = [item["name"] for item in manifest["skills"]]
    if len(declared) != 18 or len(set(declared)) != 18:
        errors.append("Manifest must identify 18 distinct skills")
    actual = {p.name for p in (root / "skills").iterdir() if p.is_dir()}
    if actual != set(declared):
        errors.append(f"Skill directory mismatch: {actual.symmetric_difference(declared)}")
    official = None
    if official_path:
        spec = importlib.util.spec_from_file_location("official_validator", official_path)
        official = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(official)
    for name in declared:
        skill = root / "skills" / name
        local_errors = []
        try:
            text = (skill / "SKILL.md").read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---", text, re.S)
            if not match:
                raise ValueError("Missing YAML frontmatter")
            meta = yaml.safe_load(match.group(1))
            if meta.get("name") != name or not isinstance(meta.get("description"), str) or not meta["description"].strip():
                local_errors.append("Invalid name or description")
            ui = yaml.safe_load((skill / "agents/openai.yaml").read_text(encoding="utf-8"))
            if "$" + name not in ui["interface"].get("default_prompt", ""):
                local_errors.append("Default prompt does not invoke this skill")
            if not 25 <= len(ui["interface"].get("short_description", "")) <= 64:
                local_errors.append("UI description length invalid")
            if ui.get("policy", {}).get("allow_implicit_invocation", True) is not True:
                local_errors.append("Automatic selection unexpectedly disabled")
            if official:
                ok, message = official.validate_skill(skill)
                if not ok:
                    local_errors.append(message)
            markdown_files = list(skill.rglob("*.md"))
            linked = set()
            for path in markdown_files:
                content = path.read_text(encoding="utf-8")
                if "\ufffd" in content or "[TODO:" in content:
                    local_errors.append(f"Unfinished or corrupt text: {path.name}")
                for link in re.findall(r"\]\(([^\s)]+)\)", content):
                    if "://" in link or link.startswith("#"):
                        continue
                    target = (path.parent / link.split("#")[0]).resolve()
                    if not target.exists():
                        local_errors.append(f"Broken resource link: {path.name} -> {link}")
                    elif not target.is_relative_to(root.resolve()):
                        local_errors.append(f"Nonportable link outside package: {link}")
                    linked.add(target)
            for resource in (skill / "references").glob("*.md"):
                if resource.resolve() not in linked:
                    local_errors.append(f"Reference has no discoverable link: {resource.name}")
            results.append({"name": name, "skill_characters": len(text), "references": len(list((skill / "references").glob("*.md"))), "errors": local_errors})
        except (OSError, ValueError, KeyError, TypeError) as exc:
            local_errors.append(str(exc))
            results.append({"name": name, "errors": local_errors})
        errors.extend(f"{name}: {message}" for message in local_errors)
    return {"passed": not errors, "skill_count": len(declared), "official_validator_used": bool(official), "skills": results, "errors": errors}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--official-validator", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.root, args.official_validator)
    output = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    sys.exit(0 if report["passed"] else 1)
