#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Publish a GitHub Actions step summary for a cisco-ai-skill-scanner JSON report.

Called by the skill-scan-result job of skill-security-scanner-pr.yml (RESULTS_DIR: one
artifact per plugin, whose paths the scan jobs already turned into GitHub URLs), and by
skill-security-scanner.yml (one report per job). All configuration is read from environment
variables set by the workflow.

Environment variables:
  GITHUB_STEP_SUMMARY  — path to the step summary file (set by GH Actions)
  REPO_URL             — e.g. https://github.com/org/repo
  SCAN_MODE            — scan tier: "simple", "advanced-1", or "advanced-2"
  RUN_ID               — GitHub Actions run ID
  REPO                 — e.g. org/repo
  SCANNED_SHA          — the exact commit SHA that was checked out and scanned
  BRANCH               — the branch that was scanned
  JOB_INDEX            — matrix index, used by the scheduled scanner's artifact names
  RESULTS_DIR          — set by the consolidating job: directory of downloaded artifacts
  SELECTED_PLUGINS     — JSON list of plugins the consolidating job expects results for
  SELECT_RESULT        — result of the select-plugins job, as seen by the consolidating job
"""

import glob
import json
import os
import sys
import traceback
from urllib.parse import quote

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
# The consolidating job passes the plugins it selected, so a plugin whose scan never produced
# a report is still listed instead of silently disappearing from the totals.
SELECTED    = os.environ.get("SELECTED_PLUGINS", "")
NO_SKILLS   = "No skills found to scan."
SELECT_RESULT = os.environ.get("SELECT_RESULT", "")

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


def read_shard(shard_dir: str):
    """Return (report, note) for one scan's output directory.

    note is None when the directory holds a readable report, else a short reason. The scanner
    writes no results.json when it exits early, so "no skills" is told apart from a failed
    scan by the message it leaves in scan.log.
    """
    path = os.path.join(shard_dir, "results.json")
    content = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            content = f.read().strip()
    if content:
        try:
            return json.loads(content), None
        except json.JSONDecodeError:
            return None, f"unreadable report: {scan_log_hint(shard_dir)}"
    log = os.path.join(shard_dir, "scan.log")
    if os.path.exists(log):
        with open(log, encoding="utf-8", errors="replace") as lf:
            if NO_SKILLS in lf.read():
                return None, "no skills"
    return None, f"no report: {scan_log_hint(shard_dir)}"


def shard_status(shard_dir: str) -> str:
    """The scan job's own outcome, saved next to its report: clean, findings or error.

    A missing file means the scan step stopped before its end, which is a failure too.
    """
    try:
        with open(os.path.join(shard_dir, "scan_status"), encoding="utf-8") as f:
            return f.read().strip() or "error"
    except OSError:
        return "error"


def shard_plugin(shard_dir: str) -> str:
    """The plugin its scan job wrote into the artifact, or "" when the file is missing."""
    try:
        with open(os.path.join(shard_dir, "plugin"), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def shards() -> list:
    """List (name, directory) for every scan this summary has to account for."""
    if not RESULTS_DIR:
        return [("this repository", os.path.dirname(RESULTS_PATH))]
    prefix, suffix = f"skill-scan-{SCAN_MODE}-", f"-results-{RUN_ID}"
    found = {}
    for d in sorted(glob.glob(os.path.join(RESULTS_DIR, "*"))):
        base = os.path.basename(d)
        if os.path.isdir(d) and base.startswith(prefix) and base.endswith(suffix):
            found[base[len(prefix):-len(suffix)]] = d
    # download-artifact extracts a lone matching artifact straight into RESULTS_DIR, without the
    # per-artifact directory it creates for two or more; the plugin file its scan job wrote names it.
    flat = shard_plugin(RESULTS_DIR)
    if flat:
        found[flat] = RESULTS_DIR
    expected = json.loads(SELECTED) if SELECTED.strip() else sorted(found)
    # A selected plugin with no artifact maps to a directory that does not exist, which
    # read_shard reports as "no report" with the hint that nothing was uploaded.
    return [(name, found.get(name, os.path.join(RESULTS_DIR, f"{prefix}{name}{suffix}"))) for name in expected]


# When plugin selection failed (for example, a skill file outside the plugins directory),
# nothing was scanned: say so rather than reporting an empty scan as "no skills".
if RESULTS_DIR and SELECT_RESULT and SELECT_RESULT != "success":
    write_summary(f"❌ **Skill Security Scan: nothing was scanned** — plugin selection ended with `{SELECT_RESULT}`. "
                  "The reason is in the select-plugins job and its summary above.")
    sys.exit(0)

reports = []
notes = []
failed = []
for name, shard_dir in shards():
    report, note = read_shard(shard_dir)
    # Every shard, also one without a report: a plugin with no skill whose plugin-level scan
    # failed leaves "No skills found" in its log, but its job still ended with an error.
    if RESULTS_DIR and shard_status(shard_dir) == "error":
        failed.append(name)
    if report is not None:
        # Tag each part with its plugin, so the consolidated summary has one section per plugin.
        for r in report.get("results", []):
            r.setdefault("_plugin", name if RESULTS_DIR else "")
        reports.append(report)
    elif RESULTS_DIR and not os.path.isdir(shard_dir):
        notes.append((name, "not uploaded: the scan job stopped before its upload step"))
    else:
        notes.append((name, note))

if not reports:
    if all(note == "no skills" for _, note in notes) and not failed:
        write_summary("**Skill Security Scan:** No skills found in this repository — nothing to scan.")
    else:
        rows = [f"- `{n}`: {why}" for n, why in notes if why != "no skills" or n not in failed]
        rows += [f"- `{n}`: the scan job ended with an error; see its log" for n in sorted(set(failed)) if n not in {m for m, _ in notes} or dict(notes).get(n) == "no skills"]
        write_summary("❌ **Skill Security Scan: no results**\n\n" + "\n".join(rows))
    sys.exit(0)

data = merge(reports)

summary = data.get("summary", {})
results = sorted(
    data.get("results", []),
    key=lambda r: (SEV_ORDER.get(r.get("max_severity", "INFO"), 99), r.get("skill_name", "")),
)

MODE_LABELS = {
    "simple":     "simple (static + behavioral)",
    # The model of each tier is set in the scanner workflows and printed in the scan job log.
    "advanced-1": "advanced-1 (AI analysis + VirusTotal)",
    "advanced-2": "advanced-2 (AI analysis + VirusTotal)",
}
mode_label    = MODE_LABELS.get(SCAN_MODE, SCAN_MODE)
artifact_url  = f"https://github.com/{REPO}/actions/runs/{RUN_ID}"
if RESULTS_DIR:
    full_report = f"[`skill-scan-{SCAN_MODE}-*-results-{RUN_ID}`]({artifact_url}), one artifact per plugin"
else:
    full_report = f"[skill-scan-{SCAN_MODE}-{JOB_INDEX + '-' if JOB_INDEX else ''}results-{RUN_ID}]({artifact_url})"

scanned = summary.get("total_skills_scanned", "?")
total   = summary.get("total_findings", "?")
safe    = summary.get("safe_skills", "?")

lines = []

# ── Header (Markdown) ─────────────────────────────────────────────────────────
lines.append("## Skill Security Scan")
lines.append("")
lines.append(f"**Target:** [{REPO_URL}]({REPO_URL}) @ `{BRANCH}`")
lines.append(f"**Mode:** {mode_label}")
plugin_parts = sum(1 for r in results if r.get("plugin_level_files"))
if plugin_parts:
    safe_parts = sum(1 for r in results if r.get("is_safe"))
    lines.append(f"**Results:** {len(results) - plugin_parts} skills and {plugin_parts} plugin-level parts scanned"
                 f" — {total} findings ({safe_parts} safe)")
else:
    lines.append(f"**Results:** {scanned} skills scanned — {total} findings ({safe} safe)")


def high(r: dict) -> int:
    return sum(1 for f in r.get("findings", []) if f.get("severity") in ("CRITICAL", "HIGH"))


# The same split as the gate in the PR scan jobs: on a pull request each part carries
# changed_by_pr, and only critical or high findings in a changed part fail the check. Without
# it, all count. Only the PR workflow's consolidated summary gates; the scheduled scan reports.
if RESULTS_DIR:
    counted = sum(high(r) for r in results if r.get("changed_by_pr", True))
    ignored = sum(high(r) for r in results if r.get("changed_by_pr") is False)
    # A scan that ended in an error, or left no report, fails the check without a finding.
    failed += [n for n, why in notes if why != "no skills"]
    gate = f"**Gate:** {counted} critical or high {'finding' if counted == 1 else 'findings'}"
    if any("changed_by_pr" in r for r in results):
        gate += " in the parts this PR changes"
    gate += " — fails the check" if counted or failed else " — passes"
    if failed:
        gate += (". The scan of " + ", ".join(f"`{n}`" for n in sorted(set(failed)))
                 + " ended with an error, for example a SKILL.md it could not load or a file too large for"
                 " the AI analysis; see its job log")
    if ignored:
        gate += f". {ignored} more in parts this PR does not change: reported only"
    lines.append(gate)
lines.append(f"**Full report:** {full_report}")
if notes:
    lines.append("**Not in these totals:** " + "; ".join(f"`{n}` ({why})" for n, why in notes))
lines.append("")

# ── Per-part collapsible sections ─────────────────────────────────────────────
# <details>/<summary> are used here because GitHub-Flavored Markdown has no
# collapsible block syntax — HTML is unavoidable for this feature.
SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]


def tally(parts: list) -> dict:
    """Findings per severity across the given parts."""
    counts = {}
    for r in parts:
        for finding in r.get("findings", []):
            sev = finding.get("severity", "INFO")
            counts[sev] = counts.get(sev, 0) + 1
    return counts


def tally_row(parts: list) -> str:
    counts = tally(parts)
    return ", ".join(f"{counts.get(s, 0)} {s.capitalize()}" for s in SEVERITIES)


def part_lines(r: dict) -> list:
    """One collapsible section: a skill folder, or a plugin's files outside its skill folders."""
    out = []
    skill_path = r.get("skill_path", "")
    findings   = r.get("findings", [])

    # The annotation step has already rewritten runner paths to GitHub URLs of the form
    # {REPO_URL}/tree/{SCANNED_SHA}/{relative/path}. Strip that prefix to get the
    # display path; use the annotated value directly as the href.
    url_prefix = f"{REPO_URL}/tree/{SCANNED_SHA}/"
    if skill_path.startswith(url_prefix):
        rel_path  = skill_path[len(url_prefix):]
        skill_url = skill_path
    elif skill_path == url_prefix.rstrip("/"):
        # The repository root, for a repository that is itself one plugin (PLUGIN_ROOT ".").
        rel_path  = "."
        skill_url = skill_path
    else:
        rel_path  = ""
        skill_url = REPO_URL
    display_path = rel_path if rel_path else REPO_URL
    # The plugin's files outside its skill folders, scanned as one unit and mapped to the plugin
    # directory by the scan job.
    kind = " (plugin-level files)" if r.get("plugin_level_files") else ""
    if "changed_by_pr" in r:
        kind += " · changed by this PR" if r["changed_by_pr"] else " · not changed by this PR: reported only"

    # Severity tally for this part
    counts = tally([r])
    sev_cells = "".join(
        f"<td>{SEV_EMOJI[s]} <strong>{s}</strong>: {counts.get(s, 0)}</td>"
        for s in SEVERITIES
    )

    # Mini HTML table used as the <summary> label so the row shows status + severity counts.
    status = "✅" if r.get("is_safe") else "❌"
    mini_table = (
        f"<table>"
        f'<tr><td colspan="5">{status} <a href="{skill_url}" target="_blank"><code>{display_path}</code></a>{kind}</td></tr>'
        f"<tr>{sev_cells}</tr>"
        f"</table>"
    )

    out.append("<details>")
    out.append(f"<summary>{mini_table}</summary>")
    out.append("")
    if findings:
        out.append("| Severity | Rule | Title | File |")
        out.append("|---|---|---|---|")
        for finding in sorted(findings, key=lambda x: SEV_ORDER.get(x.get("severity", "INFO"), 99)):
            fsev  = finding.get("severity", "")
            fpath = finding.get("file_path") or ""
            if r.get("plugin_level_files") and fpath == "SKILL.md":
                # The plugin-level package's SKILL.md is generated by the scan job: no file to link.
                flink = "`SKILL.md` (generated by the scan, not a file of the plugin)"
            elif fpath.startswith(url_prefix):
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
            title = finding.get("title", "")
            if (finding.get("metadata") or {}).get("meta_false_positive"):
                # A deterministic finding the AI review dismissed: the gate still counts it.
                title += " (the AI review called it a likely false positive; it still counts)"
            out.append(
                f"| {SEV_EMOJI.get(fsev, '')} {fsev}"
                f" | `{finding.get('rule_id', '')}`"
                f" | {title}"
                f" | {flink} |"
            )
        out.append("")
    # Every file the part was scanned with, recorded by the scan job, so a part without
    # findings still shows what it covered.
    files = r.get("scanned_files") or []
    if files:
        out.append(f"**{len(files)} {'file' if len(files) == 1 else 'files'} scanned:**")
        out.append("")
        for f in files:
            out.append(f"- [`{f}`]({skill_url}/{quote(f)})" if skill_url != REPO_URL else f"- `{f}`")
        out.append("")
    out.append("</details>")
    out.append("")
    return out


groups = {}
for r in results:
    groups.setdefault(r.get("_plugin", ""), []).append(r)

if list(groups) == [""]:
    # One report with no plugins (the scheduled scan): all parts under one collapsible block.
    lines.append("<details>")
    lines.append(
        f"<summary>"
        f"<strong>{scanned} skills scanned</strong><br>"
        f"{safe} safe / {total} findings ({tally_row(results)})"
        f"</summary>"
    )
    lines.append("")
    for r in results:
        lines.extend(part_lines(r))
    lines.append("</details>")
    lines.append("")
else:
    # The pull request scan: one section per plugin, with its skills and plugin-level files.
    for plugin in sorted(groups):
        parts = groups[plugin]
        lines.append(f"### `{plugin}`")
        lines.append("")
        lines.append(f"{len(parts)} {'part' if len(parts) == 1 else 'parts'} scanned — {tally_row(parts)}")
        lines.append("")
        for r in parts:
            lines.extend(part_lines(r))

write_summary("\n".join(lines))
