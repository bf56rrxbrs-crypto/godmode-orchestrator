#!/usr/bin/env python3
"""
Value-Aware GODMODE Agent
-------------------------
Default: only invoke full skills when they add value.
Override: --force / FORCE_GODMODE=1 bypasses the router.

Full-skill path uses multi_perspective.synthesize (two-phase by default)
so Final Synthesis is enforced, not merely prompted.
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


def run_full_skills(query: str, forced: bool = False, domain: str | None = None) -> str:
    """Full path: multi-perspective two-phase synthesis + tip."""
    try:
        from multi_perspective import synthesize, has_final_synthesis
    except ImportError:
        synthesize = None
        has_final_synthesis = lambda t: "final synthesis" in t.lower()

    if synthesize is not None:
        body = synthesize(query, domain=domain, two_phase=True)
    else:
        # Fallback single call if module missing
        godmode = load_skill("GODMODE")
        multi = load_skill("MultiPerspectiveSynthesizer")
        force_card = load_skill("FORCE_GODMODE") if forced else ""
        system = "\n\n---\n\n".join(p for p in (force_card, godmode, multi) if p)
        user = f"Apply MultiPerspectiveSynthesizer fully to:\n\n{query}\n\nMandatory Final Synthesis."
        resp = client.chat.completions.create(
            model=os.getenv("MODEL", "grok-4"),
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.35,
            max_tokens=2000,
        )
        body = resp.choices[0].message.content or ""

    tip_block = ""
    try:
        tip = client.chat.completions.create(
            model=os.getenv("MODEL", "grok-4"),
            messages=[{
                "role": "user",
                "content": f"One actionable prompt-improvement tip for someone who asked: {query}\nReply with one sentence only, no preamble.",
            }],
            temperature=0.4,
            max_tokens=120,
        )
        tip_text = (tip.choices[0].message.content or "").strip()
        if tip_text:
            tip_block = f"\n\n---\n**Prompt tip:** {tip_text}"
    except Exception:
        pass

    out = body + tip_block
    if forced and not out.lstrip().startswith("[FORCE GODMODE]"):
        out = f"[FORCE GODMODE]\n\n{out}"
    if synthesize is not None and not has_final_synthesis(out):
        out += "\n\n_Note: synthesis validator did not detect Final Synthesis markers._"
    return out


def value_aware_agent(
    query: str,
    force: bool = False,
    domain: str | None = None,
) -> str:
    env_force = os.getenv("FORCE_GODMODE", "").strip().lower() in {"1", "true", "yes", "on"}
    forced = force or env_force

    if forced:
        print("[Value Decision] Use skills: True | Reason: FORCE GODMODE override")
        result = run_full_skills(query, forced=True, domain=domain)
        return f"**Skills activated** (FORCE GODMODE override)\n\n{result}"

    use, reason = should_use_skills(query)
    print(f"[Value Decision] Use skills: {use} | Reason: {reason}")

    if use:
        result = run_full_skills(query, forced=False, domain=domain)
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
    parser.add_argument("--force", action="store_true", help="Force GODMODE: bypass router")
    parser.add_argument("--domain", default=None, help="Optional domain bias")
    args = parser.parse_args()
    query = " ".join(args.query) if args.query else (
        "Should I switch my personal agent system from sequential to LangGraph for better state handling?"
    )
    print(value_aware_agent(query, force=args.force, domain=args.domain))


if __name__ == "__main__":
    main()
