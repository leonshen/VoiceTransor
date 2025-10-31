# -*- coding: utf-8 -*-
"""
Local LLM text operations using Ollama.
- Provides privacy-preserving text processing without cloud APIs
- Compatible interface with openai_textops.py
- Supports multiple models: llama3.1, qwen2.5, gemma2, etc.
"""
from __future__ import annotations
from typing import Optional, Dict, Any, List
import requests
import json
import sys

import logging
log = logging.getLogger(__name__)

try:
    # markdown-it-py is robust and small; optional
    from markdown_it import MarkdownIt  # type: ignore
    _md = MarkdownIt()
except Exception:
    _md = None


# Default Ollama models
DEFAULT_MODELS = [
    "llama3.1:8b",      # Default, strong in English
    "qwen2.5:7b",       # Balanced Chinese/English
    "gemma2:9b",        # Google's model
]


def check_ollama_available(base_url: str = "http://localhost:11434") -> tuple[bool, str]:
    """
    Check if Ollama service is running and accessible.

    Returns:
        (is_available, message): bool and status message
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=1)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            model_names = [m.get("name", "") for m in models]
            return True, f"Ollama is running. Available models: {', '.join(model_names[:5])}"
        else:
            return False, f"Ollama responded with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Ollama. Please ensure Ollama is installed and running."
    except requests.exceptions.Timeout:
        return False, "Connection to Ollama timed out."
    except Exception as e:
        return False, f"Error checking Ollama: {str(e)}"


def list_ollama_models(base_url: str = "http://localhost:11434") -> List[str]:
    """
    Get list of installed Ollama models.

    Returns:
        List of model names
    """
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=1)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]
        return []
    except Exception as e:
        log.warning(f"Failed to list Ollama models: {e}")
        return []


def _mk_user_payload(transcript: str, user_prompt: str) -> str:
    """
    Build a compact prompt for the LLM.
    """
    return (
        "Follow the instruction below and apply it to the provided source text.\n\n"
        "Instruction (from user):\n"
        f"{user_prompt.strip()}\n\n"
        "Source text:\n"
        f"{transcript.strip()}\n\n"
    )


def _to_html(markdown_text: str) -> Optional[str]:
    """Convert markdown to HTML."""
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
    model: str = "llama3.1:8b",
    base_url: str = "http://localhost:11434",
    signals=None,
    stop_flag=None,
) -> Dict[str, Any]:
    """
    Perform a generic text operation using Ollama.

    Args:
        transcript: The source text to process
        prompt: User instruction for the LLM
        model: Ollama model name (e.g., "llama3.1:8b")
        base_url: Ollama API base URL
        signals: WorkerSignals for progress updates
        stop_flag: threading.Event for cancellation

    Returns:
        dict with keys: {"plain": str, "markdown": Optional[str], "html": Optional[str]}

    Raises:
        RuntimeError: If Ollama is not available or request fails
    """
    # Check Ollama availability
    is_available, status_msg = check_ollama_available(base_url)
    if not is_available:
        # Platform-specific installation instructions
        if sys.platform == "win32":
            install_script = "install_ollama.bat"
            run_cmd = "install_ollama.bat"
        else:
            install_script = "install_ollama.sh"
            run_cmd = "bash install_ollama.sh"

        raise RuntimeError(
            f"Ollama is not available: {status_msg}\n\n"
            "Please install and start Ollama:\n"
            f"1. Run '{run_cmd}' in the project directory, OR\n"
            "2. Download from https://ollama.com/download\n"
            "3. After installation, run 'ollama serve' in a terminal"
        )

    if signals:
        signals.message.emit(f"Sending request to Ollama ({model})...")

    user_payload = _mk_user_payload(transcript, prompt)
    log.debug(f"Using Ollama model: {model}")
    log.debug(f"User payload:\n{user_payload}")

    # Prepare the request
    api_url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": user_payload,
        "system": "You are a concise, accurate assistant.",
        "stream": False,  # Non-streaming for simplicity
        "options": {
            "temperature": 0.2,
        }
    }

    try:
        # Send request to Ollama
        if signals:
            signals.message.emit(f"Processing with {model}...")

        response = requests.post(
            api_url,
            json=payload,
            timeout=300,  # 5 minutes timeout for long processing
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Ollama API returned status {response.status_code}:\n"
                f"{response.text}"
            )

        # Parse response
        result = response.json()
        text = result.get("response", "").strip()

        if not text:
            raise RuntimeError("Ollama returned an empty response")

        log.debug(f"Ollama response:\n{text}")

        md = text.strip()
        html = _to_html(md)

        if signals:
            signals.message.emit("Text operation finished.")

        return {"plain": text, "markdown": md, "html": html}

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Request to Ollama timed out. The model may be too slow or not responding.\n"
            "Try using a smaller model or check if Ollama is running properly."
        )
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Lost connection to Ollama during processing.\n"
            "Please ensure Ollama is still running."
        )
    except Exception as e:
        raise RuntimeError(f"Failed to process text with Ollama: {str(e)}")


def pull_ollama_model(model: str, base_url: str = "http://localhost:11434") -> bool:
    """
    Download/pull an Ollama model.

    Args:
        model: Model name to pull (e.g., "llama3.1:8b")
        base_url: Ollama API base URL

    Returns:
        True if successful, False otherwise
    """
    try:
        api_url = f"{base_url}/api/pull"
        payload = {"name": model, "stream": False}

        response = requests.post(api_url, json=payload, timeout=600)  # 10 min timeout
        return response.status_code == 200
    except Exception as e:
        log.error(f"Failed to pull model {model}: {e}")
        return False
