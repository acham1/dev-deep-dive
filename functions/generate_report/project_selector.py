import json
import os
import urllib.request

import anthropic

from firestore_client import get_covered_projects
from prompts import build_selection_prompt


def select_project() -> dict:
    covered = get_covered_projects()
    covered_names = [p["name"] for p in covered]
    recent = covered[-5:] if covered else []

    prompt = build_selection_prompt(covered_names, recent)

    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    project = json.loads(text)

    for field in ("name", "repo_url", "category"):
        if field not in project:
            raise ValueError(f"Selection missing '{field}': {text}")

    _validate_repo(project["repo_url"])
    return project


def _validate_repo(url: str) -> None:
    if "github.com" not in url:
        return

    parts = url.rstrip("/").split("github.com/")[-1].split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {url}")

    owner, repo = parts[0], parts[1]
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    req = urllib.request.Request(api_url, headers={"User-Agent": "deep-dive-bot"})

    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                raise ValueError(
                    f"GitHub repo not accessible (HTTP {resp.status}): {url}"
                )
    except urllib.error.HTTPError as e:
        raise ValueError(f"GitHub repo not accessible (HTTP {e.code}): {url}") from e
