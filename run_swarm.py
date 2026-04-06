#!/usr/bin/env python3
"""run_swarm.py
CLI entry point for the Children of Israel Agent Swarm.

Usage:
    python run_swarm.py --mission "Your mission here"
    python run_swarm.py --mission "..." --session-id my-session-001
    python run_swarm.py --resume my-session-001
"""

import argparse
import sys
import uuid


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run or resume a Children of Israel Agent Swarm session.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mission",
        metavar="TEXT",
        help="The mission to run (required unless --resume is given).",
    )
    parser.add_argument(
        "--session-id",
        metavar="TEXT",
        default=None,
        help="Optional session ID. Auto-generated UUID if not provided.",
    )
    parser.add_argument(
        "--resume",
        metavar="SESSION_ID",
        default=None,
        help="Resume a previous session from its checkpoint.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    # Validate argument combinations
    if not args.resume and not args.mission:
        print(
            "error: --mission is required unless --resume is given.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        from children_of_israel.composer import build_graph
        from children_of_israel.agent_state import AgentState

        # Determine session ID
        if args.resume:
            session_id = args.resume
        else:
            session_id = args.session_id or str(uuid.uuid4())

        # Build the compiled swarm graph
        swarm = build_graph()

        # Build initial state
        if args.resume:
            # Minimal state — LangGraph rehydrates the rest from the checkpoint
            initial_state: AgentState = {"session_id": session_id}  # type: ignore[typeddict-item]
        else:
            initial_state = AgentState(
                mission=args.mission,
                session_id=session_id,
                mandate="Mission issued by Moses",
                jethro_tier=0,
                constitution_violations=[],
                oral_law_precedents=[],
            )

        # Invoke the swarm
        result = swarm.invoke(
            initial_state,
            config={"configurable": {"thread_id": session_id}},
        )

        summary = result.get("final_summary", "No summary produced")
        print(summary)

    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
