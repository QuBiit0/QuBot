"""
GitHub Tool - Full GitHub API integration for autonomous code management.
Agents can read/write files, create issues, PRs, search code without human intervention.
"""

import time
from typing import Any

from .base import BaseTool, ToolCategory, ToolParameter, ToolResult, ToolRiskLevel


class GitHubTool(BaseTool):
    """
    Interact with GitHub repositories via REST API.
    Requires GITHUB_TOKEN environment variable (Personal Access Token or GitHub App token).

    Operations:
    - list_repos: List user/org repositories
    - get_file: Read a file from a repository
    - create_file / update_file: Write files to a repository
    - list_issues: List open issues
    - create_issue: Open a new issue
    - list_prs: List pull requests
    - create_pr: Create a pull request
    - search_code: Search code across GitHub
    - get_repo: Get repository metadata
    - list_commits: List recent commits
    """

    name = "github"
    description = (
        "Interact with GitHub: read/write files, create issues and pull requests, "
        "search code, list repositories and commits. "
        "Requires GITHUB_TOKEN. Use to manage code without manual intervention."
    )
    category = ToolCategory.CODE
    risk_level = ToolRiskLevel.NORMAL

    API_BASE = "https://api.github.com"

    def _get_parameters_schema(self) -> dict[str, ToolParameter]:
        return {
            "operation": ToolParameter(
                name="operation",
                type="string",
                description=(
                    "Operation to perform: list_repos, get_repo, get_file, create_file, "
                    "update_file, list_issues, create_issue, list_prs, create_pr, "
                    "search_code, list_commits, get_commit"
                ),
                required=True,
                enum=[
                    "list_repos", "get_repo", "get_file", "create_file", "update_file",
                    "list_issues", "create_issue", "list_prs", "create_pr",
                    "search_code", "list_commits", "get_commit",
                ],
            ),
            "owner": ToolParameter(
                name="owner",
                type="string",
                description="Repository owner (user or organization)",
                required=False,
                default=None,
            ),
            "repo": ToolParameter(
                name="repo",
                type="string",
                description="Repository name",
                required=False,
                default=None,
            ),
            "path": ToolParameter(
                name="path",
                type="string",
                description="File path within the repository",
                required=False,
                default=None,
            ),
            "content": ToolParameter(
                name="content",
                type="string",
                description="File content (for create_file/update_file)",
                required=False,
                default=None,
            ),
            "message": ToolParameter(
                name="message",
                type="string",
                description="Commit message (for create_file/update_file)",
                required=False,
                default=None,
            ),
            "title": ToolParameter(
                name="title",
                type="string",
                description="Issue or PR title",
                required=False,
                default=None,
            ),
            "body": ToolParameter(
                name="body",
                type="string",
                description="Issue or PR body/description",
                required=False,
                default=None,
            ),
            "branch": ToolParameter(
                name="branch",
                type="string",
                description="Branch name (default: repo default branch)",
                required=False,
                default=None,
            ),
            "base_branch": ToolParameter(
                name="base_branch",
                type="string",
                description="Base branch for PR (default: main)",
                required=False,
                default="main",
            ),
            "query": ToolParameter(
                name="query",
                type="string",
                description="Search query (for search_code)",
                required=False,
                default=None,
            ),
            "labels": ToolParameter(
                name="labels",
                type="array",
                description="Labels for issues (list of strings)",
                required=False,
                default=None,
            ),
            "sha": ToolParameter(
                name="sha",
                type="string",
                description="Commit SHA (for get_commit or updating files)",
                required=False,
                default=None,
            ),
            "per_page": ToolParameter(
                name="per_page",
                type="integer",
                description="Results per page (default 20, max 100)",
                required=False,
                default=20,
            ),
        }

    def _validate_config(self) -> None:
        import os
        self.token = self.config.get("token") or os.getenv("GITHUB_TOKEN", "")
        self.default_owner = self.config.get("default_owner", "")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _request(self, method: str, endpoint: str, json_data: Any = None,
                       params: dict | None = None) -> tuple[int, Any]:
        """Make an authenticated GitHub API request."""
        try:
            import httpx
        except ImportError:
            raise ImportError("httpx not installed: pip install httpx")

        url = f"{self.API_BASE}{endpoint}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.request(
                method, url,
                headers=self._headers(),
                json=json_data,
                params=params,
            )
            try:
                body = resp.json()
            except Exception:
                body = resp.text
            return resp.status_code, body

    async def execute(self, operation: str, owner: str | None = None, repo: str | None = None,
                      path: str | None = None, content: str | None = None,
                      message: str | None = None, title: str | None = None,
                      body: str | None = None, branch: str | None = None,
                      base_branch: str = "main", query: str | None = None,
                      labels: list | None = None, sha: str | None = None,
                      per_page: int = 20) -> ToolResult:
        start_time = time.time()

        if not self.token:
            return ToolResult(
                success=False,
                error="GITHUB_TOKEN not configured. Set it via environment variable or tool config.",
            )

        owner = owner or self.default_owner
        per_page = min(max(1, per_page), 100)

        try:
            status, data = await self._dispatch(
                operation, owner, repo, path, content, message, title, body,
                branch, base_branch, query, labels, sha, per_page,
            )

            if status >= 400:
                error_msg = data.get("message", str(data)) if isinstance(data, dict) else str(data)
                return ToolResult(
                    success=False,
                    error=f"GitHub API error {status}: {error_msg}",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                )

            # Build human-readable summary
            stdout = self._format_result(operation, data)

            return ToolResult(
                success=True,
                data=data,
                stdout=stdout,
                execution_time_ms=int((time.time() - start_time) * 1000),
                metadata={"operation": operation, "status": status},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=f"GitHub operation failed: {e}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    async def _dispatch(self, operation: str, owner, repo, path, content, message, title,
                        body, branch, base_branch, query, labels, sha, per_page):
        import base64

        if operation == "list_repos":
            endpoint = f"/users/{owner}/repos" if owner else "/user/repos"
            return await self._request("GET", endpoint, params={"per_page": per_page, "sort": "updated"})

        elif operation == "get_repo":
            return await self._request("GET", f"/repos/{owner}/{repo}")

        elif operation == "get_file":
            params = {"ref": branch} if branch else {}
            return await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}", params=params)

        elif operation == "create_file":
            encoded = base64.b64encode((content or "").encode()).decode()
            payload: dict[str, Any] = {"message": message or f"Add {path}", "content": encoded}
            if branch:
                payload["branch"] = branch
            return await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json_data=payload)

        elif operation == "update_file":
            # Need existing file SHA
            file_sha = sha
            if not file_sha:
                status, existing = await self._request("GET", f"/repos/{owner}/{repo}/contents/{path}")
                if status == 200 and isinstance(existing, dict):
                    file_sha = existing.get("sha")
            encoded = base64.b64encode((content or "").encode()).decode()
            payload = {"message": message or f"Update {path}", "content": encoded, "sha": file_sha}
            if branch:
                payload["branch"] = branch
            return await self._request("PUT", f"/repos/{owner}/{repo}/contents/{path}", json_data=payload)

        elif operation == "list_issues":
            return await self._request(
                "GET", f"/repos/{owner}/{repo}/issues",
                params={"state": "open", "per_page": per_page},
            )

        elif operation == "create_issue":
            payload = {"title": title or "New Issue", "body": body or ""}
            if labels:
                payload["labels"] = labels
            return await self._request("POST", f"/repos/{owner}/{repo}/issues", json_data=payload)

        elif operation == "list_prs":
            return await self._request(
                "GET", f"/repos/{owner}/{repo}/pulls",
                params={"state": "open", "per_page": per_page},
            )

        elif operation == "create_pr":
            payload = {
                "title": title or "New PR",
                "body": body or "",
                "head": branch,
                "base": base_branch,
            }
            return await self._request("POST", f"/repos/{owner}/{repo}/pulls", json_data=payload)

        elif operation == "search_code":
            q = query or ""
            if owner and repo:
                q = f"{q} repo:{owner}/{repo}"
            return await self._request("GET", "/search/code", params={"q": q, "per_page": per_page})

        elif operation == "list_commits":
            params: dict[str, Any] = {"per_page": per_page}
            if branch:
                params["sha"] = branch
            return await self._request("GET", f"/repos/{owner}/{repo}/commits", params=params)

        elif operation == "get_commit":
            return await self._request("GET", f"/repos/{owner}/{repo}/commits/{sha}")

        else:
            return 400, {"message": f"Unknown operation: {operation}"}

    def _format_result(self, operation: str, data: Any) -> str:
        """Format API response as readable text for the LLM."""
        if operation == "list_repos" and isinstance(data, list):
            lines = [f"Repositories ({len(data)}):\n"]
            for r in data[:20]:
                lines.append(f"- {r.get('full_name')} ★{r.get('stargazers_count',0)} — {r.get('description','')[:60]}")
            return "\n".join(lines)

        elif operation == "get_file" and isinstance(data, dict):
            import base64
            content = data.get("content", "")
            try:
                decoded = base64.b64decode(content).decode("utf-8", errors="replace")
                return f"File: {data.get('path')} ({data.get('size')} bytes)\n\n{decoded[:5000]}"
            except Exception:
                return f"File: {data.get('path')}"

        elif operation == "list_issues" and isinstance(data, list):
            lines = [f"Open Issues ({len(data)}):\n"]
            for i in data[:20]:
                lines.append(f"#{i.get('number')} {i.get('title')} [{i.get('state')}]")
            return "\n".join(lines)

        elif operation == "list_prs" and isinstance(data, list):
            lines = [f"Open PRs ({len(data)}):\n"]
            for pr in data[:20]:
                lines.append(f"#{pr.get('number')} {pr.get('title')} ({pr.get('head',{}).get('ref')} → {pr.get('base',{}).get('ref')})")
            return "\n".join(lines)

        elif operation == "search_code" and isinstance(data, dict):
            items = data.get("items", [])
            lines = [f"Code search results ({data.get('total_count',0)} total):\n"]
            for item in items[:10]:
                lines.append(f"- {item.get('repository',{}).get('full_name')}/{item.get('path')}")
            return "\n".join(lines)

        elif operation == "list_commits" and isinstance(data, list):
            lines = [f"Commits ({len(data)}):\n"]
            for c in data[:20]:
                sha_short = c.get("sha", "")[:7]
                msg = c.get("commit", {}).get("message", "").split("\n")[0][:60]
                author = c.get("commit", {}).get("author", {}).get("name", "")
                lines.append(f"{sha_short} — {msg} ({author})")
            return "\n".join(lines)

        elif isinstance(data, dict):
            # Generic: show key fields
            import json
            return json.dumps({k: v for k, v in data.items() if k not in ("content",)}, indent=2)[:3000]

        return str(data)[:3000]
