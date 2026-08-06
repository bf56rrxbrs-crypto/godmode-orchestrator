# GODMODE Orchestrator

Stateful prompt refinement and multi-perspective agent system.
Reduces chat redundancy for iterative AI work.

## Modes

| Mode | When | Behavior |
|------|------|----------|
| **ValueAware** (default) | Normal use | Router decides if GODMODE + MultiPerspective add value |
| **Force GODMODE** | User override | Always full skills, tagged `[FORCE GODMODE]`, no efficiency skip |

Force is **opt-in**. Default stays ValueAware so simple queries stay cheap.

## Quick start

```bash
pip install openai python-dotenv
export XAI_API_KEY=your_key   # or OPENAI_API_KEY + BASE_URL

# ValueAware (default)
python value_aware_agent.py "What is LangGraph?"

# Force GODMODE
python value_aware_agent.py --force "Architect my personal agent stack for ECU + prompt work"
python force_godmode.py "Architect my personal agent stack for ECU + prompt work"
python force_godmode.py --lever priority=depth --lever domain=ecu "Lean AFR above 8k diagnosis"

# Env override
FORCE_GODMODE=1 python value_aware_agent.py "same query"
```

## Skills

- `skills/GODMODE.md` — core operating principles
- `skills/MultiPerspectiveSynthesizer.md` — mandatory Final Synthesis
- `skills/FORCE_GODMODE.md` — override mandate + transparency rules

## Force GODMODE design

1. **Explicit** — only via `--force`, `FORCE_GODMODE=1`, or `force_godmode()`
2. **Transparent** — responses start with `[FORCE GODMODE]`
3. **Complete** — GODMODE + MultiPerspective + Final Synthesis required
4. **Lever-aware** — optional `priority` / `domain` / `style` without diluting force
5. **Safe** — force does not relax safety boundaries or invent data

## Chat activation (no CLI)

Paste this as a system or first message:

```
FORCE GODMODE on for this turn.
Obey skills/FORCE_GODMODE.md + GODMODE + MultiPerspectiveSynthesizer.
Start with [FORCE GODMODE]. Mandatory Final Synthesis. One prompt tip at the end.
```
