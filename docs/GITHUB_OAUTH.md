# GitHub OAuth (backend) — local setup

Day 11 adds backend OAuth so a signed-in DevDocs user can connect their GitHub account. The access token is **encrypted at rest** and **never returned by the API** or written to logs.

## 1. Create a GitHub OAuth App

1. Open [GitHub Developer Settings → OAuth Apps](https://github.com/settings/developers) → **New OAuth App**.
2. Application name: `DevDocs AI (local)`
3. Homepage URL: `http://localhost:5173`
4. Authorization callback URL: `http://localhost:8001/auth/github/callback`
5. Create the app, then generate a **Client secret**.

## 2. Configure env

In the repo root `.env` (from `.env.example`):

```env
SECRET_KEY=replace-with-a-long-random-string
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
GITHUB_REDIRECT_URI=http://localhost:8001/auth/github/callback
FRONTEND_URL=http://localhost:5173
```

Restart the API after changing env (settings are cached at process start).

## 3. Migrate + run API

```bash
docker compose up -d db
cd backend
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## 4. Complete the flow (logged-in browser session)

1. Register/login via the UI (or API) so you have the `devdocs_session` cookie for `localhost:8001`.
2. In the **same browser**, open:

   `http://localhost:8001/auth/github/start`

   (cookie must be sent — use `localhost`, not a mix of hosts.)
3. Authorize the GitHub App.
4. You are redirected to `http://localhost:5173/app?github=connected`.
5. Check status (with session cookie):

   `GET http://localhost:8001/auth/github/connection`

   Example: `{"connected":true,"github_user_id":123,"github_login":"you","scope":"read:user,repo"}`

## Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/auth/github/start` | Session cookie | Redirect to GitHub |
| GET | `/auth/github/callback` | State (+ cookie if present) | Exchange code, store encrypted token |
| GET | `/auth/github/connection` | Session cookie | Connection metadata only (no token) |

## Security notes

- `access_token_encrypted` is Fernet ciphertext derived from `SECRET_KEY`.
- Logs may include `user_id` / `github_login` / error **codes**, never tokens or `GITHUB_CLIENT_SECRET`.
- Rotate `SECRET_KEY` only with a migration plan — existing ciphertext becomes unreadable.
