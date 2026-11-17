---
name: template
description: Route template-domain requests through existing reusable templates and creators.
---
# template

## Purpose
Prefer declarative reusable templates over one-off hardcoded scaffolding.

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
