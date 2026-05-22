from __future__ import annotations

import re
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

QUERY_STOP_WORDS = STOP_WORDS | {
    "관한",
    "관련",
    "궁금",
    "궁금해",
    "대해",
    "말해",
    "말해줘",
    "보기",
    "설명",
    "설명해",
    "설명해줘",
    "알려",
    "알려줘",
    "위한",
    "조사",
    "조사해",
    "좀",
}

KOREAN_SUFFIXES = (
    "으로부터",
    "에게서는",
    "에서는",
    "에게서",
    "이라는",
    "라는",
    "으로",
    "에서",
    "에게",
    "께서",
    "까지",
    "부터",
    "보다",
    "처럼",
    "만큼",
    "하고",
    "이나",
    "거나",
    "이다",
    "이며",
    "이고",
    "입니다",
    "세요",
    "인가",
    "인지",
    "하는",
    "되는",
    "적인",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "에",
    "의",
    "와",
    "과",
    "로",
    "도",
    "만",
    "좀",
)

QUERY_REPLACEMENTS = (
    (r"에 대해 조사해 보기 위한 방법은\??", " 방법"),
    (r"에 대해 알려줘\.?", ""),
    (r"에 대해 설명해줘\.?", ""),
    (r"하기 위한 방법중", " 방법"),
    (r"하기 위한 방법은", " 방법"),
    (r"키우는 노하우좀", " 재배 방법"),
    (r"키우는 노하우", " 재배 방법"),
    (r"무엇인지 알려줘\.?", ""),
    (r"누구야\??", ""),
    (r"좀 해줘!?\s*$", ""),
    (r"궁금해\.?", ""),
    (r"말해줘\.?", ""),
    (r"알려줘\.?", ""),
)

TOKEN_ALIASES = {
    "노하우좀": ("노하우", "방법"),
    "키우는": ("키우", "재배"),
    "기르는": ("기르", "재배"),
    "헥타르": ("hectare",),
    "제곱킬로미터": ("km2",),
}

KEEP_SUFFIXED_TERMS = {
    "같은",
    "작은",
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value)).lower()
    text = text.replace("대히", "대해")
    text = text.replace("나쁜줄말", "나쁜줄만")
    text = text.replace("초코렛", "초콜릿")
    text = text.replace("디엔에이", "dna")
    text = text.replace("아세틸 콜린", "아세틸콜린")
    text = text.replace("슈퍼옥시드", "superoxide")
    text = text.replace("디스무타아제", "dismutase")
    text = text.replace("퓨린", "푸린")
    text = text.replace("㎢", " km2 ")
    text = re.sub(r"(?i)\bkm\s*\^\s*2\b", " km2 ", text)
    text = re.sub(r"(?i)\bkm\s*2\b", " km2 ", text)
    text = re.sub(r"(?i)\bcovid\s*[-_]\s*19\b", " covid19 ", text)
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(r"(?<=\d)(?=[가-힣A-Za-z])", " ", text)
    text = re.sub(r"[/·ㆍ]", " ", text)
    text = re.sub(r"[-_]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_query(value: object) -> str:
    query = normalize_text(value)
    query = query.replace("리보오솜", "리보솜")
    query = query.replace("trojan", "트로이군")
    query = query.replace("interferon", "인터페론")
    for pattern, replacement in QUERY_REPLACEMENTS:
        query = re.sub(pattern, replacement, query)
    terms = [
        term
        for term in _unique_preserving_order(_query_terms(query))
        if _keep_term(term, QUERY_STOP_WORDS)
    ]
    return " ".join(terms).strip()


def tokenize(value: object) -> list[str]:
    terms: list[str] = []
    for term in _alnum_terms(normalize_text(value)):
        if not _keep_term(term, STOP_WORDS):
            continue
        for candidate in _term_variants(term):
            if _keep_term(candidate, STOP_WORDS):
                terms.append(candidate)
    return terms


def _query_terms(text: str) -> Iterable[str]:
    for term in _alnum_terms(text):
        if not _keep_term(term, QUERY_STOP_WORDS):
            continue
        stripped = _strip_korean_suffix(term)
        yield stripped if stripped not in QUERY_STOP_WORDS else term


def _term_variants(term: str) -> list[str]:
    variants = [term]
    stripped = _strip_korean_suffix(term)
    if stripped != term:
        variants.append(stripped)
        if stripped.endswith("들") and len(stripped) > 2:
            variants.append(stripped[:-1])
    if term.endswith("들") and len(term) > 2:
        variants.append(term[:-1])
    variants.extend(TOKEN_ALIASES.get(term, ()))
    variants.extend(TOKEN_ALIASES.get(stripped, ()))
    return _unique_preserving_order(variants)


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


def _strip_korean_suffix(term: str) -> str:
    if not any("가" <= char <= "힣" for char in term):
        return term
    if term in KEEP_SUFFIXED_TERMS:
        return term
    for suffix in KOREAN_SUFFIXES:
        if term.endswith(suffix) and len(term) > len(suffix):
            return term[: -len(suffix)]
    return term


def _keep_term(term: str, stop_words: set[str]) -> bool:
    if not term or term in stop_words:
        return False
    if len(term) > 1:
        return True
    return any("가" <= char <= "힣" for char in term) or term.isnumeric()


def _unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value and value not in seen:
            unique.append(value)
            seen.add(value)
    return unique
