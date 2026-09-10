"""Pydantic models mirroring `POST /advisory-chat` in docs/api-contract.md."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatContext(BaseModel):
    business_id: Optional[str] = None
    conversation_id: Optional[str] = None


class AdvisoryChatRequest(BaseModel):
    message: str = Field(min_length=1)
    # ISO 639-1. Omitted means "detect it for me" — see app/language.py.
    language: Optional[str] = None
    context: Optional[ChatContext] = None


class CitedSource(BaseModel):
    scheme: str
    document: str
    url: Optional[str] = None


class AdvisoryChatResponse(BaseModel):
    request_id: str
    response_text: str
    # Required by the contract but may be empty — an ungrounded answer returns []
    # rather than dropping the key.
    cited_sources: List[CitedSource]
    detected_language: str
