# Backend (FastAPI)

Python FastAPI API for DevDocs AI.

## Layout

```text
backend/
├── app/
│   ├── __init__.py
│   ├── config.py    # DATABASE_URL from env
│   ├── db.py        # Postgres ping helper
│   └── main.py      # FastAPI app + /health + /db/ping
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
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

If port 8000 is blocked on Windows, keep using `8001`.

- Health: http://127.0.0.1:8001/health → `{"status":"ok"}`
- DB ping: http://127.0.0.1:8001/db/ping → `{"database":"ok"}`
- OpenAPI docs: http://127.0.0.1:8001/docs

See the repo root [README](../README.md) and [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).
