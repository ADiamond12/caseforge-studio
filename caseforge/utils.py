from __future__ import annotations

import re
from collections import Counter


STOPWORDS = {
    "a",
    "an",
    "and",
    "the",
    "to",
    "of",
    "for",
    "with",
    "on",
    "in",
    "by",
    "from",
    "into",
    "is",
    "it",
    "this",
    "that",
    "as",
    "be",
    "can",
    "we",
    "you",
    "i",
    "or",
    "but",
    "not",
    "about",
    "my",
    "your",
    "our",
}

SHORT_TECH_TOKENS = {"ai", "ml", "ui", "ux", "db"}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", text)]


def significant_tokens(text: str, *, limit: int = 8) -> tuple[str, ...]:
    tokens = [
        token
        for token in tokenize(text)
        if token not in STOPWORDS and (len(token) > 2 or token in SHORT_TECH_TOKENS)
    ]
    counts = Counter(tokens)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return tuple(token for token, _ in ranked[:limit])


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "caseforge-dossier"


def titleize(value: str) -> str:
    return " ".join(part.capitalize() for part in re.split(r"[\s_-]+", value.strip()) if part)


def choose_best_title(brief: str, explicit_title: str | None) -> str:
    if explicit_title:
        return explicit_title.strip()
    for line in brief.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            heading = stripped.lstrip("#").strip()
            if heading:
                return heading
        if stripped:
            break
    tokens = significant_tokens(brief, limit=3)
    if tokens:
        return titleize(" ".join(tokens))
    return "Interview Project"
