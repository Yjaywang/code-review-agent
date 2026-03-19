import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    github_token: str
    anthropic_api_key: str
    review_language: str
    model: str


def load_config() -> Config:
    load_dotenv()

    github_token = os.environ.get("GITHUB_TOKEN", "")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")

    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    review_language = os.environ.get("REVIEW_LANGUAGE", "zh-TW")
    model = os.environ.get("MODEL", "claude-sonnet-4-6")

    return Config(
        github_token=github_token,
        anthropic_api_key=anthropic_api_key,
        review_language=review_language,
        model=model,
    )
