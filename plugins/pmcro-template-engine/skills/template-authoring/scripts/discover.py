#!/usr/bin/env python3
"""Discover: inspect a target directory before any generation. Read-only.

Usage: discover.py <target-dir> [--source DIR ...]
Prints JSON: existence, emptiness, detected project shape, existing skills/plugins/csproj,
and whether each --source reference resolves. Never writes anything.
"""
import argparse, json, sys
from pathlib import Path

IGNORE = {".git", "node_modules", "bin", "obj", "__pycache__"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("--source", action="append", default=[])
    a = ap.parse_args()
    t = Path(a.target)
    files = []
    if t.is_dir():
        for p in t.rglob("*"):
            if p.is_file() and not (set(p.relative_to(t).parts) & IGNORE):
                files.append(p.relative_to(t).as_posix())
    shape = []
    if (t / ".claude-plugin/marketplace.json").exists():
        shape.append("marketplace")
    if any(f.endswith(".csproj") for f in files):
        shape.append("dotnet")
    if any(f.endswith("SKILL.md") for f in files):
        shape.append("skills")
    out = {
        "target": str(t),
        "exists": t.exists(),
        "empty": t.exists() and not files,
        "file_count": len(files),
        "shape": shape,
        "skills": sorted({Path(f).parent.name for f in files if f.endswith("SKILL.md")}),
        "csproj": [f for f in files if f.endswith(".csproj")],
        "has_pmcro_state": (t / ".pmcro").exists(),
        "sources": {s: Path(s).exists() for s in a.source},
        "mode": "greenfield" if not files else "extend (existing files are never overwritten)",
    }
    print(json.dumps(out, indent=2))
    return 0 if all(out["sources"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
