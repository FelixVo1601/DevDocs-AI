"""Which repository paths to keep when fetching contents (MVP filters)."""

from __future__ import annotations

from pathlib import PurePosixPath

# Skip any path whose parts include these directory names.
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".next",
        ".nuxt",
        "dist",
        "build",
        "coverage",
        "vendor",
        "target",
        "bin",
        "obj",
    }
)

ALLOWED_EXTENSIONS = frozenset(
    {
        ".py",
        ".pyi",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".md",
        ".mdx",
        ".json",
        ".yml",
        ".yaml",
        ".toml",
        ".ini",
        ".cfg",
        ".txt",
        ".rst",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".cs",
        ".sql",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".vue",
        ".svelte",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cc",
        ".rb",
        ".php",
        ".swift",
        ".sh",
        ".bash",
        ".zsh",
        ".ps1",
        ".graphql",
        ".gql",
        ".proto",
        ".xml",
    }
)

SPECIAL_FILENAMES = frozenset(
    {
        "dockerfile",
        "makefile",
        "gemfile",
        "procfile",
        "license",
        "licence",
        "readme",
        ".gitignore",
        ".dockerignore",
        ".env.example",
    }
)

EXTENSION_LANGUAGE = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".md": "markdown",
    ".mdx": "markdown",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".cs": "csharp",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".vue": "vue",
    ".svelte": "svelte",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".sh": "shell",
    ".bash": "shell",
    ".ps1": "powershell",
}

MAX_FILE_BYTES = 200_000
MAX_FILES_PER_FETCH = 150


def guess_language(path: str) -> str | None:
    name = PurePosixPath(path).name.lower()
    if name == "dockerfile":
        return "dockerfile"
    return EXTENSION_LANGUAGE.get(PurePosixPath(path).suffix.lower())


def should_include_path(path: str, size_bytes: int | None) -> bool:
    """Return True if this blob path should be fetched for indexing."""
    if not path or path.endswith("/"):
        return False

    parts = PurePosixPath(path).parts
    if any(part in SKIP_DIR_NAMES for part in parts):
        return False

    if size_bytes is not None and size_bytes > MAX_FILE_BYTES:
        return False

    name = PurePosixPath(path).name.lower()
    if name in SPECIAL_FILENAMES:
        return True

    suffix = PurePosixPath(path).suffix.lower()
    return suffix in ALLOWED_EXTENSIONS
