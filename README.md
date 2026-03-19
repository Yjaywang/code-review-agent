# Code Review Agent

使用 Claude Agent SDK 打造的 AI Code Review 工具，類似 Gemini Code Assist。不只檢查 PR 修改的部分，還會掃描整個專案找到相關程式碼，再到 GitHub 上發結構化的 review comments 和 issues。

## 功能

- **PR Diff 分析** — 取得 PR 的變更檔案和 patch
- **全專案掃描** — 用 Glob/Grep/Read 搜尋整個 codebase，找出相關的 callers、tests、config
- **結構化 Review** — 在 GitHub PR 上發 inline comments，附帶嚴重程度標籤（🔴🟠🟡🔵）和 suggestion blocks
- **Summary Comment** — 在 PR conversation tab 發一個總結，列出所有發現
- **自動開 Issue** — 跨多個檔案的 cross-cutting concerns 會自動建立 GitHub Issue
- **多語言支援** — Review 語言可透過 `REVIEW_LANGUAGE` 設定，預設繁體中文

## 架構

```
code-review-agent/
├── review.py               # CLI 進入點，agent orchestration
├── config.py               # 環境變數設定
├── tools/
│   ├── github_tools.py     # 自訂 MCP tools：fetch PR、post review、create issue
│   └── repo_tools.py       # 自訂 MCP tool：clone repo
├── prompts/
│   ├── review_system.md    # Agent system prompt（review 流程與格式）
│   └── templates.py        # Comment 模板（severity emoji/labels）
└── .github/workflows/
    └── code-review.yml     # GitHub Actions workflow
```

## 前置需求

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) 套件管理工具
- GitHub Personal Access Token（需要 `repo` 和 `issues` 權限）
- Anthropic API Key

## 安裝

```bash
cd code-review-agent
cp .env.example .env
```

編輯 `.env` 填入你的 token：

```
GITHUB_TOKEN=ghp_your_token
ANTHROPIC_API_KEY=sk-ant-your_key
REVIEW_LANGUAGE=zh-TW
MODEL=claude-sonnet-4-6
```

安裝依賴：

```bash
uv sync
```

## 使用方式

### CLI

```bash
uv run python review.py https://github.com/owner/repo/pull/123
```

### GitHub Actions

1. 在你的 repo 設定 Secrets：
   - `ANTHROPIC_API_KEY`
2. 將 `.github/workflows/code-review.yml` 複製到你的 repo
3. 開 PR 時會自動觸發 review

## Agent 工作流程

### Phase 1: Context Gathering
- 呼叫 `fetch_pr_info` 取得 PR metadata 和 diff
- 理解 PR 的目的和修改內容

### Phase 2: Deep Project Scanning
使用 `Glob`、`Grep`、`Read` 掃描整個專案：
- 找出 import/call 變更函式的檔案
- 找出相關的測試檔案
- 找出引用變更模組的設定檔
- 找出其他地方的類似 pattern

### Phase 3: Post Results
- `post_review` — 批次發送所有 inline comments（含 severity 標籤和 suggestion blocks）
- `post_pr_summary` — 發總結 comment
- `create_issue` — 對影響 3+ 檔案的 cross-cutting concerns 開 issue

## 自訂 Review 語言

透過 `REVIEW_LANGUAGE` 環境變數控制：

| 值 | 語言 |
|----|------|
| `zh-TW` | 繁體中文（預設）|
| `en` | English |
| `ja` | 日本語 |
| `ko` | 한국어 |

## Review Comment 範例

### Inline Comment
```
🟡 **中 Priority**

使用 queueIndex: [0, 1] 會導致這個 cron job 同時在兩個 queue 上被觸發，
但 RETRY_FAILED_TASK action 使用了 Redlock 確保同一站點只有一個實例在執行。
建議將此任務排在單一的 queue 上。

```suggestion
"queueIndex": 0
```
```

### Summary Comment
```
## Code Review

這個 PR 為 QC 站點新增了兩個 cron job。發現 RETRY_FAILED_TASK 的設定存在效率問題。

| 嚴重程度 | 數量 |
|----------|------|
| 🔴 嚴重 | 0 |
| 🟠 高 | 0 |
| 🟡 中 | 1 |
| 🔵 低 | 0 |
```
