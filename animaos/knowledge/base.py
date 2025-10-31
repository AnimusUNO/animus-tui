"""Local knowledge base for animaOS.

Provides lightweight keyword search over the Animus repository docs so that
knowledge mode can respond without contacting remote services.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


class KnowledgeNotFound(Exception):
    """Raised when the knowledge base cannot answer a query."""


@dataclass
class Document:
    """Simple text document."""

    path: Path
    text: str

    def score(self, tokens: Sequence[str]) -> int:
        """Return a simple frequency score for the given tokens."""

        lowered = self.text.lower()
        return sum(lowered.count(token) for token in tokens)


class KnowledgeBase:
    """File-backed knowledge store with naive keyword search."""

    def __init__(self, roots: Iterable[Path], encoding: str = "utf-8") -> None:
        self.roots = [Path(root) for root in roots]
        self.encoding = encoding
        self.documents: List[Document] = []
        self._loaded = False

    def load(self) -> None:
        """Load documents from disk; no-op if already loaded."""

        if self._loaded:
            return

        for root in self.roots:
            if not root.exists():
                continue
            if root.is_file():
                self._add_file(root)
            elif root.is_dir():
                for extension in ("*.md", "*.txt"):
                    for path in root.rglob(extension):
                        self._add_file(path)

        self._loaded = True

    def _add_file(self, path: Path) -> None:
        try:
            text = path.read_text(encoding=self.encoding, errors="ignore")
        except OSError:
            return
        if text.strip():
            self.documents.append(Document(path=path, text=text))

    def search(self, query: str, top: int = 1) -> List[tuple[str, str]]:
        """Return top matches as (document_name, snippet)."""

        if not self._loaded:
            self.load()

        tokens = [token for token in query.lower().split() if len(token) > 2]
        if not tokens:
            return []

        scored = []
        for document in self.documents:
            score = document.score(tokens)
            if score:
                snippet = self._extract_snippet(document.text, tokens)
                scored.append((score, document.path.name, snippet))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [(name, snippet) for _, name, snippet in scored[:top]]

    def answer(self, query: str) -> str:
        """Return a formatted answer for the query."""

        matches = self.search(query, top=1)
        if not matches:
            raise KnowledgeNotFound(query)

        name, snippet = matches[0]
        return f"[{name}] {snippet.strip()}"

    @staticmethod
    def _extract_snippet(text: str, tokens: Sequence[str], window: int = 320) -> str:
        lowered = text.lower()
        for token in tokens:
            idx = lowered.find(token)
            if idx != -1:
                start = max(0, idx - 120)
                end = min(len(text), idx + window)
                raw = text[start:end]
                return " ".join(raw.split())
        trimmed = text[:window]
        return " ".join(trimmed.split())


def default_knowledge_base() -> KnowledgeBase:
    """Construct the default knowledge base from project docs."""

    project_root = Path.cwd()
    roots = [project_root / "README.md", project_root / "docs"]
    return KnowledgeBase(roots=roots)

