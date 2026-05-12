#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Generate Codex plugin manifest and marketplace from the Claude plugin metadata.

This repo distributes one plugin (`zama-protocol`) directly from the repo root —
unlike `zama-marketplace` which has many plugins under `plugins/`. Outputs:

- `.codex-plugin/plugin.json`             — the Codex manifest for this plugin
- `.agents/plugins/marketplace.json`      — the Codex marketplace index (single entry)

Run from the repo root:

    uv run scripts/generate_codex_artifacts.py
    uv run scripts/generate_codex_artifacts.py --check   # pre-commit / CI mode
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PASSTHROUGH_FIELDS = (
    "name",
    "version",
    "description",
    "author",
    "license",
    "repository",
    "keywords",
)


def read_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, data: dict, check: bool) -> bool:
    rendered = json.dumps(data, indent=2) + "\n"
    if check:
        if not path.exists() or path.read_text() != rendered:
            print(f"Outdated: {path}", file=sys.stderr)
            return False
        return True

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered)
    return True


def codex_manifest(repo_root: Path, claude_meta: dict, version: str) -> dict:
    manifest = {field: claude_meta[field] for field in PASSTHROUGH_FIELDS if field in claude_meta}
    manifest["version"] = version

    capabilities: list[str] = []
    if (repo_root / "skills").exists():
        manifest["skills"] = "./skills/"
        capabilities.append("Skills")
    if (repo_root / "agents").exists():
        manifest["agents"] = "./agents/"
        capabilities.append("Agents")
    if (repo_root / "commands").exists():
        manifest["commands"] = "./commands/"
        capabilities.append("Commands")
    if (repo_root / ".mcp.json").exists():
        manifest["mcpServers"] = "./.mcp.json"
        capabilities.append("MCP")
    if (repo_root / "hooks.json").exists():
        manifest["hooks"] = "./hooks.json"
        capabilities.append("Hooks")
    if (repo_root / "assets").exists():
        manifest["assets"] = "./assets/"
        capabilities.append("Assets")

    author_name = (claude_meta.get("author") or {}).get("name") or "Zama Team"
    manifest["interface"] = {
        "displayName": claude_meta.get("name", "zama-protocol"),
        "shortDescription": claude_meta.get("description", ""),
        "developerName": author_name,
        "category": "Developer Tools",
        "capabilities": capabilities or ["Skills"],
    }
    return manifest


def marketplace_index(marketplace_meta: dict, codex_manifest: dict) -> dict:
    """Build the Codex marketplace index pointing at the single plugin at repo root."""
    entry = {
        "name": codex_manifest["name"],
        "source": {
            "source": "local",
            "path": "./",
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_USE",
        },
        "category": codex_manifest.get("interface", {}).get("category", "Developer Tools"),
        "interface": {
            "displayName": codex_manifest.get("interface", {}).get("displayName", codex_manifest["name"]),
        },
    }
    return {
        "name": marketplace_meta.get("name", "zama-skills"),
        "interface": {
            "displayName": (marketplace_meta.get("metadata") or {}).get("displayName")
            or "Zama Skills",
        },
        "plugins": [entry],
    }


def generate(repo_root: Path, check: bool) -> bool:
    claude_plugin = read_json(repo_root / ".claude-plugin" / "plugin.json")
    marketplace = read_json(repo_root / ".claude-plugin" / "marketplace.json")

    # Take the version from the marketplace plugin entry (single source of truth for versioning).
    version = "0.0.0"
    for plugin in marketplace.get("plugins", []):
        if plugin.get("name") == claude_plugin.get("name"):
            version = plugin.get("version", version)
            break

    manifest = codex_manifest(repo_root, claude_plugin, version)
    index = marketplace_index(marketplace, manifest)

    ok = True
    ok = write_json(repo_root / ".codex-plugin" / "plugin.json", manifest, check) and ok
    ok = write_json(repo_root / ".agents" / "plugins" / "marketplace.json", index, check) and ok
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify generated files are up-to-date")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    ok = generate(repo_root, args.check)
    if not ok:
        return 1

    print(f"{'Verified' if args.check else 'Generated'} Codex plugin artifacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
