"""Pydantic request/response schemas."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Length = Literal["short", "medium", "long"]
Language = Literal["en", "zh"]
CitationStyle = Literal["apa", "mla", "ieee", "gbt7714"]


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=80)

    @field_validator("email")
    @classmethod
    def _email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("invalid email address")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PaperCreateRequest(BaseModel):
    title: str = Field(min_length=4, max_length=300)
    field: str = Field(default="", max_length=120)
    keywords: List[str] = Field(default_factory=list)
    length: Length = "medium"
    citation_style: CitationStyle = "gbt7714"
    language: Language = "zh"
    target_words: Optional[int] = Field(default=None, ge=800, le=12000)
    reference_count: int = Field(default=12, ge=4, le=40)
    instructions: str = Field(default="", max_length=2000)

    @field_validator("keywords")
    @classmethod
    def _keywords(cls, value: List[str]) -> List[str]:
        cleaned: List[str] = []
        for item in value:
            item = item.strip()[:40]
            if item and item not in cleaned:
                cleaned.append(item)
        return cleaned[:12]


class SectionUpdateRequest(BaseModel):
    content: str


class PaperPatchRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=300)
    sections: Optional[Dict[str, str]] = None


class RegenerateSectionRequest(BaseModel):
    instructions: str = Field(default="", max_length=1000)


class LiteratureSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    limit: int = Field(default=15, ge=1, le=50)
    year_from: Optional[int] = Field(default=None, ge=1900, le=2100)
    sources: List[str] = Field(default_factory=list)


class ApiStatus(BaseModel):
    version: str
    environment: str
    llm_configured: bool
    provider: str
    model: str
    model_fast: str
    literature_sources: List[str]
    citation_styles: List[str]
    length_options: List[str]
    language_options: Dict[str, str]
    max_concurrent_jobs: int
    allow_registration: bool


class StatsOut(BaseModel):
    total: int
    completed: int
    running: int
    failed: int
    words: int
    by_style: Dict[str, int]


class PaperSummary(BaseModel):
    id: str
    title: str
    status: str
    stage: str
    progress: int
    created_at: str
    updated_at: str
    language: str
    citation_style: str
    word_count: int
    error: str = ""


class PaperDetail(BaseModel):
    id: str
    title: str
    status: str
    stage: str
    progress: int
    created_at: str
    updated_at: str
    finished_at: Optional[str] = None
    error: str = ""
    request: Dict[str, Any] = Field(default_factory=dict)
    outline: Dict[str, Any] = Field(default_factory=dict)
    sections: Dict[str, str] = Field(default_factory=dict)
    references: List[Dict[str, Any]] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)
    images: List[Dict[str, Any]] = Field(default_factory=list)
