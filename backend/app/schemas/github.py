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


class FetchedRepositoryFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    content_sha: str
    language: str | None = None
    size_bytes: int | None = None
    line_count: int | None = None
    content: str


class FetchRepositoryContentsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: str
    full_name: str
    ref: str
    commit_sha: str
    file_count: int
    skipped_over_cap: int = 0
    files: list[FetchedRepositoryFile] = Field(default_factory=list)
