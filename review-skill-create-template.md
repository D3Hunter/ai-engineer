i want to write a skill to review things related to “Code Structure, Encapsulation, and Duplication”
This skill accepts exactly three input parameters:

- `code_path` (required): absolute path to the cloned codebase; this is the working directory for review.
- `diff_filename` (required): filename of the diff to review.
- `output_filename` (required): final output JSON filename for the rendered findings payload.

its output

- Final output must be a file named exactly as `output_filename`.
- File content format is already defined by [review-output-format](../review-output-format/SKILL.md).
- Do not invent or emit an alternate output schema.


the reviewed finding risks(severity) are
Blocker
Major
Minor
Info
Nit

for each finding, you should include
- `severity`, `title`, `why`, `scope`, `risk_if_unchanged`, `evidence`, `change_request`.
- Keep scope concrete (`path:line`, module, branch, or scenario boundary).


all below are some raw materials or checklist items you can use:
