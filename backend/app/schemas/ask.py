"""Ask endpoint schemas (answer + citations)."""

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=4000)
    k: int = Field(default=5, ge=1, le=20)


class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chunk_id: str
    path: str
    chunk_index: int
    start_line: int | None = None
    end_line: int | None = None
    distance: float


class AskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str
    question: str
    answer: str
    model: str
    citations: list[Citation] = Field(default_factory=list)
