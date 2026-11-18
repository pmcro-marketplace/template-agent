---
name: template
description: Route template-domain requests through existing reusable templates and creators. USE FOR discovering and selecting an existing reusable template or deciding whether creator is required. DO NOT USE FOR authoring a new template after a gap is proven or managing the template plugin package; use creator or Plugin Agent.
---
# template

## Purpose
Prefer existing declarative reusable templates over one-off scaffolding and route only genuine gaps to the creator skill.

## When to Use
Use when a template-domain request must first be resolved against the available validated template inventory.

## When Not to Use
Do not author a missing template after discovery proves a gap; use `creator`. Do not create or update the template plugin package; use Plugin Agent.

## Inputs
A bounded template request, validated template inventory, constraints, authorization, and required output shape.

## Deliverables
A selected reusable template, a concrete route to `creator`, or `BLOCKED` / `NOT_INVOKED`.

## Workflow
1. Inspect validated reusable templates.
2. Match the request against declared inputs, outputs, and constraints.
3. Reuse the narrowest fitting template when available.
4. Route a genuine gap to `creator`.
5. Verify the selected route or artifact with evidence.

## Validation
PASS requires an actual selected template or downstream creator evidence; routing text alone is not execution.

## Pitfalls
Do not duplicate a reusable template because of minor parameter differences and do not confuse a template artifact with its plugin package.

## Resources
See `references/contract.md`, `assets/request.json`, and `scripts/validate.py`.
