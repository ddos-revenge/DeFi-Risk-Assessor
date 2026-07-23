#!/usr/bin/env python3
"""Minimal Jira + Confluence Cloud REST client, authenticated via API token (Basic Auth).

Only the operations this sync needs are implemented. Every call raises AtlassianApiError
on a non-2xx response with the response body attached, so callers can log/skip cleanly
instead of the whole CI run dying on one bad request.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from dataclasses import dataclass


class AtlassianApiError(RuntimeError):
    def __init__(self, method: str, url: str, status: int, body: str):
        super().__init__(f"{method} {url} -> {status}: {body[:500]}")
        self.status = status
        self.body = body


@dataclass
class AtlassianClient:
    site_url: str
    email: str
    api_token: str

    def __post_init__(self):
        self.site_url = self.site_url.rstrip("/")
        auth_raw = f"{self.email}:{self.api_token}".encode("utf-8")
        self._auth_header = "Basic " + base64.b64encode(auth_raw).decode("ascii")

    def _request(self, method: str, url: str, payload: dict | None = None) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", self._auth_header)
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AtlassianApiError(method, url, exc.code, body) from exc

    # ---------------------------------------------------------------- Jira

    def jira_search(self, jql: str, fields: list[str] | None = None) -> list[dict]:
        url = f"{self.site_url}/rest/api/3/search/jql"
        payload = {"jql": jql, "fields": fields or ["summary", "status", "labels"], "maxResults": 50}
        result = self._request("POST", url, payload)
        return result.get("issues", [])

    def jira_find_by_label(self, project_key: str, label: str) -> dict | None:
        jql = f'project = "{project_key}" AND labels = "{label}" ORDER BY created DESC'
        issues = self.jira_search(jql)
        return issues[0] if issues else None

    def jira_create_issue(
        self,
        *,
        project_key: str,
        summary: str,
        description_text: str,
        labels: list[str],
        issue_type: str = "Task",
    ) -> dict:
        url = f"{self.site_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary[:255],
                "description": _text_to_adf(description_text),
                "issuetype": {"name": issue_type},
                "labels": labels,
            }
        }
        return self._request("POST", url, payload)

    def jira_transitions(self, issue_key: str) -> list[dict]:
        url = f"{self.site_url}/rest/api/3/issue/{issue_key}/transitions"
        result = self._request("GET", url)
        return result.get("transitions", [])

    def jira_transition_issue(self, issue_key: str, transition_id: str) -> None:
        url = f"{self.site_url}/rest/api/3/issue/{issue_key}/transitions"
        self._request("POST", url, {"transition": {"id": transition_id}})

    def jira_add_comment(self, issue_key: str, comment_text: str) -> None:
        url = f"{self.site_url}/rest/api/3/issue/{issue_key}/comment"
        self._request("POST", url, {"body": _text_to_adf(comment_text)})

    # ----------------------------------------------------------- Confluence

    def confluence_find_page(self, space_key: str, title: str) -> dict | None:
        from urllib.parse import quote

        url = (
            f"{self.site_url}/wiki/rest/api/content"
            f"?spaceKey={quote(space_key)}&title={quote(title)}&expand=version"
        )
        result = self._request("GET", url)
        results = result.get("results", [])
        return results[0] if results else None

    def confluence_create_page(self, space_key: str, title: str, storage_html: str) -> dict:
        url = f"{self.site_url}/wiki/rest/api/content"
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {"storage": {"value": storage_html, "representation": "storage"}},
        }
        return self._request("POST", url, payload)

    def confluence_update_page(self, page_id: str, title: str, storage_html: str, next_version: int) -> dict:
        url = f"{self.site_url}/wiki/rest/api/content/{page_id}"
        payload = {
            "id": page_id,
            "type": "page",
            "title": title,
            "body": {"storage": {"value": storage_html, "representation": "storage"}},
            "version": {"number": next_version},
        }
        return self._request("PUT", url, payload)


def _text_to_adf(text: str) -> dict:
    """Wrap plain text into a minimal Atlassian Document Format paragraph block."""
    paragraphs = [p for p in (text or "").split("\n\n") if p.strip()] or [""]
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": p}]} for p in paragraphs
        ],
    }
