# Code Review Agent

An AI-powered code review tool built with the Claude Agent SDK, similar to Gemini Code Assist. It doesn't just check the modified files in a PR — it scans the entire project to find related code, then posts structured review comments and issues on GitHub.

## Features

- **PR Diff Analysis** — Fetches changed files and patches from the PR
- **Full Project Scanning** — Uses Glob/Grep/Read to search the entire codebase for related callers, tests, and configs
- **Structured Review** — Posts individual inline comments on GitHub PR lines, each with severity labels (🔴🟠🟡🔵) and suggestion blocks
- **Summary Comment** — Posts a summary on the PR conversation tab listing all findings
- **Auto Issue Creation** — Automatically creates GitHub Issues for cross-cutting concerns spanning multiple files
- **Multi-language Support** — Review language configurable via `REVIEW_LANGUAGE`, defaults to Traditional Chinese



## Architecture

```
code-review-agent/
├── review.py               # CLI entry point, agent orchestration
├── config.py               # Environment variable configuration
├── tools/
│   ├── github_tools.py     # Custom MCP tools: fetch PR, post review, create issue
│   └── repo_tools.py       # Custom MCP tool: clone repo
├── prompts/
│   ├── review_system.md    # Agent system prompt (review workflow & format)
│   └── templates.py        # Comment templates (severity emoji/labels)
└── .github/workflows/
    └── code-review.yml     # GitHub Actions workflow
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- GitHub Personal Access Token (requires `repo` and `issues` permissions)
- Anthropic API Key

## Setup

```bash
cd code-review-agent
cp .env.example .env
```

Edit `.env` with your tokens:

```
GITHUB_TOKEN=ghp_your_token
ANTHROPIC_API_KEY=sk-ant-your_key
REVIEW_LANGUAGE=zh-TW
MODEL=claude-sonnet-4-6
```

Install dependencies:

```bash
uv sync
```

## Usage

### CLI

```bash
uv run python review.py https://github.com/owner/repo/pull/123
```

### GitHub Actions

1. Add the following secret to your repo settings:
   - `ANTHROPIC_API_KEY`
2. Copy `.github/workflows/code-review.yml` to your repo
3. Reviews will be triggered automatically when a PR is opened

## Agent Workflow

### Phase 1: Context Gathering
- Calls `fetch_pr_info` to get PR metadata and diff
- Understands the purpose and scope of the PR

### Phase 2: Deep Project Scanning
Uses `Glob`, `Grep`, and `Read` to scan the full project:
- Finds files that import/call the changed functions
- Finds related test files
- Finds config files referencing changed modules
- Finds similar patterns elsewhere in the codebase

### Phase 3: Post Results
- `post_review_comment` — Posts individual inline comments with severity labels and suggestion blocks
- `post_review` — Submits the final review verdict (APPROVE / REQUEST_CHANGES / COMMENT)
- `post_pr_summary` — Posts a summary comment
- `create_issue` — Creates issues for cross-cutting concerns affecting 3+ files

## Review Language

Controlled via the `REVIEW_LANGUAGE` environment variable:

| Value | Language |
|-------|----------|
| `zh-TW` | Traditional Chinese (default) |
| `en` | English |
| `ja` | Japanese |
| `ko` | Korean |

## Review Comment Examples

### Inline Comment
```
🟡 **Medium Priority**

Using queueIndex: [0, 1] causes this cron job to be triggered on two queues simultaneously,
but the RETRY_FAILED_TASK action uses Redlock to ensure only one instance runs per site.
Consider assigning this task to a single queue.

```suggestion
"queueIndex": 0
```
```

### Summary Comment
```
## Code Review

This PR adds two cron jobs for the QC site. An efficiency issue was found in the RETRY_FAILED_TASK configuration.

| Severity | Count |
|----------|-------|
| 🔴 Critical | 0 |
| 🟠 High | 0 |
| 🟡 Medium | 1 |
| 🔵 Low | 0 |
```


## Performance
<img width="947" height="672" alt="image" src="https://github.com/user-attachments/assets/e9edcfbb-f472-43eb-9481-ce3d9048499e" />
<img width="948" height="634" alt="image" src="https://github.com/user-attachments/assets/b9281531-65c5-42e6-b7bc-833a8f87c65e" />