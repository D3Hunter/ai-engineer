# Streaming and Framing

Use only when the diff affects actual token/record framing, chunked or buffered reads, cross-file reconstruction, scanner direction, or framing-related flags/fallbacks. Generic state, transaction, or SQL changes do not trigger this reference.

Follow a logical record from producer to consumer, including token shape, ordering, offsets, pending buffers, start/end markers, and emission decisions. Distinguish a valid empty record from a delimiter-only artifact under that format's contract.

For each applicable alternate path (such as forward/reverse scan or fallback reader), reason through this matrix:

| Pending record | Token | Boundary concern |
| --- | --- | --- |
| Empty | Empty | Noise versus valid empty record; flags/offsets remain correct |
| Empty | Nonempty | Correct start, ownership, and emission |
| Nonempty | Empty | Framing noise cannot become payload or reset the pending record |
| Nonempty | Nonempty | Correct continuation, joining order, and completion |

Include a delimiter-at-chunk-end case where the next chunk continues the same logical record, plus relevant buffer/file splits. Verify reconstruction neither drops nor duplicates content and equivalent paths yield equivalent logical records.

Inspect unchanged neighboring fallback/error branches sharing the markers or state flags. Benign framing artifacts must not be classified as malformed records, trigger record loss, or reset semantic state. Check normal completion and early exits against the same handoff assumptions.
