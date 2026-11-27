#!/usr/bin/env python3
"""Validate: verify an increment (or everything) before generation continues, and run tests.

Usage: validate.py --manifest M.json [--stage S] [--run-tests] [--evidence-dir DIR]
Per file: exists, sha unchanged, no TODO(template-authoring) marker, no leftover {{var}}, JSON parses,
Python compiles, SKILL.md frontmatter (name == folder, description present), declared `references/`,
`scripts/`, `assets/` paths resolve. Per stage gates: every generated skill has populated scripts/,
references/, assets/; plugin.json is registered in marketplace.json; marketplace sources exist.
Tests (--run-tests, stage `tests`): a missing tool is BLOCKED, never passed; output is saved as evidence.
Exit: 0 all pass, 1 failures, 3 blocked only.
"""
import argparse, json, re, shutil, subprocess, sys
from pathlib import Path
from _common import MARKER, VAR, sha, load, save

DONE = {"verified", "existing"}
REF = re.compile(r"`((?:references|scripts|assets)/[^`\s<>*]+)`")


def split_front(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    fm = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm


def check_entry(root, e):
    errs, p = [], root / e["path"]
    if not p.exists():
        return ["missing file"]
    if e["status"] == "existing":
        return []
    if e.get("sha256") and sha(p) != e["sha256"]:
        errs.append("content changed since generation (drift)")
    text = p.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        errs.append(f"contains unresolved marker {MARKER}")
    if "template" in e and VAR.search(text):
        errs.append("leftover {{placeholder}}")
    if p.suffix == ".json":
        try:
            json.loads(text)
        except Exception as x:
            errs.append(f"invalid JSON: {x}")
    if p.suffix == ".py":
        try:
            compile(text, str(p), "exec")
        except Exception as x:
            errs.append(f"python does not compile: {x}")
    if p.name == "SKILL.md":
        fm = split_front(text)
        if not fm:
            errs.append("SKILL.md has no valid frontmatter")
        else:
            if fm.get("name") != p.parent.name:
                errs.append(f"frontmatter name '{fm.get('name')}' != folder '{p.parent.name}'")
            if not fm.get("description"):
                errs.append("frontmatter description missing")
        for ref in REF.findall(text):
            if not (p.parent / ref).exists():
                errs.append(f"declared path does not resolve: {ref}")
    return errs


def stage_gates(root, m, stage):
    fails, es = [], [e for e in m["entries"] if e["stage"] == stage]
    for e in es:
        pp = Path(e["path"])
        if pp.name == "SKILL.md":
            for sub in ("scripts", "references", "assets"):
                d = root / pp.parent / sub
                if not (d.is_dir() and any(f.is_file() and f.stat().st_size > 0 for f in d.rglob("*"))):
                    fails.append(f"{pp.parent}: {sub}/ missing or empty")
        if pp.name == "plugin.json" and (root / e["path"]).exists():
            try:
                if not json.loads((root / e["path"]).read_text(encoding="utf-8")).get("name"):
                    fails.append(f"{e['path']}: no name")
            except Exception as x:
                fails.append(f"{e['path']}: {x}")
        if pp.as_posix() == ".claude-plugin/marketplace.json" and (root / e["path"]).exists():
            # Integration gate: every plugin in the manifest is registered, every registered source is real.
            try:
                srcs = [str(x.get("source", "")).lstrip("./").rstrip("/") for x in
                        json.loads((root / e["path"]).read_text(encoding="utf-8")).get("plugins", [])]
                for x in m["entries"]:
                    if Path(x["path"]).name == "plugin.json":
                        pdir = Path(x["path"]).parent.parent.as_posix()
                        if pdir not in srcs:
                            fails.append(f"plugin '{pdir}' not registered in marketplace.json")
                for src in srcs:
                    if not (root / src / ".claude-plugin/plugin.json").exists():
                        fails.append(f"marketplace source has no plugin.json: {src}")
            except Exception as x:
                fails.append(f"marketplace.json: {x}")
    return fails


def run_tests(root, m, ev_dir):
    out, blocked, failed = [], False, False
    for t in m["tests"]:
        tool = t["cmd"][0]
        if not shutil.which(tool):
            t.update(status="blocked", reason=f"required tool '{tool}' not installed here")
            blocked = True
        else:
            try:
                r = subprocess.run(t["cmd"], cwd=root / t.get("cwd", ""), capture_output=True, text=True, timeout=600)
                log = ev_dir / f"{t['id']}.log"
                log.write_text((r.stdout or "") + (r.stderr or ""), encoding="utf-8")
                t.update(status="passed" if r.returncode == 0 else "failed", exit_code=r.returncode,
                         evidence=str(log.relative_to(root)), evidence_sha256=sha(log), reason=None)
                failed |= r.returncode != 0
            except Exception as x:
                t.update(status="failed", reason=str(x)); failed = True
        out.append({"id": t["id"], "status": t["status"], "reason": t.get("reason")})
    return out, blocked, failed


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--stage")
    ap.add_argument("--run-tests", action="store_true")
    ap.add_argument("--evidence-dir")
    a = ap.parse_args()
    m = load(a.manifest)
    root = Path(m["root"])
    stages = [a.stage] if a.stage else m["stages"]
    problems, report = [], {}
    for s in stages:
        res = {"verified": [], "failed": {}, "blocked": [], "pending": []}
        for e in [x for x in m["entries"] if x["stage"] == s]:
            if e["status"] in ("pending",):
                res["pending"].append(e["path"]); continue
            if e["status"] == "blocked":
                res["blocked"].append({e["path"]: e["reason"]}); continue
            errs = check_entry(root, e)
            if errs:
                res["failed"][e["path"]] = errs
                if e["status"] == "verified":
                    e["status"] = "generated"
            else:
                if e["status"] == "generated":
                    e["status"] = "verified"
                res["verified"].append(e["path"])
        gf = stage_gates(root, m, s)
        ok = not (res["failed"] or res["blocked"] or res["pending"] or gf)
        m["gates"][s] = {"passed": ok, "failures": gf}
        res["gate_failures"] = gf
        res["stage_passed"] = ok
        report[s] = res
        problems.append(res)
    tests, tblocked, tfailed = [], False, False
    if a.run_tests:
        ev = Path(a.evidence_dir) if a.evidence_dir else root / ".pmcro/evidence"
        ev.mkdir(parents=True, exist_ok=True)
        tests, tblocked, tfailed = run_tests(root, m, ev)
    save(a.manifest, m)
    print(json.dumps({"stages": report, "tests": tests}, indent=2))
    failed = any(p["failed"] or p["gate_failures"] for p in problems) or tfailed
    blocked = any(p["blocked"] or p["pending"] for p in problems) or tblocked
    return 1 if failed else (3 if blocked else 0)


if __name__ == "__main__":
    sys.exit(main())
