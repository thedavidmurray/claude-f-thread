# claude-f-thread

Multi-agent consensus for Claude Code. Run prompts across N agents in parallel, synthesize for higher-confidence outputs.

## What It Is

An **F-thread** (fusion thread) is a consensus pattern: send the same prompt to N independent agents simultaneously, then synthesize their responses into a unified recommendation with a confidence score.

Single agents have blind spots. Three agents will disagree where one would hallucinate confidently. The synthesis step surfaces that disagreement and forces explicit tradeoff analysis.

## When to Use

**Use F-thread when:**
- High-stakes architecture, strategy, or security decisions
- Code review where multiple perspectives reduce bug slip-through
- Complex debugging where parallel hypothesis generation matters
- Any situation where a wrong answer has real cost

**Don't use when:**
- Simple lookup or generation tasks
- Latency-sensitive real-time responses
- Low-stakes decisions where 3x token cost isn't justified

## Quick Start

```bash
# CLI usage
python fthread_cli.py "Design a rate limiting strategy for an API gateway" -n 3

# With a specific synthesis strategy
python fthread_cli.py "Review this architecture decision" --strategy agreement

# Deep analysis with 5 agents
python fthread_cli.py "Analyze the security tradeoffs of JWT vs sessions" -n 5 --strategy weighted
```

## Programmatic Usage

```python
import asyncio
from f_thread import f_thread, f_thread_quick, f_thread_deep

# Simple: get synthesis text only
async def main():
    synthesis = await f_thread_quick("What are the tradeoffs of event sourcing?")
    print(synthesis)

# Full result with confidence, disagreements, individual responses
async def main_deep():
    result = await f_thread_deep(
        prompt="Design the authentication layer for a multi-tenant SaaS",
        n_agents=3
    )
    print(result.format_report())
    print(f"Confidence: {result.confidence_score:.0%}")
    print(f"Agreement: {result.agreement_level}")

asyncio.run(main())
```

## Agent Interface

F-thread requires a `delegate_task` coroutine. By default it uses a stub that returns placeholder responses. Replace it with your agent system:

Create `agent_interface.py` in the same directory:

```python
# agent_interface.py -- implement for your backend

async def delegate_task(goal: str, context: str = "", toolsets=None):
    """
    Submit work to an agent and return the result.

    Must return an object with:
      .summary: str       -- agent's response text
      .tokens_used: int   -- token count (can be approximate)
    """
    # Example: Claude Code subagent
    # result = await Task(subagent_type="general-purpose", prompt=goal, ...)
    # return result

    # Example: OpenAI
    # response = await openai_client.chat.completions.create(...)
    # ...

    raise NotImplementedError("Implement delegate_task for your agent system")
```

## Synthesis Strategies

### `weighted` (default)

A judge agent reads all N responses and produces a unified recommendation with explicit consensus/divergence analysis. Best quality, highest token cost.

**Output format:**
```
Consensus: [what all/most agents agreed on]
Key Alternatives: [legitimate different approaches]
Unified Recommendation: [synthesized guidance, HIGH/MEDIUM/LOW confidence]
```

### `agreement`

Calculate agreement level (3/3 = high, 2/3 = medium, 1/3 = low). Present all viewpoints with confidence labels. No judge agent needed — fastest and cheapest.

### `union`

Combine all unique points from all responses. Good for brainstorming where you want maximum idea coverage, not convergence.

## Example Output

```
============================================================
F-THREAD CONSENSUS REPORT
============================================================

Agreement Level: MEDIUM (70%)
Token Cost: 7,000
Agents Consulted: 3

------------------------------------------------------------
SYNTHESIS
------------------------------------------------------------
**Consensus:** All three agents recommended token bucket algorithm
over sliding window for its simplicity and predictable memory use.

**Key Alternatives:**
- Agent 1: Redis-based distributed bucket (strong consistency)
- Agent 2: In-memory with async sync (lower latency)
- Agent 3: Hybrid local+shared (balance of both)

**Unified Recommendation:** Start with Agent 3's hybrid approach.
Local token bucket per instance, async sync to shared store.
Confidence: HIGH

------------------------------------------------------------
KEY DISAGREEMENTS (Worth Reviewing)
------------------------------------------------------------
  - Storage backend choice affects failover behavior
  - Redis adds operational overhead at small scale

============================================================
```

## Cost Guide

| Config | Agents | Strategy | ~Tokens | ~Latency |
|--------|--------|----------|---------|---------|
| Minimal | 2 | union | 4K | 15s |
| **Standard** | **3** | **weighted** | **8K** | **25s** |
| Deep | 5 | weighted | 15K | 40s |
| Fast | 3 | agreement | 6K | 20s |

Rule of thumb: F-thread costs ~3x a single agent call and reduces error rate ~40%.

## Files

| File | Purpose |
|------|---------|
| `f_thread.py` | Core implementation — `f_thread()`, `FThreadResult`, synthesis strategies |
| `fthread_cli.py` | CLI wrapper for direct invocation |
| `skill.md` | Skill descriptor for Claude Code skill system integration |

## License

MIT — see [LICENSE](LICENSE).
