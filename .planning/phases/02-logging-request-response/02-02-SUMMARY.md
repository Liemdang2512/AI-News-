---
phase: 02-logging-request-response
plan: "02"
subsystem: logging
tags: [logging, openai, gemini, redaction, correlation, httpx]

# Dependency graph
requires:
  - phase: 02-01
    provides: app_logger singleton with redact_secrets, request_context ContextVar
provides:
  - OpenAI client logs (ai.openai.request / ai.openai.response / ai.openai.error) with request_id correlation
  - Gemini REST client logs (ai.gemini.request / ai.gemini.response / ai.gemini.error / ai.gemini.request_url_context) with request_id correlation
  - API key redaction in all AI-call log events via redact_secrets
affects: [phase 02-03, future AI client changes]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "log-before/after HTTP call pattern: start timer, log request, post, compute latency_ms, log response/error"
    - "safe_url pattern: call redact_secrets(url) before any logging to strip ?key= query param"
    - "api_key_present boolean flag instead of logging key value"

key-files:
  created: []
  modified:
    - backend/services/openai_client.py
    - backend/services/fast_gemini.py

key-decisions:
  - "Log api_key_present as bool, never log key string — prevents accidental secret leak in logs"
  - "Compute safe_url via redact_secrets before log statement — sanitisation at point of use"
  - "Use time.monotonic() for latency_ms — monotonic clock avoids wall-clock drift errors"

patterns-established:
  - "AI call logging: log event+request_id+model+prompt_chars before call, latency_ms+status_code after"
  - "Error log uses redact_secrets on response.text[:400] to avoid API key in error_preview field"

requirements-completed:
  - LOG-003

# Metrics
duration: 5min
completed: 2026-03-26
---

# Phase 02 Plan 02: AI-call Logging + Redaction Summary

**OpenAI and Gemini REST clients now emit structured logs (ai.X.request / ai.X.response / ai.X.error) with correlation request_id, latency_ms, and API key redaction via redact_secrets.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-26T04:14:00Z
- **Completed:** 2026-03-26T04:16:44Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- OpenAI client logs ai.openai.request before HTTP call (model, prompt_chars, max_tokens, temperature, api_key_present bool)
- OpenAI client logs ai.openai.response on 200 and ai.openai.error on non-200 with sanitized error_preview
- Gemini client generate_content logs ai.gemini.request with generationConfig, ai.gemini.response/error with latency_ms
- Gemini client generate_content_with_url logs ai.gemini.request_url_context with safe_url (key stripped) + article_url
- All logs carry correlation request_id from ContextVar; pytest test_logging.py: 4 passed

## Task Commits

Each task was committed atomically:

1. **Task 1: Add OpenAI AI-call logging + redaction** - `66cf2aa` (feat)
2. **Task 2: Add Gemini REST AI-call logging + redaction** - `33d4cac` (feat)

## Files Created/Modified
- `backend/services/openai_client.py` - Added import of logger/redact_secrets/get_request_id; wrapped HTTP call with request/response/error logs and latency timer
- `backend/services/fast_gemini.py` - Same pattern for generate_content and generate_content_with_url; safe_url computed via redact_secrets before log

## Decisions Made
- Log api_key_present as bool, never log key string — prevents accidental secret leak in structured log fields
- safe_url computed via redact_secrets(url) before log statement — sanitisation enforced at point of use
- time.monotonic() for latency_ms — avoids wall-clock drift errors in async context

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed curly/smart quotes in fast_gemini.py causing SyntaxError**
- **Found during:** Task 2 verification (pytest collection failed)
- **Issue:** The Edit tool introduced Unicode smart-quote characters (U+201C/U+201D) around a string literal in the original file header, causing Python SyntaxError
- **Fix:** Binary-replaced all curly quote bytes with straight ASCII quotes
- **Files modified:** backend/services/fast_gemini.py
- **Verification:** pytest test_logging.py 4 passed
- **Committed in:** 33d4cac (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Required for Task 2 to be importable. No scope creep.

## Issues Encountered
- Unicode smart-quote characters were injected during the Edit operation on fast_gemini.py, causing a SyntaxError at collection time. Resolved by binary-fixing the file.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- AI call logging complete; all providers (OpenAI, Gemini REST, Gemini URL-context) log request/response events with correlation
- Wave 02 logging foundation ready for plan 03 if applicable
- pytest test_logging.py remains GREEN (4 passed)

---
*Phase: 02-logging-request-response*
*Completed: 2026-03-26*

## Self-Check: PASSED

- FOUND: backend/services/openai_client.py
- FOUND: backend/services/fast_gemini.py
- FOUND: .planning/phases/02-logging-request-response/02-02-SUMMARY.md
- FOUND commit: 66cf2aa (Task 1 - OpenAI logging)
- FOUND commit: 33d4cac (Task 2 - Gemini logging)
