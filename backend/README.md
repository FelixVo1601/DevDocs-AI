# Backend (FastAPI)

Python FastAPI API for DevDocs AI.

## Layout

```text
backend/
├── alembic/                 # Migrations
│   └── versions/
├── alembic.ini
├── app/
│   ├── config.py            # DATABASE_URL from env
│   ├── db.py                # Engine + ping helpers
│   ├── main.py              # FastAPI routes
│   └── models/              # SQLAlchemy users + sessions
└── requirements.txt
```

## Prerequisites

From the **repo root**, start PostgreSQL:

```bash
docker compose up -d db
```

Ensure a root `.env` exists (`copy .env.example .env` on Windows) so `DATABASE_URL` matches Compose.

## Run locally

```bash
cd backend
python -m venv .venv
```

Activate the venv:

- Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

If port 8000 is blocked on Windows, keep using `8001`.

- Health: http://127.0.0.1:8001/health → `{"status":"ok"}`
- DB ping: http://127.0.0.1:8001/db/ping → `{"database":"ok"}`
- Schema: http://127.0.0.1:8001/db/schema → `{"users_and_sessions":true}`
- OpenAPI docs: http://127.0.0.1:8001/docs

## Auth API (session cookies)

Auth uses **HttpOnly session cookies** (not JWT). See [docs/DECISIONS.md](../docs/DECISIONS.md).

```powershell
# Register
curl.exe -s -X POST http://127.0.0.1:8001/auth/register `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"demo@example.com\",\"password\":\"password123\"}"

# Login (saves cookie)
curl.exe -s -c cookies.txt -X POST http://127.0.0.1:8001/auth/login `
  -H "Content-Type: application/json" `
  -d "{\"email\":\"demo@example.com\",\"password\":\"password123\"}"

# Protected check
curl.exe -s -b cookies.txt http://127.0.0.1:8001/auth/me

# Logout
curl.exe -s -b cookies.txt -c cookies.txt -X POST http://127.0.0.1:8001/auth/logout

# Should fail with 401
curl.exe -s -b cookies.txt http://127.0.0.1:8001/auth/me
```

## Migrations

Apply schema on an empty database:

```bash
cd backend
alembic upgrade head
```

Fresh Compose volume (destroys data):

```bash
# from repo root
docker compose down -v
docker compose up -d db
cd backend
alembic upgrade head
```

See the repo root [README](../README.md) and [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).
