---
phase: 01-quy-trinh-doc-va-tom-tat
plan: "01"
subsystem: content-extraction
tags: [trafilatura, html-parsing, content-extraction, python]
dependency_graph:
  requires: [01-00]
  provides: [trafilatura-layer-0, improved-content-extraction]
  affects: [backend/services/summarizer.py]
tech_stack:
  added: [trafilatura>=2.0.0, lxml>=4.9.0, lxml_html_clean>=0.1.0]
  patterns: [layered-extraction, graceful-degradation]
key_files:
  modified:
    - backend/services/summarizer.py
    - backend/requirements.txt
decisions:
  - Use try/except import guard so app starts even if trafilatura not installed
  - Add lxml_html_clean as explicit dep due to lxml 6.x split of html.clean module
  - Use >= version constraints to allow patch updates
metrics:
  duration: ~10 minutes
  completed: 2026-03-24
  tasks: 2
  files: 2
---

# Phase 01 Plan 01: Content Extraction — trafilatura Layer 0 Summary

**One-liner:** Added trafilatura (F1: 0.945) as layer 0 in `_extract_content()` with graceful degradation to existing JSON-LD + BS4 fallback chain.

## What Was Built

Integrated trafilatura ML-based boilerplate removal as the first extraction layer in `Summarizer._extract_content()`. If trafilatura returns >= 200 chars, the result is used immediately without reaching BeautifulSoup selectors. When trafilatura returns None or short text (e.g., for paywall-only content), the code falls through to the existing JSON-LD + CSS selector chain unchanged.

Key design choices:
- `try/except ImportError` guard at module top — app starts even if pip install was skipped
- `try/except Exception` around the trafilatura call — one bad HTML won't crash the method
- `_TRAFILATURA_AVAILABLE` boolean gate checked before each call
- Empty string input still returns `""` as before

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Install trafilatura and add to requirements.txt | c46ee8b | backend/requirements.txt |
| 2 | Add trafilatura as layer 0 in _extract_content() | 54bd5cf | backend/services/summarizer.py |

## Verification Results

```
pytest test_extract.py -x -q
.....
5 passed, 1 warning in 0.36s
```

All 5 tests PASS GREEN including:
- `test_extract_laodong_selector` — .fck_detail content >= 200 chars
- `test_extract_dantri_selector` — .detail__content content >= 200 chars
- `test_extract_empty_html` — returns "" for empty input
- `test_extract_json_ld` — JSON-LD fallback still works
- `test_extract_meta_fallback` — og:description fallback still works

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Dep] Added lxml_html_clean to requirements.txt**
- **Found during:** Task 1 verification
- **Issue:** `trafilatura 2.0.0` depends on `justext` which imports `lxml.html.clean`. In lxml >= 6.0, `lxml.html.clean` was split into the separate `lxml_html_clean` package. Without it, `import trafilatura` raises `ImportError: lxml.html.clean module is now a separate project lxml_html_clean.`
- **Fix:** Added `lxml_html_clean>=0.1.0` to requirements.txt and installed in venv
- **Files modified:** backend/requirements.txt
- **Commit:** c46ee8b (included in Task 1 commit)

## Known Stubs

None — all extraction paths are wired and functional.

## Self-Check: PASSED

- [x] `backend/services/summarizer.py` exists and contains `import trafilatura as _trafilatura`
- [x] `backend/requirements.txt` contains `trafilatura>=2.0.0` and `lxml>=4.9.0`
- [x] Commit c46ee8b exists
- [x] Commit 54bd5cf exists
- [x] `pytest test_extract.py -x`: 5 passed
