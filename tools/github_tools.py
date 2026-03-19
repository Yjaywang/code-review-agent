"""Custom tools for GitHub PR interactions using PyGithub."""

import json
import os
from typing import Any

from claude_agent_sdk import tool, create_sdk_mcp_server
from github import Github


def _get_github() -> Github:
    token = os.environ.get("GITHUB_TOKEN", "")
    return Github(token)


def _parse_repo_and_pr(owner: str, repo: str, pr_number: int):
    g = _get_github()
    repository = g.get_repo(f"{owner}/{repo}")
    pr = repository.get_pull(pr_number)
    return repository, pr


@tool(
    "fetch_pr_info",
    "Fetch PR metadata, changed files, and unified diff. Returns PR title, body, "
    "list of changed files with their patches, and commit SHA.",
    {"owner": str, "repo": str, "pr_number": int},
)
async def fetch_pr_info(args: dict[str, Any]) -> dict[str, Any]:
    owner = args["owner"]
    repo = args["repo"]
    pr_number = args["pr_number"]

    _, pr = _parse_repo_and_pr(owner, repo, pr_number)

    files = []
    for f in pr.get_files():
        files.append({
            "filename": f.filename,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
            "changes": f.changes,
            "patch": f.patch or "",
        })

    result = {
        "title": pr.title,
        "body": pr.body or "",
        "state": pr.state,
        "base_branch": pr.base.ref,
        "head_branch": pr.head.ref,
        "head_sha": pr.head.sha,
        "changed_files_count": pr.changed_files,
        "additions": pr.additions,
        "deletions": pr.deletions,
        "files": files,
    }

    return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}


@tool(
    "post_pr_summary",
    "Post a general summary comment on the PR conversation tab. "
    "Use this after completing the review to post an overall summary.",
    {"owner": str, "repo": str, "pr_number": int, "body": str},
)
async def post_pr_summary(args: dict[str, Any]) -> dict[str, Any]:
    owner = args["owner"]
    repo = args["repo"]
    pr_number = args["pr_number"]
    body = args["body"]

    _, pr = _parse_repo_and_pr(owner, repo, pr_number)
    comment = pr.create_issue_comment(body)

    return {"content": [{"type": "text", "text": f"Summary comment posted: {comment.html_url}"}]}


@tool(
    "post_review_comment",
    "Post a single inline review comment on a specific line of a file. "
    "Each comment becomes its own thread that can be replied to and resolved independently. "
    "Call this once per finding.",
    {
        "owner": str,
        "repo": str,
        "pr_number": int,
        "path": str,
        "body": str,
        "line": int,
        "side": str,
        "start_line": int,
        "start_side": str,
    },
)
async def post_review_comment(args: dict[str, Any]) -> dict[str, Any]:
    owner = args["owner"]
    repo = args["repo"]
    pr_number = args["pr_number"]
    path = args["path"]
    body = args["body"]
    line = args["line"]

    _, pr = _parse_repo_and_pr(owner, repo, pr_number)
    commit = pr.get_commits().reversed[0]

    kwargs: dict[str, Any] = {
        "body": body,
        "commit": commit,
        "path": path,
        "line": line,
    }
    if "side" in args:
        kwargs["side"] = args["side"]
    if "start_line" in args:
        kwargs["start_line"] = args["start_line"]
    if "start_side" in args:
        kwargs["start_side"] = args["start_side"]

    try:
        comment = pr.create_review_comment(**kwargs)
        return {"content": [{"type": "text", "text": f"Comment posted: {comment.html_url}"}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Failed to post comment on {path}:{line}: {str(e)}"}]}


@tool(
    "post_review",
    "Submit the final review verdict on the PR. Use this AFTER posting all inline comments "
    "with post_review_comment. The event can be 'COMMENT', 'REQUEST_CHANGES', or 'APPROVE'. "
    "Do NOT include inline comments here — they should already be posted individually.",
    {
        "owner": str,
        "repo": str,
        "pr_number": int,
        "body": str,
        "event": str,
    },
)
async def post_review(args: dict[str, Any]) -> dict[str, Any]:
    owner = args["owner"]
    repo = args["repo"]
    pr_number = args["pr_number"]
    body = args["body"]
    event = args["event"]

    _, pr = _parse_repo_and_pr(owner, repo, pr_number)
    commit = pr.get_commits().reversed[0]

    review = pr.create_review(
        commit=commit,
        body=body,
        event=event,
    )

    return {"content": [{"type": "text", "text": f"Review posted: {review.html_url}"}]}


@tool(
    "create_issue",
    "Create a GitHub issue for cross-cutting concerns found during review. "
    "Use this for problems that affect multiple files or require broader changes.",
    {"owner": str, "repo": str, "title": str, "body": str, "labels": list},
)
async def create_issue(args: dict[str, Any]) -> dict[str, Any]:
    owner = args["owner"]
    repo = args["repo"]
    title = args["title"]
    body = args["body"]
    labels = args.get("labels", [])

    g = _get_github()
    repository = g.get_repo(f"{owner}/{repo}")

    issue = repository.create_issue(
        title=title,
        body=body,
        labels=labels if labels else [],
    )

    return {"content": [{"type": "text", "text": f"Issue created: {issue.html_url}"}]}


# Bundle all tools into an MCP server
github_server = create_sdk_mcp_server(
    "github-tools",
    tools=[fetch_pr_info, post_pr_summary, post_review_comment, post_review, create_issue],
)
