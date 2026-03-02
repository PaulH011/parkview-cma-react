# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Parkview CMA Tool — a financial web app with two required local services:

| Service | Command (from repo root) | Port |
|---------|--------------------------|------|
| FastAPI backend | `uvicorn api.main:app --reload --port 8000` | 8000 |
| Next.js frontend | `cd web && npm run dev` | 3000 |

Supabase and Anthropic API are **optional** — the app degrades gracefully without them (hardcoded defaults, localStorage scenarios, auth disabled).

### Running services

- Start the backend first; the frontend calls it at `http://localhost:8000` by default.
- `~/.local/bin` must be on `PATH` for `uvicorn` (pip installs there as non-root). Run `export PATH="$HOME/.local/bin:$PATH"` if needed.
- A `.env` file in the repo root is loaded by `python-dotenv`. At minimum set `DEBUG=true` and `FRONTEND_URL=http://localhost:3000`. See `.env.example` for the full list.

### Lint / Build / Test

- **Frontend lint**: `cd web && npx eslint` (pre-existing warnings/errors exist in the codebase).
- **Frontend build**: `cd web && npm run build` (uses Turbopack).
- **Backend health check**: `curl http://localhost:8000/health` — returns `{"status":"healthy"}` when the engine is importable.
- **Calculation engine standalone**: `python3 -m ra_stress_tool` or `python3 example_usage.py`.
- No automated test suite exists in this repo.

### Gotchas

- The Python deps install to `~/.local/` (user site-packages) since system site-packages is not writable. This is fine but means `uvicorn` binary lands in `~/.local/bin`.
- The frontend uses `package-lock.json` → always use `npm` (not pnpm/yarn).
- Swagger docs are available at `http://localhost:8000/docs` when `DEBUG=true`.
