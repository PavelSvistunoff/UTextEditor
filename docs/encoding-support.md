# Encoding support investigation — TASK-011.01

Decision: retain strict UTF-8 as the default. Add explicit encoding selection
for standalone documents in TASK-011.02; do not guess legacy encodings or use
replacement/ignore error handlers. This document proposes future behavior;
the application still opens UTF-8 only.

## Current implementation

FileManager.open decodes UTF-8 with optional BOM removal, normalizes editor
text to LF, detects the source line-ending style and fingerprints raw bytes.
Document.encoding defaults to utf-8. Save encodes before creating a temporary
file, then checks the raw-byte fingerprint before replacement. Unicode encode
failure therefore preserves source bytes, dirty text and the saved digest.
UTF-8 BOM is currently removed on save; it is not preserved as document metadata.

Project manifests, scenes, notes and exports use UTF-8 independently of the
standalone FileManager path. Conflict review decodes standalone files with
utf-8-sig. Recovery stores Unicode text, with no original encoding metadata.
These callers must be updated deliberately before offering legacy-file editing.

## Codec experiment

Python's built-in codecs round-tripped these synthetic samples exactly:

| Codec | Sample | Encoded bytes |
| --- | --- | --- |
| utf-8 | Український текст 😀 | 38 |
| utf-16 | Український текст 😀 | 42 |
| utf-16-le | Український текст 😀 | 40 |
| cp1251 | Український текст | 17 |
| cp1252 | A café | 6 |

CP1251 bytes for «Привіт» also decode successfully as CP1252 to «Ïðèâ³ò».
Successful decoding is not evidence of the intended encoding. A Latin-1 fallback
would likewise hide decoding mistakes rather than resolve them. No probabilistic
detection dependency is justified for an explicitly chosen codec.

## Implementation recommendation

1. Offer a bounded allowlist for standalone Open with Encoding and Save As:
   UTF-8, UTF-8 with BOM, UTF-16 with BOM, Windows-1251 and Windows-1252.
   BOM-less UTF-16 requires an explicit endian choice; never infer native endian.
2. Keep canonical codec and BOM policy in document/save snapshots. Retain the
   original raw-byte digest regardless of the decoded text. Decode strictly,
   then perform binary/NUL checks on decoded text, not UTF-16 bytes.
3. Capture codec/BOM choices in existing workers and generation checks. Preview
   a reopen before replacing an unsaved buffer. Changing output encoding requires
   an explicit choice; an encode error must offer another choice or cancellation,
   never silently replace unrepresentable characters.
4. Update conflict reads, recovery metadata (with backward-compatible defaults),
   status display and save snapshots together. Keep project files and exports
   UTF-8 unless a separate project-format decision is made.
5. Test emoji/unrepresentable edits, BOM/endian handling, CRLF/CR/LF, external
   byte changes, cancellation, Save As and recovery before exposing selectors.

The tests added for this investigation exercise current FileManager failure
boundaries, not a claim that legacy Open support is implemented. Large-file
limits and incremental decoding remain TASK-011.05; codec availability alone
does not bound memory or guarantee GUI latency. Native selector accessibility
and Windows codec workflows require verification when that UI is implemented.
