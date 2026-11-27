# Invocation Contract

Human target surface:
`@template-agent /<function> [arguments]`

Internal target identity:
`/<plugin>:<skill>:<function>`

Hook Agent is the autonomous lifecycle layer above this plugin when installed and available.

Direct lifecycle resolution:
`/<lifecycle-function>` -> `@hook-agent /<lifecycle-function>` -> `/hook:hook:<lifecycle-function>`.

Core flow:
`RESOLVE -> HOOK AGENT TOP LAYER (when available) -> INVOKE TARGET -> VERIFY -> EVIDENCE`.

This plugin does not implement lifecycle functions.
If no real lifecycle provider exists, Hook Agent returns `NOT_INVOKED`.
**Emission is not invocation.**
