#!/usr/bin/env python3
"""
Value-Aware GODMODE Agent
Only invokes GODMODE + MultiPerspectiveSynthesizer when it clearly adds user value.
"""

import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL", "https://api.x.ai/v1")
)

SKILLS_DIR = Path("skills")
MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)

def load_skill(name: str) -> str:
    path = SKILLS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""

def should_use_skills(query: str) -> tuple[bool, str]:
    """Decide if the skills add value. Returns (use: bool, reason: str)"""
    # Fast heuristic first
    q = query.lower()
    value_signals = [
        "refine", "improve", "analyze", "compare", "decide", "recommend",
        "trade-off", "pros", "cons", "strategy", "best way", "should i",
        "ecu", "tune", "mapping", "prompt", "system", "agent", "tot", "got",
        "multi-perspective", "synthesis", "complex", "architecture"
    ]
    heuristic_hit = any(s in q for s in value_signals) or len(query.split()) > 25

    if not heuristic_hit:
        return False, "Simple or low-complexity query"

    # LLM confirmation for borderline / positive heuristic cases
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
            max_tokens=80
        )
        text = resp.choices[0].message.content.strip().lower()
        use = "yes" in text.split("use:")[-1][:15]
        reason = text.split("reason:")[-1].strip() if "reason:" in text else "Heuristic + LLM decision"
        return use, reason
    except Exception:
        return heuristic_hit, "Heuristic only (LLM decision failed)"

def run_full_skills(query: str) -> str:
    godmode = load_skill("GODMODE")
    multi = load_skill("MultiPerspectiveSynthesizer")
    system = f"{godmode}\n\n{multi}"
    user = f"""Fully apply the MultiPerspectiveSynthesizer skill (mandatory Final Synthesis) to this request:

{query}

End every response with exactly one high-value, immediately actionable prompt-improvement tip."""
    resp = client.chat.completions.create(
        model=os.getenv("MODEL", "grok-4"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ],
        temperature=0.35
    )
    return resp.choices[0].message.content

def value_aware_agent(query: str) -> str:
    use, reason = should_use_skills(query)
    print(f"[Value Decision] Use skills: {use} | Reason: {reason}")

    if use:
        result = run_full_skills(query)
        return f"**Skills activated** ({reason})\n\n{result}"
    else:
        # Lightweight pass-through
        resp = client.chat.completions.create(
            model=os.getenv("MODEL", "grok-4"),
            messages=[{"role": "user", "content": query}],
            temperature=0.5
        )
        return f"**Skills skipped for efficiency** ({reason})\n\n{resp.choices[0].message.content}"

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Should I switch my personal agent system from sequential to LangGraph for better state handling?"
    print(value_aware_agent(query))
