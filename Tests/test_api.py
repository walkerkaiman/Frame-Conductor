from fastapi.testclient import TestClient
from api_server import app, sender, config

client = TestClient(app)

def test_save_config():
    payload = {"total_frames": 1234, "frame_rate": 25}
    resp = client.post("/api/config", json=payload)
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    # Config should be updated in memory
    assert config["total_frames"] == 1234
    assert config["frame_rate"] == 25

def test_start_sender():
    # Set config first
    client.post("/api/config", json={"total_frames": 10, "frame_rate": 15})
    resp = client.post("/api/start")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert sender.is_running
    assert not sender.is_paused
    assert sender.target_frame == 10
    assert sender.frame_rate == 15

def test_pause_and_resume_sender():
    # Start first
    client.post("/api/config", json={"total_frames": 5, "frame_rate": 10})
    client.post("/api/start")
    # Pause
    resp = client.post("/api/pause")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert sender.is_paused
    # Resume
    resp = client.post("/api/pause")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert not sender.is_paused

def test_reset_sender():
    client.post("/api/config", json={"total_frames": 5, "frame_rate": 10})
    client.post("/api/start")
    resp = client.post("/api/reset")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert not sender.is_running
    assert not sender.is_paused
    assert sender.current_frame == 0 