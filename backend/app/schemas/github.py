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
