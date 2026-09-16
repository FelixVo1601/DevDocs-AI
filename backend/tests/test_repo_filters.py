"""Sample-path coverage for the ingestion file filters."""

from __future__ import annotations

import pytest

from app.services.repo_filters import (
    MAX_FILE_BYTES,
    REASON_BINARY_EXT,
    REASON_GENERATED,
    REASON_IGNORED_DIR,
    REASON_SECRET_LIKE,
    REASON_TOO_LARGE,
    REASON_UNSUPPORTED_EXT,
    classify_path,
    guess_language,
    should_include_path,
)

ALLOWED_PATHS = [
    "app/main.py",
    "backend/app/services/repo_filters.py",
    "frontend/src/routes/+page.svelte",
    "frontend/src/lib/api.ts",
    "src/components/Button.tsx",
    "src/index.js",
    "README.md",
    "docs/ARCHITECTURE.md",
    "docs/adr/0001-choice.rst",
    "pyproject.toml",
    "package.json",
    "docker-compose.yml",
    "Dockerfile",
    "Makefile",
    "LICENSE",
    "CODEOWNERS",
    ".gitignore",
    ".env.example",
    "scripts/dev.ps1",
    "scripts/dev.sh",
    "infra/main.tf",
    "api/schema.graphql",
    "db/migrations/0001_init.sql",
    "web/styles/app.scss",
    "cmd/server/main.go",
    "src/lib.rs",
]

IGNORED_DIR_PATHS = [
    "node_modules/lodash/index.js",
    "frontend/node_modules/svelte/package.json",
    "dist/bundle.js",
    "frontend/build/app.js",
    "backend/.venv/lib/site.py",
    "__pycache__/module.pyc",
    ".git/config",
    "target/debug/main.rs",
    "coverage/lcov-report/index.html",
    "vendor/github.com/pkg/errors/errors.go",
    ".svelte-kit/generated/root.svelte",
    ".next/server/pages/index.js",
]

BINARY_PATHS = [
    "docs/screenshot.png",
    "static/logo.svg.png",
    "assets/font.woff2",
    "media/demo.mp4",
    "release/app.zip",
    "lib/native.so",
    "bundle/app.wasm",
    "docs/spec.pdf",
    "data/embeddings.bin",
    "models/model.safetensors",
    "data/local.sqlite3",
]

SECRET_PATHS = [
    ".env",
    ".env.local",
    ".env.production",
    "backend/.env",
    "config/credentials.json",
    "config/secrets.yaml",
    "certs/server.pem",
    "certs/server.key",
    "keys/app.p12",
    "deploy/id_rsa",
    ".npmrc",
    ".pypirc",
    ".netrc",
]

GENERATED_PATHS = [
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Cargo.lock",
    "go.sum",
    "static/vendor.min.js",
    "static/app.min.css",
    "static/app.js.map",
    "tests/__snapshots__/App.test.js.snap",
]

UNSUPPORTED_PATHS = [
    "docs/notes.pages",
    "data/sample.csv.gz2",
    "weird.unknownext",
]


@pytest.mark.parametrize("path", ALLOWED_PATHS)
def test_allows_source_and_doc_paths(path: str) -> None:
    assert should_include_path(path) is True


@pytest.mark.parametrize("path", IGNORED_DIR_PATHS)
def test_skips_dependency_and_build_directories(path: str) -> None:
    decision = classify_path(path)
    assert decision.include is False
    assert decision.reason == REASON_IGNORED_DIR


@pytest.mark.parametrize("path", BINARY_PATHS)
def test_skips_binaries(path: str) -> None:
    decision = classify_path(path)
    assert decision.include is False
    assert decision.reason == REASON_BINARY_EXT


@pytest.mark.parametrize("path", SECRET_PATHS)
def test_skips_secret_like_paths(path: str) -> None:
    decision = classify_path(path)
    assert decision.include is False
    assert decision.reason == REASON_SECRET_LIKE


@pytest.mark.parametrize("path", GENERATED_PATHS)
def test_skips_generated_artifacts(path: str) -> None:
    decision = classify_path(path)
    assert decision.include is False
    assert decision.reason == REASON_GENERATED


@pytest.mark.parametrize("path", UNSUPPORTED_PATHS)
def test_skips_unknown_extensions(path: str) -> None:
    decision = classify_path(path)
    assert decision.include is False
    assert decision.reason == REASON_UNSUPPORTED_EXT


@pytest.mark.parametrize(
    "path",
    [".env.example", ".env.sample", ".env.template"],
)
def test_env_templates_stay_allowed(path: str) -> None:
    assert should_include_path(path) is True


def test_size_cap_applies_to_allowed_extensions() -> None:
    assert should_include_path("app/main.py", MAX_FILE_BYTES) is True

    decision = classify_path("app/main.py", MAX_FILE_BYTES + 1)
    assert decision.include is False
    assert decision.reason == REASON_TOO_LARGE


def test_denylist_wins_over_allowed_extension() -> None:
    # Same filename is kept at the top level but skipped under node_modules.
    assert should_include_path("index.js") is True
    assert should_include_path("node_modules/pkg/index.js") is False


def test_empty_and_directory_paths_are_skipped() -> None:
    assert should_include_path("") is False
    assert should_include_path("src/") is False


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("app/main.py", "python"),
        ("src/api.ts", "typescript"),
        ("README.md", "markdown"),
        ("Dockerfile", "dockerfile"),
        ("Makefile", "make"),
        ("infra/main.tf", "terraform"),
        ("CODEOWNERS", None),
    ],
)
def test_guess_language(path: str, expected: str | None) -> None:
    assert guess_language(path) == expected
