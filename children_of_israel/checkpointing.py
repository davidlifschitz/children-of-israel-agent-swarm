"""checkpointing.py
Factory for LangGraph checkpointing backends.
Supports memory (default), postgres, and redis backends.
"""

import logging
import os

logger = logging.getLogger(__name__)

DEFAULT_BACKEND = "memory"


def get_checkpointer(backend: str = "memory"):
    """Return a LangGraph checkpointer for the given backend.

    Parameters
    ----------
    backend:
        One of "memory", "postgres", or "redis".
        Unknown values fall back to "memory" with a warning.

    Returns
    -------
    A checkpointer instance compatible with ``graph.compile(checkpointer=...)``.
    """
    if backend == "memory":
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()

    if backend == "postgres":
        try:
            from langgraph.checkpoint.postgres import AsyncPostgresSaver
        except ImportError:
            logger.warning(
                "langgraph-checkpoint-postgres is not installed; "
                "falling back to MemorySaver. "
                "Install it with: pip install langgraph-checkpoint-postgres"
            )
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()

        url = os.environ.get("POSTGRES_URL")
        if not url:
            logger.warning(
                "POSTGRES_URL env var is not set; falling back to MemorySaver."
            )
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()

        return AsyncPostgresSaver.from_conn_string(url)

    if backend == "redis":
        try:
            from langgraph.checkpoint.redis import RedisSaver
        except ImportError:
            logger.warning(
                "langgraph-checkpoint-redis is not installed; "
                "falling back to MemorySaver. "
                "Install it with: pip install langgraph-checkpoint-redis"
            )
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()

        url = os.environ.get("REDIS_URL")
        if not url:
            logger.warning(
                "REDIS_URL env var is not set; falling back to MemorySaver."
            )
            from langgraph.checkpoint.memory import MemorySaver
            return MemorySaver()

        return RedisSaver.from_conn_string(url)

    # Unknown backend — warn and fall back
    logger.warning(
        "Unknown checkpointing backend %r; falling back to MemorySaver.", backend
    )
    from langgraph.checkpoint.memory import MemorySaver
    return MemorySaver()
