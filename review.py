#!/usr/bin/env python3
"""Code Review Agent — CLI entry point.

Usage:
    python review.py <pr-url>

Example:
    python review.py https://github.com/owner/repo/pull/123
"""

import re
import sys
import os
import subprocess
import tempfile

import anyio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)

from config import load_config
from tools.github_tools import github_server
from tools.repo_tools import repo_server


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pr_number)."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        print(f"Error: Invalid PR URL: {url}")
        print("Expected format: https://github.com/owner/repo/pull/123")
        sys.exit(1)
    return match.group(1), match.group(2), int(match.group(3))


def clone_repo(owner: str, repo: str, head_branch: str) -> str:
    """Clone the repository and checkout the PR branch. Returns the repo path."""
    token = os.environ.get("GITHUB_TOKEN", "")
    clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
    tmp_dir = tempfile.mkdtemp(prefix="code-review-")
    repo_path = os.path.join(tmp_dir, repo)

    print(f"Cloning {owner}/{repo} (branch: {head_branch})...")
    subprocess.run(
        ["git", "clone", "--branch", head_branch, clone_url, repo_path],
        check=True,
        capture_output=True,
        text=True,
    )
    print(f"Cloned to {repo_path}")
    return repo_path


def build_review_prompt(owner: str, repo: str, pr_number: int, language: str) -> str:
    """Build the review prompt with PR context."""
    # Read the system prompt template
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "review_system.md")
    with open(prompt_path) as f:
        system_template = f.read()

    # Map language codes to display names
    lang_map = {
        "zh-TW": "繁體中文",
        "en": "English",
        "ja": "日本語",
        "ko": "한국어",
    }
    review_language = lang_map.get(language, language)

    return f"""Please review the following GitHub Pull Request:
- Repository: {owner}/{repo}
- PR number: {pr_number}

Start by calling `fetch_pr_info` with owner="{owner}", repo="{repo}", pr_number={pr_number} to get the PR details.

Then scan the full project codebase to find related code, potential impacts, and cross-cutting concerns.

Finally, post your review findings as structured comments on GitHub.

Write all review comments in {review_language}.

Important: When posting inline comments with `post_review_comment`, each comment's `line` must refer to a line number within the diff hunk (a line that appears in the patch). Use the RIGHT side line numbers for added/unchanged lines and LEFT side for deleted lines.
"""


async def main():
    if len(sys.argv) < 2:
        print("Usage: python review.py <pr-url>")
        print("Example: python review.py https://github.com/owner/repo/pull/123")
        sys.exit(1)

    pr_url = sys.argv[1]
    config = load_config()

    owner, repo, pr_number = parse_pr_url(pr_url)
    print(f"Reviewing PR #{pr_number} in {owner}/{repo}...")

    # Clone the repo so the agent can scan the full codebase
    repo_path = clone_repo(owner, repo, "main")

    # Try to also fetch the PR branch
    try:
        subprocess.run(
            ["git", "fetch", "origin", f"pull/{pr_number}/head:pr-{pr_number}"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "checkout", f"pr-{pr_number}"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        print("Warning: Could not checkout PR branch, using default branch")

    # Read system prompt
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "review_system.md")
    with open(prompt_path) as f:
        system_prompt = f.read()

    lang_map = {"zh-TW": "繁體中文", "en": "English", "ja": "日本語", "ko": "한국어"}
    review_language = lang_map.get(config.review_language, config.review_language)
    system_prompt = system_prompt.replace("{review_language}", review_language)

    # Build the user prompt
    user_prompt = build_review_prompt(owner, repo, pr_number, config.review_language)

    # Set environment for PyGithub inside the agent
    os.environ["GITHUB_TOKEN"] = config.github_token

    # Run the agent with custom tools
    options = ClaudeAgentOptions(
        cwd=repo_path,
        allowed_tools=[
            "Read", "Glob", "Grep", "Bash",
            "mcp__github-tools__fetch_pr_info",
            "mcp__github-tools__post_pr_summary",
            "mcp__github-tools__post_review_comment",
            "mcp__github-tools__post_review",
            "mcp__github-tools__create_issue",
            "mcp__repo-tools__clone_and_checkout",
        ],
        permission_mode="bypassPermissions",
        model=config.model,
        system_prompt=system_prompt,
        mcp_servers={
            "github-tools": github_server,
            "repo-tools": repo_server,
        },
        max_turns=30,
    )

    print("\nStarting code review...\n")

    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_prompt)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
            elif isinstance(message, ResultMessage):
                print(f"\n✅ Review complete. Stop reason: {message.stop_reason}")


if __name__ == "__main__":
    anyio.run(main)
