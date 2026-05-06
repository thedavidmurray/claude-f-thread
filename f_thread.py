"""
F-Thread: Multi-Agent Consensus Pattern Implementation

Usage:
    from f_thread import f_thread, FThreadResult

    result = await f_thread(
        prompt="Analyze the tradeoffs of microservices vs monoliths",
        n_agents=3,
        synthesis_strategy="weighted"
    )

    print(result.synthesis)
    print(f"Confidence: {result.confidence_score}")
"""

import asyncio
from dataclasses import dataclass, field
from typing import List, Literal, Optional
import hashlib


# ---------------------------------------------------------------------------
# Agent interface
#
# F-Thread requires a `delegate_task` coroutine that submits work to an agent
# and returns an object with:
#   .summary (str)   -- the agent's textual response
#   .tokens_used (int) -- approximate token count (for cost tracking)
#
# Implement this interface for your agent system. A stub is provided for
# testing without a live agent backend.
# ---------------------------------------------------------------------------

try:
    from agent_interface import delegate_task  # type: ignore[import]
except ImportError:
    # Default stub -- replace with your actual agent integration
    async def delegate_task(goal: str, context: str = "", toolsets: List[str] = None):
        """
        Stub implementation of delegate_task.

        Replace this with a real implementation that calls your agent system,
        for example:
          - Claude Code subagents via Task()
          - OpenAI Assistants API
          - LangChain agents
          - Any async callable that accepts (goal, context, toolsets)

        Must return an object with:
          .summary: str       -- agent's response text
          .tokens_used: int   -- token count (can be approximate)
        """
        class StubResult:
            def __init__(self):
                self.summary = f"[STUB] Response to: {goal[:50]}..."
                self.tokens_used = 1000
        return StubResult()


@dataclass
class FThreadResult:
    """Result container for F-thread execution."""
    individual_responses: List[str]
    synthesis: str
    agreement_level: Literal["high", "medium", "low"]
    confidence_score: float
    cost_tokens: int
    disagreement_points: List[str] = field(default_factory=list)
    unique_insights: List[str] = field(default_factory=list)

    def format_report(self) -> str:
        """Format a human-readable synthesis report."""
        lines = [
            "=" * 60,
            "F-THREAD CONSENSUS REPORT",
            "=" * 60,
            f"",
            f"Agreement Level: {self.agreement_level.upper()} ({self.confidence_score:.0%})",
            f"Token Cost: {self.cost_tokens:,}",
            f"Agents Consulted: {len(self.individual_responses)}",
            f"",
            "-" * 60,
            "SYNTHESIS",
            "-" * 60,
            self.synthesis,
        ]

        if self.disagreement_points:
            lines.extend([
                f"",
                "-" * 60,
                "KEY DISAGREEMENTS (Worth Reviewing)",
                "-" * 60,
            ])
            for point in self.disagreement_points:
                lines.append(f"  - {point}")

        if self.unique_insights:
            lines.extend([
                f"",
                "-" * 60,
                "UNIQUE INSIGHTS (Individual Contributions)",
                "-" * 60,
            ])
            for insight in self.unique_insights:
                lines.append(f"  - {insight}")

        lines.extend([
            f"",
            "-" * 60,
            "RAW RESPONSES",
            "-" * 60,
        ])
        for i, resp in enumerate(self.individual_responses, 1):
            lines.append(f"\n--- Agent {i} ---")
            lines.append(resp[:500] + "..." if len(resp) > 500 else resp)

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)


def calculate_agreement(responses: List[str]) -> tuple:
    """
    Calculate agreement level using simple hash-based clustering.

    Production enhancement: Use embeddings + cosine similarity for
    semantic agreement detection.
    """
    # Simple approach: hash responses, count unique hashes
    hashes = [hashlib.md5(r.strip().lower().encode()).hexdigest()[:16] for r in responses]
    unique_hashes = len(set(hashes))
    total = len(responses)

    if unique_hashes == 1:
        return "high", 0.90
    elif unique_hashes == total:
        return "low", 0.40
    else:
        # Partial agreement
        ratio = 1 - (unique_hashes - 1) / (total - 1)
        if ratio >= 0.66:
            return "medium", 0.70
        else:
            return "low", 0.55


def extract_key_points(text: str) -> List[str]:
    """Extract bullet points or key sentences from text."""
    lines = text.split('\n')
    points = []
    for line in lines:
        line = line.strip()
        # Look for bullet points or numbered items
        if line.startswith(('-', '*', '-', '1.', '2.', '3.', '4.', '5.')):
            points.append(line.lstrip('- *-123456789.').strip())
        # Or sentences with key markers
        elif any(m in line.lower() for m in ['key', 'important', 'critical', 'main', 'primary']):
            points.append(line)
    return points[:5]  # Limit to top 5


def find_disagreements(responses: List[str]) -> List[str]:
    """Identify points of disagreement between responses."""
    all_points = []
    for resp in responses:
        all_points.append(set(extract_key_points(resp)))

    # Find points unique to each response (potential disagreements)
    disagreements = []
    for i, points in enumerate(all_points):
        others = set().union(*[p for j, p in enumerate(all_points) if j != i])
        unique = points - others
        for point in unique:
            if len(point) > 20:  # Filter out trivial differences
                disagreements.append(point)

    return disagreements[:3]  # Top 3 disagreements


def find_unique_insights(responses: List[str]) -> List[str]:
    """Identify unique valuable insights from individual agents."""
    all_points = []
    for resp in responses:
        all_points.append(set(extract_key_points(resp)))

    insights = []
    for i, points in enumerate(all_points):
        others = set().union(*[p for j, p in enumerate(all_points) if j != i])
        unique = points - others
        for point in unique:
            if any(m in point.lower() for m in ['insight', 'consider', 'note', 'alternatively', 'however']):
                insights.append(f"Agent {i+1}: {point}")

    return insights[:3]


async def weighted_synthesis(
    task_prompt: str,
    responses: List[str],
    disagreement_points: List[str],
    unique_insights: List[str]
) -> str:
    """
    Use a judge agent to synthesize all responses into a unified recommendation.

    This is the default strategy for complex outputs.
    """
    responses_formatted = "\n\n".join(
        f"=== Agent {i+1} ===\n{r[:2000]}" for i, r in enumerate(responses)
    )

    synthesis_prompt = f"""You are a synthesis judge reviewing multiple independent agent responses.

ORIGINAL TASK:
{task_prompt}

RESPONSES FROM {len(responses)} AGENTS:
{responses_formatted}

YOUR JOB:
1. Identify what ALL agents agreed on (consensus points)
2. Identify meaningful disagreements or alternative approaches
3. Highlight unique insights from individual agents
4. Provide a UNIFIED RECOMMENDATION that synthesizes the best thinking

FORMAT YOUR RESPONSE AS:

**Consensus:** (what most/all agents agreed on)

**Key Alternatives:** (legitimate different approaches to consider)

**Unified Recommendation:** (your synthesized guidance with confidence level: HIGH/MEDIUM/LOW)

SYNTHESIS:"""

    try:
        result = await delegate_task(
            goal=synthesis_prompt,
            context="You are a synthesis judge. Merge multiple independent analyses into coherent, actionable guidance. Be decisive but acknowledge legitimate uncertainty.",
            toolsets=[]  # Pure reasoning task
        )
        return result.summary
    except Exception as e:
        # Fallback: simple concatenation
        return f"[Synthesis Error: {e}]\n\nSimple merge:\n" + "\n---\n".join(responses[:2])


def union_merge(responses: List[str]) -> str:
    """
    Simple union strategy: combine all unique points.

    Fast but can be verbose. Good for brainstorming/creative tasks.
    """
    points = []
    for i, resp in enumerate(responses, 1):
        points.append(f"\n--- Agent {i} Contributions ---\n{resp}")

    return "\n".join(points)


def agreement_summary(responses: List[str], agreement_level: str) -> str:
    """
    Simple agreement scoring: present all views with confidence.

    Fastest synthesis strategy. Good for simple decisions.
    """
    lines = [
        f"Agreement Level: {agreement_level.upper()}",
        f"Agents Consulted: {len(responses)}",
        "",
        "Individual Responses:",
    ]

    for i, resp in enumerate(responses, 1):
        lines.append(f"\nAgent {i}: {resp[:500]}...")

    return "\n".join(lines)


async def f_thread(
    prompt: str,
    n_agents: int = 3,
    synthesis_strategy: Literal["weighted", "union", "agreement"] = "weighted",
    context: str = "",
    toolsets: Optional[List[str]] = None
) -> FThreadResult:
    """
    Execute F-thread: spawn N parallel agents, synthesize results.

    Args:
        prompt: The task/question to send to all agents
        n_agents: Number of parallel agents (2-5 recommended, default 3)
        synthesis_strategy: How to merge results
            - "weighted": Judge agent synthesis (default, best quality)
            - "union": Simple concatenation (fastest)
            - "agreement": Present all views with confidence score
        context: Additional context for all agents
        toolsets: Tools to provide to worker agents

    Returns:
        FThreadResult with synthesis, confidence score, and metadata
    """
    if n_agents < 2:
        raise ValueError("F-thread requires at least 2 agents")
    if n_agents > 5:
        print(f"Warning: n_agents={n_agents} is high. Consider cost/latency tradeoffs.")

    toolsets = toolsets or ["web", "terminal", "file"]

    # 1. Spawn N agents in parallel
    tasks = [
        delegate_task(
            goal=prompt,
            context=f"F-thread worker {i+1}/{n_agents}. Provide independent analysis. {context}",
            toolsets=toolsets
        )
        for i in range(n_agents)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any failures
    responses = []
    for r in results:
        if isinstance(r, Exception):
            responses.append(f"[Agent failed: {r}]")
        else:
            responses.append(r.summary)

    # 2. Calculate agreement metrics
    agreement_level, confidence_score = calculate_agreement(responses)

    # 3. Identify disagreements and unique insights
    disagreement_points = find_disagreements(responses)
    unique_insights = find_unique_insights(responses)

    # 4. Synthesize based on strategy
    if synthesis_strategy == "weighted":
        synthesis = await weighted_synthesis(prompt, responses, disagreement_points, unique_insights)
    elif synthesis_strategy == "union":
        synthesis = union_merge(responses)
    else:  # agreement
        synthesis = agreement_summary(responses, agreement_level)

    # 5. Estimate cost (rough heuristic)
    # Assume ~2K tokens per worker + 1K for synthesis
    cost_tokens = n_agents * 2000 + 1000

    return FThreadResult(
        individual_responses=responses,
        synthesis=synthesis,
        agreement_level=agreement_level,
        confidence_score=confidence_score,
        cost_tokens=cost_tokens,
        disagreement_points=disagreement_points,
        unique_insights=unique_insights
    )


# Convenience wrappers

async def f_thread_quick(prompt: str, n_agents: int = 3) -> str:
    """Quick F-thread: returns just the synthesis text."""
    result = await f_thread(prompt, n_agents, synthesis_strategy="agreement")
    return result.synthesis


async def f_thread_deep(prompt: str, n_agents: int = 3) -> FThreadResult:
    """Deep F-thread: full weighted synthesis with all metadata."""
    return await f_thread(prompt, n_agents, synthesis_strategy="weighted")


if __name__ == "__main__":
    # Simple test
    async def test():
        print("F-Thread implementation loaded.")
        print(f"Calculate agreement test: {calculate_agreement(['A', 'A', 'A'])}")
        print(f"Calculate agreement test: {calculate_agreement(['A', 'B', 'C'])}")

    asyncio.run(test())
