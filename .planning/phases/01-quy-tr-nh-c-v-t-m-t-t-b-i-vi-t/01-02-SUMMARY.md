---
phase: 01-quy-trinh-doc-va-tom-tat
plan: "02"
subsystem: backend/services
tags: [playwright, timeout, performance, one-line-change]

# Dependency graph
requires:
  - 01-00 (test scaffold)
provides:
  - PlaywrightFetcher with wait_for_selector timeout=2000ms
affects:
  - backend/services/playwright_fetcher.py

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Playwright selector wait timeout tuned for Vietnamese news render speed (1-2s after DOMContentLoaded)

key-files:
  created: []
  modified:
    - backend/services/playwright_fetcher.py

key-decisions:
  - "Reduce wait_for_selector timeout from 5000ms to 2000ms — Vietnamese news sites render content within 1-2s, making 5s wasteful; worst-case per-article time drops from 60s to 24s"

# Metrics
duration: <1min
completed: 2026-03-25
---

# Phase 1 Plan 02: Playwright Timeout Reduction Summary

**One-line change: wait_for_selector timeout 5000ms -> 2000ms in PlaywrightFetcher, cutting worst-case per-article Playwright time from 60s to 24s**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-03-25T02:41:02Z
- **Completed:** 2026-03-25T02:41:30Z
- **Tasks:** 2/2
- **Files modified:** 1

## Accomplishments

- Changed `await page.wait_for_selector(selector, timeout=5000)` to `timeout=2000` in PlaywrightFetcher.fetch()
- Updated inline comment from "tối đa 5s" to "tối đa 2s" for consistency
- Import verified: `from services.playwright_fetcher import playwright_fetcher, ARTICLE_SELECTORS` exits 0, 12 selectors confirmed
- All 14 tests still pass/skip as expected (11 passed, 3 skipped — no regression)

## Task Commits

Each task was committed atomically:

1. **Task 1: Reduce wait_for_selector timeout from 5000ms to 2000ms** - `3437640` (fix)
2. **Task 2: Verify app import and smoke test** - verification only, no new commit needed

## Files Created/Modified

- `backend/services/playwright_fetcher.py` — line 104 comment updated, line 107 timeout changed from 5000 to 2000

## Decisions Made

- Vietnamese news sites render content in 1-2s after DOMContentLoaded, so 5s per selector was wasteful
- With 12 selectors: worst case 12 x 5s = 60s -> 12 x 2s = 24s per article
- No other logic was changed — strictly one timeout parameter

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: backend/services/playwright_fetcher.py — confirmed timeout=2000, no timeout=5000
- FOUND: commit 3437640 (Task 1)
- grep "timeout=5000" returns 0 lines
- grep "timeout=2000" returns line 107 (wait_for_selector)
- Import: playwright_fetcher + ARTICLE_SELECTORS (12) loads OK
- pytest: 11 passed, 3 skipped (no regression)

---
*Phase: 01-quy-trinh-doc-va-tom-tat*
*Completed: 2026-03-25*
