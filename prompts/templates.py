"""Comment templates for code review formatting."""

SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
}

SEVERITY_LABELS = {
    "zh-TW": {
        "critical": "嚴重",
        "high": "高",
        "medium": "中",
        "low": "低",
    },
    "en": {
        "critical": "Critical",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    },
}


def get_summary_template(language: str = "zh-TW") -> str:
    if language == "zh-TW":
        return """## Code Review

{summary}

| 嚴重程度 | 數量 |
|----------|------|
| 🔴 嚴重 | {critical_count} |
| 🟠 高 | {high_count} |
| 🟡 中 | {medium_count} |
| 🔵 低 | {low_count} |

{details}"""
    else:
        return """## Code Review

{summary}

| Severity | Count |
|----------|-------|
| 🔴 Critical | {critical_count} |
| 🟠 High | {high_count} |
| 🟡 Medium | {medium_count} |
| 🔵 Low | {low_count} |

{details}"""


def get_inline_comment_template(severity: str, language: str = "zh-TW") -> str:
    emoji = SEVERITY_EMOJI.get(severity, "🔵")
    labels = SEVERITY_LABELS.get(language, SEVERITY_LABELS["en"])
    label = labels.get(severity, severity)
    return f"{emoji} **{label} Priority**\n\n"
