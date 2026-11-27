from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
req=[root/'SKILL.md',root/'references'/'contract.md',root/'assets'/'request.json']
missing=[str(p) for p in req if not p.exists()]
if missing:
    print('FAIL: missing '+', '.join(missing)); sys.exit(1)
print('PASS: creator')
