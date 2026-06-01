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
    "build",
    "create",
    "design",
    "ship",
    "develop",
    "make",
    "implement",
    "turn",
    "turns",
}

SHORT_TECH_TOKENS = {"ai", "ml", "ui", "ux", "db"}
TITLE_ACRONYMS = {"ai": "AI", "ml": "ML", "ui": "UI", "ux": "UX", "api": "API", "db": "DB", "llm": "LLM"}


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_-]*", text)]


def significant_tokens(text: str, *, limit: int = 8) -> tuple[str, ...]:
    tokens = [
        token
        for token in tokenize(text)
        if token not in STOPWORDS and (len(token) > 2 or token in SHORT_TECH_TOKENS)
    ]
    counts = Counter(tokens)
    first_seen = {token: tokens.index(token) for token in counts}
    ranked = sorted(counts.items(), key=lambda item: (-item[1], first_seen[item[0]]))
    return tuple(token for token, _ in ranked[:limit])


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "caseforge-blueprint"


def titleize(value: str) -> str:
    words = []
    for part in re.split(r"[\s_-]+", value.strip()):
        if not part:
            continue
        words.append(TITLE_ACRONYMS.get(part.lower(), part.capitalize()))
    return " ".join(words)


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

    inferred = infer_product_title(brief)
    if inferred:
        return inferred

    tokens = significant_tokens(brief, limit=3)
    if tokens:
        return titleize(" ".join(tokens))
    return "Project Blueprint"


def infer_product_title(brief: str) -> str:
    first_sentence = re.split(r"[.!?\n]", brief.strip(), maxsplit=1)[0]
    match = re.search(
        r"\b(?:build|create|design|ship|develop|make|implement)\s+(?:(?:an|a|the)\s+)?(.+?)(?:\s+that\b|\s+for\b|\s+with\b|\s+to\b|\s+into\b|$)",
        first_sentence,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""

    raw_title = match.group(1).strip(" :-")
    words = [word for word in re.split(r"\s+", raw_title) if word]
    if not words:
        return ""
    return titleize(" ".join(words[:5]))
