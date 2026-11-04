"""The agent's two tools: a webpage reader and a document reader.

Both tools are intentionally simple (per the proposal's "lightweight,
self-contained" scope). Carson: this is a first working pass so the
rest of the testbed has something real to call. Feel free to extend
these (better HTML cleaning, more file types, timeouts/size limits
tuned differently, etc.) — just keep the function signatures and the
TOOLS schema list in sync, since agent.py dispatches on tool "name".
"""

from __future__ import annotations

import os

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

MAX_CONTENT_CHARS = 8000  # keep tool output small enough for the context window
REQUEST_TIMEOUT_SECS = 10

# Tool schemas in Anthropic's tool-use format. Passed to the API so the
# model knows these exist and how to call them.
TOOLS = [
    {
        "name": "webpage_reader",
        "description": (
            "Fetch a webpage by URL and return its visible text content "
            "(HTML tags, scripts, and styles stripped out). Use this when "
            "the user asks you to read, summarize, or answer questions "
            "about a specific webpage."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL of the webpage to fetch, including http(s)://",
                }
            },
            "required": ["url"],
        },
    },
    {
        "name": "document_reader",
        "description": (
            "Read a local document (.txt or .pdf) from the testbed's "
            "document store and return its text content. Use this when "
            "the user asks you to read, summarize, or answer questions "
            "about a document they've provided."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the document, relative to the testbed's document store.",
                }
            },
            "required": ["path"],
        },
    },
]

# Tools are only allowed to read from this directory. This is the one
# authorization boundary the testbed enforces today; the tool_abuse_path
# attack in attacks/direct_injection_payloads.py exists specifically to
# probe whether a direct instruction can talk the agent into asking for
# a path outside of it.
DOCUMENT_STORE_ROOT = os.path.join(os.path.dirname(__file__), "..", "sample_documents")


def webpage_reader(url: str) -> str:
    """Fetch `url` and return cleaned, truncated visible text."""
    try:
        resp = requests.get(
            url,
            timeout=REQUEST_TIMEOUT_SECS,
            headers={"User-Agent": "cis6614-agentic-ui-testbed/0.1"},
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return f"[webpage_reader error] could not fetch {url}: {exc}"

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(separator=" ").split())
    return text[:MAX_CONTENT_CHARS]


def document_reader(path: str) -> str:
    """Read a local document from DOCUMENT_STORE_ROOT and return its text.

    Resolves `path` against DOCUMENT_STORE_ROOT and refuses anything that
    escapes it (via .. or an absolute path), so a request for something
    like /etc/passwd fails closed rather than silently reading it.
    """
    if os.path.isabs(path):
        return (
            f"[document_reader error] refused: '{path}' is an absolute path; "
            "only paths inside the document store are allowed."
        )

    root = os.path.realpath(DOCUMENT_STORE_ROOT)
    requested = os.path.realpath(os.path.join(root, path))

    if not requested.startswith(root + os.sep) and requested != root:
        return (
            f"[document_reader error] refused: '{path}' resolves outside the "
            "document store and was not read."
        )

    if not os.path.isfile(requested):
        return f"[document_reader error] no such file: {path}"

    try:
        if requested.lower().endswith(".pdf"):
            reader = PdfReader(requested)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            with open(requested, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
    except Exception as exc:  # noqa: BLE001 - surface any read failure to the agent, not a crash
        return f"[document_reader error] failed to read {path}: {exc}"

    return text[:MAX_CONTENT_CHARS]


DISPATCH = {
    "webpage_reader": lambda tool_input: webpage_reader(tool_input["url"]),
    "document_reader": lambda tool_input: document_reader(tool_input["path"]),
}


def run_tool(name: str, tool_input: dict) -> str:
    """Execute a tool call by name. Raises KeyError for an unknown tool name."""
    return DISPATCH[name](tool_input)
