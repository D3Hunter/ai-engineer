# Phrase Bank (Data-Derived)

Purpose:
- keep wording aligned with observed D3Hunter review style
- provide short stems you can adapt with concrete scope/evidence
- speed up drafting while keeping comments direct and actionable

How to use:
- use these as phrase stems, not mandatory copy-paste text
- fill in concrete path/line/risk when asking for non-trivial changes
- prefer one stem per comment to keep focus

Clarify intent:
- `what's this for?`
- `when will this happen? seems a bug`
- `do we still need this?`
- `why not use <api/primitive>?`

Request change:
- `seems no need to <step>; can we remove it?`
- `maybe move this to <pkg/component>`
- `prefer <name>; current name is confusing`
- `we can return early on <condition> to reduce indent level`
- `this looks duplicated with <path:line>; can we keep one canonical definition?`

Tests and validation:
- `add UT for it`
- `please add an integration test for this path`
- `add a case for <negative/edge scenario>`
- `make sure retry/cancel path is covered`
- `add a test to ensure SQL/table definitions are unique (for example repeated select $$ cases)`

Comments and rationale:
- `please add a short why-comment for this branch`
- `what's this comment for?`
- `this workflow is clear enough; comment may be removed`

Compatibility and scale:
- `is this backward compatible with N-1 nodes?`
- `should this be guarded by version gate/feature flag?`
- `will this concurrency be too large when store count is large?`

Observed phrase signals (2021-2026 local corpus):
- common starters: `maybe`, `we`, `this`, `why`, `can`, `please`, `seems`
- common stems: `seems no need`, `please add`, `can we`, `what's this`, `do we need`
