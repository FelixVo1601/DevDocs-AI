"""Schemas for GitHub connection status (no secrets)."""

from pydantic import BaseModel, ConfigDict


class GitHubConnectionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    connected: bool
    github_user_id: int | None = None
    github_login: str | None = None
    scope: str | None = None
