# Backend (FastAPI)

Python FastAPI API for DevDocs AI.

## Layout

```text
backend/
├── app/
│   ├── __init__.py
│   └── main.py      # FastAPI app + GET /health
└── requirements.txt
```

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: http://localhost:8000/health → `{"status":"ok"}`
- OpenAPI docs: http://localhost:8000/docs

See the repo root [README](../README.md) and [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).
