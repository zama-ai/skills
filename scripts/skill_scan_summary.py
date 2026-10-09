"""
Publish a GitHub Actions step summary for a cisco-ai-skill-scanner JSON report.

Called by the skill-security-scanner-pr.yml workflow after the annotation step,
so results.json already contains GitHub URLs in place of runner paths.
All configuration is read from environment variables set by the workflow.

Environment variables:
  GITHUB_STEP_SUMMARY  — path to the step summary file (set by GH Actions)
  REPO_URL             — e.g. https://github.com/org/repo
  SCAN_MODE            — scan tier: "simple", "advanced-1", or "advanced-2"
  RUN_ID               — GitHub Actions run ID
  REPO                 — e.g. org/repo
  SCANNED_SHA          — the exact commit SHA that was checked out and scanned
"""

import glob
import json
import os
import sys
import traceback

RESULTS_PATH = "/tmp/scan-results/results.json"
# Set by the consolidating job to a directory of per-plugin scan artifacts. When unset, a
# single scan job is reporting on its own results.
RESULTS_DIR  = os.environ.get("RESULTS_DIR")

SUMMARY     = os.environ.get("GITHUB_STEP_SUMMARY")
REPO_URL    = os.environ.get("REPO_URL", "")
SCAN_MODE   = os.environ.get("SCAN_MODE", "advanced")
RUN_ID      = os.environ.get("RUN_ID", "")
REPO        = os.environ.get("REPO", "")
SCANNED_SHA = os.environ.get("SCANNED_SHA", "main")
BRANCH      = os.environ.get("BRANCH", "main")
JOB_INDEX   = os.environ.get("JOB_INDEX", "")

SEV_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
SEV_EMOJI = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵", "INFO": "⚪"}


def write_summary(text: str) -> None:
    if SUMMARY:
        with open(SUMMARY, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    else:
        print(text)


def report_crash(exc_type, exc, tb) -> None:
    """Put the traceback in the job summary, not only in the runner log.

    Actions logs are awkward to retrieve, and a summary that fails silently looks
    identical to a scan that found nothing. Re-raises through the default hook so the
    step still exits non-zero.
    """
    write_summary(
        "**Skill Security Scan:** could not render the report.\n\n```\n"
        + "".join(traceback.format_exception(exc_type, exc, tb))
        + "```"
    )
    sys.__excepthook__(exc_type, exc, tb)


sys.excepthook = report_crash


def scan_log_hint(results_dir: str) -> str:
    """First error-looking line, else the last line, of the scan.log beside a results file."""
    hint = ""
    last_line = ""
    scan_log_path = os.path.join(results_dir, "scan.log")
    if os.path.exists(scan_log_path):
        with open(scan_log_path, encoding="utf-8", errors="replace") as lf:
            for line in lf:
                stripped = line.strip()
                if stripped:
                    last_line = stripped
                if stripped and any(k in stripped for k in ("Error", "Exception", "Failed", "failed")):
                    hint = stripped[:300]
                    break
    return hint or last_line[:300] or "Check the uploaded scan artifact for details."


def merge(reports: list) -> dict:
    """Combine per-plugin reports into the single report shape used below.

    The PR scan is sharded one job per plugin, so a consolidated summary has to sum the
    headline counts and concatenate the per-skill results. Skill paths were already
    rewritten to GitHub URLs by the annotation step in each scan job.
    """
    merged = {"summary": {}, "results": []}
    for key in ("total_skills_scanned", "total_findings", "safe_skills"):
        merged["summary"][key] = sum(r.get("summary", {}).get(key) or 0 for r in reports)
    for report in reports:
        merged["results"].extend(report.get("results", []))
    return merged


if RESULTS_DIR:
    paths = sorted(glob.glob(os.path.join(RESULTS_DIR, "**", "results.json"), recursive=True))
else:
    paths = [RESULTS_PATH] if os.path.exists(RESULTS_PATH) else []

if not paths:
    print("results.json not found — skipping summary.")
    sys.exit(0)

reports = []
unreadable = []
for path in paths:
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        continue
    try:
        reports.append(json.loads(content))
    except json.JSONDecodeError:
        # One unreadable shard must not cost us the report for the others.
        shard = os.path.dirname(path)
        unreadable.append(f"{os.path.basename(shard)}: {scan_log_hint(shard)}")

if not reports:
    if unreadable:
        write_summary("❌ **Failed to parse scan results**\n\n" + "\n".join(f"- `{u}`" for u in unreadable))
        sys.exit(0)
    write_summary("**Skill Security Scan:** No skills found in this repository — nothing to scan.")
    sys.exit(0)

data = merge(reports)

summary = data.get("summary", {})
results = sorted(
    data.get("results", []),
    key=lambda r: (SEV_ORDER.get(r.get("max_severity", "INFO"), 99), r.get("skill_name", "")),
)

MODE_LABELS = {
    "simple":     "simple (static + behavioral)",
    "advanced-1": "advanced-1 (Haiku 4.5 + VirusTotal + Consensus 2)",
    "advanced-2": "advanced-2 (Opus 4.6 + VirusTotal + Consensus 1)",
}
mode_label    = MODE_LABELS.get(SCAN_MODE, SCAN_MODE)
artifact_name = f"skill-scan-{SCAN_MODE}-{JOB_INDEX + '-' if JOB_INDEX else ''}results-{RUN_ID}"
artifact_url  = f"https://github.com/{REPO}/actions/runs/{RUN_ID}"

scanned = summary.get("total_skills_scanned", "?")
total   = summary.get("total_findings", "?")
safe    = summary.get("safe_skills", "?")

lines = []

# ── Header (Markdown) ─────────────────────────────────────────────────────────
lines.append("## Skill Security Scan")
lines.append("")
lines.append(f"**Target:** [{REPO_URL}]({REPO_URL}) @ `{BRANCH}`")
lines.append(f"**Mode:** {mode_label}")
lines.append(f"**Results:** {scanned} skills scanned — {total} findings ({safe} safe)")
lines.append(f"**Full report:** [{artifact_name}]({artifact_url})")
if unreadable:
    lines.append(f"**Unreadable results:** {'; '.join(unreadable)}")
lines.append("")

# ── Per-skill collapsible sections ────────────────────────────────────────────
# <details>/<summary> are used here because GitHub-Flavored Markdown has no
# collapsible block syntax — HTML is unavoidable for this feature.
if results:
    global_tally = {}
    for r in results:
        for finding in r.get("findings", []):
            sev = finding.get("severity", "INFO")
            global_tally[sev] = global_tally.get(sev, 0) + 1
    sev_row = ", ".join(
        f"{global_tally.get(s, 0)} {s.capitalize()}"
        for s in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    )
    lines.append("<details>")
    lines.append(
        f"<summary>"
        f"<strong>{scanned} skills scanned</strong><br>"
        f"{safe} safe / {total} findings ({sev_row})"
        f"</summary>"
    )
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
