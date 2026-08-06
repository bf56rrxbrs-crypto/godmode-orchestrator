#!/usr/bin/env python3
"""
Value-Aware GODMODE Agent (optimized)
-------------------------------------
- Heuristic router by default (0 extra LLM calls)
- Optional --llm-router for borderline confirmation
- Full path: multi_perspective single-pass + repair
- Tip embedded in synthesis call (no third call)
- Auto domain detect from query
"""

from __future__ import annotations

import argparse
import os
import re

from lib import append_memory, chat, detect_domain, load_config, load_skill
from multi_perspective import has_final_synthesis, synthesize

# Strong signals → always full path (no LLM router needed)
STRONG_SIGNALS = [
    r"\bshould i\b", r"\brecommend\b", r"\btrade-?offs?\b", r"\bpros and cons\b",
    r"\banaly[sz]e\b", r"\bcompare\b", r"\bdecide\b", r"\bstrateg(y|ic)\b",
    r"\barchitect\b", r"\bmigrate\b", r"\brefine\b", r"\bimprove\b",
    r"\becu\b", r"\bafr\b", r"\btun(e|ing)\b", r"\bgrom\b", r"\bminix\b",
    r"\bgodmode\b", r"\blanggraph\b", r"\bmulti-?perspective\b",
]

WEAK_SKIP = [
    r"^(hi|hello|hey|thanks|ok|okay|yes|no)\b",
    r"\bwhat is the capital\b", r"\bdefine\b", r"\bwho (is|was)\b",
]


def should_use_skills(query: str, llm_router: bool = False) -> tuple[bool, str]:
    q = query.strip()
    ql = q.lower()

    for pat in WEAK_SKIP:
        if re.search(pat, ql):
            return False, "Simple / low-value pattern"

    strong = any(re.search(p, ql) for p in STRONG_SIGNALS)
    longish = len(q.split()) > 22

    if strong:
        return True, "Strong value signal"
    if not longish and not strong:
        return False, "No high-value signal"

    # Borderline: long query without strong keywords
    if not llm_router:
        return True, "Length/complexity heuristic"

    decision_prompt = f"""Does this query benefit from multi-perspective + high-capacity reasoning?
Answer exactly:
USE: yes or no
REASON: one short sentence

Query: {query}"""
    try:
        text = chat(
            "You are a strict routing classifier. Prefer no unless analysis clearly helps.",
            decision_prompt,
            max_tokens=60,
            temperature=0.0,
        ).lower()
        use = "yes" in text.split("use:")[-1][:15]
        reason = text.split("reason:")[-1].strip() if "reason:" in text else "LLM router"
        return use, reason
    except Exception:
        return True, "Borderline — heuristic fallback"


def run_full_skills(
    query: str,
    *,
    forced: bool = False,
    domain: str | None = None,
    two_phase: bool | None = None,
) -> str:
    body = synthesize(query, domain=domain, two_phase=two_phase)
    out = body
    if forced and not out.lstrip().startswith("[FORCE GODMODE]"):
        out = f"[FORCE GODMODE]\n\n{out}"
    if not has_final_synthesis(out):
        out += "\n\n_Note: Final Synthesis markers not detected._"
    return out


def value_aware_agent(
    query: str,
    *,
    force: bool = False,
    domain: str | None = None,
    llm_router: bool | None = None,
    two_phase: bool | None = None,
) -> str:
    cfg = load_config()
    env_force = os.getenv("FORCE_GODMODE", "").strip().lower() in {"1", "true", "yes", "on"}
    forced = force or env_force
    if domain is None:
        domain = detect_domain(query)
    if llm_router is None:
        llm_router = bool(cfg.get("llm_router", False))

    if forced:
        print(f"[Router] FORCE | domain={domain or '-'}")
        result = run_full_skills(query, forced=True, domain=domain, two_phase=two_phase)
        append_memory(query, result, domain=domain)
        return f"**Skills activated** (FORCE GODMODE)\n\n{result}"

    use, reason = should_use_skills(query, llm_router=llm_router)
    print(f"[Router] use={use} | {reason} | domain={domain or '-'}")

    if use:
        result = run_full_skills(query, forced=False, domain=domain, two_phase=two_phase)
        append_memory(query, result, domain=domain)
        return f"**Skills activated** ({reason})\n\n{result}"

    text = chat(
        "You are a precise, concise assistant. Answer directly.",
        query,
        max_tokens=800,
        temperature=0.4,
    )
    return f"**Skills skipped** ({reason})\n\n{text}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Value-Aware GODMODE (optimized)")
    parser.add_argument("query", nargs="*", help="Task / question")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--domain", default=None)
    parser.add_argument("--llm-router", action="store_true", help="Use LLM for borderline routing")
    parser.add_argument("--two-phase", action="store_true")
    args = parser.parse_args()
    query = " ".join(args.query) if args.query else (
        "Should I switch my personal agent system from sequential to LangGraph?"
    )
    print(
        value_aware_agent(
            query,
            force=args.force,
            domain=args.domain,
            llm_router=True if args.llm_router else None,
            two_phase=True if args.two_phase else None,
        )
    )


if __name__ == "__main__":
    main()
