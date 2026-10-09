#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# ///
"""Compile the Solidity examples embedded in skills/zama-solidity.

Each ```solidity block becomes part of one contract: blocks that declare functions are added as
members, other blocks become the body of a function. The contract declares the state the examples
use, so an example that relies on a new name fails here until that name is declared below.

Run after `npm install` in tests/solidity-examples:

    uv run scripts/check_solidity_examples.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT = REPO_ROOT / "tests" / "solidity-examples"

HEADER = """// SPDX-License-Identifier: BSD-3-Clause-Clear
pragma solidity ^0.8.27;

import {FHE, ebool, euint64, eaddress, externalEuint64} from "@fhevm/solidity/lib/FHE.sol";
import {ZamaEthereumConfig} from "@fhevm/solidity/config/ZamaConfig.sol";
import {IERC7984} from "@openzeppelin/confidential-contracts/interfaces/IERC7984.sol";

contract SkillExamples is ZamaEthereumConfig {
    enum Stage { Open, Revealing, Settled }

    IERC7984 token;
    Stage stage;
    uint256 endTime;
    address seller;
    euint64 total;
    euint64 highestBid;
    eaddress highestBidder;
    bytes32 winnerHandle;
"""


def extract_blocks(skill_dir: Path) -> list[tuple[Path, str]]:
    blocks = []
    for md in sorted(skill_dir.rglob("*.md")):
        for code in re.findall(r"```solidity\n(.*?)```", md.read_text(encoding="utf-8"), re.DOTALL):
            blocks.append((md.relative_to(REPO_ROOT), code))
    return blocks


def indent(code: str, prefix: str) -> str:
    return "".join(f"{prefix}{line}\n" if line else "\n" for line in code.splitlines())


def render(blocks: list[tuple[Path, str]]) -> str:
    parts = [HEADER]
    for index, (source, code) in enumerate(blocks):
        if re.search(r"^function ", code, re.MULTILINE):
            body = indent(code, "    ")
        else:
            body = f"    function example{index}() internal {{\n{indent(code, '        ')}    }}\n"
        parts.append(f"\n    // {source}\n{body}")
    parts.append("}\n")
    return "".join(parts)


def main() -> int:
    blocks = extract_blocks(REPO_ROOT / "skills" / "zama-solidity")
    if not blocks:
        print("No Solidity examples found", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(dir=PROJECT) as build:
        contract = Path(build) / "SkillExamples.sol"
        contract.write_text(render(blocks), encoding="utf-8")
        result = subprocess.run(
            ["node_modules/.bin/solcjs", "--abi", "--base-path", ".", "--include-path", "node_modules",
             "--output-dir", build, str(contract.relative_to(PROJECT))],
            cwd=PROJECT, capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(result.stdout + result.stderr, file=sys.stderr)
            print(contract.read_text(encoding="utf-8"), file=sys.stderr)
            return 1

    print(f"Compiled {len(blocks)} Solidity examples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
