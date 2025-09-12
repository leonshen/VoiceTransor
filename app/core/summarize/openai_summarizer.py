# -*- coding: utf-8 -*-
"""OpenAI-based summarization with Project-aware API usage."""
from __future__ import annotations
import os
from typing import Literal, Optional, Dict, Any

STYLE = {
    "brief": "Write a very concise, bullet-style summary (~100-150 chars).",
    "normal": "Write a clear paragraph summary (~200-300 chars) covering key points.",
    "detailed": "Write a detailed summary (~400-600 chars) with structured takeaways.",
}


def build_prompt(text: str, style: Literal["brief", "normal", "detailed"]) -> str:
    """Build a summarization prompt."""
    hint = STYLE.get(style, STYLE["normal"])
    return (
        f"{hint}\n\n"
        "Requirements:\n"
        "- Keep the original language (Chinese in, Chinese out; English in, English out).\n"
        "- Do not fabricate facts; stay faithful to the source.\n"
        "- Keep it readable and logically clear.\n\n"
        "Source:\n"
        "----\n"
        f"{text}\n"
        "----\n"
    )


def _mk_client(api_key: str, project_id: Optional[str]):
    """Create OpenAI client; prefer project-aware constructor if available."""
    from openai import OpenAI  # type: ignore

    project_id = (project_id or os.getenv("OPENAI_PROJECT") or "").strip() or None
    if project_id:
        try:
            return OpenAI(api_key=api_key, project=project_id), project_id, True
        except TypeError:
            return OpenAI(api_key=api_key), project_id, False
    else:
        return OpenAI(api_key=api_key), None, False


def _raise_humanized_error(e: Exception) -> RuntimeError:
    """Return a RuntimeError with actionable guidance for project mismatch."""
    msg = str(e)
    if "OpenAI-Project" in msg or "mismatched_project" in msg or "Project `" in msg:
        msg += (
            "\n\nHint: Your API key may be project-scoped or your org enforces Projects. "
            "Set the correct Project ID (proj_...) in settings, or create a key under that Project."
        )
    return RuntimeError(f"OpenAI request failed: {msg}")


def summarize_with_openai(
    text: str,
    api_key: str,
    model: str = "gpt-4o-mini",
    style: str = "normal",
    project: Optional[str] = None,
) -> str:
    """Summarize text with the Chat Completions API.

    Handles both new SDKs (constructor supports project) and legacy ones
    (falls back to passing 'OpenAI-Project' via extra_headers).
    """
    try:
        from openai import OpenAI  # noqa: F401
    except Exception as e:
        raise RuntimeError("openai package not installed. Run: pip install openai") from e

    prompt = build_prompt(text, style if style in STYLE else "normal")
    try:
        client, project_id, ctor_supported = _mk_client(api_key=api_key, project_id=project)
        req_kwargs: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a concise and accurate summarizer."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        if project_id and not ctor_supported:
            req_kwargs["extra_headers"] = {"OpenAI-Project": project_id}

        resp = client.chat.completions.create(**req_kwargs)
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        raise _raise_humanized_error(e)
