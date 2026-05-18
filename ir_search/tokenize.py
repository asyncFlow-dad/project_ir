from __future__ import annotations

import unicodedata
from collections.abc import Iterable

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
    "는",
    "은",
    "이",
    "가",
    "을",
    "를",
    "에",
    "의",
    "와",
    "과",
    "로",
    "으로",
}


def tokenize(value: object) -> list[str]:
    text = unicodedata.normalize("NFKC", str(value)).lower()
    return [
        term
        for term in _alnum_terms(text)
        if len(term) > 1 and term not in STOP_WORDS
    ]


def _alnum_terms(text: str) -> Iterable[str]:
    token: list[str] = []
    for char in text:
        if char.isalpha() or char.isnumeric():
            token.append(char)
            continue
        if token:
            yield "".join(token)
            token.clear()
    if token:
        yield "".join(token)
