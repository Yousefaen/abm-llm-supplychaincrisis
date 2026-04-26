"""Generate persona text for a sim agent from a cached EDGAR filing.

Calls Sonnet with two existing hand-crafted personas as few-shot examples
(BoschAuto and EuroChip — both Tier-1 / chip-designer tier so they are not
in the EDGAR target set, which is OEMs + foundry + designer NXP).

Schema enforced by the prompt — matches what agents.py:PERSONAS uses:
1. Opening paragraph: "You are the [role] of [company]..." + 2-3 ALL-CAPS
   personality traits + behavioral tells (~120 words).
2. INTERNAL DYNAMICS: 3 stakeholder/board tensions (~80 words).
3. YOUR KPIs: 4 numbered KPIs with concrete thresholds (~50 words).
"""

from __future__ import annotations

import re
from pathlib import Path

import anthropic

# Re-use the project's existing personas as few-shot examples so the generated
# style matches what the sim already consumes.
from agents import PERSONAS, MODEL_SONNET

# 10-Ks/20-Fs commonly run 500K-1M chars in plain text. Sonnet 4 has a 200K
# context window; we send the first ~50K tokens which usually covers Item 1
# (Business) and the start of Item 1A (Risk Factors) — exactly the sections
# that disclose strategy, supplier/customer concentration, and competitive
# positioning.
_MAX_FILING_CHARS = 200_000

# Inline-XBRL filings front-load 100KB+ of taxonomy tags before any prose.
# Skip to the first narrative section header.  10-Ks use "ITEM 1. Business",
# 20-Fs use "Item 4. Information on the Company".
_NARRATIVE_START = re.compile(
    r"(ITEM\s+1\.\s*Business|Item\s+4\.\s*Information\s+on\s+the\s+Company"
    r"|Item\s+4A?\.\s*History\s+and\s+Development)",
    re.IGNORECASE,
)


def _trim_to_narrative(text: str) -> str:
    """Skip past XBRL/cover-page boilerplate to the first prose section."""
    m = _NARRATIVE_START.search(text)
    if m:
        return text[m.start():]
    return text

SYSTEM_PROMPT = """You write executive-style personas for a procurement \
supply-chain simulation. Each persona becomes the system prompt for an LLM \
agent that role-plays a real company's senior decision-maker during a chip \
shortage.

Output exactly one persona block, no preamble or commentary, matching the \
schema of the provided examples:

1) Opening paragraph: starts with "You are the [role] of [company]," then 2-3 \
   ALL-CAPS personality traits, then behavioral tells under stress. ~120 words.
2) INTERNAL DYNAMICS: a paragraph naming three stakeholder/board tensions \
   that pull the executive in different directions. ~80 words.
3) YOUR KPIs: four numbered KPIs, each with a concrete numeric threshold. \
   ~50 words.

Total length: 250-300 words. Match the voice and concreteness of the examples. \
Ground every personality trait, internal-dynamics tension, and KPI in something \
the source filing actually says about the company's strategy, risk factors, \
competitors, or operating model. Do not invent numbers — pull thresholds from \
the filing where you can."""


def build_persona(
    agent_id: str,
    role: str,
    company: str,
    upstream_desc: str,
    downstream_desc: str,
    doc_path: Path,
    client: anthropic.Anthropic | None = None,
) -> tuple[str, dict]:
    """Generate a persona text for ``agent_id``.

    Returns (persona_text, usage_dict).  ``usage_dict`` carries input/output
    tokens so the caller can total cost.
    """
    client = client or anthropic.Anthropic()
    raw = doc_path.read_text(encoding="utf-8")
    filing_text = _trim_to_narrative(raw)[:_MAX_FILING_CHARS]

    # Use two existing personas as schema/tone exemplars.  Both sit outside
    # the EDGAR target set, so we never feed Sonnet the answer it's asked to
    # produce.
    user = f"""Generate a procurement-sim persona for {company}, who in the \
simulation plays the role of "{role}".

Their upstream suppliers in the sim: {upstream_desc}
Their downstream customers in the sim: {downstream_desc}

EXAMPLE PERSONA 1 (BoschAuto — Tier-1 supplier):
{PERSONAS['BoschAuto']}

EXAMPLE PERSONA 2 (EuroChip — chip designer):
{PERSONAS['EuroChip']}

SOURCE DOCUMENT (excerpt from {company}'s most recent SEC filing):

{filing_text}

Generate the persona for {company}. Output only the persona block."""

    resp = client.messages.create(
        model=MODEL_SONNET,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    text = resp.content[0].text.strip() if resp.content else ""
    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
    }
    return text, usage
