"""
Contract test for src.api.auth module — verifies the logger fix.

Ensures the auth module has a properly configured logger so that exception
handlers can safely call logger.exception(...) without raising NameError.
"""
import logging
import importlib

import pytest


class TestAuthModuleLogger:
    """Verify that src.api.auth exports a usable logger."""

    def test_module_imports_without_errors(self):
        """The auth module must be importable."""
        try:
            import src.api.auth  # noqa: F401
        except Exception as exc:
            pytest.fail(f"Importing src.api.auth raised {type(exc).__name__}: {exc}")

    def test_module_has_logger_attribute(self):
        """The auth module must expose a 'logger' attribute."""
        import src.api.auth

        assert hasattr(src.api.auth, 'logger'), (
            "src.api.auth is missing the 'logger' attribute. "
            "The auth module exception handlers may raise NameError if they "
            "reference an undefined logger."
        )

    def test_logger_is_logging_logger_instance(self):
        """logger must be a logging.Logger with the correct dotted name."""
        import src.api.auth

        logger = src.api.auth.logger
        assert isinstance(logger, logging.Logger), (
            f"Expected logging.Logger, got {type(logger).__name__}"
        )
        assert logger.name == 'src.api.auth', (
            f"Logger name should be 'src.api.auth', got '{logger.name}'"
        )

    def test_reimport_idempotent(self):
        """Reloading the module must not produce a different logger."""
        import src.api.auth

        logger_first = src.api.auth.logger
        importlib.reload(src.api.auth)
        logger_second = src.api.auth.logger

        # logging.getLogger returns the same instance for the same name.
        assert logger_first is logger_second, (
            "Logger identity changed across reload — "
            "expected the same logging.Logger instance."
        )

    def test_no_name_error_on_logger_call(self):
        """Exception handlers that reference logger must not raise NameError."""
        import src.api.auth

        # Simulate what an exception handler would do.
        try:
            src.api.auth.logger.exception("test exception message")
        except NameError:
            pytest.fail(
                "logger.exception() raised NameError — "
                "exception handlers referencing logger will fail."
            )
        except Exception:
            # Any other exception (e.g. no handlers configured) is fine —
            # we only care about NameError here.
            pass
