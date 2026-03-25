---
phase: 01-quy-trinh-doc-va-tom-tat
plan: "00"
subsystem: testing
tags: [pytest, beautifulsoup, html-fixtures, vietnamese-news, prompts]

# Dependency graph
requires: []
provides:
  - HTML fixtures for laodong.vn and dantri.com.vn article extraction tests
  - pytest test scaffold covering REQ-001, REQ-002, REQ-003
  - test_extract.py with 5 tests for _extract_content() selectors
  - test_summarizer.py with 5 tests for fallback/bullet validation
  - test_prompts.py with 4 tests for prompt format compliance
affects:
  - 01-01 (implementation must make test_extract.py go GREEN)
  - 01-02 (content fetch implementation)
  - 01-03 (must add _has_bullet_content to make test_summarizer.py go GREEN)

# Tech tracking
tech-stack:
  added: [pytest-8.4.2]
  patterns:
    - sys.path.insert(0, os.path.dirname(__file__)) pattern for backend test imports
    - try/except AttributeError + pytest.skip() for future-method tests
    - HTML fixtures in backend/fixtures/ for unit testing without live HTTP

key-files:
  created:
    - backend/fixtures/laodong_article.html
    - backend/fixtures/dantri_article.html
    - backend/test_extract.py
    - backend/test_summarizer.py
    - backend/test_prompts.py
  modified: []

key-decisions:
  - "Use try/except AttributeError + pytest.skip() for _has_bullet_content tests so they skip gracefully before plan 03 implements it"
  - "Fixtures include JSON-LD articleBody, og:description meta, and correct CSS selectors (fck_detail, detail__content) to match _extract_content() selector chain"
  - "test_extract.py tests may run RED at Wave 0 — this is expected and acceptable per plan design"

patterns-established:
  - "Test scaffold pattern: write failing tests first (TDD Wave 0), implement in subsequent plans"
  - "Backend tests use sys.path.insert(0, os.path.dirname(__file__)) for relative imports"
  - "HTML fixture files in backend/fixtures/ provide realistic Vietnamese news article HTML for unit tests"

requirements-completed: [REQ-001, REQ-002, REQ-003]

# Metrics
duration: 15min
completed: 2026-03-25
---

# Phase 1 Plan 00: Test Scaffold Summary

**pytest scaffold with 14 tests (HTML fixtures + 3 test files) for Vietnamese news article extraction, bullet validation, and prompt format — tests run RED at Wave 0 and go GREEN as plans 01-03 implement features**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-25T02:20:00Z
- **Completed:** 2026-03-25T02:38:28Z
- **Tasks:** 2/2
- **Files modified:** 5 created

## Accomplishments
- Created two realistic HTML fixtures for laodong.vn (.fck_detail) and dantri.com.vn (.detail__content) with Vietnamese article content, JSON-LD structured data, and noise elements (nav, script) for _extract_content() testing
- Wrote 14 pytest tests across 3 files covering _extract_content() selectors, _excerpt_only_fallback() bullet behavior, and prompt format requirements
- test_prompts.py (4 tests) and test_summarizer.py tests 1-2 pass immediately; _has_bullet_content tests skip with AttributeError guard until plan 03 adds the method

## Task Commits

Each task was committed atomically:

1. **Task 1: Create HTML fixtures for Vietnamese news sites** - `e389185` (chore)
2. **Task 2: Write unit test files for REQ-001, REQ-002, REQ-003** - `e826fc6` (test)

## Files Created/Modified
- `backend/fixtures/laodong_article.html` - Realistic laodong.vn HTML with fck_detail, JSON-LD, og:description
- `backend/fixtures/dantri_article.html` - Realistic dantri.com.vn HTML with detail__content, JSON-LD, meta description
- `backend/test_extract.py` - 5 tests for _extract_content(): laodong selector, dantri selector, empty HTML, JSON-LD, meta fallback
- `backend/test_summarizer.py` - 5 tests: 2 for _excerpt_only_fallback (PASS now), 3 for _has_bullet_content (SKIP until plan 03)
- `backend/test_prompts.py` - 4 tests for SINGLE_ARTICLE_SUMMARIZE_PROMPT and SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT format (all PASS)

## Decisions Made
- Used `try/except AttributeError` + `pytest.skip()` for the three `test_has_bullet_*` tests so collection never fails regardless of whether `_has_bullet_content` exists
- Fixtures are minimal but realistic: include the exact CSS selectors _extract_content() uses, plus JSON-LD and meta tags to exercise the full fallback chain

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The system Python3 path (`/Users/tanliem/Library/Application Support/crawbot/nodejs/bin/python3`) did not have pytest installed; used `/Library/Developer/CommandLineTools/usr/bin/python3` which had pytest available. Tests pass with system Python3.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Test scaffold complete: plans 01-03 can use `pytest test_extract.py test_summarizer.py test_prompts.py` as the automated verify command
- Plan 01 must implement trafilatura-based extraction to make test_extract.py go GREEN
- Plan 03 must add `_has_bullet_content` staticmethod to Summarizer to make the 3 skipped tests run GREEN

---
*Phase: 01-quy-trinh-doc-va-tom-tat*
*Completed: 2026-03-25*
