"""Schemas for GitHub connection and repository listing (no secrets)."""

from pydantic import BaseModel, ConfigDict, Field


class GitHubConnectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connected: bool
    github_user_id: int | None = None
    github_login: str | None = None
    scope: str | None = None


class GitHubRepo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: str | None = None
    default_branch: str
    language: str | None = None
    updated_at: str | None = None


class GitHubRepoListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repos: list[GitHubRepo] = Field(default_factory=list)
    count: int


class SelectRepositoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    github_repo_id: int = Field(gt=0)


class SelectedRepositoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    github_repo_id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    default_branch: str
    description: str | None = None


class SelectedRepositoryEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected: SelectedRepositoryResponse | None = None


class FetchedFileChunk(BaseModel):
    """Citation-ready chunk: path + inclusive line range + text."""

    model_config = ConfigDict(extra="forbid")

    path: str
    chunk_index: int
    start_line: int
    end_line: int
    content: str
    token_count: int | None = None


class FetchedRepositoryFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    content_sha: str
    language: str | None = None
    size_bytes: int | None = None
    line_count: int | None = None
    chunk_count: int = 0
    chunks: list[FetchedFileChunk] = Field(default_factory=list)


class FetchRepositoryContentsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: str
    full_name: str
    ref: str
    commit_sha: str
    file_count: int
    chunk_count: int = 0
    skipped_over_cap: int = 0
    files: list[FetchedRepositoryFile] = Field(default_factory=list)


class EmbedRepositoryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    model: str
    embedded: int
    skipped_empty: int = 0
    skipped_existing: int = 0
    truncated: int = 0
    force: bool = False


class IndexJobInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    status: str
    error_message: str | None = None
    commit_sha: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None


class IndexSelectedInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    default_branch: str


class IndexStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    selected: IndexSelectedInfo | None = None
    job: IndexJobInfo | None = None
    file_count: int = 0
    chunk_count: int = 0
    embedded_count: int = 0
    embedded: int | None = None
    skipped_empty: int | None = None
    truncated: int | None = None
