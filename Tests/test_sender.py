import pytest
from unittest.mock import MagicMock, patch
from utils.sacn_sender import SACNSender

def test_initializes_with_defaults():
    sender = SACNSender()
    assert sender.universe == 1
    assert sender.frame_length == 512
    assert sender.frame_rate == 30
    assert sender.current_frame == 0

def test_encodes_frame_number_correctly():
    sender = SACNSender()
    for frame in [0, 1, 255, 256, 65535]:
        msb = (frame >> 8) & 0xFF
        lsb = frame & 0xFF
        dmx_data = [0] * 512
        dmx_data[0] = msb
        dmx_data[1] = lsb
        assert ((dmx_data[0] << 8) | dmx_data[1]) == frame

def test_start_sending_sets_state(monkeypatch):
    sender = SACNSender()
    monkeypatch.setattr(sender, '_initialize_sender_once', lambda: True)
    monkeypatch.setattr(sender, '_sender_loop', lambda: None)
    assert sender.start_sending(100, 30)
    assert sender.is_running
    assert not sender.is_paused
    assert sender.target_frame == 100
    assert sender.frame_rate == 30

def test_pause_and_resume():
    sender = SACNSender()
    sender.is_running = True
    sender.is_paused = False
    sender.pause()
    assert sender.is_paused
    sender.resume()
    assert not sender.is_paused

def test_stop_sending_cleans_up(monkeypatch):
    sender = SACNSender()
    sender.sender = MagicMock()
    sender.sender_thread = MagicMock()
    sender.sender_thread.is_alive.return_value = False
    sender.is_running = True
    sender.stop_sending()
    assert not sender.is_running
    assert not sender.is_paused
    assert sender.current_frame == 0

def test_handles_invalid_universe(monkeypatch):
    sender = SACNSender()
    monkeypatch.setattr(sender, '_initialize_sender_once', lambda: False)
    assert not sender.start_sending(100, 30)

def test_frame_callback_called():
    sender = SACNSender()
    called = []
    def cb(frame):
        called.append(frame)
    sender.set_frame_callback(cb)
    sender.is_running = True
    sender.is_paused = False
    sender.target_frame = 2
    sender.current_frame = 0
    def fake_loop():
        for i in range(3):
            if sender.frame_callback:
                sender.frame_callback(i)
    sender._sender_loop = fake_loop
    sender._sender_loop()
    assert called == [0, 1, 2] 