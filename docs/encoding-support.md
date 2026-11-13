# Encoding support investigation

> **Evidence snapshot:** This document records an earlier investigation or verification, not a fresh test run or a second implementation queue. Check [active tickets](../TASKS.md) and the [latest checkpoint](../IMPLEMENTATION_PROGRESS.md) before using it to close a gate. Native GUI and screen-reader checks require real platform evidence.

The application currently opens UTF-8 only and uses strict decoding. This
investigation records codec behavior and current compatibility boundaries.

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
These callers currently have different encoding responsibilities.

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
detection dependency is justified by successful decoding alone.

The tests added for this investigation exercise current FileManager failure
boundaries, not a claim that legacy Open support is implemented. Codec
availability alone does not bound memory or guarantee GUI latency.
