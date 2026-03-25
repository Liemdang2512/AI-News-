---
phase: 01-quy-trinh-doc-va-tom-tat
plan: "03"
subsystem: backend/services
tags: [summarizer, validation, bullet, batch, performance, prompts]

# Dependency graph
requires:
  - 01-00 (test scaffold)
  - 01-01 (trafilatura extraction)
  - 01-02 (playwright timeout)
provides:
  - _has_bullet_content staticmethod in Summarizer class
  - Strict bullet validation in 3 _process_single_article checks
  - BATCH_SIZE=10 and inter-batch sleep=0.5s
  - Hardened SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT
affects:
  - backend/services/summarizer.py
  - backend/prompts.py

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Regex-based bullet detection (r'^- .{20,}' MULTILINE) instead of substring search
    - Batch throughput tuning: BATCH_SIZE=10, inter-batch delay=0.5s

key-files:
  created: []
  modified:
    - backend/services/summarizer.py
    - backend/prompts.py

key-decisions:
  - "Use regex r'^- .{20,}' with MULTILINE flag to detect real bullet lines, avoiding false-positives from URL paths with dashes"
  - "BATCH_SIZE 5->10 and inter-batch sleep 2s->0.5s doubles batch throughput and reduces idle wait time between article batches"
  - "SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT already had required instructions — verified correct, committed existing hardened version"

# Metrics
duration: ~10min
completed: 2026-03-24
---

# Phase 1 Plan 03: Bullet Validation + BATCH_SIZE + Prompt Hardening Summary

**Strict bullet validation via _has_bullet_content staticmethod replaces naive '- ' substring check; BATCH_SIZE doubled to 10 with inter-batch sleep halved to 0.5s; prompt instructions verified correct.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-03-24
- **Tasks:** 3/3
- **Files modified:** 2

## Accomplishments

- Added `Summarizer._has_bullet_content(summary)` staticmethod using `re.search(r'^- .{20,}', summary, re.MULTILINE)` to distinguish real bullet lines from URL dashes
- Replaced `"- " in summary` with `Summarizer._has_bullet_content(summary)` in all 3 validation checks in `_process_single_article()`
- Increased `BATCH_SIZE` from 5 to 10 in `summarize_articles_generator()`
- Reduced inter-batch `asyncio.sleep(2)` to `asyncio.sleep(0.5)` — per-article sleep (0.5s) left unchanged
- Verified `SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT` already contains "KHÔNG dùng dấu ngoặc vuông" and "bắt đầu bằng dấu gạch ngang" — committed hardened version from prior work
- Full test suite: 14 passed, 0 failures, 0 skips

## Task Commits

Each task was committed atomically:

1. **Task 1: Add _has_bullet_content() + fix validation** - `5d72dc6` (feat)
2. **Task 2: BATCH_SIZE 10, inter-batch sleep 0.5s** - `99751af` (feat)
3. **Task 3: Verify and commit hardened prompts** - `b6380cf` (feat)

## Files Created/Modified

- `backend/services/summarizer.py` — new `_has_bullet_content` staticmethod (lines 151-162), 3 validation call sites updated, BATCH_SIZE=10, inter-batch sleep=0.5s
- `backend/prompts.py` — committed hardened SINGLE_ARTICLE_URL_SUMMARIZE_PROMPT and SINGLE_ARTICLE_SUMMARIZE_PROMPT with explicit no-bracket and bullet-dash instructions

## Decisions Made

- Regex approach `r'^- .{20,}'` with MULTILINE catches lines starting with `- ` followed by at least 20 characters — correctly ignores URL-embedded dashes
- `_has_bullet_content(None)` returns False via early guard, satisfying the None-safety requirement
- BATCH_SIZE=10 aligns with the semaphore limit of 10 concurrent tasks, fully utilizing available concurrency
- 0.5s inter-batch delay is enough to avoid rate-limiting bursts while minimizing idle time

## Deviations from Plan

None - plan executed exactly as written. The prompt was already correct as noted in the plan context.

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: `backend/services/summarizer.py` — `_has_bullet_content` at line 151 + 3 call sites (lines 448, 509, 538)
- FOUND: `"- " in summary` returns 0 matches (old pattern fully removed)
- FOUND: `BATCH_SIZE = 10` at line 294
- FOUND: `asyncio.sleep(0.5)` at line 328 (inter-batch); per-article sleep at line 427 unchanged
- FOUND: commit 5d72dc6 (Task 1), 99751af (Task 2), b6380cf (Task 3)
- pytest test_extract.py test_summarizer.py test_prompts.py: **14 passed, 0 failures, 0 skips**
- `python3 -c "from services.summarizer import summarizer"` exits 0
- REQ-002: _has_bullet_content exists + 3 call sites + tests pass
- REQ-003: Both SINGLE_ARTICLE_*_PROMPT have "KHÔNG dùng dấu ngoặc vuông" and "bắt đầu bằng dấu gạch ngang"

---
*Phase: 01-quy-trinh-doc-va-tom-tat*
*Completed: 2026-03-24*
