#!/usr/bin/env python3
"""Parses Hodler Suite roadmap/sprint docs into structured items for Atlassian sync.

Two known doc shapes are supported:
  1. Table rows: "| **U-066** | Item text | Source | Notes |" (hodler-suite-unified-sprint-and-roadmap-*.md)
  2. Session headers: "### Session P12 — Title" followed by body until the next "###" or "---"
     (production-release-sprint-sessions-*.md)

Unknown/malformed rows are skipped with a warning rather than raising, so a stray
formatting change in the docs cannot break the whole CI run.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field


ID_PATTERN = re.compile(r"^[UOP]-?\d+$")


@dataclass
class RoadmapItem:
    item_id: str  # normalized, e.g. "U-066", "P12"
    title: str
    body: str
    source_doc: str
    source_section: str = ""


def _normalize_id(raw: str) -> str:
    raw = raw.strip().upper()
    match = re.match(r"^([UOP])-?(\d+)$", raw)
    if not match:
        return raw
    letter, digits = match.groups()
    # U/O ids keep the hyphen (U-066); P ids from session headers don't (P12).
    return f"{letter}-{digits}" if letter in ("U", "O") else f"{letter}{digits}"


def _parse_table_rows(text: str, source_doc: str) -> list[RoadmapItem]:
    items: list[RoadmapItem] = []
    current_section = ""
    for line in text.splitlines():
        section_match = re.match(r"^#{2,4}\s+(.*)$", line.strip())
        if section_match:
            current_section = section_match.group(1).strip()
            continue

        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 2:
            continue

        id_cell = cells[0]
        id_match = re.match(r"^\*\*([UO]-?\d+)\*\*$", id_cell)
        if not id_match:
            continue  # header/separator row or a table this parser doesn't own

        item_id = _normalize_id(id_match.group(1))
        title = cells[1] if len(cells) > 1 else ""
        extra = " | ".join(cells[2:]) if len(cells) > 2 else ""
        if not title:
            print(f"[roadmap_parser] WARN: {source_doc}: row for {item_id} has no title, skipping", file=sys.stderr)
            continue

        items.append(
            RoadmapItem(
                item_id=item_id,
                title=title,
                body=extra,
                source_doc=source_doc,
                source_section=current_section,
            )
        )
    return items


def _parse_session_headers(text: str, source_doc: str) -> list[RoadmapItem]:
    items: list[RoadmapItem] = []
    header_pattern = re.compile(r"^###\s+Session\s+(P\d+)\s*[—\-–]\s*(.+?)\s*$")
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        match = header_pattern.match(lines[i].strip())
        if not match:
            i += 1
            continue
        item_id = _normalize_id(match.group(1))
        title = match.group(2).strip()
        body_lines: list[str] = []
        i += 1
        while i < len(lines):
            line = lines[i]
            if header_pattern.match(line.strip()) or line.strip() == "---" or re.match(r"^##\s+", line.strip()):
                break
            body_lines.append(line)
            i += 1
        body = "\n".join(body_lines).strip()
        if not body:
            print(f"[roadmap_parser] WARN: {source_doc}: session {item_id} has no body, skipping", file=sys.stderr)
            continue
        items.append(
            RoadmapItem(
                item_id=item_id,
                title=title,
                body=body,
                source_doc=source_doc,
                source_section="Session list",
            )
        )
    return items


def parse_roadmap_doc(path: str) -> list[RoadmapItem]:
    """Parse a single roadmap/sprint doc file, auto-detecting its shape."""
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    items = _parse_table_rows(text, path)
    items.extend(_parse_session_headers(text, path))

    seen: set[str] = set()
    deduped: list[RoadmapItem] = []
    for item in items:
        if item.item_id in seen:
            print(f"[roadmap_parser] WARN: {path}: duplicate id {item.item_id}, keeping first occurrence", file=sys.stderr)
            continue
        seen.add(item.item_id)
        deduped.append(item)
    return deduped


def parse_roadmap_docs(paths: list[str]) -> dict[str, RoadmapItem]:
    """Parse multiple docs, returning {item_id: RoadmapItem}. Later files win on id clashes."""
    all_items: dict[str, RoadmapItem] = {}
    for path in paths:
        for item in parse_roadmap_doc(path):
            all_items[item.item_id] = item
    return all_items


def find_referenced_ids(text: str) -> list[str]:
    """Extract roadmap IDs referenced in free text (commit messages, PR titles/bodies)."""
    found: list[str] = []
    for raw in re.findall(r"\b([UOP]-?\d{1,4})\b", text or ""):
        candidate = _normalize_id(raw)
        if ID_PATTERN.match(candidate.replace("-", "")) or re.match(r"^[UOP]-?\d+$", candidate):
            if candidate not in found:
                found.append(candidate)
    return found


if __name__ == "__main__":
    import json

    docs = sys.argv[1:]
    if not docs:
        print("Usage: roadmap_parser.py <doc1.md> [doc2.md ...]", file=sys.stderr)
        sys.exit(1)
    parsed = parse_roadmap_docs(docs)
    print(json.dumps({k: vars(v) for k, v in parsed.items()}, indent=2))
