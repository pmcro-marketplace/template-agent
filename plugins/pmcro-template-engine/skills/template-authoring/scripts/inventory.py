#!/usr/bin/env python3
"""Inventory: compare the actual tree to the generation manifest and write the final verification report.

Usage: inventory.py --manifest M.json [--out REPORT.md]
Verdict is COMPLETE only when every entry is verified/existing, every stage gate passed, and every
declared test passed. Anything missing, blocked, pending, unverified or not run is listed explicitly,
with a resumable next step. Exit 0 COMPLETE, 1 INCOMPLETE.
"""
import argparse, sys, datetime
from pathlib import Path
from _common import load

IGNORE = {".git", "bin", "obj", "node_modules", "__pycache__", "evidence"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    m = load(a.manifest)
    root = Path(m["root"])
    gaps, counts = [], {}
    for e in m["entries"]:
        counts[e["status"]] = counts.get(e["status"], 0) + 1
        if not (root / e["path"]).exists():
            gaps.append(f"MISSING  {e['path']} ({e['status']})")
        elif e["status"] not in ("verified", "existing"):
            gaps.append(f"{e['status'].upper():8} {e['path']}" + (f" - {e['reason']}" if e.get("reason") else ""))
    for s in m["stages"]:
        if any(x["stage"] == s for x in m["entries"]) and not m["gates"].get(s, {}).get("passed"):
            gaps.append(f"GATE     stage '{s}' not passed: {m['gates'].get(s, {}).get('failures') or 'not run'}")
    for t in m["tests"]:
        if t["status"] != "passed":
            gaps.append(f"TEST     {t['id']}: {t['status']}" + (f" - {t.get('reason')}" if t.get("reason") else ""))
    planned = {e["path"] for e in m["entries"]}
    extra = sorted(p.relative_to(root).as_posix() for p in root.rglob("*")
                   if p.is_file() and not (set(p.relative_to(root).parts) & IGNORE)
                   and p.relative_to(root).as_posix() not in planned)
    verdict = "COMPLETE" if not gaps else "INCOMPLETE"
    lines = [f"# Verification report: {m['name']} ({m['type']})", "",
             f"Generated {datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}",
             f"Verdict: **{verdict}**", "", "## Artifact inventory",
             f"Planned entries: {len(m['entries'])}; by status: {counts}", "",
             "## Gaps (never reported as complete)"] + ([f"- {g}" for g in gaps] or ["- none"]) + [
             "", "## Tests"] + ([f"- {t['id']}: {t['status']} {t.get('evidence', '')}" for t in m["tests"]] or ["- none declared"]) + [
             "", "## Present but not in manifest"] + ([f"- {x}" for x in extra] or ["- none"]) + ["", "## Next step"]
    if gaps:
        lines.append("Resume with `generate.py --manifest <m>` (next incomplete stage), then `validate.py`. "
                     "Blocked entries need the named variables or tools; nothing above is skipped silently.")
    else:
        lines.append("None. Every artifact accounted for and verified.")
    text = "\n".join(lines) + "\n"
    out = Path(a.out) if a.out else root / ".pmcro/verification-report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
