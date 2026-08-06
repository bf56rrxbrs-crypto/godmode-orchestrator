#!/usr/bin/env python3
"""
Multi-Perspective Synthesis Engine
----------------------------------
Two-phase pipeline so Final Synthesis cannot be skipped:

  Phase 1 — Expand: Technical / Practical / Strategic perspectives
  Phase 2 — Synthesize: forced reconciliation into one recommendation

Usage:
  python multi_perspective.py "Should I migrate to LangGraph?"
  python multi_perspective.py --single-pass "same"   # one call, validated
  python multi_perspective.py --json "same"          # structured dict-ish text

Import:
  from multi_perspective import synthesize
  text = synthesize("your question")
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.x.ai/v1"),
)

ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"
MODEL = os.getenv("MODEL", "grok-4")

SYNTHESIS_MARKERS = re.compile(
    r"final synthesis|\*\*recommendation:\*\*|confidence:\s*(high|medium|low)",
    re.IGNORECASE,
)


def load_skill(name: str) -> str:
    path = SKILLS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _chat(system: str, user: str, max_tokens: int = 1600, temperature: float = 0.35) -> str:
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


def has_final_synthesis(text: str) -> bool:
    """True if output includes a real Final Synthesis block."""
    if not text:
        return False
    if not re.search(r"final synthesis", text, re.I):
        return False
    # Require at least a recommendation signal or confidence tag
    if re.search(r"recommendation\s*:" , text, re.I):
        return True
    if re.search(r"confidence\s*:\s*(high|medium|low)", text, re.I):
        return True
    return False


def phase_expand(query: str, domain: str | None = None) -> str:
    """Phase 1: three perspectives only — no final pick yet."""
    skill = load_skill("MultiPerspectiveSynthesizer")
    system = (
        "You are a rigorous multi-perspective analyst.\n\n" + skill
        if skill
        else "You are a rigorous multi-perspective analyst."
    )
    domain_line = f"\nDomain context: {domain}\n" if domain else ""
    user = f"""{domain_line}
TASK:
{query}

INSTRUCTIONS FOR THIS PHASE:
- Produce ONLY the three perspectives: Technical Expert, End-User/Practical, Strategic/Long-term.
- For each: Key insights, Risks, Opportunities.
- Do NOT give a final recommendation yet.
- Do NOT write a Final Synthesis section in this phase.
"""
    return _chat(system, user, max_tokens=1400)


def phase_synthesize(query: str, perspectives: str, domain: str | None = None) -> str:
    """Phase 2: forced reconciliation into one recommendation."""
    system = """You are the Synthesis Judge.
Your only job: reconcile multiple perspectives into ONE decisive recommendation.

Rules:
- Do not re-list full perspectives; reference them only as needed.
- Name the strongest conflicts and how you resolve them.
- Confidence must be High, Medium, or Low.
- State change-conditions and a single next action.
- Forbidden: ending with unresolved options or pure "it depends".
"""
    domain_line = f"Domain: {domain}\n" if domain else ""
    user = f"""{domain_line}Original question:
{query}

Perspectives to reconcile:
{perspectives}

Now produce ONLY the Final Synthesis section using this skeleton:

## Final Synthesis
**Recommendation:** <one clear path>
**Conflicts resolved:** <named tensions + how resolved>
**Confidence:** High|Medium|Low
**Would change if:** <conditions>
**Next action:** <single concrete step>
"""
    return _chat(system, user, max_tokens=900, temperature=0.25)


def synthesize_two_phase(query: str, domain: str | None = None) -> str:
    """Expand then synthesize. Guarantees a Final Synthesis section."""
    perspectives = phase_expand(query, domain=domain)
    synthesis = phase_synthesize(query, perspectives, domain=domain)

    if not has_final_synthesis(synthesis):
        # One repair pass
        synthesis = phase_synthesize(
            query,
            perspectives + "\n\n[REPAIR] Previous synthesis missing required fields. Fill all fields.",
            domain=domain,
        )

    return f"{perspectives.rstrip()}\n\n{synthesis.lstrip()}"


def synthesize_single_pass(query: str, domain: str | None = None) -> str:
    """One model call with validation + repair if Final Synthesis missing."""
    skill = load_skill("MultiPerspectiveSynthesizer")
    system = skill or "You are a multi-perspective analyst. Always end with Final Synthesis."
    domain_line = f"Domain context: {domain}\n" if domain else ""
    user = f"""{domain_line}
TASK:
{query}

Follow MultiPerspectiveSynthesizer fully.
You MUST include the Final Synthesis section with Recommendation, Conflicts resolved, Confidence, Would change if, and Next action.
"""
    text = _chat(system, user, max_tokens=2000)

    if has_final_synthesis(text):
        return text

    # Repair: force synthesis from whatever was produced
    repair = phase_synthesize(query, text, domain=domain)
    if has_final_synthesis(repair):
        return f"{text.rstrip()}\n\n{repair.lstrip()}"
    return f"{text.rstrip()}\n\n## Final Synthesis\n**Recommendation:** Insufficient structure from model — re-run with --two-phase.\n**Confidence:** Low\n**Next action:** Re-run synthesis with two-phase pipeline."


def synthesize(
    query: str,
    *,
    domain: str | None = None,
    two_phase: bool = True,
) -> str:
    """Public API. Default two-phase for reliability."""
    if two_phase:
        return synthesize_two_phase(query, domain=domain)
    return synthesize_single_pass(query, domain=domain)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-perspective synthesis with forced Final Synthesis")
    parser.add_argument("query", nargs="+", help="Question or decision to analyze")
    parser.add_argument("--domain", default=None, help="Optional domain bias (e.g. ecu, agents, prompts)")
    parser.add_argument(
        "--single-pass",
        action="store_true",
        help="One model call instead of expand→synthesize (still validated)",
    )
    args = parser.parse_args()
    query = " ".join(args.query)
    result = synthesize(query, domain=args.domain, two_phase=not args.single_pass)
    print(result)
    print("\n---")
    print(f"Final Synthesis present: {has_final_synthesis(result)}")


if __name__ == "__main__":
    main()
