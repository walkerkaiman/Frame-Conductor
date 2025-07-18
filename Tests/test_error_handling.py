import pytest
from unittest.mock import patch, MagicMock
from config_manager import ConfigManager
from sacn_sender import SACNSender

def test_invalid_frame_value():
    cm = ConfigManager('test_config.json')
    config = cm.load_config()
    config['total_frames'] = -1
    assert cm.save_config(config)
    loaded = cm.load_config()
    assert loaded['total_frames'] == -1  # App should handle this gracefully elsewhere

def test_invalid_fps_value():
    cm = ConfigManager('test_config.json')
    config = cm.load_config()
    config['frame_rate'] = 0
    assert cm.save_config(config)
    loaded = cm.load_config()
    assert loaded['frame_rate'] == 0  # App should handle this gracefully elsewhere

def test_missing_sacn_library(monkeypatch):
    monkeypatch.setitem(__import__('sys').modules, 'sacn', None)
    with patch('builtins.print') as mock_print:
        sender = SACNSender()
        assert not sender.is_sacn_available() or sender.is_sacn_available() is False

# Network error handling would require integration or mock testing of the sender's _sender_loop 