---
phase: 02-logging-request-response
plan: "00"
subsystem: testing
tags: [pytest, fastapi, testclient, sse, ndjson, x-request-id, redaction, logging]

requires:
  - phase: 01-quy-trinh-doc-va-tom-tat
    provides: stable FastAPI backend with middleware and streaming endpoints

provides:
  - backend/test_logging.py scaffold with 4 tests covering X-Request-ID, SSE, NDJSON, redaction

affects: [02-01, 02-02, 02-03]

tech-stack:
  added: []
  patterns:
    - "Wave 0 test scaffold pattern: write RED tests first, go GREEN as implementation waves complete"
    - "FastAPI TestClient with client.stream() for SSE/NDJSON streaming test assertions"

key-files:
  created:
    - backend/test_logging.py
  modified: []

key-decisions:
  - "Test scaffold runs with 3/4 tests GREEN at Wave 0 because X-Request-ID middleware was already in main.py; only redact_secrets test stays RED"
  - "Used /usr/bin/python3 (system Python 3.9) for pytest since app crawbot Python does not have pytest installed"

patterns-established:
  - "Wave 0 scaffold: pytest.fail() for missing imports keeps test RED without breaking collection"
  - "SSE test uses client.stream() context manager + iter_lines() to read first chunk only"

requirements-completed: [LOG-001, LOG-002, LOG-003, LOG-004, LOG-005]

duration: 5min
completed: 2026-03-26
---

# Phase 02 Plan 00: Logging Test Scaffold Summary

**pytest scaffold for FastAPI logging middleware verification — 4 tests covering X-Request-ID round-trip, SSE stream format, NDJSON stream error line, and redact_secrets helper (RED until Wave 01)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-26T00:00:00Z
- **Completed:** 2026-03-26T00:05:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Created `backend/test_logging.py` with 4 test functions covering all required logging behaviors
- Confirmed `pytest --collect-only` collects all 4 tests with no syntax/import errors
- Smoke-checked that SSE (`/api/rss/fetch_stream`) and NDJSON (`/api/articles/summarize_stream`) tests reach assertions and pass — X-Request-ID middleware was already present in main.py
- `test_redact_secrets_removes_api_key_tokens` correctly RED-fails with descriptive message since `services.app_logger` does not yet exist

## Task Commits

Each task was committed atomically:

1. **Task 1: Add backend logging tests scaffold** - `20c849f` (test)
2. **Task 2: Smoke-check streaming endpoints** - verified in-process, no additional files modified

## Files Created/Modified

- `backend/test_logging.py` - Test scaffold: X-Request-ID, SSE, NDJSON, redact_secrets tests

## Decisions Made

- Used `pytest.fail()` on ImportError for `redact_secrets` to keep test RED without blocking collection — aligns with Wave 0 design
- Used `client.stream()` + `iter_lines()` and break after first line to avoid long-running stream reads in tests

## Deviations from Plan

None - plan executed exactly as written.

**Unexpected finding:** The X-Request-ID middleware was already implemented in `main.py` as part of the `request_db_logging_middleware` (from a prior unplanned implementation). As a result, tests 1-3 pass GREEN immediately at Wave 0. Only `test_redact_secrets_removes_api_key_tokens` is RED as expected.

## Issues Encountered

- The default `python3` in the environment (`crawbot` python) does not have pytest. Used `/usr/bin/python3` (system Python 3.9) which has pytest installed. Test suite should be run with `python3 -m pytest` from the system Python.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Test scaffold ready; Wave 01 can implement `services/request_context.py`, `services/app_logger.py`, and middleware updates to make all 4 tests GREEN
- `test_redact_secrets_removes_api_key_tokens` is the only RED test remaining

---
*Phase: 02-logging-request-response*
*Completed: 2026-03-26*
