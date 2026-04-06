"""observability.py
Structured logging for the Children of Israel Agent Swarm.
Uses structlog with JSON rendering for production, console for development.
"""

import structlog

# ---------------------------------------------------------------------------
# Log event constants — use these for consistent event names across the swarm
# ---------------------------------------------------------------------------

TRIBE_ENTRY = "tribe.entry"
TRIBE_EXIT = "tribe.exit"
CONSTITUTION_VIOLATION = "constitution.violation"
ORAL_LAW_PRECEDENT = "oral_law.precedent"
HERMES_CALL = "hermes.call"
ESCALATION = "escalation"

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_configured = False


def configure_logging(json_logs: bool = True) -> None:
    """Configure structlog once.

    Calling this function more than once is a no-op; configuration is
    applied only on the first call.

    Parameters
    ----------
    json_logs:
        When ``True`` (production default), emit JSON lines.
        When ``False`` (development mode), use structlog's coloured
        ``ConsoleRenderer``.
    """
    global _configured
    if _configured:
        return

    if json_logs:
        final_processor = structlog.processors.JSONRenderer()
    else:
        final_processor = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            final_processor,
        ],
        wrapper_class=structlog.BoundLogger,
    )
    _configured = True


def get_logger(name: str) -> structlog.BoundLogger:
    """Return a bound structlog logger for *name*.

    Ensures ``configure_logging()`` has been called at least once before
    the logger is created.

    Parameters
    ----------
    name:
        Logical name for the logger (e.g. ``"moses"``, ``"judah"``).
    """
    configure_logging()
    return structlog.get_logger(name)
