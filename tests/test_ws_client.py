"""
Tests for ws_client.py
Covers: on_open callback wiring in WebSocketManager._on_open.
"""
import pytest
from unittest.mock import MagicMock

from ws_client import WebSocketManager


def _make_manager(**kwargs):
    """Return a WebSocketManager with a mocked logger plus any extra kwargs."""
    logger = MagicMock()
    manager = WebSocketManager(logger=logger, **kwargs)
    return manager, logger


class TestWebSocketManagerOnOpen:
    def test_on_open_callback_is_invoked_when_ws_opens(self):
        on_open_cb = MagicMock()
        manager, _ = _make_manager(on_open=on_open_cb)

        manager._on_open(MagicMock())

        on_open_cb.assert_called_once()

    def test_on_open_callback_none_does_not_raise(self):
        manager, _ = _make_manager(on_open=None)

        # Must not raise even though no callback is registered
        manager._on_open(MagicMock())

    def test_on_open_sets_connected_to_true(self):
        manager, _ = _make_manager()

        manager._on_open(MagicMock())

        assert manager.connected is True

    def test_on_open_calls_status_change_callback_with_true(self):
        status_cb = MagicMock()
        manager, _ = _make_manager(on_status_change=status_cb)

        manager._on_open(MagicMock())

        status_cb.assert_called_once_with(True)

    def test_on_open_logs_connected_message(self):
        manager, logger = _make_manager()

        manager._on_open(MagicMock())

        logger.log.assert_called_with("WebSocket connected.")

    def test_on_open_status_change_is_called_before_on_open_callback(self):
        """_set_connected (status change) must fire before the on_open hook."""
        call_order = []

        def status_cb(val):
            call_order.append(("status", val))

        def open_cb():
            call_order.append(("open",))

        manager, _ = _make_manager(on_open=open_cb, on_status_change=status_cb)
        manager._on_open(MagicMock())

        assert call_order[0] == ("status", True)
        assert call_order[1] == ("open",)

    def test_on_open_without_status_change_callback_still_calls_on_open(self):
        on_open_cb = MagicMock()
        manager, _ = _make_manager(on_open=on_open_cb, on_status_change=None)

        manager._on_open(MagicMock())

        on_open_cb.assert_called_once()
        assert manager.connected is True

    def test_on_open_with_both_callbacks_none_does_not_raise(self):
        manager, _ = _make_manager(on_open=None, on_status_change=None)

        manager._on_open(MagicMock())

        assert manager.connected is True
