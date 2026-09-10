"""Assembles an `/advisory-chat` response: detect -> retrieve -> ground -> cite.

The grounding contract with the model is the important part. We do not ask for
prose and then try to guess which document it came from; we ask for a structured
answer that names the chunk ids it used, and we build `cited_sources` from those
ids. A chunk id the model invents matches nothing and is dropped, and an answer
the extracts do not support comes back with ``grounded: false`` and an empty
`cited_sources` rather than a confident guess about someone's loan eligibility.
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Optional, Sequence, Tuple

from pydantic import BaseModel

from .config import MODE_RAG, Settings
from .conversation import Turn, get_store
from .language import detect_language, get_translator, language_name
from .mock_data import mock_answer
from .retrieval import Chunk, ScoredChunk, get_retriever
from .schemas import AdvisoryChatRequest


class AdvisoryError(Exception):
    """A failure that maps onto the contract's error shape."""

    def __init__(self, code: str, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class GroundedAnswer(BaseModel):
    """Structured output schema — the model fills this in, not free prose."""

    answer: str
    cited_chunk_ids: List[str]
    grounded: bool


SYSTEM_PROMPT = """\
You are the advisory assistant for a government-scheme guidance platform used by \
first-time and small entrepreneurs in India, many of them in rural districts and \
many applying for credit for the first time.

You will be given numbered EXTRACTS from official scheme documents. Those extracts \
are the only source of fact you may use.

Grounding rules:
- Every factual claim — eligibility, required documents, subsidy percentages, loan \
ceilings, tenure, moratorium, process steps, office names — must be supported by an \
extract. Never supply a number, percentage or deadline that is not in an extract.
- Set `cited_chunk_ids` to exactly the extract ids you relied on. Do not list an \
extract you did not use.
- If the extracts do not answer the question, set `grounded` to false, put an honest \
short reply in `answer` saying you do not have that in your scheme documents, suggest \
what the person could ask instead, and leave `cited_chunk_ids` empty. Do not fall back \
on general knowledge about these schemes.

Style rules:
- Write in the language named in the request, and only that language.
- Short sentences, everyday words, no financial jargon. If a technical term is \
unavoidable, explain it in half a sentence.
- Keep scheme names and institution names in their usual form (PMEGP, MUDRA, KVIC, \
DIC) rather than translating them.
- Answer the person directly. Do not mention "extracts", "documents provided", \
"context", or that you were given source material.
"""

# Shown when retrieval comes back empty — either nothing is ingested yet or the
# question genuinely is not covered. Same honest answer either way.
_NO_MATCH_TEXT: Dict[str, str] = {
    "en": (
        "I don't have anything in my scheme documents that answers this yet. I can help "
        "with PMEGP and MUDRA — try asking about eligibility, the documents you need, or "
        "how the application is processed."
    ),
    "hi": (
        "इस सवाल का जवाब फ़िलहाल मेरे पास मौजूद योजना दस्तावेज़ों में नहीं है। मैं PMEGP और मुद्रा "
        "योजना पर मदद कर सकता हूँ — पात्रता, ज़रूरी दस्तावेज़, या आवेदन की प्रक्रिया के बारे में पूछकर "
        "देखिए।"
    ),
}


def build_advisory_response(payload: AdvisoryChatRequest, settings: Settings) -> dict:
    message = payload.message.strip()
    # An explicit `language` in the request wins; the contract only asks us to
    # detect when the caller left it out.
    detected = payload.language or detect_language(message)
    conversation_id = payload.context.conversation_id if payload.context else None

    if settings.mode == MODE_RAG:
        response_text, cited_sources = _rag_answer(
            message=message,
            language=detected,
            conversation_id=conversation_id,
            settings=settings,
        )
    else:
        response_text, cited_sources = mock_answer(message, detected, settings.manifest_path)

    if conversation_id:
        get_store().append(
            conversation_id,
            Turn(role="user", content=message),
            Turn(role="assistant", content=response_text),
        )

    return {
        "request_id": str(uuid.uuid4()),
        "response_text": response_text,
        "cited_sources": cited_sources,
        "detected_language": detected,
    }


def _rag_answer(
    *,
    message: str,
    language: str,
    conversation_id: Optional[str],
    settings: Settings,
) -> Tuple[str, List[dict]]:
    hits = get_retriever(settings.chunks_path).search(message, settings.top_k)
    if not hits:
        return _no_match_text(language), []

    translator = get_translator(settings.bhashini_api_key)
    # With Bhashini configured we generate in English and translate; otherwise
    # Claude writes directly in the target language, which keeps scheme
    # terminology intact.
    generation_language = translator.pivot_language or language

    history = (
        get_store().history(conversation_id, settings.max_history_turns)
        if conversation_id
        else []
    )

    answer = _generate(
        settings=settings,
        message=message,
        language=generation_language,
        hits=hits,
        history=history,
    )

    text = answer.answer.strip()
    if translator.pivot_language and translator.pivot_language != language:
        text = translator.translate(text, source=translator.pivot_language, target=language)

    if not answer.grounded:
        return text, []
    return text, _sources_from_ids(answer.cited_chunk_ids, hits)


def _generate(
    *,
    settings: Settings,
    message: str,
    language: str,
    hits: Sequence[ScoredChunk],
    history: Sequence[Turn],
) -> GroundedAnswer:
    # Imported here so mock mode runs without the SDK installed.
    import anthropic

    messages: List[dict] = [
        {"role": turn.role, "content": turn.content} for turn in history
    ]
    messages.append({"role": "user", "content": _user_block(message, language, hits)})

    try:
        client = anthropic.Anthropic()
        response = client.messages.parse(
            model=settings.model,
            # A ceiling, not a target: answers are short, but adaptive thinking
            # draws from the same budget and a truncated answer is unrecoverable.
            max_tokens=16000,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    # Static prefix, so it caches cleanly across the whole demo.
                    # The volatile extracts live in the user message, after it.
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=messages,
            output_format=GroundedAnswer,
        )
    except anthropic.AuthenticationError as exc:
        raise AdvisoryError(
            "llm_unauthenticated",
            "No usable Anthropic credentials. Set ANTHROPIC_API_KEY or run `ant auth login`, "
            "or set ADVISORY_MODE=mock to run without the model.",
            status_code=503,
        ) from exc
    except TypeError as exc:
        # When no credential source resolves at all, the SDK raises this at
        # request-build time — before any HTTP call, so it's a TypeError, not
        # AuthenticationError. Same underlying problem, same response to the
        # caller; anything else named TypeError is a real bug and should surface.
        if "authentication" not in str(exc).lower():
            raise
        raise AdvisoryError(
            "llm_unauthenticated",
            "No usable Anthropic credentials. Set ANTHROPIC_API_KEY or run `ant auth login`, "
            "or set ADVISORY_MODE=mock to run without the model.",
            status_code=503,
        ) from exc
    except anthropic.APIConnectionError as exc:
        raise AdvisoryError(
            "llm_unreachable", "Could not reach the Anthropic API.", status_code=503
        ) from exc
    except anthropic.APIStatusError as exc:
        raise AdvisoryError(
            "llm_error", f"Anthropic API error: {exc.message}", status_code=502
        ) from exc

    if response.stop_reason == "refusal":
        raise AdvisoryError(
            "llm_refused", "The model declined to answer this request.", status_code=502
        )

    parsed = response.parsed_output
    if parsed is None:
        raise AdvisoryError(
            "llm_malformed_output", "The model did not return a usable answer.", status_code=502
        )
    return parsed


def _user_block(message: str, language: str, hits: Sequence[ScoredChunk]) -> str:
    extracts = "\n\n".join(_format_extract(hit.chunk) for hit in hits)
    return (
        f"Answer in: {language_name(language)} ({language})\n\n"
        f"Question: {message}\n\n"
        f"EXTRACTS:\n{extracts}"
    )


def _format_extract(chunk: Chunk) -> str:
    location = f"{chunk.scheme} — {chunk.document}"
    if chunk.page is not None:
        location += f" (page {chunk.page})"
    return f"[{chunk.id}] {location}\n{chunk.text}"


def _sources_from_ids(chunk_ids: Sequence[str], hits: Sequence[ScoredChunk]) -> List[dict]:
    """Map cited chunk ids back to documents, deduped, in the order cited.

    Ids that were not in the prompt are dropped — a hallucinated id cites nothing.
    """
    by_id: Dict[str, Chunk] = {hit.chunk.id: hit.chunk for hit in hits}
    sources: List[dict] = []
    seen = set()

    for chunk_id in chunk_ids:
        chunk = by_id.get(chunk_id)
        if chunk is None:
            continue
        key = (chunk.scheme, chunk.document, chunk.url)
        if key in seen:
            continue
        seen.add(key)
        source = {"scheme": chunk.scheme, "document": chunk.document}
        if chunk.url:
            source["url"] = chunk.url
        sources.append(source)

    return sources


def _no_match_text(language: str) -> str:
    return _NO_MATCH_TEXT.get(language, _NO_MATCH_TEXT["en"])
