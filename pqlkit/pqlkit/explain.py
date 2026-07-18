"""Translate a PQL expression into plain English.

This is intentionally heuristic. It reads the shape of the expression and
describes it the way a practitioner would explain it in a stand-up, which
is exactly the gap the raw query leaves.
"""

from __future__ import annotations

import re
from typing import List

from .lexer import strip_ws, tokenize

OP_WORDS = {
    "=": "is",
    "!=": "is not",
    ">": "is greater than",
    "<": "is less than",
    ">=": "is at least",
    "<=": "is at most",
}

# Friendly names for the XDM paths people actually hit most.
PATH_WORDS = {
    "homeAddress.countryISO": "home country",
    "homeAddress.stateProvince": "home state/province",
    "homeAddress.city": "home city",
    "workAddress.countryISO": "work country",
    "person.birthYear": "birth year",
    "person.gender": "gender",
    "person.name.firstName": "first name",
    "person.name.lastName": "last name",
    "personalEmail.address": "personal email address",
    "mobilePhone.number": "mobile number",
    "consents.marketing.email.val": "email marketing consent",
}


def humanize_path(path: str) -> str:
    if path in PATH_WORDS:
        return PATH_WORDS[path]
    tail = path.split(".")[-1]
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", tail).lower()
    return spaced.replace("_", " ")


def explain(src: str) -> str:
    """Return a plain-English description of a PQL expression."""
    text = " ".join(src.split())
    if not text:
        return ""

    notes: List[str] = []

    lowered = text.lower()
    uses_events = "xevent" in lowered
    quantifier = None
    if re.search(r"\bexists\b", text):
        quantifier = "exists"
    elif re.search(r"\bforall\b", text):
        quantifier = "forall"

    has_aggregate = bool(re.search(r"\b(sum|count|average|min|max)\b", text))
    has_let = bool(re.search(r"\blet\b", text))

    # Headline
    if has_aggregate and has_let:
        headline = "Includes people based on a calculated total across their events."
    elif quantifier == "exists":
        headline = "Includes people who have at least one matching event."
    elif quantifier == "forall":
        headline = "Includes people where every matching event meets the condition."
    elif uses_events:
        headline = "Includes people based on their event history."
    else:
        headline = "Includes people based on profile attributes."

    notes.append(headline)

    # Attribute comparisons
    for path, op, value in _comparisons(text):
        notes.append(
            f"  - {humanize_path(path)} {OP_WORDS.get(op, op)} {_clean_value(value)}"
        )

    # Boolean shape
    ands = len(re.findall(r"\band\b", text))
    ors = len(re.findall(r"\bor\b", text))
    if ands and ors:
        notes.append(
            "  - Mixes AND and OR. Check the parentheses: precedence here is the "
            "usual source of surprise audience sizes."
        )
    elif ands:
        notes.append("  - All of the above conditions must be true.")
    elif ors:
        notes.append("  - Any one of the above conditions is enough to qualify.")

    if has_aggregate:
        agg = re.search(r"\b(sum|count|average|min|max)\b", text)
        if agg:
            notes.append(
                f"  - Aggregates events using {agg.group(1)}, so the whole event "
                "history is scanned. Watch the cost on high-volume profiles."
            )

    return "\n".join(notes)


def _comparisons(text: str):
    """Yield (path, operator, value) triples for simple comparisons."""
    pattern = re.compile(
        r"([A-Za-z_][\w]*(?:\.[A-Za-z_][\w]*)+)\s*(>=|<=|!=|=|>|<)\s*(\"[^\"]*\"|[\w.]+)"
    )
    for m in pattern.finditer(text):
        yield m.group(1), m.group(2), m.group(3)


def _clean_value(value: str) -> str:
    return value.strip('"')
