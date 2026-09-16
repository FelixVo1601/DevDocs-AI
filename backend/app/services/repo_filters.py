"""Which repository paths to keep when fetching contents (MVP filters)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

# Reason codes returned by classify_path (also used for skip logging).
REASON_EMPTY_PATH = "empty-path"
REASON_IGNORED_DIR = "ignored-directory"
REASON_SECRET_LIKE = "secret-like"
REASON_BINARY_EXT = "binary-extension"
REASON_GENERATED = "generated-artifact"
REASON_TOO_LARGE = "too-large"
REASON_UNSUPPORTED_EXT = "unsupported-extension"
REASON_ALLOWED_FILENAME = "allowed-filename"
REASON_ALLOWED_EXT = "allowed-extension"

# Skip any path containing one of these directory names.
SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".ssh",
        ".idea",
        ".vscode",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "bower_components",
        "jspm_packages",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".gradle",
        ".terraform",
        ".svelte-kit",
        ".next",
        ".nuxt",
        ".output",
        ".parcel-cache",
        ".cache",
        "dist",
        "build",
        "out",
        "coverage",
        "htmlcov",
        "site-packages",
        "vendor",
        "third_party",
        "target",
        "bin",
        "obj",
        "migrations_backup",
    }
)

# Common source and documentation extensions we index.
ALLOWED_EXTENSIONS = frozenset(
    {
        # Python
        ".py",
        ".pyi",
        # JS / TS
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".svelte",
        ".vue",
        # Docs / text
        ".md",
        ".mdx",
        ".rst",
        ".txt",
        ".adoc",
        # Config
        ".json",
        ".jsonc",
        ".yml",
        ".yaml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".properties",
        # Web
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".less",
        # Other languages
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".kts",
        ".scala",
        ".cs",
        ".fs",
        ".c",
        ".h",
        ".cc",
        ".cpp",
        ".hpp",
        ".m",
        ".mm",
        ".rb",
        ".php",
        ".swift",
        ".dart",
        ".ex",
        ".exs",
        ".erl",
        ".lua",
        ".pl",
        ".r",
        ".sql",
        # Shell / infra
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".ps1",
        ".psm1",
        ".tf",
        ".tfvars",
        # Schemas
        ".graphql",
        ".gql",
        ".proto",
        ".xml",
        ".xsd",
    }
)

# Extensionless or dot-prefixed files worth indexing.
ALLOWED_FILENAMES = frozenset(
    {
        "dockerfile",
        "containerfile",
        "makefile",
        "justfile",
        "rakefile",
        "gemfile",
        "procfile",
        "brewfile",
        "readme",
        "license",
        "licence",
        "notice",
        "changelog",
        "contributing",
        "authors",
        "codeowners",
        ".gitignore",
        ".gitattributes",
        ".dockerignore",
        ".editorconfig",
        ".env.example",
        ".env.sample",
        ".env.template",
    }
)

# Binary / non-text payloads: images, media, archives, compiled artifacts, models.
BINARY_EXTENSIONS = frozenset(
    {
        # Images
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".tif",
        ".tiff",
        ".ico",
        ".icns",
        ".webp",
        ".avif",
        ".psd",
        ".ai",
        # Fonts
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        # Audio / video
        ".mp3",
        ".wav",
        ".flac",
        ".ogg",
        ".mp4",
        ".m4a",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
        # Archives
        ".zip",
        ".tar",
        ".gz",
        ".tgz",
        ".bz2",
        ".xz",
        ".zst",
        ".7z",
        ".rar",
        ".jar",
        ".war",
        ".ear",
        # Compiled / native
        ".pyc",
        ".pyo",
        ".pyd",
        ".class",
        ".o",
        ".a",
        ".obj",
        ".lib",
        ".so",
        ".dll",
        ".dylib",
        ".exe",
        ".msi",
        ".wasm",
        # Documents
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".odt",
        ".ods",
        # Data / models
        ".db",
        ".sqlite",
        ".sqlite3",
        ".mdb",
        ".parquet",
        ".avro",
        ".bin",
        ".dat",
        ".pkl",
        ".pickle",
        ".npy",
        ".npz",
        ".h5",
        ".hdf5",
        ".pt",
        ".pth",
        ".ckpt",
        ".onnx",
        ".safetensors",
        ".gguf",
        # Disk images
        ".iso",
        ".dmg",
        ".img",
    }
)

# Generated or machine-managed files: huge, low signal for Q&A.
GENERATED_FILENAMES = frozenset(
    {
        "package-lock.json",
        "packages.lock.json",
        "npm-shrinkwrap.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "bun.lockb",
        "poetry.lock",
        "pipfile.lock",
        "uv.lock",
        "cargo.lock",
        "composer.lock",
        "gemfile.lock",
        "go.sum",
        "mix.lock",
        "podfile.lock",
        "pubspec.lock",
    }
)

GENERATED_SUFFIXES = (
    ".min.js",
    ".min.mjs",
    ".min.css",
    ".map",
    ".snap",
)

# Filenames that usually hold credentials.
SECRET_FILENAMES = frozenset(
    {
        ".env",
        ".envrc",
        ".netrc",
        ".npmrc",
        ".pypirc",
        ".pgpass",
        ".htpasswd",
        ".flaskenv",
        "credentials",
        "credentials.json",
        "credentials.yml",
        "credentials.yaml",
        "secrets.json",
        "secrets.yml",
        "secrets.yaml",
        "secring.gpg",
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
        "known_hosts",
        "service-account.json",
        "serviceaccount.json",
    }
)

# Key / certificate material.
SECRET_EXTENSIONS = frozenset(
    {
        ".pem",
        ".key",
        ".pfx",
        ".p12",
        ".p8",
        ".jks",
        ".keystore",
        ".truststore",
        ".ppk",
        ".asc",
        ".gpg",
        ".kdbx",
    }
)

# ".env.<anything>" is secret unless it is one of these templates.
ENV_TEMPLATE_NAMES = frozenset(
    {
        ".env.example",
        ".env.sample",
        ".env.template",
        ".env.defaults",
        ".env.dist",
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
    ".svelte": "svelte",
    ".vue": "vue",
    ".md": "markdown",
    ".mdx": "markdown",
    ".rst": "rst",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".scala": "scala",
    ".cs": "csharp",
    ".c": "c",
    ".h": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".dart": "dart",
    ".lua": "lua",
    ".r": "r",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".ps1": "powershell",
    ".tf": "terraform",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".proto": "protobuf",
    ".xml": "xml",
}

MAX_FILE_BYTES = 200_000
MAX_FILES_PER_FETCH = 150


@dataclass(frozen=True)
class FilterDecision:
    """Why a path was kept or skipped."""

    include: bool
    reason: str


def guess_language(path: str) -> str | None:
    name = PurePosixPath(path).name.lower()
    if name in {"dockerfile", "containerfile"}:
        return "dockerfile"
    if name in {"makefile", "justfile"}:
        return "make"
    return EXTENSION_LANGUAGE.get(PurePosixPath(path).suffix.lower())


def is_secret_like(path: str) -> bool:
    """True for credential-ish paths (env files, keys, certs, known secret names)."""
    name = PurePosixPath(path).name.lower()
    if name in ENV_TEMPLATE_NAMES:
        return False
    if name in SECRET_FILENAMES:
        return True
    if name == ".env" or name.startswith(".env."):
        return True
    if name.startswith("env.") and name.endswith((".local", ".prod", ".production")):
        return True
    return PurePosixPath(name).suffix in SECRET_EXTENSIONS


def is_generated_artifact(path: str) -> bool:
    """True for lockfiles, minified bundles, source maps, and test snapshots."""
    name = PurePosixPath(path).name.lower()
    if name in GENERATED_FILENAMES:
        return True
    return name.endswith(GENERATED_SUFFIXES)


def classify_path(path: str, size_bytes: int | None = None) -> FilterDecision:
    """
    Decide whether a repository blob should be fetched for indexing.

    Checks run denylist-first so noisy paths never slip through on a
    permitted extension (e.g. ``node_modules/foo/index.js``).
    """
    if not path or path.endswith("/"):
        return FilterDecision(False, REASON_EMPTY_PATH)

    pure = PurePosixPath(path)
    name = pure.name.lower()
    suffix = pure.suffix.lower()

    if any(part.lower() in SKIP_DIR_NAMES for part in pure.parts[:-1]):
        return FilterDecision(False, REASON_IGNORED_DIR)
    if is_secret_like(path):
        return FilterDecision(False, REASON_SECRET_LIKE)
    if suffix in BINARY_EXTENSIONS:
        return FilterDecision(False, REASON_BINARY_EXT)
    if is_generated_artifact(path):
        return FilterDecision(False, REASON_GENERATED)
    if size_bytes is not None and size_bytes > MAX_FILE_BYTES:
        return FilterDecision(False, REASON_TOO_LARGE)

    if name in ALLOWED_FILENAMES:
        return FilterDecision(True, REASON_ALLOWED_FILENAME)
    if suffix in ALLOWED_EXTENSIONS:
        return FilterDecision(True, REASON_ALLOWED_EXT)
    return FilterDecision(False, REASON_UNSUPPORTED_EXT)


def should_include_path(path: str, size_bytes: int | None = None) -> bool:
    """Return True if this blob path should be fetched for indexing."""
    return classify_path(path, size_bytes).include
