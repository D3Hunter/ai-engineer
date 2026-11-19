# Maintainability

Use when changed names, comments, interfaces, placement, or abstractions could obscure a contract or make future changes unsafe. A finding needs concrete risk or evidence of a repository policy violation; personal style preferences are not sufficient.

## Intent and boundaries

- Compare names and documentation with actual side effects, mutability, units, optionality, error categories, and domain meaning. A “validate” operation that writes state or a unit-ambiguous timeout can mislead callers; a merely different preferred name is not a defect.
- Check comments and public examples for contradictions with changed behavior. Missing rationale matters when an invariant, ordering constraint, or workaround becomes unsafe to maintain without it; comment density and TODO formatting alone are not automatic findings.
- Inspect placement and encapsulation when logic crosses ownership or layer boundaries. Explain which dependency, caller assumption, or invariant becomes harder to preserve.
- Additional exports, wrappers, or interfaces can be justified by consumers or test seams. Identify actual compatibility burden, hidden timeout/retry/transaction semantics, or coupling before requesting a smaller surface.

## Structure and duplication

- Extraction and abstraction depend on responsibilities and risk, not function length, nesting depth, or a fixed callsite count. Avoid replacing deliberate specialization with a helper that conflates distinct contracts.
- For positional data or primitive argument packs, check whether order/unit/polarity ambiguity can cause a concrete misuse; named types are one possible remedy.
- In changed maps, switches, registries, and test tables, inspect duplicate keys/IDs/cases for overriding, shadowing, or missing coverage. Compare both definitions and their effects.
- SQL tests differing in whitespace, case, quoting, or placeholder syntax may intentionally exercise lexical behavior. Do not normalize these distinctions away or infer redundancy without examining their assertions and purpose.
- Unrelated edits warrant concern when they introduce demonstrable risk or violate repository scope policy, rather than because a PR includes cleanup.
