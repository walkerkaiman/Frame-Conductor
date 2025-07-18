import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_URL = 'http://localhost:9000/api';
const WS_URL = 'ws://localhost:9000/ws/progress';

function App() {
  // State for config fields
  const [totalFrames, setTotalFrames] = useState(1000);
  const [frameRate, setFrameRate] = useState(30);
  // State for sender
  const [status, setStatus] = useState('Ready');
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  // Progress
  const percent = totalFrames > 0 ? Math.floor((currentFrame / totalFrames) * 100) : 0;
  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);

  // Load config on mount
  useEffect(() => {
    fetch(`${API_URL}/config`)
      .then(res => res.json())
      .then(cfg => {
        if (cfg.total_frames) setTotalFrames(cfg.total_frames);
        if (cfg.frame_rate) setFrameRate(cfg.frame_rate);
      })
      .catch(() => {});
  }, []);

  // Connect to WebSocket for real-time progress
  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (typeof data.frame === 'number') setCurrentFrame(data.frame);
        // if (typeof data.total_frames === 'number') setTotalFrames(data.total_frames); // Prevent overwriting user input
        if (typeof data.status === 'string') setStatus(data.status);
      } catch {}
    };
    ws.onclose = () => { setStatus('Disconnected'); };
    return () => { ws.close(); };
  }, []);

  // Handlers
  const handlePauseResume = () => {
    if (status === 'Ready' || status === 'Complete') {
      // Start sending
      fetch(`${API_URL}/start`, { method: 'POST' });
      setStatus('Sending frames...');
      setIsPaused(false);
    } else {
      // Toggle pause/resume
      fetch(`${API_URL}/pause`, { method: 'POST' });
      setIsPaused((prev) => !prev);
      setStatus(isPaused ? 'Sending frames...' : 'Paused');
    }
  };
  const handleReset = () => {
    fetch(`${API_URL}/reset`, { method: 'POST' });
    setCurrentFrame(0);
    setStatus('Ready');
    setIsPaused(false);
  };
  const handleSave = () => {
    const payload = { total_frames: totalFrames, frame_rate: frameRate };
    console.log('Sending config payload:', payload);
    fetch(`${API_URL}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then(data => {
        console.log('Config save response:', data);
        setStatus('Ready');
        setIsPaused(false);
        setCurrentFrame(0);
      })
      .catch(err => {
        console.error('Config save error:', err);
        setStatus('Config save error');
      });
  };

  return (
    <div className="App">
      <h1>Frame Conductor</h1>
      <div className="config-section">
        <h2>Configuration</h2>
        <label>
          Total Frames:
          <input type="number" min={1} max={65535} value={totalFrames} onChange={e => setTotalFrames(Number(e.target.value))} />
        </label>
        <label>
          Frame Rate (fps):
          <input type="number" min={1} max={120} value={frameRate} onChange={e => setFrameRate(Number(e.target.value))} />
        </label>
        <button onClick={handleSave}>💾 Save Config</button>
      </div>
      <div className="status-section">
        <h2>Status</h2>
        <div>Status: <b>{status}</b></div>
        <div>Current Frame: <b>{currentFrame}</b></div>
        <div>Total Frames: <b>{totalFrames}</b></div>
      </div>
      <div className="controls-section">
        <h2>Controls</h2>
        <button
          onClick={handlePauseResume}
          disabled={status === 'Disconnected'}
        >
          {(status === 'Ready' || status === 'Complete') ? '▶ Start' : (isPaused ? '▶ Resume' : '⏸ Pause')}
        </button>
        <button onClick={handleReset}>🔄 Reset</button>
      </div>
      <div className="progress-section">
        <h2>Progress</h2>
        <progress value={currentFrame} max={totalFrames} style={{ width: '100%' }} />
        <div>{currentFrame} / {totalFrames} ({percent}%)</div>
      </div>
    </div>
  );
}

export default App;
