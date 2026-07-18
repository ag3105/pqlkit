"""Tokenizer for Profile Query Language (PQL).

Deliberately small. PQL has no public grammar, so this is a pragmatic
tokenizer that handles the constructs seen in Adobe's documented examples
rather than a complete parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, List

KEYWORDS = {
    "and", "or", "not", "in", "notIn", "exists", "forall", "from", "where",
    "select", "let", "over", "in", "if", "then", "else", "true", "false",
}

# Longest first so multi-char operators win.
OPERATORS = [
    ">=", "<=", "!=", "=", ">", "<",
]

PUNCT = ["(", ")", "[", "]", ",", ".", "^", "$", ":"]


@dataclass
class Token:
    kind: str   # keyword | ident | number | string | op | punct | ws
    value: str
    pos: int

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Token({self.kind}, {self.value!r})"


def tokenize(src: str) -> List[Token]:
    """Turn a PQL string into a flat token list."""
    tokens: List[Token] = []
    i = 0
    n = len(src)

    while i < n:
        ch = src[i]

        # whitespace (collapsed, but recorded so we can rebuild)
        if ch.isspace():
            j = i
            while j < n and src[j].isspace():
                j += 1
            tokens.append(Token("ws", " ", i))
            i = j
            continue

        # double-quoted string literal
        if ch == '"':
            j = i + 1
            while j < n and src[j] != '"':
                if src[j] == "\\":
                    j += 1
                j += 1
            j = min(j + 1, n)
            tokens.append(Token("string", src[i:j], i))
            i = j
            continue

        # number
        if ch.isdigit():
            j = i
            while j < n and (src[j].isdigit() or src[j] == "."):
                # don't swallow a property access like 5.foo
                if src[j] == "." and (j + 1 >= n or not src[j + 1].isdigit()):
                    break
                j += 1
            tokens.append(Token("number", src[i:j], i))
            i = j
            continue

        # identifier / keyword
        if ch.isalpha() or ch == "_":
            j = i
            while j < n and (src[j].isalnum() or src[j] in "_"):
                j += 1
            word = src[i:j]
            kind = "keyword" if word in KEYWORDS else "ident"
            tokens.append(Token(kind, word, i))
            i = j
            continue

        # operators
        matched = False
        for op in OPERATORS:
            if src.startswith(op, i):
                tokens.append(Token("op", op, i))
                i += len(op)
                matched = True
                break
        if matched:
            continue

        # punctuation
        if ch in PUNCT:
            tokens.append(Token("punct", ch, i))
            i += 1
            continue

        # anything else: keep it so we never silently drop input
        tokens.append(Token("op", ch, i))
        i += 1

    return tokens


def strip_ws(tokens: List[Token]) -> List[Token]:
    return [t for t in tokens if t.kind != "ws"]
