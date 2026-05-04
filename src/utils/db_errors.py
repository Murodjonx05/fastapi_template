from collections.abc import Iterable
from enum import StrEnum

from sqlalchemy.exc import IntegrityError


class ConstraintViolationKind(StrEnum):
    UNIQUE = "unique"
    FOREIGN_KEY = "foreign_key"
    NOT_NULL = "not_null"
    CHECK = "check"
    UNKNOWN = "unknown"


_POSTGRES_ERROR_CODES = {
    "23505": ConstraintViolationKind.UNIQUE,
    "23503": ConstraintViolationKind.FOREIGN_KEY,
    "23502": ConstraintViolationKind.NOT_NULL,
    "23514": ConstraintViolationKind.CHECK,
}

_MYSQL_ERROR_CODES = {
    1062: ConstraintViolationKind.UNIQUE,
    1452: ConstraintViolationKind.FOREIGN_KEY,
    1048: ConstraintViolationKind.NOT_NULL,
    3819: ConstraintViolationKind.CHECK,
}

_FALLBACK_MARKERS = (
    (
        (
            "unique constraint failed",
            "duplicate key value violates unique constraint",
            "duplicate entry",
        ),
        ConstraintViolationKind.UNIQUE,
    ),
    (
        (
            "foreign key constraint failed",
            "violates foreign key constraint",
            "cannot add or update a child row",
        ),
        ConstraintViolationKind.FOREIGN_KEY,
    ),
    (
        (
            "not null constraint failed",
            "null value in column",
            "cannot be null",
        ),
        ConstraintViolationKind.NOT_NULL,
    ),
    (
        (
            "check constraint failed",
            "violates check constraint",
        ),
        ConstraintViolationKind.CHECK,
    ),
)


def _marker_matches(markers: list[str], message: str) -> bool:
    return len(markers) == 0 or any(m in message for m in markers)


def _match_or_unknown(
    markers: list[str], kind: ConstraintViolationKind, message: str
) -> ConstraintViolationKind:
    return kind if _marker_matches(markers, message) else ConstraintViolationKind.UNKNOWN


def _classify_by_mapping(
    markers: list[str],
    code: str | int | None,
    mapping: dict[str | int, ConstraintViolationKind],
    message: str,
) -> ConstraintViolationKind | None:
    kind = mapping.get(code)
    return None if kind is None else _match_or_unknown(markers, kind, message)


def get_constraint_violation_kind(
    exc: IntegrityError,
    *,
    message_markers: Iterable[str] = (),
) -> ConstraintViolationKind:
    """Classify IntegrityError constraint violations across DB backends."""
    markers = [m.lower() for m in message_markers]

    orig = exc.orig
    msg = str(orig) if orig is not None else str(exc)
    msg_lower = msg.lower()

    # PostgreSQL SQLSTATE class 23 (integrity constraint violation)
    pg_code = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    pg_kind = _classify_by_mapping(markers, pg_code, _POSTGRES_ERROR_CODES, msg_lower)
    if pg_kind is not None:
        return pg_kind

    # MySQL
    mysql_code = getattr(orig, "errno", None)
    args = getattr(orig, "args", None)
    if mysql_code is None and isinstance(args, (list, tuple)) and args:
        mysql_code = args[0]

    mysql_kind = _classify_by_mapping(markers, mysql_code, _MYSQL_ERROR_CODES, msg_lower)
    if mysql_kind is not None:
        return mysql_kind

    for marker_group, kind in _FALLBACK_MARKERS:
        if any(m in msg_lower for m in marker_group):
            return _match_or_unknown(markers, kind, msg_lower)

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


def _marker_matches(markers: list[str], message: str) -> bool:
    if len(markers) == 0:
        return True
    return any(marker in message for marker in markers)


def _match_or_unknown(
    markers: list[str],
    kind: ConstraintViolationKind,
    message: str,
) -> ConstraintViolationKind:
    if _marker_matches(markers, message):
        return kind
    return ConstraintViolationKind.UNKNOWN


def _classify_by_mapping(
    markers: list[str],
    code: str | int | None,
    mapping: dict[str | int, ConstraintViolationKind],
    message: str,
) -> ConstraintViolationKind | None:
    kind = mapping.get(code)
    if kind is None:
        return None
    return _match_or_unknown(markers, kind, message)


def get_constraint_violation_kind(
    exc: IntegrityError,
    *,
    message_markers: Iterable[str] = (),
) -> ConstraintViolationKind:
    """Classify IntegrityError constraint violations across DB backends."""
    markers = [marker.lower() for marker in message_markers]

    orig = exc.orig
    msg = str(orig) if orig is not None else str(exc)
    msg_lower = msg.lower()

    # PostgreSQL SQLSTATE class 23 (integrity constraint violation)
    pg_code = getattr(orig, "pgcode", None) or getattr(orig, "sqlstate", None)
    pg_kind = _classify_by_mapping(markers, pg_code, _POSTGRES_ERROR_CODES, msg_lower)
    if pg_kind is not None:
        return pg_kind

    # MySQL
    mysql_code = getattr(orig, "errno", None)
    args = getattr(orig, "args", None)
    if mysql_code is None and isinstance(args, (list, tuple)) and args:
        mysql_code = args[0]

    mysql_kind = _classify_by_mapping(markers, mysql_code, _MYSQL_ERROR_CODES, msg_lower)
    if mysql_kind is not None:
        return mysql_kind

    for marker_group, kind in _FALLBACK_MARKERS:
        if any(marker in msg_lower for marker in marker_group):
            return _match_or_unknown(markers, kind, msg_lower)

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
