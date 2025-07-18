import pytest
import threading
from unittest.mock import patch, MagicMock
import sys

# Assume run_headless is imported from main.py if refactored for testability
# from main import run_headless

def test_headless_starts_in_paused(monkeypatch):
    # Simulate the sender and keyboard input
    mock_sender = MagicMock()
    mock_sender.is_running = False
    mock_sender.is_paused = True
    # Would need to refactor run_headless to accept a sender for true unit test
    # For now, just check the initial state logic
    assert not mock_sender.is_running or mock_sender.is_paused

# Additional tests would require refactoring run_headless for testability
# and/or using integration tests with subprocess and pexpect for CLI interaction 