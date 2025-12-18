"""Tests for configuration."""

import os
from unittest.mock import patch

from src.config import _get_log_level, _get_webhook_bearer


class TestLogLevel:
    """Tests for log level configuration."""

    def test_default_log_level(self):
        """Test default log level is INFO."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove LOG_LEVEL if it exists
            os.environ.pop("LOG_LEVEL", None)
            level = _get_log_level()
            assert level == "INFO"

    def test_log_level_debug(self):
        """Test DEBUG log level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            level = _get_log_level()
            assert level == "DEBUG"

    def test_log_level_warning(self):
        """Test WARNING log level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}):
            level = _get_log_level()
            assert level == "WARNING"

    def test_log_level_error(self):
        """Test ERROR log level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            level = _get_log_level()
            assert level == "ERROR"

    def test_log_level_critical(self):
        """Test CRITICAL log level."""
        with patch.dict(os.environ, {"LOG_LEVEL": "CRITICAL"}):
            level = _get_log_level()
            assert level == "CRITICAL"

    def test_log_level_case_insensitive(self):
        """Test log level is case insensitive."""
        with patch.dict(os.environ, {"LOG_LEVEL": "debug"}):
            level = _get_log_level()
            assert level == "DEBUG"

        with patch.dict(os.environ, {"LOG_LEVEL": "Info"}):
            level = _get_log_level()
            assert level == "INFO"

    def test_invalid_log_level_defaults_to_info(self):
        """Test invalid log level falls back to INFO."""
        with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}):
            level = _get_log_level()
            assert level == "INFO"

        with patch.dict(os.environ, {"LOG_LEVEL": "TRACE"}):
            level = _get_log_level()
            assert level == "INFO"


class TestWebhookBearer:
    """Tests for webhook bearer token configuration."""

    def test_no_bearer_token(self):
        """Test returns None when WEBHOOK_BEARER not set."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("WEBHOOK_BEARER", None)
            token = _get_webhook_bearer()
            assert token is None

    def test_empty_bearer_token(self):
        """Test returns None when WEBHOOK_BEARER is empty."""
        with patch.dict(os.environ, {"WEBHOOK_BEARER": ""}):
            token = _get_webhook_bearer()
            assert token is None

    def test_bearer_token_set(self):
        """Test returns token when WEBHOOK_BEARER is set."""
        with patch.dict(os.environ, {"WEBHOOK_BEARER": "my-secret-token"}):
            token = _get_webhook_bearer()
            assert token == "my-secret-token"
