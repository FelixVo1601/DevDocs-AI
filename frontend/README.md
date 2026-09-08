# Frontend (SvelteKit)

SvelteKit + TypeScript app for DevDocs AI.

## Run locally

```bash
cd frontend
copy .env.example .env   # Windows; or cp .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`.

Set `PUBLIC_API_URL` to your FastAPI base URL (default `http://localhost:8001`). The backend must be running, and CORS must allow `http://localhost:5173`.

### Auth pages

- `/register` — create account (then auto-login)
- `/login` — sign in (supports `?next=/app`)
- `/app` — **protected**; redirects to `/login` when signed out
- Header **Log out** — clears the session cookie
- Shared client: `src/lib/api.ts` (`apiRequest` / `apiGet` / `apiPost` with credentials)

See the repo root [README](../README.md) and [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).
