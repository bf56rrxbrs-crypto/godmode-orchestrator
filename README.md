# GODMODE Orchestrator

Stateful prompt refinement and multi-perspective agent system.
Reduces chat redundancy for iterative AI work.

## Modes

| Mode | When | Behavior |
|------|------|----------|
| **ValueAware** (default) | Normal use | Router decides if full skills add value |
| **Force GODMODE** | User override | Always full skills, tagged `[FORCE GODMODE]` |
| **Multi-Perspective** | Core engine | Two-phase expand → forced Final Synthesis |

## Multi-perspective synthesis (core)

Listing views without reconciliation cuts usefulness ~40–60%.
This repo **enforces** synthesis in code, not only in the prompt:

1. **Phase 1 — Expand** — Technical / Practical / Strategic (no final pick)
2. **Phase 2 — Synthesize** — one recommendation, conflicts resolved, confidence, change-conditions, next action
3. **Validate** — repair pass if Final Synthesis markers are missing

```bash
python multi_perspective.py "Should I migrate my agent to LangGraph?"
python multi_perspective.py --domain ecu "Lean AFR above 8k with MiniX"
python multi_perspective.py --single-pass "faster but less reliable path"
```

## Quick start

```bash
pip install openai python-dotenv
export XAI_API_KEY=your_key   # or OPENAI_API_KEY + BASE_URL

# Synthesis engine directly
python multi_perspective.py "Architect my personal agent stack"

# ValueAware (router)
python value_aware_agent.py "What is LangGraph?"
python value_aware_agent.py --force "Architect my agent stack"

# Force GODMODE
python force_godmode.py "Architect my agent stack"
python force_godmode.py --lever priority=depth --lever domain=ecu "Lean AFR diagnosis"
```

## Skills

| File | Role |
|------|------|
| `skills/GODMODE.md` | Core operating principles |
| `skills/MultiPerspectiveSynthesizer.md` | Perspective + mandatory synthesis contract |
| `skills/FORCE_GODMODE.md` | Override mandate + transparency |

## Files

| File | Role |
|------|------|
| `multi_perspective.py` | Two-phase synthesis engine + validator |
| `value_aware_agent.py` | Router + force flag → synthesis engine |
| `force_godmode.py` | Explicit full-capacity entrypoint |

## Chat activation

```
FORCE GODMODE on for this turn.
Run multi-perspective (Technical, Practical, Strategic) then mandatory Final Synthesis:
Recommendation, Conflicts resolved, Confidence, Would change if, Next action.
Start with [FORCE GODMODE]. One prompt tip at the end.
```
