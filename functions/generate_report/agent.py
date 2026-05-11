import os

import anyio
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    query,
)

from prompts import build_system_prompt


def run_agent(project: dict) -> dict:
    return anyio.run(_run_agent, project)


async def _run_agent(project: dict) -> dict:
    system_prompt = build_system_prompt(project)

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        max_turns=30,
        max_budget_usd=float(os.environ.get("MAX_BUDGET_USD", "0.50")),
        allowed_tools=["WebSearch", "WebFetch", "Bash", "Read", "Glob", "Grep"],
        disallowed_tools=["Write", "Edit"],
    )

    full_text = ""
    async for message in query(
        prompt=(
            f"Research and write a Weekly Deep Dive report on: "
            f"{project['name']} ({project['repo_url']})"
        ),
        options=options,
    ):
        if isinstance(message, ResultMessage):
            full_text = message.result

    return parse_report(full_text)


SECTION_MAP = {
    "title": "title",
    "tagline": "tagline",
    "why it matters": "why_it_matters",
    "beginner level": "beginner",
    "intermediate level": "intermediate",
    "advanced level": "advanced",
    "key takeaways": "key_takeaways",
}


def parse_report(text: str) -> dict:
    sections = {}
    current_key = None
    current_lines: list[str] = []

    for line in text.split("\n"):
        if line.startswith("## "):
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            header = line[3:].strip().lower()
            current_key = SECTION_MAP.get(header)
            current_lines = []
        else:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return {
        "title": sections.get("title", "Untitled"),
        "tagline": sections.get("tagline", ""),
        "why_it_matters": sections.get("why_it_matters", ""),
        "beginner": sections.get("beginner", ""),
        "intermediate": sections.get("intermediate", ""),
        "advanced": sections.get("advanced", ""),
        "key_takeaways": sections.get("key_takeaways", ""),
        "raw_markdown": text,
    }
