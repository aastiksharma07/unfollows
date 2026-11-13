"""Find Instagram accounts you follow that don't follow you back.

Usage::

      python unfollows.py followers_1.json following.json
      python unfollows.py followers_1.json followers_2.json following.json --sort az
      python unfollows.py followers_1.json following.json --json

Only the standard library is used.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

__all__ = [
    "Account",
    "extract_accounts",
    "not_following_back",
    "sort_accounts",
    "compare",
    "profile_url",
]

_HREF_RE = re.compile(r"instagram\.com/(?:_u/)?([^/?#]+)", re.IGNORECASE)


@dataclass(frozen=True)
class Account:
    username: str
    timestamp: int = 0  # Unix seconds when the follow happened; 0 if unknown.

    @property
    def key(self) -> str:
        return self.username.lower()


def _username_from_href(href: str | None) -> str:
    if not href:
        return ""
    match = _HREF_RE.search(str(href))
    return match.group(1) if match else ""


def _items(data: Any) -> list[Any]:
    """Return the list of relationship records from any known export shape.

    Instagram has shipped several layouts:

    * ``followers_1.json`` -> ``[ {"string_list_data": [{"href", "value", "timestamp"}]} ]``
    * ``following.json``   -> ``{"relationships_following": [ {...} ]}``
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        items: list[Any] = []
        for value in data.values():
            if isinstance(value, list):
                items.extend(value)
        return items
    return []


def extract_accounts(data: Any) -> list[Account]:
    """Parse one Instagram export (already JSON-decoded) into accounts.

    Newer exports keep the username in ``title`` and omit ``value``; older ones
    do the reverse. As a last resort the username is taken from ``href``.
    """
    accounts: list[Account] = []
    for item in _items(data):
        if not isinstance(item, dict):
            continue
        entries = item.get("string_list_data") or [{}]
        first = entries[0] if isinstance(entries[0], dict) else {}
        username = (
            first.get("value")
            or item.get("title")
            or _username_from_href(first.get("href"))
            or ""
        ).strip()
        if not username:
            continue
        try:
            timestamp = int(first.get("timestamp") or 0)
        except (TypeError, ValueError):
            timestamp = 0
        accounts.append(Account(username, timestamp))
    return accounts


def not_following_back(
    followers: Iterable[Account], following: Iterable[Account]
) -> list[Account]:
    """Accounts in ``following`` that are not in ``followers`` (case-insensitive, de-duplicated)."""
    follower_keys = {a.key for a in followers}
    seen: set[str] = set()
    result: list[Account] = []
    for account in following:
        if account.key in follower_keys or account.key in seen:
            continue
        seen.add(account.key)
        result.append(account)
    return result


def sort_accounts(accounts: Iterable[Account], mode: str = "recent") -> list[Account]:
    """Sort by ``recent`` (newest follow first), ``oldest`` or ``az``."""
    if mode == "az":
        return sorted(accounts, key=lambda a: a.key)
    if mode == "oldest":
        return sorted(accounts, key=lambda a: a.timestamp)
    if mode == "recent":
        return sorted(accounts, key=lambda a: a.timestamp, reverse=True)
    raise ValueError(f"Unknown sort mode: {mode!r}")


def profile_url(username: str) -> str:
    return f"https://www.instagram.com/{username}/"


def compare(
    followers_data: Iterable[Any], following_data: Iterable[Any], sort: str = "recent"
) -> dict[str, Any]:
    """Compare decoded export files and return a summary dict.

    ``followers_data`` / ``following_data`` are iterables of decoded JSON
    documents, so split exports (``followers_1.json``, ``followers_2.json``) work.
    """
    followers = [a for doc in followers_data for a in extract_accounts(doc)]
    following = [a for doc in following_data for a in extract_accounts(doc)]

    if not followers:
        raise ValueError("No followers found — is that the right file?")
    if not following:
        raise ValueError("No following found — is that the right file?")

    result = sort_accounts(not_following_back(followers, following), sort)
    return {
        "followers": len({a.key for a in followers}),
        "following": len({a.key for a in following}),
        "not_following_back": [asdict(a) for a in result],
    }


def _decode(text: str, name: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"“{name}” isn’t valid JSON.") from exc


# ---------------------------------------------------------------- CLI


def _classify(paths: list[Path]) -> tuple[list[Path], list[Path]]:
    followers = [p for p in paths if p.name.lower().startswith("followers")]
    following = [p for p in paths if p.name.lower().startswith("following")]
    return followers, following


def _format_date(timestamp: int) -> str:
    if not timestamp:
        return ""
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%d %b %Y")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List Instagram accounts you follow that don't follow you back."
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="followers_*.json and following.json from your Instagram export",
    )
    parser.add_argument("--sort", choices=["recent", "oldest", "az"], default="recent")
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args(argv)

    followers_paths, following_paths = _classify(args.files)
    if not followers_paths or not following_paths:
        parser.error("pass at least one followers*.json and one following*.json file")

    try:
        result = compare(
            [_decode(p.read_text(encoding="utf-8"), p.name) for p in followers_paths],
            [_decode(p.read_text(encoding="utf-8"), p.name) for p in following_paths],
            args.sort,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    people = result["not_following_back"]
    print(
        f"Following {result['following']} · Followers {result['followers']} · "
        f"Don't follow back {len(people)}\n"
    )
    width = max((len(p["username"]) for p in people), default=0) + 1
    for p in people:
        print(f"@{p['username']:<{width}} {_format_date(p['timestamp']):>11}  {profile_url(p['username'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
