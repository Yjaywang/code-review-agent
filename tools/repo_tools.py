"""Tools for cloning and managing repository checkouts."""

import os
import subprocess
import tempfile
from typing import Any

from claude_agent_sdk import tool, create_sdk_mcp_server


@tool(
    "clone_and_checkout",
    "Clone a GitHub repository and checkout the PR branch. "
    "Returns the local path to the cloned repository.",
    {"owner": str, "repo": str, "head_branch": str, "base_branch": str},
)
async def clone_and_checkout(args: dict[str, Any]) -> dict[str, Any]:
    owner = args["owner"]
    repo = args["repo"]
    head_branch = args["head_branch"]
    base_branch = args["base_branch"]

    token = os.environ.get("GITHUB_TOKEN", "")
    clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"

    tmp_dir = tempfile.mkdtemp(prefix="code-review-")
    repo_path = os.path.join(tmp_dir, repo)

    # Clone with full history for better analysis
    subprocess.run(
        ["git", "clone", "--branch", head_branch, clone_url, repo_path],
        check=True,
        capture_output=True,
        text=True,
    )

    return {
        "content": [
            {
                "type": "text",
                "text": f"Repository cloned to {repo_path} (branch: {head_branch})",
            }
        ]
    }


repo_server = create_sdk_mcp_server(
    "repo-tools",
    tools=[clone_and_checkout],
)
