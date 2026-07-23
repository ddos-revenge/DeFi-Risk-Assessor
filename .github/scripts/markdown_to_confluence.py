#!/usr/bin/env python3
"""Pragmatic Markdown -> Confluence storage-format (XHTML) converter.

Not a general CommonMark implementation - only covers what the two Hodler Suite
roadmap docs actually use: headers, tables, bullet lists, bold/inline-code,
links, and horizontal rules. Anything else passes through as an escaped
paragraph rather than crashing the sync.
"""

from __future__ import annotations

import html
import re


def _inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def _render_table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    header, *body = rows
    out = ["<table><tbody>"]
    out.append("<tr>" + "".join(f"<th>{_inline(c)}</th>" for c in header) + "</tr>")
    for row in body:
        out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in row) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def markdown_to_confluence_storage(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    out: list[str] = []
    i = 0
    in_list = False
    table_buffer: list[list[str]] = []

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def flush_table():
        nonlocal table_buffer
        if table_buffer:
            out.append(_render_table(table_buffer))
            table_buffer = []

    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()

        if not stripped:
            flush_list()
            flush_table()
            i += 1
            continue

        if re.match(r"^-{3,}$", stripped):
            flush_list()
            flush_table()
            out.append("<hr/>")
            i += 1
            continue

        header_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if header_match:
            flush_list()
            flush_table()
            level = min(len(header_match.group(1)), 6)
            out.append(f"<h{level}>{_inline(header_match.group(2))}</h{level}>")
            i += 1
            continue

        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if re.match(r"^-{2,}$", cells[0].replace(":", "")) or all(
                re.match(r"^:?-{2,}:?$", c) for c in cells
            ):
                i += 1
                continue  # separator row
            table_buffer.append(cells)
            i += 1
            continue

        flush_table()

        bullet_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if bullet_match:
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{_inline(bullet_match.group(1))}</li>")
            i += 1
            continue

        flush_list()
        out.append(f"<p>{_inline(stripped)}</p>")
        i += 1

    flush_list()
    flush_table()
    return "\n".join(out)


if __name__ == "__main__":
    import sys

    for path in sys.argv[1:]:
        with open(path, "r", encoding="utf-8") as fh:
            print(markdown_to_confluence_storage(fh.read()))
