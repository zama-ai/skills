#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Translate SKILL.md files to Cursor IDE rules (.mdc) for this repo.

This is the fheskills variant: one plugin (`zama-protocol`) at the repo root, with
skills at `skills/<skill-name>/SKILL.md`. The output filename pattern is
`{plugin}-{skill}.mdc` (and `{plugin}-{skill}--{ref}.mdc` for references).

Run from the repo root:

    uv run scripts/translate_for_cursor.py
    uv run scripts/translate_for_cursor.py --dry-run
    uv run scripts/translate_for_cursor.py --check    # pre-commit / CI mode
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


def to_kebab_case(name: str) -> str:
    name = name.replace("&", "and")
    name = re.sub(r"[_\s]+", "-", name)
    name = re.sub(r"[^a-zA-Z0-9-]", "", name)
    name = re.sub(r"([a-z])([A-Z])", r"\1-\2", name)
    name = re.sub(r"-+", "-", name)
    return name.lower().strip("-")


def find_skill_file(skill_dir: Path) -> Path | None:
    for name in ("SKILL.md", "skill.md", "Skill.md"):
        path = skill_dir / name
        if path.exists():
            return path
    return None


def parse_skill_md(path: Path, fallback_name: str) -> dict:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        heading_match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
        name = heading_match.group(1) if heading_match else fallback_name.replace("-", " ").title()
        return {"name": name, "description": f"Skill for {name.lower()}", "body": content.strip()}

    frontmatter_str, body = match.groups()
    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        frontmatter = {}

    description = frontmatter.get("description", f"Skill for {fallback_name}")
    if isinstance(description, str):
        description = " ".join(description.split())

    return {
        "name": frontmatter.get("name", fallback_name),
        "description": description,
        "body": body.strip(),
    }


def parse_reference_md(path: Path, skill_name: str, plugin_name: str) -> dict:
    content = path.read_text(encoding="utf-8")
    ref_name = path.stem

    description = ""
    body = content
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if match:
        frontmatter_str, body = match.groups()
        try:
            frontmatter = yaml.safe_load(frontmatter_str) or {}
            description = frontmatter.get("description", "")
        except yaml.YAMLError:
            description = ""

    if not description:
        readable = ref_name.replace("-", " ").replace("_", " ")
        description = f"Detailed reference for {readable} ({skill_name} skill)"

    return {
        "name": ref_name,
        "skill_name": skill_name,
        "plugin_name": plugin_name,
        "description": description,
        "body": body.strip(),
    }


def render_skill_mdc(skill: dict) -> str:
    return "\n".join([
        "---",
        f"description: {skill['description']}",
        "alwaysApply: false",
        "---",
        "",
        f"# {skill['name']}",
        "",
        skill["body"],
    ]) + "\n"


def render_reference_mdc(ref: dict, kind: str = "reference") -> str:
    pretty = ref["name"].replace("-", " ").replace("_", " ").title()
    return "\n".join([
        "---",
        f"description: {ref['description']}",
        "alwaysApply: false",
        "---",
        "",
        f"# {pretty}",
        "",
        f"_{kind.title()} for {ref['skill_name']} skill ({ref['plugin_name']} plugin)_",
        "",
        ref["body"],
    ]) + "\n"


def write_or_check(path: Path, content: str, check: bool, dry_run: bool) -> bool:
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            print(f"  ✗ {path.name} (needs update)")
            return False
        print(f"  ✓ {path.name}")
        return True
    if dry_run:
        print(f"  → {path.name}  (dry-run)")
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  → {path.name}")
    return True


def walk_references(skill_dir: Path) -> list[Path]:
    """Find all reference markdown files recursively, ignoring `addresses.md` symlinks."""
    refs_dir = skill_dir / "references"
    if not refs_dir.exists():
        return []
    out = []
    for md in sorted(refs_dir.rglob("*.md")):
        # Skip symlinks pointing outside the skill (e.g. shared addresses.md)
        if md.is_symlink() and not md.resolve().is_relative_to(skill_dir.resolve()):
            continue
        out.append(md)
    return out


def translate(repo_root: Path, output_dir: Path, dry_run: bool, check: bool) -> bool:
    plugin_json = repo_root / ".claude-plugin" / "plugin.json"
    plugin_meta = json.loads(plugin_json.read_text())
    plugin_name = plugin_meta.get("name", "zama-protocol")
    plugin_kebab = to_kebab_case(plugin_name)

    skills_dir = repo_root / "skills"
    if not skills_dir.exists():
        print(f"No skills/ directory at {skills_dir}", file=sys.stderr)
        return False

    ok = True

    for skill_dir in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
        skill_md = find_skill_file(skill_dir)
        if not skill_md:
            continue

        skill = parse_skill_md(skill_md, skill_dir.name)
        skill_kebab = to_kebab_case(skill["name"])
        print(f"Skill: {skill['name']}")

        main_path = output_dir / f"{plugin_kebab}-{skill_kebab}.mdc"
        ok = write_or_check(main_path, render_skill_mdc(skill), check, dry_run) and ok

        for ref_path in walk_references(skill_dir):
            ref = parse_reference_md(ref_path, skill["name"], plugin_name)
            ref_kebab = to_kebab_case(ref["name"])
            rel_segments = ref_path.relative_to(skill_dir / "references").with_suffix("").parts
            joined = "-".join(to_kebab_case(s) for s in rel_segments)
            ref_filename = f"{plugin_kebab}-{skill_kebab}--{joined or ref_kebab}.mdc"
            ref_out = output_dir / ref_filename
            ok = write_or_check(ref_out, render_reference_mdc(ref), check, dry_run) and ok

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    repo_root = Path(__file__).resolve().parent.parent
    parser.add_argument("--output", type=Path, default=repo_root / ".cursor" / "rules",
                        help="Output directory for .mdc files (default: ./.cursor/rules)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--check", action="store_true", help="Verify files are up-to-date (exit 1 if not)")
    args = parser.parse_args()

    if not args.dry_run and not args.check:
        args.output.mkdir(parents=True, exist_ok=True)

    ok = translate(repo_root, args.output.resolve(), args.dry_run, args.check)
    if args.check and not ok:
        print("\nRun without --check to regenerate.", file=sys.stderr)
        return 1
    print(f"\n{'Verified' if args.check else 'Generated'} Cursor .mdc rules")
    return 0


if __name__ == "__main__":
    sys.exit(main())
