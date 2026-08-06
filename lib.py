#!/usr/bin/env python3
"""Shared helpers: config, client, skill cache, domain detect, memory."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent
SKILLS_DIR = ROOT / "skills"
MEMORY_DIR = ROOT / "memory"
CONFIG_PATH = ROOT / "config.json"

_DEFAULT_CONFIG = {
    "model": "grok-4",
    "default_mode": "auto",
    "synthesis": "single_pass",
    "llm_router": False,
    "embed_tip": True,
    "auto_domain": True,
    "memory": True,
    "domains": {
        "ecu": ["ecu", "aracer", "minix", "afr", "grom", "msx", "tune", "tuning", "yoshimura", "fuel map", "ignition"],
        "prompt": ["prompt", "godmode", "skill", "system prompt", "tot", "got", "multi-perspective"],
        "agent": ["agent", "langgraph", "crewai", "orchestrator", "router", "framework"],
        "ios": ["iphone", "ios", "scriptable", "shortcut", "draw things", "testflight"],
    },
}


@lru_cache(maxsize=1)
def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            merged = {**_DEFAULT_CONFIG, **data}
            if "domains" in data:
                merged["domains"] = {**_DEFAULT_CONFIG["domains"], **data["domains"]}
            return merged
        except Exception:
            pass
    return dict(_DEFAULT_CONFIG)


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    return OpenAI(
        api_key=os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("BASE_URL", "https://api.x.ai/v1"),
    )


def model_id() -> str:
    return os.getenv("MODEL") or str(load_config().get("model", "grok-4"))


@lru_cache(maxsize=16)
def load_skill(name: str) -> str:
    path = SKILLS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def detect_domain(query: str) -> str | None:
    cfg = load_config()
    if not cfg.get("auto_domain", True):
        return None
    q = query.lower()
    scores: dict[str, int] = {}
    for domain, keywords in cfg.get("domains", {}).items():
        scores[domain] = sum(1 for kw in keywords if kw in q)
    best = max(scores, key=scores.get) if scores else None
    if best and scores.get(best, 0) > 0:
        return best
    return None


def chat(
    system: str,
    user: str,
    *,
    max_tokens: int = 1600,
    temperature: float = 0.35,
) -> str:
    resp = get_client().chat.completions.create(
        model=model_id(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


def append_memory(query: str, summary: str, domain: str | None = None) -> None:
    cfg = load_config()
    if not cfg.get("memory", True):
        return
    MEMORY_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    # Keep summary short to avoid localStorage-style bloat on disk
    snippet = re.sub(r"\s+", " ", summary)[:500]
    path = MEMORY_DIR / f"run_{stamp}.md"
    path.write_text(
        f"# {stamp}\n**Domain:** {domain or '-'}\n**Query:** {query}\n**Summary:** {snippet}\n",
        encoding="utf-8",
    )
    # Cap memory files at 40
    files = sorted(MEMORY_DIR.glob("run_*.md"))
    for old in files[:-40]:
        try:
            old.unlink()
        except OSError:
            pass
