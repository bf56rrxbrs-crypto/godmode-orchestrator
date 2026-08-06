#!/usr/bin/env python3
"""
Unified GODMODE CLI (optimized entrypoint)
------------------------------------------
  python godmode.py "query"                 # auto (ValueAware)
  python godmode.py --force "query"         # Force GODMODE
  python godmode.py --synth "query"         # synthesis only
  python godmode.py --fast "query"          # single-pass, no tip overhead knobs
  python godmode.py --domain ecu "query"
"""

from __future__ import annotations

import argparse
import sys

from lib import detect_domain, load_config
from multi_perspective import has_final_synthesis, synthesize
from value_aware_agent import value_aware_agent


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="godmode",
        description="Optimized GODMODE orchestrator — auto | force | synth",
    )
    parser.add_argument("query", nargs="+", help="Your question or task")
    parser.add_argument("--force", "-f", action="store_true", help="Force GODMODE")
    parser.add_argument("--synth", "-s", action="store_true", help="Synthesis engine only")
    parser.add_argument("--fast", action="store_true", help="Single-pass, minimal extras")
    parser.add_argument("--two-phase", action="store_true", help="Expand then synthesize")
    parser.add_argument("--domain", "-d", default=None, help="ecu|prompt|agent|ios")
    parser.add_argument("--llm-router", action="store_true", help="LLM borderline routing")
    args = parser.parse_args()

    query = " ".join(args.query)
    domain = args.domain or detect_domain(query)
    two_phase = True if args.two_phase else (False if args.fast else None)

    if args.synth or args.fast and not args.force:
        # Direct synthesis path
        result = synthesize(query, domain=domain, two_phase=bool(args.two_phase))
        print(result)
        print(f"\n---\nDomain: {domain or 'none'} | Synthesis OK: {has_final_synthesis(result)}", file=sys.stderr)
        return

    print(
        value_aware_agent(
            query,
            force=args.force,
            domain=domain,
            llm_router=True if args.llm_router else None,
            two_phase=two_phase,
        )
    )


if __name__ == "__main__":
    main()
