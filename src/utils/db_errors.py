from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy.exc import IntegrityError


def is_unique_violation(
    exc: IntegrityError,
    *,
    message_markers: Iterable[str] = (),
) -> bool:
    """Return True when IntegrityError represents a unique-constraint violation."""
    orig = exc.orig
    msg = str(orig) if orig is not None else str(exc)
    msg_lower = msg.lower()

    # PostgreSQL
    if getattr(orig, "pgcode", None) == "23505":
        return True
    if getattr(orig, "sqlstate", None) == "23505":
        return True

    # MySQL
    if getattr(orig, "errno", None) == 1062:
        return True
    args = getattr(orig, "args", None)
    if isinstance(args, (list, tuple)) and args and args[0] == 1062:
        return True

    # SQLite and text-based fallbacks
    generic_markers = (
        "unique constraint failed",
        "duplicate key value violates unique constraint",
        "duplicate entry",
    )
    if any(marker in msg_lower for marker in generic_markers):
        if not message_markers:
            return True
        return any(marker.lower() in msg_lower for marker in message_markers)

    return False
