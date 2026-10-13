"""Deterministic writing-rule checks. Code catches these every time; a model reviewer doesn't.
The model critic still judges tone, framing and the softer rules in prompts/style-guide.md."""

import re

# Clear-cut AI-sounding words that almost never belong in the author's posts.
BANNED_WORDS = (
    "delve", "leverage", "leveraging", "unlock", "unlocking", "harness", "game-changer",
    "game changer", "cutting-edge", "revolutionize", "revolutionise", "transformative",
    "seamless", "seamlessly", "robust", "crucial", "pivotal", "underscore", "underscores",
    "highlight", "highlights", "showcase", "showcases", "foster", "elevate", "empower",
    "streamline", "groundbreaking", "unprecedented", "paradigm", "synergy", "holistic",
    "tapestry", "realm", "testament", "meticulous", "meticulously", "supercharge",
    "future-proof", "state-of-the-art",
)

BANNED_PHRASES = (
    "serves as", "serve as", "serving as", "stands as", "stand as", "plays a role in",
    "play a role in", "it's worth noting", "it is worth noting",
    "it's important to note", "it is important to note", "let's dive in", "in today's",
    "furthermore", "moreover", "additionally", "that said", "that being said", "moving forward",
    "at the end of the day", "let that sink in", "read that again", "paving the way",
    "a pivotal moment", "broader implications", "in other words",
    # Advice to readers, which doesn't fit a learner's voice
    "teams should", "teams must", "leaders should", "leaders must", "companies should",
    "organisations should", "organizations should", "you need to", "here's how to",
    "here is how to", "the playbook",
)

# "It's not X, it's Y" and its relatives. Kept narrow to avoid flagging ordinary sentences.
REFRAME_PATTERNS = (
    r"\b(?:it|this|that)(?:'s| is| isn't| is not) (?:not |n't )?(?:just |only |about |a )?[^.!?]{1,60}[.,;]\s*(?:it|this|that)(?:'s| is) ",
    r"\bnot (?:just|only|merely) [^.!?]{1,60},? but\b",
    r"\bless [a-z]+,? more [a-z]+\b",
    r"\bthe real (?:problem|issue|question|lesson|story|risk) (?:is|isn't)\b",
    r"\bthe question (?:is|isn't) not\b",
    r"\b(?:most people|many assume|at first glance|on the surface)\b",
)


def post_text(draft_markdown: str) -> str:
    """The post itself: the text under '### Draft', up to the next heading."""
    match = re.search(r"### Draft\s*(.*?)(?=\n### |\Z)", draft_markdown, re.S)
    return match.group(1).strip() if match else draft_markdown


def check(draft_markdown: str) -> list:
    """Return a list of rule breaks found in the post text. Empty means none found."""
    text = post_text(draft_markdown)
    lower = text.lower()
    findings = []

    if "—" in text:
        findings.append(f"Em dash used {text.count('—')} time(s); replace with a full stop, comma or colon.")
    for word in BANNED_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", lower):
            findings.append(f'Banned word: "{word}".')
    for phrase in BANNED_PHRASES:
        if phrase in lower:
            findings.append(f'Banned phrase: "{phrase}".')
    for pattern in REFRAME_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            findings.append(f'Reframe ("not X, but Y" pattern): "{match.group(0).strip()}".')
    if re.search(r"\*\*|^#+ ", text, re.M):
        findings.append("Bold or headings inside the post.")
    last_line = text.strip().splitlines()[-1] if text.strip() else ""
    if last_line.rstrip().endswith("?") and "[YOUR EXPERIENCE" not in last_line:
        findings.append("Ends on a question, which reads as engagement bait.")
    return findings
