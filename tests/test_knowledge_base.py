"""Tests for the local knowledge base."""

from pathlib import Path

import pytest

from animaos.knowledge.base import KnowledgeBase, KnowledgeNotFound


def write_tmp(tmp_path: Path, name: str, content: str) -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_load_and_search(tmp_path: Path) -> None:
    write_tmp(tmp_path, "doc1.md", "Animus core architecture focuses on agents.")
    kb = KnowledgeBase([tmp_path])
    kb.load()

    results = kb.search("Animus agents architecture")
    assert results
    name, snippet = results[0]
    assert name == "doc1.md"
    assert "Animus" in snippet


def test_answer_no_results(tmp_path: Path) -> None:
    write_tmp(tmp_path, "doc2.md", "No relevant info here.")
    kb = KnowledgeBase([tmp_path])

    with pytest.raises(KnowledgeNotFound):
        kb.answer("something else")

