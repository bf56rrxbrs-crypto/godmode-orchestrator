#!/usr/bin/env python3
"""
Force GODMODE
-------------
Explicit override path. Bypasses ValueAware routing and always runs
GODMODE + MultiPerspectiveSynthesizer at full capacity.

Usage:
  python force_godmode.py "your query"
  python force_godmode.py --lever priority=depth --lever domain=ecu "diagnose lean AFR"
  FORCE_GODMODE=1 python value_aware_agent.py "query"   # via integrated agent

Design rules:
  - Default OFF (ValueAware decides)
  - Force is session/query scoped, never the silent default
  - Output is tagged [FORCE GODMODE] for transparency
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

VALID_LEVERS = {
    "priority": {"speed", "depth", "creativity", "accuracy", "ethics"},
    "style": {"concise", "expansive", "collaborative", "narrative"},
}


def load_skill(name: str) -> str:
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Missing skill: {path}")
    return path.read_text(encoding="utf-8")


def parse_lever(raw: str) -> tuple[str, str]:
    if "=" not in raw:
        raise ValueError(f"Lever must be key=value, got: {raw}")
    key, value = raw.split("=", 1)
    key, value = key.strip().lower(), value.strip().lower()
    if key == "domain":
        return key, value  # free-form domain focus
    allowed = VALID_LEVERS.get(key)
    if not allowed:
        raise ValueError(f"Unknown lever '{key}'. Use priority|domain|style")
    if value not in allowed:
        raise ValueError(f"Invalid {key}={value}. Allowed: {sorted(allowed)}")
    return key, value


def build_system(levers: dict[str, str]) -> str:
    parts = [
        load_skill("FORCE_GODMODE"),
        load_skill("GODMODE"),
        load_skill("MultiPerspectiveSynthesizer"),
    ]
    if levers:
        lever_lines = "\n".join(f"- {k}: {v}" for k, v in levers.items())
        parts.append(f"## Active Levers (user-set)\n{lever_lines}")
    return "\n\n---\n\n".join(parts)


def force_godmode(query: str, levers: dict[str, str] | None = None, model: str | None = None) -> str:
    """Run full Force GODMODE pipeline. Always activates skills."""
    levers = levers or {}
    system = build_system(levers)
    lever_note = ""
    if levers:
        lever_note = " Levers: " + ", ".join(f"{k}={v}" for k, v in levers.items())

    user = f"""FORCE GODMODE is active. Do not take a lightweight path.

TASK:
{query}

INSTRUCTIONS:
1. Fully apply MultiPerspectiveSynthesizer (all three perspectives).
2. Produce mandatory Final Synthesis with conflicts resolved, confidence, and change-conditions.
3. Be decisive and high-leverage.
4. Start the response with [FORCE GODMODE].{lever_note}
5. End with exactly one actionable prompt-improvement tip."""

    resp = client.chat.completions.create(
        model=model or os.getenv("MODEL", "grok-4"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.35,
        max_tokens=2400,
    )
    text = resp.choices[0].message.content or ""
    if not text.lstrip().startswith("[FORCE GODMODE]"):
        text = f"[FORCE GODMODE]{lever_note}\n\n{text}"
    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Force GODMODE — explicit full-capacity override")
    parser.add_argument("query", nargs="+", help="Task / question")
    parser.add_argument(
        "--lever",
        action="append",
        default=[],
        help="Lever as key=value (priority=depth, domain=ecu, style=concise). Repeatable.",
    )
    parser.add_argument("--model", default=None, help="Override model id")
    args = parser.parse_args()

    levers: dict[str, str] = {}
    for raw in args.lever:
        k, v = parse_lever(raw)
        levers[k] = v

    query = " ".join(args.query)
    print(force_godmode(query, levers=levers, model=args.model))


if __name__ == "__main__":
    main()
