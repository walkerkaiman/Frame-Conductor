import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Use the current window location to determine API URLs for network access
const getApiUrl = () => {
  const hostname = window.location.hostname;
  return `http://${hostname}:9000/api`;
};

const getWsUrl = () => {
  const hostname = window.location.hostname;
  return `ws://${hostname}:9000/ws/progress`;
};

function App() {
  // State for config fields
  const [totalFrames, setTotalFrames] = useState(1000);
  const [frameRate, setFrameRate] = useState(30);
  // State for sender
  const [status, setStatus] = useState('Ready');
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  // Host IP for network access
  const [hostIP, setHostIP] = useState('');
  // Progress
  const percent = totalFrames > 0 ? Math.floor((currentFrame / totalFrames) * 100) : 0;
  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);

  // Load config and set host IP on mount
  useEffect(() => {
    // Set the host IP for display
    setHostIP(window.location.hostname);
    
    fetch(`${getApiUrl()}/config`)
      .then(res => res.json())
      .then(cfg => {
        if (cfg.total_frames) setTotalFrames(cfg.total_frames);
        if (cfg.frame_rate) setFrameRate(cfg.frame_rate);
      })
      .catch(() => {});
  }, []);

  // Connect to WebSocket for real-time progress
  useEffect(() => {
    const ws = new WebSocket(getWsUrl());
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
      fetch(`${getApiUrl()}/start`, { method: 'POST' });
      setStatus('Sending frames...');
      setIsPaused(false);
    } else {
      // Toggle pause/resume
      fetch(`${getApiUrl()}/pause`, { method: 'POST' });
      setIsPaused((prev) => !prev);
      setStatus(isPaused ? 'Sending frames...' : 'Paused');
    }
  };
  const handleReset = () => {
    fetch(`${getApiUrl()}/reset`, { method: 'POST' });
    setCurrentFrame(0);
    setStatus('Ready');
    setIsPaused(false);
  };
  const handleSave = () => {
    const payload = { total_frames: totalFrames, frame_rate: frameRate };
    console.log('Sending config payload:', payload);
    fetch(`${getApiUrl()}/config`, {
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col items-center py-8">
      <h1 className="text-4xl font-bold text-indigo-700 mb-6 drop-shadow">Frame Conductor</h1>
      <div className="bg-indigo-100 rounded-lg px-4 py-2 mb-4 border border-indigo-200">
        <p className="text-sm text-indigo-700">
          <span className="font-semibold">Network Access:</span> http://<b>{hostIP}</b>:5173
        </p>
      </div>
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md mb-8">
        <h2 className="text-xl font-semibold text-indigo-600 mb-4">Configuration</h2>
        <label className="block mb-4">
          <span className="block text-sm font-medium text-gray-700 mb-1">Total Frames:</span>
          <input type="number" min={1} max={65535} value={totalFrames} onChange={e => setTotalFrames(Number(e.target.value))} className="w-full rounded border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400" />
        </label>
        <label className="block mb-4">
          <span className="block text-sm font-medium text-gray-700 mb-1">Frame Rate (fps):</span>
          <input type="number" min={1} max={120} value={frameRate} onChange={e => setFrameRate(Number(e.target.value))} className="w-full rounded border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400" />
        </label>
        <button onClick={handleSave} className="w-full bg-indigo-500 hover:bg-indigo-600 text-white font-semibold py-2 px-4 rounded transition mb-2">💾 Save Config</button>
      </div>
      <div className="bg-white rounded-xl shadow p-6 w-full max-w-md mb-8">
        <h2 className="text-lg font-semibold text-indigo-600 mb-2">Status</h2>
        <div className="mb-1">Status: <b className="text-indigo-700">{status}</b></div>
        <div className="mb-1">Current Frame: <b>{currentFrame}</b></div>
        <div>Total Frames: <b>{totalFrames}</b></div>
      </div>
      <div className="bg-white rounded-xl shadow p-6 w-full max-w-md mb-8 flex flex-col items-center">
        <h2 className="text-lg font-semibold text-indigo-600 mb-2">Controls</h2>
        <div className="flex gap-4 mb-2">
          <button
            onClick={handlePauseResume}
            disabled={status === 'Disconnected'}
            className="bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-6 rounded disabled:opacity-50 transition"
          >
            {(status === 'Ready' || status === 'Complete') ? '▶ Start' : (isPaused ? '▶ Resume' : '⏸ Pause')}
          </button>
          <button onClick={handleReset} className="bg-yellow-400 hover:bg-yellow-500 text-white font-semibold py-2 px-6 rounded transition">🔄 Reset</button>
        </div>
      </div>
      <div className="bg-white rounded-xl shadow p-6 w-full max-w-md flex flex-col items-center">
        <h2 className="text-lg font-semibold text-indigo-600 mb-2">Progress</h2>
        <progress value={currentFrame} max={totalFrames} className="w-full h-4 mb-2" />
        <div className="text-gray-700">{currentFrame} / {totalFrames} ({percent}%)</div>
      </div>
    </div>
  );
}

export default App;
