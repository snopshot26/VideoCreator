from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.config import AppConfig


_ILLEGAL_PATTERNS = [
    r"\bchild\s*porn",
    r"\bcp\b.*\bvideo",
    r"\bminor.*\bsex",
    r"\bsexual.*\bminor",
    r"\bterror(ist)?\s*attack\s*plan",
    r"\bbomb\s*making",
    r"\bhack\s*bank",
    r"\bcredit\s*card\s*fraud",
]
_VIOLENCE_FRAUD = [
    r"\bhow\s+to\s+kill\b",
    r"\bmake\s+meth\b",
    r"\bransomware\b",
]

_FAKE_CRITICAL = [
    r"\bfake\s+confession\b",
    r"\bfake\s+endorsement\b",
    r"\bfake\s+emergency\b",
    r"\belection\s+fraud\s+instruction\b",
]


@dataclass
class SafetyResult:
    allowed: bool
    message: str = ""
    public_figure_warning: bool = False


def _matches_any(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    for p in patterns:
        if re.search(p, lowered, re.IGNORECASE):
            return True
    return False


def public_figure_hint(text: str) -> bool:
    """Heuristic: user may be asking for realistic public figure content."""
    hints = [
        "trump",
        "biden",
        "putin",
        "celebrity",
        "politician",
        "president",
        "prime minister",
    ]
    t = text.lower()
    return any(h in t for h in hints)


def check_prompt(idea: str, cfg: AppConfig) -> SafetyResult:
    if not idea or not idea.strip():
        return SafetyResult(False, "Prompt is empty.")

    if cfg.safety.block_illegal_content:
        if _matches_any(idea, _ILLEGAL_PATTERNS) or _matches_any(idea, _VIOLENCE_FRAUD):
            return SafetyResult(
                False,
                "This request appears to violate safety rules (illegal or severely harmful content).",
            )

    warn_pf = public_figure_hint(idea)
    if _matches_any(idea, _FAKE_CRITICAL):
        return SafetyResult(
            False,
            "Requests for fake confessions, fake endorsements, fake emergencies, or deceptive "
            "election instructions are not allowed.",
        )

    msg = ""
    if warn_pf:
        msg = (
            "Public figure / parody style content: use fictional parody only. "
            "Voice cloning of real people is disabled."
        )
    return SafetyResult(True, msg, public_figure_warning=warn_pf)
