---
name: creator
description: Create a new reusable generic template from a declarative request and acceptance contract.
---
# creator

## Purpose
Include variables, inputs, outputs, constraints, validation, and an example request.

## When to Use
Use this capability when it is the narrowest resolved skill for the current request.

## When Not to Use
Do not duplicate an existing validated capability, broaden scope silently, or claim execution without evidence.

## Inputs
A bounded request, resolved target identity, authorization context, and applicable evidence.

## Deliverables
One concrete result or a BLOCKED/NOT_INVOKED disposition with evidence.

## Workflow
1. Resolve Agent -> Plugin -> Skill -> Function.
2. Emit the exact functionality before execution.
3. Invoke the actual available provider or capability.
4. The installed Hook Agent may autonomously apply applicable lifecycle functions above this target; this skill does not own lifecycle behavior.
5. Verify the result with evidence.

## Validation
A PASS requires actual evidence. A declared path or emitted invocation is not proof of execution.

## Pitfalls
Emission is not invocation. Discovery is not authorization. Skills-only packaging does not itself create a runtime tool.

## Resources
See references/contract.md and assets/request.json.


## Script reference

Scripts are not loaded into context. An agent runs one only when a step needs it, and you can run the same command by hand from this skill's folder.

| Script | Purpose | Manual run |
|---|---|---|
| `scripts/validate.py` | Structural self-check: verifies the skill's required files (and request.json contents where applicable). Takes no arguments; prints `PASS: <skill>` and exits 0, or prints `FAIL: ...` and exits 1. | `python scripts/validate.py` |
