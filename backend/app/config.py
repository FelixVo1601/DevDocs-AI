"""Application settings loaded from environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "DevDocs AI"
    environment: str = "development"

    database_url: str = "postgresql://devdocs:change_me@localhost:5432/devdocs"

    frontend_url: str = "http://localhost:5173"
    # Comma-separated explicit origins (always allowed).
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    backend_host: str = "127.0.0.1"
    backend_port: int = 8001

    session_cookie_name: str = "devdocs_session"
    session_expire_minutes: int = 60 * 24 * 7  # 7 days
    cookie_secure: bool = False

    # Used for OAuth state signing + Fernet key derivation. Required for GitHub OAuth.
    secret_key: str = "dev-only-change-me-in-production"

    github_client_id: str = ""
    github_client_secret: str = ""
    github_redirect_uri: str = "http://localhost:8001/auth/github/callback"
    github_oauth_scopes: str = "read:user repo"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() in {"development", "dev", "local"}

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins

    @property
    def cors_origin_regex(self) -> str | None:
        """In development, allow any localhost / 127.0.0.1 Vite port without manual edits."""
        if self.is_development:
            return r"http://(localhost|127\.0\.0\.1):\d+"
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
