from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from sqlalchemy.exc import IntegrityError


class ConstraintViolationKind(StrEnum):
    UNIQUE = "unique"
    FOREIGN_KEY = "foreign_key"
    NOT_NULL = "not_null"
    CHECK = "check"
    UNKNOWN = "unknown"


def get_constraint_violation_kind(
    exc: IntegrityError,
    *,
    message_markers: Iterable[str] = (),
) -> ConstraintViolationKind:
    """Classify IntegrityError constraint violations across DB backends."""
    markers = [marker.lower() for marker in message_markers]

    def marker_matches(message: str) -> bool:
        if len(markers) == 0:
            return True
        return any(marker in message for marker in markers)

    orig = exc.orig
    msg = str(orig) if orig is not None else str(exc)
    msg_lower = msg.lower()

    # PostgreSQL SQLSTATE class 23 (integrity constraint violation)
    pg_code = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    if pg_code == "23505":
        return ConstraintViolationKind.UNIQUE if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if pg_code == "23503":
        return ConstraintViolationKind.FOREIGN_KEY if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if pg_code == "23502":
        return ConstraintViolationKind.NOT_NULL if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if pg_code == "23514":
        return ConstraintViolationKind.CHECK if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN

    # MySQL
    mysql_code = getattr(orig, "errno", None)
    args = getattr(orig, "args", None)
    if mysql_code is None and isinstance(args, (list, tuple)) and args:
        mysql_code = args[0]

    if mysql_code == 1062:
        return ConstraintViolationKind.UNIQUE if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if mysql_code == 1452:
        return ConstraintViolationKind.FOREIGN_KEY if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if mysql_code == 1048:
        return ConstraintViolationKind.NOT_NULL if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if mysql_code == 3819:
        return ConstraintViolationKind.CHECK if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN

    # Text fallbacks (SQLite + generic DBAPI messages)
    unique_markers = (
        "unique constraint failed",
        "duplicate key value violates unique constraint",
        "duplicate entry",
    )
    fk_markers = (
        "foreign key constraint failed",
        "violates foreign key constraint",
        "cannot add or update a child row",
    )
    not_null_markers = (
        "not null constraint failed",
        "null value in column",
        "cannot be null",
    )
    check_markers = (
        "check constraint failed",
        "violates check constraint",
    )

    if any(marker in msg_lower for marker in unique_markers):
        return ConstraintViolationKind.UNIQUE if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if any(marker in msg_lower for marker in fk_markers):
        return ConstraintViolationKind.FOREIGN_KEY if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if any(marker in msg_lower for marker in not_null_markers):
        return ConstraintViolationKind.NOT_NULL if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN
    if any(marker in msg_lower for marker in check_markers):
        return ConstraintViolationKind.CHECK if marker_matches(msg_lower) else ConstraintViolationKind.UNKNOWN

    return ConstraintViolationKind.UNKNOWN


def is_unique_violation(
    exc: IntegrityError,
    *,
    message_markers: Iterable[str] = (),
) -> bool:
    """Backward-compatible helper for unique-constraint checks."""
    return (
        get_constraint_violation_kind(exc, message_markers=message_markers)
        == ConstraintViolationKind.UNIQUE
    )
