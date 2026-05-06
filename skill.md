---
name: f-thread
description: |
  Multi-agent consensus pattern (fusion thread). Send identical prompts to N agents in parallel,
  synthesize responses for higher-confidence outputs. Catches errors through disagreement,
  surfaces alternative approaches, builds confidence when agents converge.
metadata:
  tags:
  - multi-agent
  - consensus
  - parallel
  - synthesis
  - confidence
  tier: general
  domain: orchestration
version: 1.0.0
category: orchestration
triggers:
- /fthread
- fthread
- fusion thread
- multi-agent consensus
- parallel agents
when_to_apply: |
  High-stakes decisions, architecture choices, strategy evaluation, complex problem analysis,
  code review, bug investigation -- any situation where multiple perspectives reduce error
  rate and increase confidence.
  NOT for simple/rote tasks where token cost overhead is not justified.
---

# F-Thread: Multi-Agent Consensus Pattern

## Overview

**F-threads (fusion threads)** execute the same prompt across N agents in parallel, then
synthesize results for higher-confidence outputs than any single agent can provide.

### Why Consensus Works

| Pattern | Error Detection | Alternative Views | Confidence |
|---------|-----------------|-------------------|------------|
| Single Agent | None | None | Low |
| F-Thread (3 agents) | Disagreement flags issues | Multiple approaches surfaced | High |

### Use Cases

1. **Architecture decisions** -- 3 independent proposals, compare tradeoffs
2. **Code review** -- Multiple reviewers catch different issue classes
3. **Bug investigation** -- Parallel hypothesis generation
4. **Strategy evaluation** -- Diverse perspectives on complex decisions
5. **Risk assessment** -- Cross-validate findings before acting

## Invocation

```
/fthread <prompt> [n=3] [model=default]
```

Parameters:
- `n` -- Number of parallel agents (default: 3, range: 2-5)
- `model` -- Model tier for workers (default: same as caller)

## Workflow

```
                         F-THREAD WORKFLOW

  Input Prompt
       |
       v
  +----------+  +----------+  +----------+
  | Agent 1  |  | Agent 2  |  | Agent 3  |  ... (N agents)
  | Worker   |  | Worker   |  | Worker   |
  +----+-----+  +----+-----+  +----+-----+
       |              |              |
       +--------------+--------------+
                      |
              +-------+--------+
              |   Synthesis    |  <- Judge agent merges outputs
              |    Agent       |     identifies agreements/disagreements
              +-------+--------+
                      |
              +-------+--------+
              |   F-Thread     |  <- Unified recommendation
              |   Result       |     with confidence level
              +----------------+
```

## Synthesis Strategies

### 1. Weighted Synthesis (Default)

A "judge" agent reviews all N outputs and produces a unified recommendation.

**Pros**: Nuanced merging, handles complex outputs
**Cons**: Higher token cost, adds latency

### 2. Agreement Scoring (Simple)

Calculate agreement level: 3/3 = high confidence, 2/3 = medium, 1/3 = low.
Present all viewpoints with confidence labels.

**Pros**: Fast, transparent
**Cons**: No true synthesis for complex outputs

### 3. Union Merge

Combine all unique points from all responses.

**Pros**: Captures all ideas
**Cons**: Can be verbose, no prioritization

## Cost Analysis

| Config | Workers | Synthesis | Est. Tokens | Latency |
|--------|---------|-----------|-------------|---------|
| Minimal | 2 | Union | ~4K | ~15s |
| **Standard** | **3** | **Weighted** | **~8K** | **~25s** |
| Deep | 5 | Weighted | ~15K | ~40s |
| Fast | 3 | Agreement | ~6K | ~20s |

**Rule of thumb**: F-thread adds ~3x token cost vs. single agent for ~40% error reduction.

## When to Use vs. Single Agent

### Use F-Thread When:
- High-stakes decision with costly errors
- Complex problem with multiple valid approaches
- Need to catch edge cases or subtle bugs
- Strategy evaluation requiring diverse perspectives
- Safety-critical analysis

### Use Single Agent When:
- Simple/rote tasks
- Latency-sensitive (real-time responses)
- Cost-sensitive (low-stakes decisions)
- Iterative refinement (multiple single calls better than one consensus)

## Related Patterns

- **Builder/Validator**: Simpler 2-agent version -- one builds, one validates
- **Parallel Specialists**: Multiple domain experts reviewing the same artifact
- **Swarm**: Many agents working on independent subtasks (not consensus)

## References

- IndyDevDan "Agent Threads" -- F-thread concept origin
- Consensus theory in distributed systems
- Ensemble methods in ML (bagging/boosting parallels)
