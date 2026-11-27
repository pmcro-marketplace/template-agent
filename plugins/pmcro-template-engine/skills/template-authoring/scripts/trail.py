#!/usr/bin/env python3
"""Append and verify PMCR-O trail frames (JSONL, hash-linked). Standard library only.

Usage:
  trail.py append --file TRAIL.jsonl --trail-id ID --phase PHASE --status STATUS
                  [--binding B] [--command C] [--result R] [--verification V]
                  [--evidence PATH ...] [--reason TEXT]
  trail.py verify --file TRAIL.jsonl

PHASE:  orchestrate | plan | make | check | reflect
STATUS: INVOKED | NOT_INVOKED | BLOCKED | FAILED
VERIFICATION: PENDING | VERIFIED | FAILED | NOT_APPLICABLE (default PENDING)

Rules that keep the trail honest:
  INVOKED needs --command and --result (what actually ran and what came back).
  NOT_INVOKED / BLOCKED / FAILED need --reason.
  VERIFIED needs at least one --evidence file, which is hashed (sha256).
Each frame stores prev_hash (the previous frame's hash) so edits are detectable.
Do not put secrets in any field.
"""
import argparse, hashlib, json, sys, datetime
from pathlib import Path

PHASES = ["orchestrate", "plan", "make", "check", "reflect"]
STATUSES = {"INVOKED", "NOT_INVOKED", "BLOCKED", "FAILED"}
VERIFS = {"PENDING", "VERIFIED", "FAILED", "NOT_APPLICABLE"}


def frame_hash(frame):
    body = {k: v for k, v in frame.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_frames(path):
    p = Path(path)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cmd_append(a):
    errs = []
    if a.phase not in PHASES:
        errs.append(f"phase must be one of {PHASES}")
    if a.status not in STATUSES:
        errs.append(f"status must be one of {sorted(STATUSES)}")
    if a.verification not in VERIFS:
        errs.append(f"verification must be one of {sorted(VERIFS)}")
    if a.status == "INVOKED" and not (a.command and a.result):
        errs.append("INVOKED requires --command and --result")
    if a.status in {"NOT_INVOKED", "BLOCKED", "FAILED"} and not a.reason:
        errs.append(f"{a.status} requires --reason")
    if a.status != "INVOKED" and a.verification == "VERIFIED":
        errs.append("VERIFIED requires status INVOKED")
    evidence = []
    for e in a.evidence or []:
        if not Path(e).is_file():
            errs.append(f"evidence file not found: {e}")
        else:
            evidence.append({"path": e, "sha256": file_sha(e)})
    if a.verification == "VERIFIED" and not evidence:
        errs.append("VERIFIED requires at least one --evidence file")
    if errs:
        for e in errs:
            print("ERROR:", e, file=sys.stderr)
        return 1
    frames = read_frames(a.file)
    if frames and frames[0].get("trail_id") != a.trail_id:
        print("ERROR: trail_id differs from existing frames in this file", file=sys.stderr)
        return 1
    if frames:
        last = PHASES.index(frames[-1]["phase"])
        if PHASES.index(a.phase) < last and a.phase != "orchestrate":
            print(f"WARNING: phase '{a.phase}' follows '{frames[-1]['phase']}' (out of order); "
                  "record the correction loop in --reason", file=sys.stderr)
    frame = {
        "seq": len(frames) + 1,
        "trail_id": a.trail_id,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "phase": a.phase,
        "binding": a.binding or "unresolved",
        "invocation_status": a.status,
        "command_or_api": a.command,
        "result": a.result,
        "verification": a.verification,
        "evidence": evidence,
        "reason": a.reason,
        "prev_hash": frames[-1]["hash"] if frames else None,
    }
    frame["hash"] = frame_hash(frame)
    Path(a.file).parent.mkdir(parents=True, exist_ok=True)
    with open(a.file, "a", encoding="utf-8") as f:
        f.write(json.dumps(frame, sort_keys=True) + "\n")
    print(f"Appended frame {frame['seq']} ({a.phase}/{a.status}) hash={frame['hash'][:12]}")
    return 0


def cmd_verify(a):
    frames = read_frames(a.file)
    if not frames:
        print("ERROR: no frames", file=sys.stderr)
        return 1
    bad = 0
    prev = None
    for i, f in enumerate(frames, 1):
        if f.get("seq") != i:
            print(f"ERROR: frame {i}: seq is {f.get('seq')}"); bad += 1
        if f.get("prev_hash") != prev:
            print(f"ERROR: frame {i}: prev_hash does not match previous frame"); bad += 1
        if f.get("hash") != frame_hash(f):
            print(f"ERROR: frame {i}: content hash mismatch (frame was edited)"); bad += 1
        for e in f.get("evidence", []):
            p = Path(e["path"])
            if not p.is_file():
                print(f"WARNING: frame {i}: evidence missing: {e['path']}")
            elif file_sha(p) != e["sha256"]:
                print(f"ERROR: frame {i}: evidence changed: {e['path']}"); bad += 1
        prev = f.get("hash")
    print("Trail is intact." if not bad else f"{bad} problem(s) found.")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("append")
    p.add_argument("--file", required=True); p.add_argument("--trail-id", required=True)
    p.add_argument("--phase", required=True); p.add_argument("--status", required=True)
    p.add_argument("--binding"); p.add_argument("--command"); p.add_argument("--result")
    p.add_argument("--verification", default="PENDING"); p.add_argument("--evidence", action="append")
    p.add_argument("--reason")
    v = sub.add_parser("verify"); v.add_argument("--file", required=True)
    a = ap.parse_args()
    return cmd_append(a) if a.cmd == "append" else cmd_verify(a)


if __name__ == "__main__":
    sys.exit(main())
