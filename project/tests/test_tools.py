"""Smoke tests for the tools, independent of any LLM.

    python -m pytest tests/
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_ui.tools import document_reader  # noqa: E402


def test_document_reader_reads_sample_file():
    text = document_reader("product_notes.txt")
    assert "Q3 release" in text


def test_document_reader_refuses_path_outside_store():
    text = document_reader("/etc/passwd")
    assert text.startswith("[document_reader error] refused")


def test_document_reader_refuses_parent_traversal():
    text = document_reader("../../../../etc/passwd")
    assert text.startswith("[document_reader error] refused")


def test_document_reader_missing_file():
    text = document_reader("does_not_exist.txt")
    assert text.startswith("[document_reader error] no such file")
