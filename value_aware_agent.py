#!/usr/bin/env python3
"""
Value-Aware GODMODE Agent
-------------------------
Default: only invoke GODMODE + MultiPerspective when they add value.
Override: --force / FORCE_GODMODE=1 / force_godmode() bypasses the router.

Usage:
  python value_aware_agent.py "simple question"
  python value_aware_agent.py --force "architect my agent stack"
  FORCE_GODMODE=1 python value_aware_agent.py "same"
"""

from __future__ import annotations

import argparse
import os
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
MEMORY_DIR = ROOT / "memory"
MEMORY_DIR.mkdir(exist_ok=True)

VALUE_SIGNALS = [
    "refine", "improve", "analyze", "compare", "decide", "recommend",
    "trade-off", "pros", "cons", "strategy", "best way", "should i",
    "ecu", "tune", "mapping", "prompt", "system", "agent", "tot", "got",
    "multi-perspective", "synthesis", "complex", "architecture",
    "godmode", "force",
]


def load_skill(name: str) -> str:
    path = SKILLS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def should_use_skills(query: str) -> tuple[bool, str]:
    """ValueAware router. Returns (use, reason)."""
    q = query.lower()
    heuristic_hit = any(s in q for s in VALUE_SIGNALS) or len(query.split()) > 25

    if not heuristic_hit:
        return False, "Simple or low-complexity query"

    decision_prompt = f"""Does this query benefit from full multi-perspective analysis + high-capacity reasoning (GODMODE style)?
Answer with exactly:
USE: yes or no
REASON: one short sentence

Query: {query}"""
    try:
        resp = client.chat.completions.create(
            model=os.getenv("MODEL", "grok-4"),
            messages=[{"role": "user", "content": decision_prompt}],
            temperature=0.0,
            max_tokens=80,
        )
        text = (resp.choices[0].message.content or "").strip().lower()
        use = "yes" in text.split("use:")[-1][:15]
        reason = text.split("reason:")[-1].strip() if "reason:" in text else "Heuristic + LLM decision"
        return use, reason
    except Exception:
        return heuristic_hit, "Heuristic only (LLM decision failed)"


def run_full_skills(query: str, forced: bool = False) -> str:
    force_card = load_skill("FORCE_GODMODE") if forced else ""
    godmode = load_skill("GODMODE")
    multi = load_skill("MultiPerspectiveSynthesizer")
    system = "\n\n---\n\n".join(p for p in (force_card, godmode, multi) if p)

    prefix = (
        "FORCE GODMODE is active. Do not take a lightweight path.\n\n"
        if forced
        else ""
    )
    user = f"""{prefix}Fully apply the MultiPerspectiveSynthesizer skill (mandatory Final Synthesis) to this request:

{query}

End every response with exactly one high-value, immediately actionable prompt-improvement tip."""
    if forced:
        user += "\nStart the response with [FORCE GODMODE]."

    resp = client.chat.completions.create(
        model=os.getenv("MODEL", "grok-4"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.35,
        max_tokens=2400 if forced else 1800,
    )
    text = resp.choices[0].message.content or ""
    if forced and not text.lstrip().startswith("[FORCE GODMODE]"):
        text = f"[FORCE GODMODE]\n\n{text}"
    return text


def value_aware_agent(query: str, force: bool = False) -> str:
    env_force = os.getenv("FORCE_GODMODE", "").strip().lower() in {"1", "true", "yes", "on"}
    forced = force or env_force

    if forced:
        print("[Value Decision] Use skills: True | Reason: FORCE GODMODE override")
        result = run_full_skills(query, forced=True)
        return f"**Skills activated** (FORCE GODMODE override)\n\n{result}"

    use, reason = should_use_skills(query)
    print(f"[Value Decision] Use skills: {use} | Reason: {reason}")

    if use:
        result = run_full_skills(query, forced=False)
        return f"**Skills activated** ({reason})\n\n{result}"

    resp = client.chat.completions.create(
        model=os.getenv("MODEL", "grok-4"),
        messages=[{"role": "user", "content": query}],
        temperature=0.5,
        max_tokens=800,
    )
    return f"**Skills skipped for efficiency** ({reason})\n\n{resp.choices[0].message.content}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Value-Aware GODMODE agent with Force override")
    parser.add_argument("query", nargs="*", help="Task / question")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force GODMODE: bypass ValueAware router, full skills always",
    )
    args = parser.parse_args()
    query = " ".join(args.query) if args.query else (
        "Should I switch my personal agent system from sequential to LangGraph for better state handling?"
    )
    print(value_aware_agent(query, force=args.force))


if __name__ == "__main__":
    main()
