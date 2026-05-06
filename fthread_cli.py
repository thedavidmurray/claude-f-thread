#!/usr/bin/env python3
"""
F-Thread CLI -- /fthread command implementation

Usage:
    python fthread_cli.py "Your prompt here" --agents 3 --strategy weighted
    python fthread_cli.py "Analyze microservices vs monoliths" -n 3 -s weighted
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent to path for skill imports
sys.path.insert(0, str(Path(__file__).parent))

from f_thread import f_thread, FThreadResult


async def main():
    parser = argparse.ArgumentParser(
        description="F-Thread: Multi-agent consensus pattern",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python fthread_cli.py "Design a rate limiting strategy" -n 3
    python fthread_cli.py "Review this architecture decision" --strategy agreement
    python fthread_cli.py "Analyze a complex tradeoff" -n 5 --strategy weighted
        """
    )

    parser.add_argument("prompt", help="The task/question to ask agents")
    parser.add_argument("-n", "--agents", type=int, default=3,
                       help="Number of parallel agents (default: 3)")
    parser.add_argument("-s", "--strategy", choices=["weighted", "union", "agreement"],
                       default="weighted", help="Synthesis strategy (default: weighted)")
    parser.add_argument("--no-report", action="store_true",
                       help="Output synthesis only, skip full report")
    parser.add_argument("--context", default="",
                       help="Additional context for all agents")

    args = parser.parse_args()

    print(f"F-Thread: Spawning {args.agents} agents...")
    print(f"   Prompt: {args.prompt[:60]}{'...' if len(args.prompt) > 60 else ''}")
    print(f"   Strategy: {args.strategy}")
    print()

    try:
        result = await f_thread(
            prompt=args.prompt,
            n_agents=args.agents,
            synthesis_strategy=args.strategy,
            context=args.context
        )

        if args.no_report:
            print(result.synthesis)
        else:
            print(result.format_report())

        # Return exit code based on confidence
        if result.confidence_score < 0.5:
            return 1  # Low confidence
        return 0

    except Exception as e:
        print(f"F-Thread failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
