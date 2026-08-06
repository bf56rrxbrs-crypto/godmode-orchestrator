#!/usr/bin/env python3
"""Force GODMODE — thin wrapper over optimized synthesis + tag."""

from __future__ import annotations

import argparse

from lib import append_memory, detect_domain
from multi_perspective import has_final_synthesis, synthesize


def force_godmode(query: str, domain: str | None = None, two_phase: bool | None = None) -> str:
    if domain is None:
        domain = detect_domain(query)
    body = synthesize(query, domain=domain, two_phase=two_phase)
    out = f"[FORCE GODMODE]\n\n{body}"
    if not has_final_synthesis(out):
        out += "\n\n_Warning: Final Synthesis markers not detected._"
    append_memory(query, out, domain=domain)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Force GODMODE")
    parser.add_argument("query", nargs="+")
    parser.add_argument("--domain", default=None)
    parser.add_argument("--two-phase", action="store_true")
    parser.add_argument(
        "--lever",
        action="append",
        default=[],
        help="key=value (domain=ecu still supported via --domain)",
    )
    args = parser.parse_args()
    domain = args.domain
    for raw in args.lever:
        if raw.lower().startswith("domain="):
            domain = raw.split("=", 1)[1].strip()
    print(force_godmode(" ".join(args.query), domain=domain, two_phase=True if args.two_phase else None))


if __name__ == "__main__":
    main()
