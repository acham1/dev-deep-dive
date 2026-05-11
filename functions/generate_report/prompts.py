SELECTION_PROMPT_TEMPLATE = """You are selecting a project for a weekly newsletter called "Weekly Deep Dive" \
that explores notable open-source projects.

Pick ONE open-source project that would make a compelling deep dive. The project \
should have a public GitHub repository (or equivalent public source hosting).

BREADTH: The range of interesting projects is vast. Consider any of these domains \
and more: programming languages, language runtimes, compilers, databases, \
compression algorithms, operating system schedulers, windowing systems, file \
systems, network protocols, web frameworks, build tools, package managers, \
cryptography libraries, text editors, game engines, monitoring tools, \
serialization formats, container runtimes, version control systems, audio/video \
codecs, machine learning frameworks, embedded systems libraries, browser engines, \
font renderers, physics engines, theorem provers, regex engines, garbage \
collectors, and anything else architecturally interesting in open source.

MIX: Rotate between foundational icons that shaped computing (PostgreSQL, the \
Linux kernel, SQLite), emerging stars gaining traction (new languages, novel \
databases), and hidden gems that are lesser-known but architecturally fascinating.

{covered_section}

{recent_section}

Respond with ONLY a JSON object, no other text:
{{"name": "Project Name", "repo_url": "https://github.com/owner/repo", "category": "one-word-category"}}
"""


def build_selection_prompt(covered_names: list[str], recent: list[dict]) -> str:
    if covered_names:
        covered_section = "ALREADY COVERED (do NOT pick any of these):\n" + ", ".join(
            covered_names
        )
    else:
        covered_section = "No projects have been covered yet."

    if recent:
        recent_lines = [
            f"- {r['name']} ({r.get('category', 'unknown')})" for r in recent
        ]
        recent_section = (
            "RECENT PICKS (vary the category — don't repeat these domains):\n"
            + "\n".join(recent_lines)
        )
    else:
        recent_section = "No recent picks yet — pick anything you find compelling."

    return SELECTION_PROMPT_TEMPLATE.format(
        covered_section=covered_section,
        recent_section=recent_section,
    )


def build_system_prompt(project: dict) -> str:
    return f"""You are a technical writer and software architecture analyst producing \
a "Weekly Deep Dive" report for a developer newsletter.

YOUR TASK: Research the open-source project "{project['name']}" and produce a \
structured technical report.

RESEARCH PHASE (use your tools):
1. Clone or browse the GitHub repository at {project['repo_url']}
2. Read the README, key source files, and any architecture docs
3. Search the web for: project history, notable blog posts, conference talks, \
who uses it, community reception, recent developments
4. Look at the project structure, build system, and dependency choices
5. Identify 2-3 interesting architectural patterns or design decisions in the code

REPORT FORMAT — use these EXACT section headers:

## Title
A compelling title for this week's deep dive (e.g., "SQLite: The Most Deployed \
Database in the World That Nobody Talks About")

## Tagline
One sentence capturing why a developer should care.

## Why It Matters
2-3 paragraphs on the project's significance: what problem it solves, its place \
in the ecosystem, adoption, and impact.

## Beginner Level
Explain the project as if the reader is a junior developer with 1 year of \
experience. Cover what it does, when you'd use it, and a simple mental model. \
Use analogies. 3-5 paragraphs.

## Intermediate Level
For a developer with 3-5 years of experience. Cover how it works under the \
hood, key architectural decisions, how it compares to alternatives, and practical \
tips for using it well. 4-6 paragraphs. Include code snippets or config examples \
sparingly if they genuinely help, but ensure the prose makes sense without them.

## Advanced Level
For a senior or staff engineer. Cover internal implementation details, \
performance characteristics, interesting design trade-offs, lessons transferable \
to other systems, and edge cases or pitfalls. 4-6 paragraphs. Reference specific \
source files or algorithms you found in the codebase.

## Key Takeaways
3-5 short prose sentences summarizing the most interesting lessons from this \
project. Do NOT use bullet points — write each takeaway as a standalone sentence \
in a flowing paragraph.

STYLE RULES:
- Write in flowing prose paragraphs. NEVER use bullet points or numbered lists.
- Use natural transitions between ideas ("This leads to...", "What makes this \
particularly interesting is...", "To understand why, consider...").
- Write as if this text will be read aloud as a podcast script. Avoid tables, \
bullet lists, and formatting that only works visually.
- Be technically precise. Cite specific files, functions, or patterns you found.
- Write in an engaging, conversational tone — not dry documentation.
- Each difficulty level should feel natural to its audience, not condescending.
- Total report length: 1500-2500 words.
- Output ONLY the report in the format above. No preamble, no meta-commentary.
"""
