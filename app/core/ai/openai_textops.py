# -*- coding: utf-8 -*-
"""
Generic text operations over transcript + user prompt, powered by OpenAI.
- Accepts an arbitrary instruction ("prompt") from UI
- Builds a compact, safe request using transcript as context
- Returns plain text + optional Markdown + HTML (if we can convert)
"""
from __future__ import annotations
from typing import Optional, Dict, Any
import os

import logging
log = logging.getLogger(__name__)

try:
    # markdown-it-py is robust and small; optional
    from markdown_it import MarkdownIt  # type: ignore
    _md = MarkdownIt()
except Exception:
    _md = None

# If you already have a helper/client factory in openai_summarizer.py, you can import it:
# from app.core.ai.openai_summarizer import _make_openai_client
# For isolation, we duplicate a tiny client factory here.

def _make_openai_client(api_key: Optional[str], project: Optional[str]):
    from openai import OpenAI  # OpenAI v1 SDK
    # Normalize empty strings to None, then fallback to env
    key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
    proj = (project or os.getenv("OPENAI_PROJECT") or "").strip()

    if not key:
        raise ValueError(
            "OpenAI API key is missing.\n"
            "Set it in Settings or define OPENAI_API_KEY environment variable."
        )

    return OpenAI(api_key=key, project=(proj or None))


def _mk_user_payload(transcript: str, user_prompt: str) -> str:
    """
    Build a compact prompt. We ask the model to answer in Markdown by default.
    """
    return (
        # "You are an expert text processor. Follow the instruction below and apply it to the provided source text.\n\n"
        "Follow the instruction below and apply it to the provided source text.\n\n"
        "Instruction (from user):\n"
        f"{user_prompt.strip()}\n\n"
        "Source text:\n"
        f"{transcript.strip()}\n\n"
        # "Output format: Return your answer in Markdown with clear structure (headings, lists, emphasis) "
        # "and avoid unnecessary preambles."
    )

def _to_html(markdown_text: str) -> Optional[str]:
    if not markdown_text:
        return None
    if _md is None:
        return None
    try:
        return _md.render(markdown_text)
    except Exception:
        return None

def run_text_op(
    *,
    transcript: str,
    prompt: str,
    model: str,
    api_key: Optional[str],
    project: Optional[str],
    signals=None,
    stop_flag=None,
) -> Dict[str, Any]:
    """
    Perform a generic text operation.

    Returns:
        dict with keys: {"plain": str, "markdown": Optional[str], "html": Optional[str]}
    """
    if signals:
        signals.message.emit("Sending the request to OpenAI and awaiting a response…")

    client = _make_openai_client(api_key, project)

    user_payload = _mk_user_payload(transcript, prompt)

    log.debug("user_payload: \n\n")
    log.debug( user_payload )


    # Chat Completions; you can swap to Responses API if you use that elsewhere
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a concise, accurate assistant."},
            {"role": "user", "content": user_payload},
        ],
        temperature=0.2,
    )

    text = resp.choices[0].message.content or ""
    log.debug(text)
    md = text.strip()
    html = _to_html(md)
    if signals:
        signals.message.emit("Text operation finished.")
    return {"plain": text, "markdown": md, "html": html}
