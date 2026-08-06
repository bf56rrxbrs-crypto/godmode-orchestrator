#!/usr/bin/env python3
"""
Force GODMODE
-------------
Explicit override. Bypasses ValueAware routing and always runs
multi-perspective two-phase synthesis at full capacity.

Usage:
  python force_godmode.py "your query"
  python force_godmode.py --lever priority=depth --lever domain=ecu "diagnose lean AFR"
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
        return key, value
    allowed = VALID_LEVERS.get(key)
    if not allowed:
        raise ValueError(f"Unknown lever '{key}'. Use priority|domain|style")
    if value not in allowed:
        raise ValueError(f"Invalid {key}={value}. Allowed: {sorted(allowed)}")
    return key, value


def force_godmode(query: str, levers: dict[str, str] | None = None) -> str:
    levers = levers or {}
    domain = levers.get("domain")

    from multi_perspective import synthesize, has_final_synthesis

    body = synthesize(query, domain=domain, two_phase=True)

    lever_note = ""
    if levers:
        lever_note = " Levers: " + ", ".join(f"{k}={v}" for k, v in levers.items())

    # Optional tip
    tip_block = ""
    try:
        tip = client.chat.completions.create(
            model=os.getenv("MODEL", "grok-4"),
            messages=[{
                "role": "user",
                "content": f"One actionable prompt-improvement tip for: {query}\nOne sentence only.",
            }],
            temperature=0.4,
            max_tokens=120,
        )
        tip_text = (tip.choices[0].message.content or "").strip()
        if tip_text:
            tip_block = f"\n\n---\n**Prompt tip:** {tip_text}"
    except Exception:
        pass

    out = f"[FORCE GODMODE]{lever_note}\n\n{body}{tip_block}"
    if not has_final_synthesis(out):
        out += "\n\n_Warning: Final Synthesis markers not detected._"
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Force GODMODE — full multi-perspective synthesis")
    parser.add_argument("query", nargs="+", help="Task / question")
    parser.add_argument(
        "--lever",
        action="append",
        default=[],
        help="key=value (priority=depth, domain=ecu, style=concise)",
    )
    args = parser.parse_args()

    levers: dict[str, str] = {}
    for raw in args.lever:
        k, v = parse_lever(raw)
        levers[k] = v

    print(force_godmode(" ".join(args.query), levers=levers))


if __name__ == "__main__":
    main()
