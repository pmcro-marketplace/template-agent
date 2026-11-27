"""Shared helpers for template-authoring scripts. Standard library only."""
import hashlib, json, re
from pathlib import Path

VAR = re.compile(r"\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}")
MARKER = "TODO(template-authoring)"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pascal(s):
    return "".join(w[:1].upper() + w[1:] for w in re.split(r"[-_ .]+", s) if w)


def render(text, vars):
    """Return (rendered, sorted missing variable names). Missing vars are left intact."""
    missing = set()

    def sub(m):
        k = m.group(1)
        if k in vars and vars[k] not in (None, ""):
            return str(vars[k])
        missing.add(k)
        return m.group(0)

    return VAR.sub(sub, text), sorted(missing)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def skill_root():
    return Path(__file__).resolve().parent.parent
