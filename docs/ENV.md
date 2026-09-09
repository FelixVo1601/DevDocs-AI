# Environment variables — DevDocs AI

Copy the root template once, then add a frontend override if needed:

```bash
# from repo root
cp .env.example .env          # Windows: copy .env.example .env
cp frontend/.env.example frontend/.env
```

Never commit `.env` or `frontend/.env`.

The backend loads `.env` from `backend/` **or** the repo root (`../.env`).

---

## Quick reference

| Variable | Where used | Purpose |
|----------|------------|---------|
| `ENVIRONMENT` | Backend | `development` enables localhost CORS regex |
| `FRONTEND_URL` | Backend | Canonical UI origin; also added to CORS |
| `PUBLIC_API_URL` | Frontend | Browser → FastAPI base URL |
| `CORS_ORIGINS` | Backend | Comma-separated explicit allowed origins |
| `BACKEND_HOST` / `BACKEND_PORT` | Docs / scripts | Local uvicorn bind (default `127.0.0.1:8001`) |
| `DATABASE_URL` | Backend | SQLAlchemy / Alembic / psycopg |
| `POSTGRES_*` | Docker Compose | Postgres container credentials |
| `SESSION_COOKIE_NAME` | Backend | Auth cookie name (`devdocs_session`) |
| `SESSION_EXPIRE_MINUTES` | Backend | Session lifetime |
| `COOKIE_SECURE` | Backend | Set `true` only on HTTPS |

---

## CORS (FE ↔ BE)

Auth uses **credentialed** requests (`credentials: "include"`) and an `HttpOnly` cookie.

Requirements:

1. `PUBLIC_API_URL` host matches how you call the API (prefer **`http://localhost:8001`**).
2. Open the UI at **`http://localhost:5173`** (avoid mixing `localhost` and `127.0.0.1` for cookies).
3. Backend `CORS_ORIGINS` includes the UI origin, **or** `ENVIRONMENT=development` (default) so any `http://localhost:<port>` / `http://127.0.0.1:<port>` is allowed via regex.

No browser CORS extensions or manual header hacks are required for local auth.

---

## Database

`DATABASE_URL` must match Compose:

```text
postgresql://devdocs:change_me@localhost:5432/devdocs
```

Change password in both `.env` and what Compose reads (`POSTGRES_PASSWORD`) together.

---

## Frontend-only file

`frontend/.env`:

```env
PUBLIC_API_URL=http://localhost:8001
```

SvelteKit only exposes env vars prefixed with `PUBLIC_` to the browser.
