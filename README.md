# GODMODE Orchestrator (optimized)

Fewer model calls. Faster routing. Domain-aware. One CLI.

## Call budget

| Path | Model calls |
|------|-------------|
| Simple query (skills skipped) | **1** |
| Full skills (default single-pass) | **1** (2 only if repair) |
| Full skills `--two-phase` | **2–3** |
| Router | **0** (heuristic; optional `--llm-router`) |
| Prompt tip | **0** (embedded in synthesis) |

Previously: router LLM + 2-phase synthesis + tip = **4 calls** on the hot path.

## Quick start

```bash
pip install -r requirements.txt
export XAI_API_KEY=your_key

# Unified CLI (preferred)
python godmode.py "Should I migrate to LangGraph?"
python godmode.py --force "Architect my agent stack"
python godmode.py --domain ecu "Lean AFR above 8k MiniX"
python godmode.py --synth --fast "Quick multi-perspective"
python godmode.py --two-phase "High-stakes architecture decision"
```

## Auto domain detection

Keywords map into: `ecu` | `prompt` | `agent` | `ios`  
Edit `config.json` to tune. Disable with `"auto_domain": false`.

## Config (`config.json`)

```json
{
  "model": "grok-4",
  "synthesis": "single_pass",
  "llm_router": false,
  "embed_tip": true,
  "auto_domain": true,
  "memory": true
}
```

## Modes

| Flag | Behavior |
|------|----------|
| (default) | ValueAware heuristic router → single-pass synthesis if needed |
| `--force` | Always full skills, `[FORCE GODMODE]` tag |
| `--synth` | Synthesis engine only |
| `--fast` | Single-pass, minimal path |
| `--two-phase` | Expand then synthesize (max reliability) |
| `--llm-router` | Extra LLM call for borderline routing |

## Files

| File | Role |
|------|------|
| `godmode.py` | Unified entrypoint |
| `lib.py` | Client, config, skill cache, domain, memory |
| `multi_perspective.py` | Synthesis engine |
| `value_aware_agent.py` | Router |
| `force_godmode.py` | Force wrapper |
| `config.json` | Your defaults |
| `skills/` | GODMODE, MultiPerspective, FORCE cards |

## Chat one-liner

```
FORCE GODMODE. Multi-perspective then Final Synthesis (Recommendation, Conflicts, Confidence, Would change if, Next action). One prompt tip. Start with [FORCE GODMODE].
```
