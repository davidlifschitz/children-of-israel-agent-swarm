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
                human_input=args.mission,  # fix: moses_node validates human_input (Commandment 5)
                session_id=session_id,
                mandate="Mission issued by Moses",
                jethro_tier=0,
                constitution_violations=[],
                oral_law_precedents=[],
            )

        # Stream the swarm — emit each node's output as it completes
        print(f"\n\U0001f54a\ufe0f  Swarm session started: {session_id}\n")
        result = {}
        for step in swarm.stream(
            initial_state,
            config={"configurable": {"thread_id": session_id}},
            stream_mode="updates",
        ):
            for node_name, node_output in step.items():
                print(f"[{node_name.upper()}] \u2713")
                if node_output.get("mandate"):
                    print(f"  \u2192 {node_output['mandate']}")
                if node_output.get("output"):
                    print(f"  \u2192 {node_output['output']}")
                if node_output.get("tribe_error"):
                    print(f"  \u26a0\ufe0f  Error: {node_output['tribe_error']}")
            result = step.get("summarizer", result)

        summary = result.get("final_summary", "No summary produced")
        print(f"\n{'=' * 60}\nMOSES \u2014 FINAL SESSION SUMMARY\n{'=' * 60}\n{summary}\n{'=' * 60}\n")

    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
