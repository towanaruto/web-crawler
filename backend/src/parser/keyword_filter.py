from __future__ import annotations

import re


def matches_keywords(parsed: dict, keywords: list[str], mode: str = "any") -> bool:
    """Check if a parsed article matches the given keywords.

    Args:
        parsed: Dict returned by parse_article().
        keywords: List of keyword strings to match against.
        mode: "any" (OR) — at least one keyword must match.
              "all" (AND) — every keyword must match.

    Returns:
        True if the article passes the filter, False otherwise.
    """
    if not keywords:
        return True

    corpus_parts = [
        parsed.get("title") or "",
        parsed.get("body_text") or "",
        parsed.get("excerpt") or "",
    ]
    for name in parsed.get("category_names") or []:
        corpus_parts.append(name)
    for name in parsed.get("tag_names") or []:
        corpus_parts.append(name)

    corpus = " ".join(corpus_parts).lower()

    if mode == "all":
        return all(re.search(re.escape(kw.lower()), corpus) for kw in keywords)
    else:
        return any(re.search(re.escape(kw.lower()), corpus) for kw in keywords)
