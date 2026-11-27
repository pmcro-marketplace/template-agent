---
name: template-authoring
description: Generate an entire production-ready project directory incrementally from an empty root, then verify every artifact. Builds complete Microsoft Agent Framework agent projects, Agent-Skills marketplaces and plugin packages, and PMCR-O orchestration marketplaces, and extends or migrates existing projects without overwriting them. Use whenever the user wants to scaffold, generate, bootstrap, template, migrate or extend a PMCR-O agent, skill, plugin, command, workflow or marketplace, or asks for a full project repository rather than a single file, even if they only say "init" or "set up a new project".
license: MIT
---

# template-authoring

One increment is not the deliverable. `/init` is only the first step: this skill carries a project from an empty root to a complete, verified repository, one dependency-ordered increment at a time, and refuses to call it done until every artifact is accounted for.

## Inputs

Project name, template type (`skills-marketplace`, `pmcro-marketplace`, `agent-maf`), source references (a directory of existing skills to copy from, when the type needs one), and constraints (skills, agents, hosts, package versions). Never guess a version, a path or a source; a missing value makes that artifact `blocked` and is reported.

## Workflow

All scripts live in `scripts/`; each has `--help`. State lives in one manifest file, so any run can resume.

1. **Discover.** `python scripts/discover.py <target> --source <dir>`. Read-only. Reports whether the target is empty, what shape an existing project has, and whether each source resolves.
2. **Resolve.** `python scripts/resolve_manifest.py --type T --name N --root R --out manifest.json [--skills ..] [--agents ..] [--hosts ..] [--source ..] [--set K=V]`. Writes the file-level manifest: every file, its stage, its dependencies, its status. Existing files become `existing` and are protected.
3. **Initialize and generate.** `python scripts/generate.py --manifest manifest.json`. Writes exactly one increment (the first stage not fully verified), in dependency order. Stages run foundation first, then the type's own order (see `references/template-types.md`).
4. **Validate before continuing.** `python scripts/validate.py --manifest manifest.json --stage <stage>`. `generate.py` refuses to move past a stage that is generated but unvalidated.
5. **Integrate.** The `integration` stage connects plugin manifests, marketplace registration and host adapters; its gate checks every plugin is registered and every registered source exists.
6. **Repeat** steps 3 and 4 until `generate.py` reports all stages verified.
7. **Test.** `python scripts/validate.py --manifest manifest.json --stage tests --run-tests`. A test whose tool is not installed is `blocked`, never passed. Output is saved under `.pmcro/evidence/`.
8. **Reflect and report.** `python scripts/inventory.py --manifest manifest.json` writes `.pmcro/verification-report.md` with the verdict, every gap, and a resumable next step. Record phases in a trail with `scripts/trail.py`.

## Completion contract

Complete means: every manifest entry is `verified` or protected `existing`; every generated skill has `SKILL.md` plus populated `scripts/`, `references/`, `assets/`; every plugin is registered and its manifest valid; every declared reference resolves; every test ran and passed; the inventory matches the manifest. `inventory.py` is the only thing that may say COMPLETE, and it lists anything missing, skipped, blocked or unverified instead of hiding it. Read `references/completion-contract.md` for the exact checks.

## Rules

- **Never overwrite** an existing file unless the person names that exact path (`generate.py --overwrite PATH`). Resume from verified state; do not regenerate it.
- **Blocked is a result.** If a variable, tool, source or approval is missing, preserve verified state, state the exact blocker, and give the next command. Do not fill the gap with a guess.
- **Templates are scaffolds, not finished behaviour.** Generated skill runners are minimal and working; real domain logic is authored afterwards, and `validate.py` fails any file still carrying a `TODO(template-authoring)` marker.
- **Gate mutations.** Pushes, installs, paid calls, deletions and permission changes need explicit approval.
- Generated .NET code targets the package versions the person supplies; the `dotnet build` and smoke gates decide whether that combination works. If `dotnet` is not installed, those gates are `blocked`, not green.

## Additional resources

- `references/lifecycle.md`: the eight-step lifecycle, resume and blocker handling
- `references/template-types.md`: stages, entries, variables and tests per template type; how to add a type
- `references/completion-contract.md`: exact validation checks and statuses
- `assets/specs/`: one JSON spec per template type; `assets/templates/`: the file templates they render
- `assets/manifest.template.json`, `assets/verification-report.template.md`: shapes of the manifest and the final report
- `eval.yaml`: behavioural checks for this skill


## Script reference

Scripts are not loaded into context. An agent runs one only when a step needs it, and you can run the same command by hand from this skill's folder.

| Script | Purpose | Manual run |
|---|---|---|
| `scripts/_common.py` | Shared helpers imported by the other template-authoring scripts (standard library only). Not run directly. | `(imported, not run directly)` |
