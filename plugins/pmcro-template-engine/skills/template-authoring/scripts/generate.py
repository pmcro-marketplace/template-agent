#!/usr/bin/env python3
"""Generate: write ONE increment (a stage) of the manifest, in dependency order.

Usage: generate.py --manifest M.json [--stage S] [--set KEY=VALUE ...] [--overwrite PATH ...]
                   [--allow-unvalidated] [--dry-run]

Default stage = first stage not fully verified. Refuses to continue past a stage with generated but
unvalidated files (run validate.py first) unless --allow-unvalidated. Existing files are never
overwritten unless the exact path is listed in --overwrite (explicit authorization).
Exit: 0 increment written, 2 refused (validate first / gate failing), 3 nothing generatable (blocked/waiting).
"""
import argparse, json, shutil, sys
from pathlib import Path
from _common import render, sha, load, save, skill_root

DONE = {"verified", "existing"}


def stage_incomplete(m, s):
    es = [e for e in m["entries"] if e["stage"] == s]
    gate = m["gates"].get(s, {})
    return any(e["status"] not in DONE for e in es) or (es and gate.get("passed") is not True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--stage")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--overwrite", action="append", default=[])
    ap.add_argument("--allow-unvalidated", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    m = load(a.manifest)
    root = Path(m["root"])
    for kv in a.set:
        k, _, v = kv.partition("=")
        m["vars"][k] = v
        for e in m["entries"]:
            e["vars"][k] = v
    stage = a.stage or next((s for s in m["stages"] if stage_incomplete(m, s)), None)
    if not stage:
        print(json.dumps({"stage": None, "result": "all stages verified; run inventory.py"}))
        return 0
    es = [e for e in m["entries"] if e["stage"] == stage]
    unval = [e["path"] for e in es if e["status"] == "generated"]
    if unval and not a.allow_unvalidated and not any(e["status"] in ("pending", "blocked") for e in es):
        print(json.dumps({"stage": stage, "refused": "generated but unvalidated; run validate.py --stage "
                          + stage, "files": unval}, indent=2))
        return 2
    if not unval and not any(e["status"] in ("pending", "blocked") for e in es):
        print(json.dumps({"stage": stage, "refused": "files verified but stage gate not passing; run validate.py "
                          "--stage " + stage + " and fix the listed gate failures",
                          "gate": m["gates"].get(stage)}, indent=2))
        return 2
    by_path = {e["path"]: e for e in m["entries"]}
    wrote, skipped, blocked, waiting = [], [], [], []
    for e in es:
        if e["status"] not in ("pending", "blocked"):
            continue
        waits = [r for r in e["requires"] if r in by_path and by_path[r]["status"] not in DONE | {"generated"}]
        if waits:
            waiting.append({"path": e["path"], "waiting_on": waits})
            continue
        dst = root / e["path"]
        if dst.exists() and e["path"] not in a.overwrite:
            e["status"], e["reason"], e["sha256"] = "existing", "present; not overwritten", sha(dst)
            skipped.append(e["path"])
            continue
        if "copy_from" in e:
            if a.dry_run:
                wrote.append(e["path"]); continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(e["copy_from"], dst)
        else:
            text = (skill_root() / "assets/templates" / e["template"]).read_text(encoding="utf-8")
            out, miss = render(text, e["vars"])
            if miss:
                e["status"], e["reason"] = "blocked", f"unresolved variables: {miss}"
                blocked.append({"path": e["path"], "missing": miss})
                continue
            if a.dry_run:
                wrote.append(e["path"]); continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(out, encoding="utf-8")
        if not a.dry_run:
            e["status"], e["reason"], e["sha256"] = "generated", None, sha(dst)
        wrote.append(e["path"])
    if not a.dry_run:
        m["gates"].pop(stage, None)
        save(a.manifest, m)
    print(json.dumps({"stage": stage, "wrote": wrote, "left_existing": skipped, "blocked": blocked,
                      "waiting": waiting, "next": f"validate.py --manifest {a.manifest} --stage {stage}"}, indent=2))
    return 0 if wrote else 3


if __name__ == "__main__":
    sys.exit(main())
