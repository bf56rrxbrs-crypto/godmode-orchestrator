#!/usr/bin/env python3
"""
Multi-Perspective Synthesis Engine (optimized)
----------------------------------------------
Default: single-pass + repair only if Final Synthesis missing (1 call happy path).
Optional: --two-phase for maximum reliability (2–3 calls).

Usage:
  python multi_perspective.py "Should I migrate to LangGraph?"
  python multi_perspective.py --two-phase "high-stakes decision"
  python multi_perspective.py --domain ecu "Lean AFR above 8k"
"""

from __future__ import annotations

import argparse
import re

from lib import chat, detect_domain, load_config, load_skill


def has_final_synthesis(text: str) -> bool:
    if not text:
        return False
    if not re.search(r"final synthesis", text, re.I):
        return False
    if re.search(r"recommendation\s*:", text, re.I):
        return True
    if re.search(r"confidence\s*:\s*(high|medium|low)", text, re.I):
        return True
    return False


def _tip_instruction(embed: bool) -> str:
    if not embed:
        return ""
    return "\nEnd with exactly one line: **Prompt tip:** <actionable tip>\n"


def phase_expand(query: str, domain: str | None = None) -> str:
    skill = load_skill("MultiPerspectiveSynthesizer")
    system = "You are a rigorous multi-perspective analyst.\n\n" + skill if skill else (
        "You are a rigorous multi-perspective analyst."
    )
    domain_line = f"\nDomain context: {domain}\n" if domain else ""
    user = f"""{domain_line}
TASK:
{query}

INSTRUCTIONS FOR THIS PHASE:
- Produce ONLY the three perspectives: Technical Expert, End-User/Practical, Strategic/Long-term.
- For each: Key insights, Risks, Opportunities.
- Do NOT write a Final Synthesis section yet.
"""
    return chat(system, user, max_tokens=1400)


def phase_synthesize(query: str, perspectives: str, domain: str | None = None, embed_tip: bool = True) -> str:
    system = """You are the Synthesis Judge.
Reconcile perspectives into ONE decisive recommendation.
Name strongest conflicts and how you resolve them.
Confidence: High|Medium|Low. Change-conditions. Single next action.
Forbidden: unresolved option lists or pure "it depends"."""
    domain_line = f"Domain: {domain}\n" if domain else ""
    user = f"""{domain_line}Original question:
{query}

Perspectives:
{perspectives}

Produce ONLY:

## Final Synthesis
**Recommendation:** ...
**Conflicts resolved:** ...
**Confidence:** High|Medium|Low
**Would change if:** ...
**Next action:** ...
{_tip_instruction(embed_tip)}"""
    return chat(system, user, max_tokens=900, temperature=0.25)


def synthesize_two_phase(query: str, domain: str | None = None, embed_tip: bool = True) -> str:
    perspectives = phase_expand(query, domain=domain)
    synthesis = phase_synthesize(query, perspectives, domain=domain, embed_tip=embed_tip)
    if not has_final_synthesis(synthesis):
        synthesis = phase_synthesize(
            query,
            perspectives + "\n\n[REPAIR] Fill all required Final Synthesis fields.",
            domain=domain,
            embed_tip=embed_tip,
        )
    return f"{perspectives.rstrip()}\n\n{synthesis.lstrip()}"


def synthesize_single_pass(query: str, domain: str | None = None, embed_tip: bool = True) -> str:
    skill = load_skill("MultiPerspectiveSynthesizer")
    system = skill or "You are a multi-perspective analyst. Always end with Final Synthesis."
    domain_line = f"Domain context: {domain}\n" if domain else ""
    user = f"""{domain_line}
TASK:
{query}

Follow MultiPerspectiveSynthesizer fully.
Include all three perspectives, then mandatory Final Synthesis with:
Recommendation, Conflicts resolved, Confidence, Would change if, Next action.
{_tip_instruction(embed_tip)}"""
    text = chat(system, user, max_tokens=2000)
    if has_final_synthesis(text):
        return text
    repair = phase_synthesize(query, text, domain=domain, embed_tip=embed_tip)
    if has_final_synthesis(repair):
        return f"{text.rstrip()}\n\n{repair.lstrip()}"
    return (
        f"{text.rstrip()}\n\n## Final Synthesis\n"
        "**Recommendation:** Structure incomplete — re-run with --two-phase.\n"
        "**Confidence:** Low\n**Next action:** Re-run with two-phase pipeline."
    )


def synthesize(
    query: str,
    *,
    domain: str | None = None,
    two_phase: bool | None = None,
    embed_tip: bool | None = None,
) -> str:
    cfg = load_config()
    if domain is None:
        domain = detect_domain(query)
    if two_phase is None:
        two_phase = str(cfg.get("synthesis", "single_pass")).lower() in {"two_phase", "two-phase"}
    if embed_tip is None:
        embed_tip = bool(cfg.get("embed_tip", True))

    if two_phase:
        return synthesize_two_phase(query, domain=domain, embed_tip=embed_tip)
    return synthesize_single_pass(query, domain=domain, embed_tip=embed_tip)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-perspective synthesis (optimized)")
    parser.add_argument("query", nargs="+", help="Question or decision")
    parser.add_argument("--domain", default=None, help="Domain bias (ecu|prompt|agent|ios)")
    parser.add_argument("--two-phase", action="store_true", help="Force expand→synthesize (more calls)")
    parser.add_argument("--single-pass", action="store_true", help="Force single-pass (default)")
    args = parser.parse_args()
    query = " ".join(args.query)
    two_phase = True if args.two_phase else (False if args.single_pass else None)
    result = synthesize(query, domain=args.domain, two_phase=two_phase)
    print(result)
    print("\n---")
    dom = args.domain or detect_domain(query)
    print(f"Domain: {dom or 'none'} | Final Synthesis: {has_final_synthesis(result)}")


if __name__ == "__main__":
    main()
