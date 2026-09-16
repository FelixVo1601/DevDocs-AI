# File filter rules — DevDocs AI

Which repository paths get indexed when fetching a selected repo.

Implementation: `backend/app/services/repo_filters.py` · Tests: `backend/tests/test_repo_filters.py`

## How a path is decided

`classify_path(path, size_bytes)` returns a `FilterDecision(include, reason)`. Checks run **denylist first** so a permitted extension can never rescue a noisy path — `node_modules/pkg/index.js` is skipped even though `.js` is allowed.

| Order | Check | Reason code |
|-------|-------|-------------|
| 1 | Empty path or directory entry | `empty-path` |
| 2 | Any parent directory is ignored (`node_modules`, `dist`, `.venv`, …) | `ignored-directory` |
| 3 | Credential-ish name, key, or cert | `secret-like` |
| 4 | Binary extension | `binary-extension` |
| 5 | Lockfile, minified bundle, source map, snapshot | `generated-artifact` |
| 6 | Larger than `MAX_FILE_BYTES` (200 KB) | `too-large` |
| 7 | Allowlisted filename (`Dockerfile`, `LICENSE`, `.gitignore`, …) | `allowed-filename` |
| 8 | Allowlisted extension | `allowed-extension` |
| 9 | Anything else | `unsupported-extension` |

Skip counts are aggregated per reason and logged at the end of each fetch.

## What is kept

Common source and documentation extensions, for example:

- **Code:** `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.svelte`, `.vue`, `.go`, `.rs`, `.java`, `.kt`, `.cs`, `.c`, `.h`, `.cpp`, `.rb`, `.php`, `.swift`, `.sql`
- **Docs/text:** `.md`, `.mdx`, `.rst`, `.txt`, `.adoc`
- **Config:** `.json`, `.yml`, `.yaml`, `.toml`, `.ini`, `.cfg`, `.conf`
- **Web:** `.html`, `.css`, `.scss`, `.sass`, `.less`
- **Infra/schema:** `.sh`, `.ps1`, `.tf`, `.graphql`, `.proto`, `.xml`
- **Extensionless:** `Dockerfile`, `Makefile`, `Gemfile`, `Procfile`, `README`, `LICENSE`, `CODEOWNERS`, `.gitignore`, `.editorconfig`, `.env.example`

## What is excluded

| Category | Examples |
|----------|----------|
| Dependencies | `node_modules/`, `vendor/`, `bower_components/`, `site-packages/` |
| Build output | `dist/`, `build/`, `out/`, `target/`, `.next/`, `.svelte-kit/`, `coverage/` |
| Tooling caches | `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.cache/` |
| Binaries | images, fonts, media, archives, `.so`/`.dll`/`.exe`, `.pdf`, `.sqlite3`, model weights |
| Generated | `package-lock.json`, `yarn.lock`, `poetry.lock`, `go.sum`, `*.min.js`, `*.map`, `*.snap` |
| Secrets | `.env`, `.env.local`, `credentials.json`, `secrets.yaml`, `*.pem`, `*.key`, `*.p12`, `id_rsa`, `.npmrc`, `.netrc` |

`.env.example`, `.env.sample`, and `.env.template` are deliberately **kept** — they document configuration without holding real values.

## Caps

| Cap | Value | Why |
|-----|-------|-----|
| `MAX_FILE_BYTES` | 200,000 | Skip generated/vendored blobs that blow up chunking |
| `MAX_FILES_PER_FETCH` | 150 | Keep MVP fetches inside GitHub rate limits |

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Sample paths are grouped by expected outcome (allowed, ignored dir, binary, secret, generated, unsupported) so a regression names the category that broke.
