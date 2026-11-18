---
name: creator
description: Create a new reusable generic template from a declarative request and acceptance contract. USE FOR authoring a new reusable template when no validated template already satisfies the request. DO NOT USE FOR routing to an existing template or managing plugin packages; use template or Plugin Agent.
---
# creator

## Purpose
Create one reusable declarative template with explicit variables, inputs, outputs, constraints, validation, and an example request.

## When to Use
Use after template discovery proves no existing validated template satisfies the bounded request.

## When Not to Use
Do not create duplicate templates, route an existing template request, or create/update the template plugin package itself.

## Inputs
A bounded template intent, variables, inputs, outputs, constraints, acceptance criteria, target audience, and discovery evidence.

## Deliverables
A reusable template artifact plus validation evidence, or `BLOCKED` / `NOT_INVOKED`.

## Workflow
1. Confirm no existing validated template satisfies the request.
2. Define the template contract and variable surface.
3. Produce the narrowest reusable template artifact.
4. Include validation and one representative example request.
5. Validate the result and return evidence.

## Validation
PASS requires a concrete reusable artifact plus acceptance evidence; a concept or route alone is insufficient.

## Pitfalls
Do not hardcode one-off project details into a supposedly reusable template or confuse template content with plugin packaging.

## Resources
See `references/contract.md`, `assets/request.json`, and `scripts/validate.py`.
