# MVP smoke checklist

Use this after the local setup in the [README](../README.md). The API script checks health, the database, and session gates. The browser list is the product walkthrough: connect GitHub, index one small repository, ask, and open a citation.

Open the UI at **http://localhost:5173**. Use `localhost`, not `127.0.0.1`, so the `devdocs_session` cookie matches `PUBLIC_API_URL` (`http://localhost:8001`).

## API script

With Postgres and the API already running:

```bash
python scripts/smoke.py
```

It creates a throwaway user, then checks:

| Check | Expected |
|-------|----------|
| `GET /health` | `200` `{"status":"ok"}` |
| `GET /db/ping` | `200` `{"database":"ok"}` |
| `GET /db/schema` | `200` `{"users_and_sessions":true}` |
| `POST /ask` with no cookie | `401` `Not authenticated` |
| `GET /github/repos` with no cookie | `401` `Not authenticated` |
| Register, then login | `201`, then `200`, cookie `devdocs_session` |
| `GET /auth/me` | `200` and the same email |
| `GET /github/selected-repo` | `200` `{"selected":null}` |
| `GET /github/repos` while signed in but not connected | `400` `GitHub is not connected. Connect GitHub first.` |
| `POST /ask` with no selected repo | `400` `No repository selected. Select a repository first.` |
| `POST /auth/logout`, then `GET /auth/me` | `200` `{"message":"Logged out"}`, then `401` `Not authenticated` |

The script does not call GitHub or OpenAI. It leaves one `smoke-…@example.com` user in the local database. The password is 8+ characters, which is the register/login minimum.

## Browser walkthrough

Fill `SECRET_KEY`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, and `OPENAI_API_KEY` in the root `.env`, then restart the API. OAuth callback must be `http://localhost:8001/auth/github/callback`. See [GITHUB_OAUTH.md](GITHUB_OAUTH.md).

- [ ] **http://localhost:5173** shows **Log in** and **Register**. **http://localhost:5173/app** sends you to login.
- [ ] **Register** with an email and a password of at least 8 characters. You land on `/app`, signed in (header shows your email and **Log out**).
- [ ] **Repositories** (`/app`) shows **Not connected**, the four steps (connect, select, index until ready, ask), and **Connect GitHub**.
- [ ] **Ask** (`/app/ask`) shows **GitHub is not connected** and **Connect on Repositories**. There is no question form yet.
- [ ] **Connect GitHub**, authorize the OAuth app, and return to `/app`. The page says **GitHub connected successfully.** and **Connected as** your GitHub login.
- [ ] **Your repositories** lists repos for that account. Pick a **small** one (the index keeps at most 150 files and skips files over 200 KB). The button changes from **Select** / **Saving…** to **Selected**.
- [ ] **Selected repository** shows `owner/name`, the default branch, and indexing status **not indexed**, plus “Index this repository before asking questions.”
- [ ] **Ask** now says **Repository is not indexed** and links back with **Index this repository**.
- [ ] **Index repository**. The button stays **Indexing…** and the status word is **running** until the sync job finishes (fetch, chunk, embed). This waits on the request; a small repo should end as **ready**, with “This repository is indexed and ready to search.” and **Ask a question**.
- [ ] If status is **failed**, the red error is the job or request message. Fix it and index again. Ask stays closed until **ready**.
- [ ] Open **Ask**. The line is “Asking about `owner/name`. The index status is ready.” Submit a question about that repo (for example, “What does this repository do?”). The button reads **Asking…**, then **Searching the index and writing an answer…**.
- [ ] **Answer** shows the reply. **Sources** lists each citation as `[n] path`, a line range, and a chunk id.
- [ ] Click a source title or an `[n]` marker. **Source preview** shows that path, line range, and the chunk text in a read-only block.
- [ ] **Log out** in the header returns you home. `/app` redirects to login again.

Indexing and asking both need `OPENAI_API_KEY`. Embeddings use `EMBEDDING_MODEL` (default `text-embedding-3-small`, 1536 dimensions). Answers use `CHAT_MODEL` (default `gpt-4o-mini`).
