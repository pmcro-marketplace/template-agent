# Completion contract

Read this when deciding whether generation is done, or when a validation fails.

## Contents
- Entry statuses
- Per-file checks
- Stage gates
- Tests
- Verdict

## Entry statuses
`pending` planned, not written. `blocked` cannot be written (reason recorded). `generated` written, not yet validated. `verified` written and passed every check. `existing` present before generation, protected, only its existence is checked.

## Per-file checks
Exists; sha256 unchanged since generation (else drift); no `TODO(template-authoring)` marker; no leftover `{{placeholder}}` in rendered files; `.json` parses; `.py` compiles; `SKILL.md` frontmatter has `name` equal to its folder and a `description`; every backticked `references/`, `scripts/` or `assets/` path in `SKILL.md` resolves.

## Stage gates
Every generated skill has non-empty `scripts/`, `references/`, `assets/`. Every `plugin.json` has a name. In the integration stage every plugin is registered in `.claude-plugin/marketplace.json` and every registered source has a `plugin.json`. A stage passes only if all its entries are verified or existing and its gates pass.

## Tests
Each declared test runs only if its tool exists; otherwise `blocked` with the reason. Output is stored as evidence with a sha256. Only `passed` counts.

## Verdict
`inventory.py` reports COMPLETE only if no gap exists: no missing file, no entry short of verified/existing, no failed gate, no test that is not `passed`. It also lists files present but not in the manifest, for review.
