"""Pretty-printer for PQL expressions.

Rules applied:
  * one top-level boolean operand per line
  * nested parentheses indented
  * consistent single spaces around operators
  * no space before a comma, one after
  * dotted paths kept tight (person.birthYear, not person . birthYear)
"""

from __future__ import annotations

from typing import List

from .lexer import Token, strip_ws, tokenize

INDENT = "  "

# Boolean operators that earn their own line at the current depth.
BREAKERS = {"and", "or"}

# Clause keywords that read better on a new line inside a quantifier.
CLAUSE_KEYWORDS = {"where", "from", "over", "in"}


def _needs_space_before(prev: Token | None, tok: Token) -> bool:
    if prev is None:
        return False
    if tok.kind == "punct" and tok.value in {".", ",", ")", "]", ":"}:
        return False
    if prev.kind == "punct" and prev.value in {".", "(", "[", "^", "$"}:
        return False
    return True


def format_pql(src: str, indent: str = INDENT, width_hint: int = 60) -> str:
    """Format a PQL expression.

    ``width_hint`` controls when a short expression is left on one line.
    """
    tokens = strip_ws(tokenize(src))
    if not tokens:
        return ""

    # Short expressions stay on a single line.
    single = _join(tokens)
    if len(single) <= width_hint and not _has_breaker(tokens):
        return single

    out: List[str] = []
    line: List[Token] = []
    depth = 0

    def flush() -> None:
        if line:
            out.append(indent * depth + _join(line))
            line.clear()

    def flush_with_suffix(suffix: str) -> None:
        if line:
            out.append(indent * depth + _join(line) + " " + suffix)
            line.clear()

    for tok in tokens:
        if tok.kind == "keyword" and tok.value in BREAKERS and depth >= 0:
            # Trailing operator style: keep "and"/"or" on the line it follows.
            if line:
                flush_with_suffix(tok.value)
            elif out:
                out[-1] = out[-1] + " " + tok.value
            else:
                out.append(indent * depth + tok.value)
            continue

        if tok.kind == "punct" and tok.value == "(":
            line.append(tok)
            flush()
            depth += 1
            continue

        if tok.kind == "punct" and tok.value == ")":
            flush()
            depth = max(0, depth - 1)
            out.append(indent * depth + ")")
            continue

        line.append(tok)

    flush()
    # collapse any accidental blank lines
    return "\n".join(l for l in out if l.strip())


def _has_breaker(tokens: List[Token]) -> bool:
    return any(t.kind == "keyword" and t.value in BREAKERS for t in tokens)


def _join(tokens: List[Token]) -> str:
    parts: List[str] = []
    prev: Token | None = None
    for tok in tokens:
        if _needs_space_before(prev, tok):
            parts.append(" ")
        parts.append(tok.value)
        prev = tok
    return "".join(parts).strip()
