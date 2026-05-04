"""Unit tests for utility modules: db_errors, constants, settings."""

from __future__ import annotations

from unittest.mock import MagicMock

from sqlalchemy.exc import IntegrityError

from src.utils.db_errors import (
    ConstraintViolationKind,
    get_constraint_violation_kind,
    is_unique_violation,
)
from src.core.constants import HUGE_KB, LARGE_KB, MEDIUM_CHARS, SMALL_CHARS
from src.schemas.i18n import MAX_VALUE_CHARS, TranslationSize


# ---------------------------------------------------------------------------
# db_errors
# ---------------------------------------------------------------------------


def _make_integrity_error(message: str, *, pgcode=None, errno=None):
    """Build a mock IntegrityError with the desired orig attributes."""

    orig = MagicMock()
    orig.__str__ = lambda self: message
    orig.pgcode = pgcode
    orig.sqlstate = pgcode
    orig.errno = errno
    orig.args = (errno, message) if errno else (message,)

    exc = IntegrityError(statement="", params={}, orig=orig)
    return exc


class TestGetConstraintViolationKind:
    def test_sqlite_unique(self):
        exc = _make_integrity_error("UNIQUE constraint failed: users.username")
        assert get_constraint_violation_kind(exc) == ConstraintViolationKind.UNIQUE

    def test_sqlite_foreign_key(self):
        exc = _make_integrity_error("FOREIGN KEY constraint failed")
        assert get_constraint_violation_kind(exc) == ConstraintViolationKind.FOREIGN_KEY

    def test_sqlite_not_null(self):
        exc = _make_integrity_error("NOT NULL constraint failed: users.name")
        assert get_constraint_violation_kind(exc) == ConstraintViolationKind.NOT_NULL

    def test_sqlite_check(self):
        exc = _make_integrity_error("CHECK constraint failed: ck_age")
        assert get_constraint_violation_kind(exc) == ConstraintViolationKind.CHECK

    def test_postgres_unique_by_code(self):
        exc = _make_integrity_error("duplicate key value", pgcode="23505")
        assert get_constraint_violation_kind(exc) == ConstraintViolationKind.UNIQUE

    def test_postgres_fk_by_code(self):
        exc = _make_integrity_error("violates foreign key constraint", pgcode="23503")
        assert get_constraint_violation_kind(exc) == ConstraintViolationKind.FOREIGN_KEY

    def test_with_marker_match(self):
        exc = _make_integrity_error("UNIQUE constraint failed: users.username")
        kind = get_constraint_violation_kind(exc, message_markers=("users.username",))
        assert kind == ConstraintViolationKind.UNIQUE

    def test_with_marker_no_match(self):
        exc = _make_integrity_error("UNIQUE constraint failed: users.username")
        kind = get_constraint_violation_kind(exc, message_markers=("other_table",))
        assert kind == ConstraintViolationKind.UNKNOWN

    def test_unknown_message(self):
        exc = _make_integrity_error("some obscure error")
        assert get_constraint_violation_kind(exc) == ConstraintViolationKind.UNKNOWN


class TestIsUniqueViolation:
    def test_unique_returns_true(self):
        exc = _make_integrity_error("UNIQUE constraint failed: foo.bar")
        assert is_unique_violation(exc) is True

    def test_fk_returns_false(self):
        exc = _make_integrity_error("FOREIGN KEY constraint failed")
        assert is_unique_violation(exc) is False


# ---------------------------------------------------------------------------
# Constants consistency
# ---------------------------------------------------------------------------


class TestConstants:
    def test_small_is_positive(self):
        assert SMALL_CHARS > 0

    def test_ordering(self):
        assert SMALL_CHARS < MEDIUM_CHARS < LARGE_KB * 1024 < HUGE_KB * 1024

    def test_max_value_chars_matches_constants(self):
        assert MAX_VALUE_CHARS[TranslationSize.SMALL] == SMALL_CHARS
        assert MAX_VALUE_CHARS[TranslationSize.MEDIUM] == MEDIUM_CHARS
        assert MAX_VALUE_CHARS[TranslationSize.LARGE] == LARGE_KB * 1024
        assert MAX_VALUE_CHARS[TranslationSize.HUGE] == HUGE_KB * 1024
