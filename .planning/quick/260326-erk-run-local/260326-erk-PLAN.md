---
phase: quick
plan: 260326-erk
type: execute
wave: 1
depends_on: []
files_modified:
  - start_dev.sh
autonomous: true
must_haves:
  truths:
    - "Backend starts on http://localhost:8000 with hot-reload"
    - "Frontend starts on http://localhost:3000 with hot-reload"
    - "Both servers can be stopped with a single Ctrl+C"
  artifacts:
    - path: "start_dev.sh"
      provides: "Single-command local dev startup script"
  key_links:
    - from: "frontend (localhost:3000)"
      to: "backend (localhost:8000)"
      via: "API calls from Next.js to FastAPI"
---

<objective>
Get the full-stack app (FastAPI backend + Next.js frontend) running locally in development mode with a single command.

Purpose: Developer can start hacking immediately without remembering multiple terminal commands.
Output: A `start_dev.sh` script at project root and both servers verified running.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/dev.sh (existing backend dev script — creates venv, installs deps, runs uvicorn with --reload)
@backend/config.py (Settings class with BACKEND_HOST/PORT, GEMINI_API_KEY, AI_PROVIDER)
@backend/.env.example (env var template)
@frontend/package.json (Next.js app, `npm run dev` for dev mode)
@start_prod.sh (existing production script — reference for structure)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create start_dev.sh and ensure backend/frontend deps installed</name>
  <files>start_dev.sh</files>
  <action>
Create `start_dev.sh` at project root that starts both backend and frontend in dev mode with a single command.

Script must:
1. Trap SIGINT/SIGTERM to kill both child processes on Ctrl+C
2. Backend setup: cd into backend/, create venv if missing, pip install -r requirements.txt (skip if venv already exists and requirements unchanged), copy .env.example to .env if .env missing, run `uvicorn main:app --reload --host 127.0.0.1 --port 8000 --reload-exclude '.venv'` in background
3. Frontend setup: cd into frontend/, run `npm install` if node_modules missing, run `npm run dev` in background
4. Print URLs (backend http://localhost:8000, frontend http://localhost:3000, docs http://localhost:8000/docs)
5. `wait` to keep script alive until Ctrl+C

Key details:
- Backend venv: use `python3 -m venv .venv` and `.venv/bin/pip` (matching existing dev.sh pattern)
- Stream both logs to terminal (no log files in dev mode) with prefixed output using sed: `[backend]` and `[frontend]`
- Make script executable with chmod +x
- Ensure backend/.env exists before starting (user needs GEMINI_API_KEY at minimum; print warning if .env was just created from example)
  </action>
  <verify>
    <automated>bash -n "start_dev.sh" && test -x "start_dev.sh" && echo "OK"</automated>
  </verify>
  <done>start_dev.sh exists, is executable, passes bash syntax check. Running `./start_dev.sh` starts both backend (port 8000) and frontend (port 3000) with hot-reload enabled.</done>
</task>

<task type="auto">
  <name>Task 2: Verify both servers start and respond</name>
  <files></files>
  <action>
Run `./start_dev.sh` in background, wait up to 30 seconds for both servers to become responsive, then verify:

1. `curl -s http://localhost:8000/health` returns `{"status":"healthy"}`
2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000` returns 200
3. Kill the dev script after verification

If backend fails to start, check:
- Is backend/.env present with GEMINI_API_KEY set? (warn user if missing)
- Are Python deps installed correctly?
- Is port 8000 already in use?

If frontend fails, check:
- Are node_modules installed?
- Is port 3000 already in use?
  </action>
  <verify>
    <automated>curl -sf http://localhost:8000/health && curl -sf -o /dev/null http://localhost:3000 && echo "Both servers OK"</automated>
  </verify>
  <done>Both servers respond: backend /health returns healthy, frontend returns 200. Local dev environment is fully operational.</done>
</task>

</tasks>

<verification>
- `./start_dev.sh` starts both servers with single command
- Backend accessible at http://localhost:8000/docs (FastAPI Swagger UI)
- Frontend accessible at http://localhost:3000
- Ctrl+C cleanly stops both processes
</verification>

<success_criteria>
Developer can clone the repo, run `./start_dev.sh`, and have the full app running locally with hot-reload on both backend and frontend.
</success_criteria>

<output>
After completion, create `.planning/quick/260326-erk-run-local/260326-erk-SUMMARY.md`
</output>
