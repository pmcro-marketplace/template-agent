# Generation lifecycle

Read this when running or resuming a generation.

## Contents
- Steps
- Resuming
- Blockers
- Extending an existing project

## Steps
1. Discover: inspect target, sources, existing definitions. Read-only.
2. Resolve: manifest with every file, stage, dependency, status.
3. Initialize: foundation stage (README, ignore rules, `.pmcro/` state). Only what later steps need.
4. Generate: one stage per run, dependency order inside the stage (`requires`).
5. Integrate: manifests, registration, host adapters.
6. Validate: per stage, before the next stage starts.
7. Reflect: `inventory.py` report, trail frames, next increment.
8. Repeat until all stages verified and tests pass.

## Resuming
The manifest is the state. `generate.py` picks the first stage not fully verified. Verified files are never regenerated. Edited generated files show as drift in `validate.py`; decide whether to keep the edit (re-resolve so it is `existing`) or regenerate with `--overwrite <path>`.

## Blockers
A blocked entry carries its reason (unresolved variable, missing tool, missing source). Preserve what is verified, report the exact blocker, and give the one command that resumes, for example `generate.py --manifest m.json --set MAF_VERSION=<version>`.

## Extending an existing project
Resolve against the non-empty root. Files already present become `existing` and are protected; only missing pieces are planned. Gates still apply to the generated additions.
