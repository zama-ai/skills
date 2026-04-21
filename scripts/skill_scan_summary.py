"""
Publish a GitHub Actions step summary for a cisco-ai-skill-scanner JSON report.

Called by the skill-security-scanner-pr.yml workflow after the annotation step,
so results.json already contains GitHub URLs in place of runner paths.
All configuration is read from environment variables set by the workflow.

Environment variables:
  GITHUB_STEP_SUMMARY  — path to the step summary file (set by GH Actions)
  REPO_URL             — e.g. https://github.com/org/repo
  SCAN_MODE            — "advanced" or "simple"
  RUN_ID               — GitHub Actions run ID
  REPO                 — e.g. org/repo
  SCANNED_SHA          — the exact commit SHA that was checked out and scanned
"""

import json
import os
import sys

RESULTS_PATH = "/tmp/scan-results/results.json"

SUMMARY     = os.environ.get("GITHUB_STEP_SUMMARY")
REPO_URL    = os.environ.get("REPO_URL", "")
SCAN_MODE   = os.environ.get("SCAN_MODE", "advanced")
RUN_ID      = os.environ.get("RUN_ID", "")
REPO        = os.environ.get("REPO", "")
SCANNED_SHA = os.environ.get("SCANNED_SHA", "main")

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SEV_EMOJI = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}


def write_summary(text: str) -> None:
    if SUMMARY:
        with open(SUMMARY, "a") as f:
            f.write(text + "\n")
    else:
        print(text)


if not os.path.exists(RESULTS_PATH):
    print("results.json not found — skipping summary.")
    sys.exit(0)

with open(RESULTS_PATH) as f:
    content = f.read().strip()

if not content:
    write_summary("**Skill Security Scan:** No skills found in this repository — nothing to scan.")
    sys.exit(0)

data = json.loads(content)

summary = data.get("summary", {})
results = sorted(
    data.get("results", []),
    key=lambda r: (SEV_ORDER.get(r.get("max_severity", "INFO"), 99), r.get("skill_name", "")),
)

mode_label    = "advanced (LLM + VirusTotal)" if SCAN_MODE == "advanced" else "simple (static + behavioral)"
artifact_name = f"skill-scan-{SCAN_MODE}-results-{RUN_ID}"
artifact_url  = f"https://github.com/{REPO}/actions/runs/{RUN_ID}"

scanned = summary.get("total_skills_scanned", "?")
total   = summary.get("total_findings", "?")
safe    = summary.get("safe_skills", "?")

lines = []

# ── Header (Markdown) ─────────────────────────────────────────────────────────
lines.append("## Skill Security Scan")
lines.append("")
lines.append(f"**Target:** [{REPO_URL}]({REPO_URL})")
lines.append(f"**Mode:** {mode_label}")
lines.append(f"**Results:** {scanned} skills scanned — {total} findings ({safe} safe)")
lines.append(f"**Full report:** [{artifact_name}]({artifact_url})")
lines.append("")

# ── Per-skill collapsible sections ────────────────────────────────────────────
# <details>/<summary> are used here because GitHub-Flavored Markdown has no
# collapsible block syntax — HTML is unavoidable for this feature.
if results:
    lines.append("<details>")
    lines.append(f"<summary><strong>Skills ({scanned} scanned — {total} findings, {safe} safe)</strong></summary>")
    lines.append("")

for r in results:
    skill_path = r.get("skill_path", "")
    findings   = r.get("findings", [])

    # The annotation step has already rewritten runner paths to GitHub URLs of the form
    # {REPO_URL}/tree/{SCANNED_SHA}/{relative/path}. Strip that prefix to get the
    # display path; use the annotated value directly as the href.
    url_prefix = f"{REPO_URL}/tree/{SCANNED_SHA}/"
    if skill_path.startswith(url_prefix):
        rel_path  = skill_path[len(url_prefix):]
        skill_url = skill_path
    else:
        rel_path  = ""
        skill_url = REPO_URL
    display_path = rel_path if rel_path else REPO_URL

    # Severity tally for this skill
    tally = {}
    for finding in findings:
        sev = finding.get("severity", "INFO")
        tally[sev] = tally.get(sev, 0) + 1
    sev_cells = "".join(
        f"<td>{SEV_EMOJI[s]} <strong>{s}</strong>: {tally.get(s, 0)}</td>"
        for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    )

    # Mini HTML table used as the <summary> label so the row shows status + severity counts.
    status = "✅" if r.get("is_safe") else "❌"
    mini_table = (
        f"<table>"
        f'<tr><td colspan="5">{status} <a href="{skill_url}" target="_blank"><code>{display_path}</code></a></td></tr>'
        f"<tr>{sev_cells}</tr>"
        f"</table>"
    )

    lines.append("<details>")
    lines.append(f"<summary>{mini_table}</summary>")
    lines.append("")
    if findings:
        lines.append("| Severity | Rule | Title | File |")
        lines.append("|---|---|---|---|")
        for finding in sorted(findings, key=lambda x: SEV_ORDER.get(x.get("severity", "INFO"), 99)):
            fsev  = finding.get("severity", "")
            fpath = finding.get("file_path") or ""
            if fpath.startswith(url_prefix):
                # Absolute path — annotation step already produced a full GitHub URL.
                frel  = fpath[len(url_prefix):]
                flink = f"[`{frel}`]({fpath})"
            elif fpath and fpath != "." and skill_url != REPO_URL:
                # Relative path (e.g. "SKILL.md", "scripts/gh_pr.py") — relative to the
                # skill directory, so build the URL from the skill's GitHub tree URL.
                flink = f"[`{fpath}`]({skill_url}/{fpath})"
            elif fpath == "." and skill_url != REPO_URL:
                # "." refers to the skill directory itself.
                flink = f"[`{display_path}`]({skill_url})"
            else:
                flink = f"`{fpath}`" if fpath else ""
            lines.append(
                f"| {SEV_EMOJI.get(fsev, '')} {fsev}"
                f" | `{finding.get('rule_id', '')}`"
                f" | {finding.get('title', '')}"
                f" | {flink} |"
            )
    lines.append("")
    lines.append("</details>")
    lines.append("")

if results:
    lines.append("</details>")
    lines.append("")

write_summary("\n".join(lines))
