#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = ["cisco-ai-skill-scanner==2.3.0", "litellm==1.106.0"]
# ///
"""
List the files of skill packages that the scanner's AI analysis would leave out because of
their size.

Called by skill-security-scanner-pr.yml before the scans, with the scan policy (a preset name
such as "balanced", or a policy file) and the package folders. It applies the scanner's own budget code in the order its LLM analyzer
does, so the result does not depend on the AI review: the meta-analysis can mark the scanner's
LLM_CONTEXT_BUDGET_EXCEEDED finding as a false positive and drop it from the report. A folder
the scanner cannot load is skipped here; the scan job fails on it separately.

Prints one line per left-out file: folder, file, size and reason, separated by tabs.
The workflow refuses a tab in a path, so a field can be split off safely.

Usage: python -I skill_scan_budget.py <preset or policy.yaml> <package folder>...
"""

import os
import sys

from skill_scanner.core.analyzers.llm_prompt_builder import PromptBuilder
from skill_scanner.core.loader import load_skill
from skill_scanner.core.scan_policy import ScanPolicy


def left_out(skill, lp, builder: PromptBuilder) -> list:
    """The budget gating of the scanner's LLM analyzer, without the API call."""
    skipped = []
    body = skill.instruction_body
    if len(body) > lp.max_instruction_body_chars:
        skipped.append({
            "path": "SKILL.md (instruction body)",
            "size": len(body),
            "reason": f"exceeds llm_analysis.max_instruction_body_chars ({lp.max_instruction_body_chars:,})",
        })
        body = ""
    used = len(body) + len(builder.format_manifest(skill.manifest))
    code_text, code_skipped = builder.format_code_files(
        skill,
        max_file_chars=lp.max_code_file_chars,
        max_total_chars=max(0, lp.max_total_prompt_chars - used),
    )
    used += len(code_text)
    _, ref_skipped = builder.format_referenced_files(
        skill,
        max_file_chars=lp.max_referenced_file_chars,
        remaining_budget=max(0, lp.max_total_prompt_chars - used),
    )
    # A script the instructions also reference is skipped as a reference, but it already
    # reached the analysis as code.
    as_code = {f.relative_path for f in skill.get_scripts()} - {item["path"] for item in code_skipped}
    return skipped + code_skipped + [item for item in ref_skipped if item["path"] not in as_code]


def main(argv: list) -> int:
    if len(argv) < 2:
        print("usage: skill_scan_budget.py <preset or policy.yaml> <package folder>...", file=sys.stderr)
        return 2
    policy = ScanPolicy.from_yaml(argv[1]) if os.path.isfile(argv[1]) else ScanPolicy.from_preset(argv[1])
    lp = policy.llm_analysis
    builder = PromptBuilder()
    for folder in argv[2:]:
        try:
            skill = load_skill(folder)
        except Exception:
            continue
        for item in left_out(skill, lp, builder):
            print(f"{folder}\t{item['path']}\t{item['size']:,}\t{item['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
