#!/usr/bin/env python3
"""Resolve: build the file-level generation manifest for a template type. Writes only the manifest.

Usage:
  resolve_manifest.py --type TYPE --name NAME --root DIR --out manifest.json
      [--skills a,b] [--agents x,y] [--hosts claude-code,copilot,agents-md]
      [--phases plan,make,...] [--source DIR] [--set KEY=VALUE ...] [--skill-desc skill=text ...]

TYPE: skills-marketplace | pmcro-marketplace | agent-maf   (specs in assets/specs/)
Existing files under --root become status `existing` and are never overwritten (migration/extend).
Entries needing an unsupplied variable (for example a package version) become `blocked`, never guessed.
"""
import argparse, json, sys, datetime
from pathlib import Path
from _common import render, pascal, sha, save, skill_root

LISTS = {"skills": "skill", "agents": "agent", "hosts": "host", "phases": "phase"}
DEFAULT_PHASES = "goal,startup,orchestrate,plan,make,check,reflect"


def load_spec(t):
    p = skill_root() / "assets/specs" / f"{t}.json"
    if not p.exists():
        sys.exit(f"ERROR: unknown template type '{t}' (no {p})")
    spec = json.loads(p.read_text(encoding="utf-8"))
    if spec.get("extends"):
        base = load_spec(spec["extends"])
        spec["entries"] = base["entries"] + spec["entries"]
        spec["tests"] = base.get("tests", []) + spec.get("tests", [])
        spec["defaults"] = {**base.get("defaults", {}), **spec.get("defaults", {})}
        spec["stages"] = spec.get("stages") or base["stages"]
    return spec


def when_ok(when, lists):
    return all(v in lists.get(k, []) for k, v in (when or {}).items())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--type", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    for k in LISTS:
        ap.add_argument(f"--{k}", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--skill-desc", action="append", default=[])
    a = ap.parse_args()

    spec = load_spec(a.type)
    root = Path(a.root)
    lists = {k: [x for x in getattr(a, k).split(",") if x] for k in LISTS}
    if a.type == "pmcro-marketplace" and not lists["phases"]:
        lists["phases"] = DEFAULT_PHASES.split(",")
    if not lists["skills"] and spec.get("default_skills"):
        lists["skills"] = spec["default_skills"]
    base = {**spec.get("defaults", {}), "name": a.name, "Name": pascal(a.name), "source": a.source,
            "agent": a.name, "Agent": pascal(a.name)}
    for kv in a.set:
        k, _, v = kv.partition("=")
        base[k] = v
    descs = dict(kv.partition("=")[::2] for kv in a.skill_desc)

    entries, seen = [], set()

    def add(path, stage, ev, template=None, copy_from=None, requires=()):
        path, miss = render(path, ev)
        if miss:
            sys.exit(f"ERROR: cannot plan path '{path}': missing {miss}")
        if path in seen:
            return
        seen.add(path)
        e = {"path": path, "stage": stage, "status": "pending", "sha256": None, "reason": None,
             "requires": [render(r, ev)[0] for r in requires], "vars": ev}
        if template:
            e["template"] = template
            text = (skill_root() / "assets/templates" / template).read_text(encoding="utf-8")
            _, miss = render(text, ev)
            if miss:
                e["status"], e["reason"] = "blocked", f"unresolved variables: {miss}"
        if copy_from:
            e["copy_from"] = copy_from
        fp = root / path
        if fp.exists():
            e["status"], e["reason"], e["sha256"] = "existing", "present before generation; not overwritten", sha(fp)
        entries.append(e)

    for se in spec["entries"]:
        if not when_ok(se.get("when"), lists):
            continue
        variants = [dict(base)]
        key = se.get("foreach")
        if key:
            variants = []
            for item in lists[key]:
                v = dict(base)
                single = LISTS[key]
                v[single], v[pascal(single)] = item, pascal(item)
                v[f"{single}_desc"] = descs.get(item) or (
                    f"Handle {item} work for {a.name}. Use whenever the user mentions {item} "
                    f"or asks for {item} output in the {a.name} project.")
                variants.append(v)
        for ev in variants:
            if se.get("copy_dir"):
                src, _ = render(se["copy_dir"], ev)
                dest, _ = render(se["dest"], ev)
                sp = Path(src)
                if not sp.is_dir():
                    sys.exit(f"ERROR: source reference not found: {src}")
                for f in sorted(x for x in sp.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
                    add(f"{dest}/{f.relative_to(sp).as_posix()}", se["stage"], ev,
                        copy_from=str(f), requires=se.get("requires", []))
            else:
                add(se["path"], se["stage"], ev, template=se["template"], requires=se.get("requires", []))

    tests = []
    for t in spec.get("tests", []):
        t = {**t, "status": "not_run"}
        t["cmd"] = [render(c, base)[0] for c in t["cmd"]]
        tests.append(t)
    man = {"schema": 1, "type": a.type, "name": a.name, "root": str(root),
           "created": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "vars": base, "lists": lists, "stages": spec["stages"], "gates": {}, "tests": tests,
           "entries": entries}
    save(a.out, man)
    by = {}
    for e in entries:
        by[e["status"]] = by.get(e["status"], 0) + 1
    print(json.dumps({"manifest": a.out, "entries": len(entries), "by_status": by,
                      "stages": spec["stages"], "tests": len(tests)}, indent=2))
    blocked = [e["path"] for e in entries if e["status"] == "blocked"]
    if blocked:
        print("BLOCKED (supply variables with generate.py --set KEY=VALUE):", *blocked, sep="\n  ", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
