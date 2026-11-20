"""Generate grounded answers with the Claude API."""

import anthropic

from . import config
from .retriever import Hit

SYSTEM_PROMPT = (
    "You answer questions using only the document excerpts provided in the user message. "
    "Rules: (1) If the excerpts do not contain the answer, say you could not find it in the "
    "documents. Do not guess or use outside knowledge. (2) Keep answers short and clear. "
    "(3) After each fact, cite its source in square brackets using the label of the excerpt, "
    "for example [leave_policy.txt #2]."
)


def label(hit: Hit) -> str:
    return f"{hit.chunk.source} #{hit.chunk.index}"


def build_context(hits: list[Hit]) -> str:
    """Format retrieved chunks as labelled excerpts for the prompt."""
    return "\n\n".join(f"[{label(h)}]\n{h.chunk.text}" for h in hits)


def build_user_message(question: str, hits: list[Hit]) -> str:
    return (
        f"Document excerpts:\n\n{build_context(hits)}\n\n"
        f"Question: {question}"
    )


def ask_claude(question: str, hits: list[Hit]) -> str:
    """Send the question plus retrieved excerpts to Claude and return its answer."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(question, hits)}],
    )
    return "".join(block.text for block in response.content if block.type == "text").strip()
