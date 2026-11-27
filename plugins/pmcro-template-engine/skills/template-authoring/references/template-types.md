# Template types

Read this when choosing a type, supplying variables, or adding a type.

## Contents
- skills-marketplace
- pmcro-marketplace
- agent-maf
- Host projections
- Adding a type

## skills-marketplace
Stages: foundation, skills, agents, commands, plugins, integration, tests. One plugin `plugins/<name>/` holding N skills (each `SKILL.md`, `scripts/run.py`, `references/guide.md`, `assets/example.template.md`), optional agents and one command per skill, `.claude-plugin/marketplace.json`. Test: every skill's `run.py --selfcheck`. Inputs: `--skills`, `--agents`, `--hosts`.

## pmcro-marketplace
Extends skills-marketplace. Adds the phase skills copied verbatim from `--source` (default phases goal, startup, orchestrate, plan, make, check, reflect; override with `--phases`), a command per phase and an orchestrator agent. Requires `--source`: a directory containing one folder per phase skill. Missing source fails at resolve.

## agent-maf
Stages: foundation, runtime, skills, agents, integration, tests. A .NET Microsoft Agent Framework agent over an Ollama `IChatClient`: `src/<Name>.Agent` (csproj, factory, audit middleware, Program, appsettings), a smoke project, skills, an agent definition, docs. Variables: `MAF_VERSION` and `OLLAMASHARP_VERSION` are required and never defaulted; `TFM`, `OLLAMA_ENDPOINT`, `OLLAMA_MODEL` have editable defaults. Tests: skill selfchecks, `dotnet build`, `dotnet run` of the smoke project (blocked where `dotnet` is absent). The MAF API surface changes between releases; the build gate is what decides whether the generated code matches the pinned version.

## Host projections
`--hosts claude-code,copilot,agents-md` adds `CLAUDE.md`, `.github/copilot-instructions.md`, `AGENTS.md` in the integration stage.

## Adding a type
Add `assets/specs/<type>.json` (stages, entries with `stage`, `template` or `copy_dir`, optional `foreach`, `when`, `requires`, and `tests`), add any new templates under `assets/templates/`, run `resolve_manifest.py` and a full generate/validate cycle on a scratch directory, and only then rely on it. `extends` reuses another spec's entries.
