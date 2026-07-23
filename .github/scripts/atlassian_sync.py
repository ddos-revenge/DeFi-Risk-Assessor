#!/usr/bin/env python3
"""Hodler Suite <-> Atlassian sync.

Three subcommands, run from CI (see .github/workflows/atlassian-roadmap-sync.yml):

  propose         Parse the roadmap docs; create a Jira issue for any item that
                  doesn't have one yet (matched via label `roadmap-<ID>`).
  resolve         Read commit messages from stdin; for every roadmap ID mentioned,
                  transition the matching Jira issue to a "done"-like status and
                  comment with a link back to the commit.
  confluence-sync Render the roadmap docs to Confluence storage format and push
                  them to a single page (created on first run).

Every operation logs what it did/skipped and never raises past main() - a bad
row in a doc or one failed API call should not take down the whole CI job.
"""

from __future__ import annotations

import argparse
import os
import sys

from atlassian_client import AtlassianApiError, AtlassianClient
from markdown_to_confluence import markdown_to_confluence_storage
from roadmap_parser import find_referenced_ids, parse_roadmap_docs

DONE_LIKE_STATUS_NAMES = {"done", "closed", "resolved", "complete", "completed"}
DONE_LIKE_TRANSITION_NAMES = {"done", "close", "closed", "resolve", "resolved", "complete", "completed", "mark as done"}
ROADMAP_LABEL_PREFIX = "roadmap-"
GENERAL_LABEL = "hodler-suite-roadmap"
CONFLUENCE_PAGE_TITLE = "Hodler Suite — Roadmap & Sprint Sessions (auto-synced)"


def _client_from_env() -> AtlassianClient:
    site_url = os.environ.get("ATLASSIAN_SITE_URL", "").strip()
    email = os.environ.get("ATLASSIAN_EMAIL", "").strip()
    token = os.environ.get("ATLASSIAN_API_TOKEN", "").strip()
    missing = [name for name, val in (("ATLASSIAN_SITE_URL", site_url), ("ATLASSIAN_EMAIL", email), ("ATLASSIAN_API_TOKEN", token)) if not val]
    if missing:
        print(f"[atlassian_sync] ERROR: missing required env vars: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return AtlassianClient(site_url=site_url, email=email, api_token=token)


def cmd_propose(args: argparse.Namespace) -> int:
    client = _client_from_env()
    project_key = os.environ["JIRA_PROJECT_KEY"]

    items = parse_roadmap_docs(args.docs)
    print(f"[propose] parsed {len(items)} roadmap items from {len(args.docs)} doc(s)")

    created, skipped, failed = 0, 0, 0
    for item_id, item in sorted(items.items()):
        label = f"{ROADMAP_LABEL_PREFIX}{item_id}"
        try:
            existing = client.jira_find_by_label(project_key, label)
        except AtlassianApiError as exc:
            print(f"[propose] ERROR checking {item_id}: {exc}", file=sys.stderr)
            failed += 1
            continue

        if existing:
            skipped += 1
            continue

        description = (
            f"Synced from {item.source_doc} (section: {item.source_section or 'n/a'}).\n\n"
            f"{item.body}\n\n"
            f"Do not edit the roadmap ID label ({label}) - it is how this issue is matched "
            f"back to the source doc for auto-resolve."
        )
        try:
            issue = client.jira_create_issue(
                project_key=project_key,
                summary=f"[{item_id}] {item.title}",
                description_text=description,
                labels=[label, GENERAL_LABEL],
            )
            print(f"[propose] created {issue.get('key', '?')} for {item_id}")
            created += 1
        except AtlassianApiError as exc:
            print(f"[propose] ERROR creating issue for {item_id}: {exc}", file=sys.stderr)
            failed += 1

    print(f"[propose] done: created={created} skipped(existing)={skipped} failed={failed}")
    return 1 if failed else 0


def _find_done_transition(transitions: list[dict]) -> dict | None:
    for t in transitions:
        name = str(t.get("name", "")).strip().lower()
        to_status = str(t.get("to", {}).get("name", "")).strip().lower()
        if name in DONE_LIKE_TRANSITION_NAMES or to_status in DONE_LIKE_STATUS_NAMES:
            return t
    return None


def cmd_resolve(args: argparse.Namespace) -> int:
    client = _client_from_env()
    project_key = os.environ["JIRA_PROJECT_KEY"]

    commit_text = sys.stdin.read()
    referenced_ids = find_referenced_ids(commit_text)
    if not referenced_ids:
        print("[resolve] no roadmap IDs referenced in the supplied commit messages, nothing to do")
        return 0

    print(f"[resolve] found references to: {', '.join(referenced_ids)}")

    resolved, already_done, not_found, failed = 0, 0, 0, 0
    for item_id in referenced_ids:
        label = f"{ROADMAP_LABEL_PREFIX}{item_id}"
        try:
            issue = client.jira_find_by_label(project_key, label)
        except AtlassianApiError as exc:
            print(f"[resolve] ERROR looking up {item_id}: {exc}", file=sys.stderr)
            failed += 1
            continue

        if not issue:
            print(f"[resolve] WARN: no Jira issue found for {item_id} (label {label}) - run `propose` first, or this id doesn't exist in the roadmap docs")
            not_found += 1
            continue

        issue_key = issue["key"]
        current_status = str(issue.get("fields", {}).get("status", {}).get("name", "")).strip().lower()
        if current_status in DONE_LIKE_STATUS_NAMES:
            print(f"[resolve] {issue_key} ({item_id}) already in status '{current_status}', skipping transition")
            already_done += 1
            continue

        try:
            transitions = client.jira_transitions(issue_key)
            done_transition = _find_done_transition(transitions)
            if not done_transition:
                available = ", ".join(sorted({t.get("name", "?") for t in transitions})) or "none"
                print(f"[resolve] WARN: no done-like transition available for {issue_key}; available transitions: {available}", file=sys.stderr)
                failed += 1
                continue
            client.jira_transition_issue(issue_key, done_transition["id"])
            comment = args.comment_prefix + f"\n\nRoadmap ID: {item_id}"
            client.jira_add_comment(issue_key, comment)
            print(f"[resolve] transitioned {issue_key} ({item_id}) -> {done_transition.get('name')}")
            resolved += 1
        except AtlassianApiError as exc:
            print(f"[resolve] ERROR transitioning {issue_key}: {exc}", file=sys.stderr)
            failed += 1

    print(f"[resolve] done: resolved={resolved} already_done={already_done} not_found={not_found} failed={failed}")
    return 1 if failed else 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    client = _client_from_env()
    configured_key = os.environ.get("CONFLUENCE_SPACE_KEY", "")

    print(f"[diagnose] configured CONFLUENCE_SPACE_KEY = {configured_key!r}")

    try:
        spaces = client.confluence_list_spaces()
        print(f"[diagnose] account can see {len(spaces)} space(s):")
        for sp in spaces:
            print(f"  key={sp.get('key')!r} id={sp.get('id')!r} type={sp.get('type')!r} name={sp.get('name')!r}")
    except AtlassianApiError as exc:
        print(f"[diagnose] ERROR listing spaces: {exc}", file=sys.stderr)

    try:
        detail = client.confluence_get_space(configured_key)
        print(f"[diagnose] GET space by configured key succeeded: id={detail.get('id')!r} name={detail.get('name')!r}")
    except AtlassianApiError as exc:
        print(f"[diagnose] ERROR fetching configured space key directly: {exc}", file=sys.stderr)

    return 0


def cmd_confluence_sync(args: argparse.Namespace) -> int:
    client = _client_from_env()
    space_key = os.environ["CONFLUENCE_SPACE_KEY"]

    sections = []
    for doc_path in args.docs:
        with open(doc_path, "r", encoding="utf-8") as fh:
            sections.append(markdown_to_confluence_storage(fh.read()))

    banner = (
        "<p><em>This page is synced automatically from the repository's roadmap docs "
        "on every push to main. Edit the source .md files in docs/Website/, not this "
        "page directly - manual changes here will be overwritten on the next sync.</em></p><hr/>"
    )
    storage_html = banner + "\n<hr/>\n".join(sections)

    try:
        existing = client.confluence_find_page(space_key, CONFLUENCE_PAGE_TITLE)
        if existing:
            current_version = int(existing.get("version", {}).get("number", 1))
            client.confluence_update_page(existing["id"], CONFLUENCE_PAGE_TITLE, storage_html, current_version + 1)
            print(f"[confluence-sync] updated page {existing['id']} (version {current_version + 1})")
        else:
            created = client.confluence_create_page(space_key, CONFLUENCE_PAGE_TITLE, storage_html)
            print(f"[confluence-sync] created page {created.get('id', '?')}")
    except AtlassianApiError as exc:
        print(f"[confluence-sync] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    propose_p = sub.add_parser("propose", help="Create Jira issues for roadmap items missing one")
    propose_p.add_argument("docs", nargs="+", help="Roadmap doc paths to parse")
    propose_p.set_defaults(func=cmd_propose)

    resolve_p = sub.add_parser("resolve", help="Transition Jira issues referenced in commit messages (read from stdin)")
    resolve_p.add_argument("--comment-prefix", default="Resolved automatically by the Hodler Suite CI sync.")
    resolve_p.set_defaults(func=cmd_resolve)

    confluence_p = sub.add_parser("confluence-sync", help="Push roadmap docs to Confluence")
    confluence_p.add_argument("docs", nargs="+", help="Roadmap doc paths to render")
    confluence_p.set_defaults(func=cmd_confluence_sync)

    diagnose_p = sub.add_parser("diagnose", help="List visible Confluence spaces and check the configured space key")
    diagnose_p.set_defaults(func=cmd_diagnose)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
