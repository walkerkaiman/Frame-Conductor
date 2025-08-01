import React, { useState, useEffect, useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import './App.css';

/**
 * Frame Conductor React Application
 * 
 * A modern web interface for controlling sACN frame transmission.
 * This component provides real-time control and monitoring of sACN
 * frame transmission with network accessibility and multi-browser synchronization.
 * 
 * Features:
 * - Real-time progress monitoring via WebSocket
 * - Configuration management with persistence
 * - Multi-browser synchronization
 * - Network accessibility from any device
 * - Responsive design with modern UI
 * 
 * @component
 */

// API URL helper functions
/**
 * Get the API base URL for the backend
 * @returns {string} The API base URL (e.g., "http://<host>:9000/api")
 */
const getApiUrl = (): string => {
  return `http://${window.location.hostname}:9000/api`;
};

/**
 * Get the WebSocket URL for the backend
 * @returns {string} The WebSocket URL (e.g., "ws://<host>:9000/ws/progress")
 */
const getWsUrl = (): string => {
  return `ws://${window.location.hostname}:9000/ws/progress`;
};

// Type definitions for better type safety
interface ConfigData {
  total_frames: number;
  frame_rate: number;
  universe?: number;
  frame_length?: number;
}

interface ProgressData {
  frame: number;
  total_frames: number;
  status: string;
  percent: number;
}

interface ConfigUpdateData {
  type: 'config_update';
  config: ConfigData;
}

function App(): React.JSX.Element {
  // State for configuration fields
  const [totalFrames, setTotalFrames] = useState<number>(1000);
  const [frameRate, setFrameRate] = useState<number>(30);
  
  // State for sender control
  const [status, setStatus] = useState<string>('Ready');
  const [currentFrame, setCurrentFrame] = useState<number>(0);
  const [senderState, setSenderState] = useState<string>('stopped');
  
  // Host IP for network access display
  const [hostIP, setHostIP] = useState<string>('');
  
  // Calculated progress percentage
  const percent: number = totalFrames > 0 ? Math.floor((currentFrame / totalFrames) * 100) : 0;
  
  // WebSocket connection reference
  const wsRef = useRef<WebSocket | null>(null);

  /**
   * Load initial configuration and set host IP on component mount
   * Fetches the current configuration from the backend and updates the UI
   */
  useEffect(() => {
    // Fetch the local IP from the backend for display in the network access section
    fetch(`http://${window.location.hostname}:9000/api/local_ip`)
      .then(res => res.json())
      .then(data => setHostIP(data.ip))
      .catch(() => setHostIP(window.location.hostname));

    // Fetch initial configuration from backend
    fetch(`${getApiUrl()}/config`)
      .then(res => res.json())
      .then((cfg: ConfigData) => {
        if (cfg.total_frames) setTotalFrames(cfg.total_frames);
        if (cfg.frame_rate) setFrameRate(cfg.frame_rate);
      })
      .catch((error) => {
        console.error('Failed to load configuration:', error);
      });

    // Fetch initial sender state
    fetch(`${getApiUrl()}/state`)
      .then(res => res.json())
      .then((stateData) => {
        setSenderState(stateData.state);
        setCurrentFrame(stateData.current_frame);
        if (stateData.state === 'paused') {
          setStatus('Paused');
        } else if (stateData.state === 'running') {
          setStatus('Sending frames...');
        } else {
          setStatus('Ready');
        }
      })
      .catch((error) => {
        console.error('Failed to load sender state:', error);
      });
  }, []);

  /**
   * Establish WebSocket connection for real-time progress updates
   * Handles progress updates, status changes, and configuration synchronization
   */
  useEffect(() => {
    const ws = new WebSocket(getWsUrl());
    wsRef.current = ws;
    
    ws.onmessage = (event) => {
      try {
        const data: ProgressData | ConfigUpdateData = JSON.parse(event.data);
        
        // Handle progress updates
        if ('frame' in data && typeof data.frame === 'number') {
          setCurrentFrame(data.frame);
        }
        
        // Handle status updates
        if ('status' in data && typeof data.status === 'string') {
          setStatus(data.status);
          // Update sender state based on status
          if (data.status === 'Paused') {
            setSenderState('paused');
          } else if (data.status === 'Sending frames...') {
            setSenderState('running');
          } else if (data.status === 'Ready' || data.status === 'Complete') {
            setSenderState('stopped');
          }
        }
        
        // Handle configuration updates from other browsers
        if ('type' in data && data.type === 'config_update' && 'config' in data && data.config && typeof data.config === 'object') {
          if (data.config.total_frames) setTotalFrames(data.config.total_frames);
          if (data.config.frame_rate) setFrameRate(data.config.frame_rate);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onclose = () => { 
      setStatus('Disconnected'); 
    };
    
    // Cleanup WebSocket connection on component unmount
    return () => { 
      ws.close(); 
    };
  }, []);

  /**
   * Handle toggle button clicks
   * Performs the appropriate action based on current sender state
   */
  const handleToggle = (): void => {
    if (senderState === 'stopped') {
      // Start sending frames
      fetch(`${getApiUrl()}/start`, { method: 'POST' });
      setStatus('Sending frames...');
      setSenderState('running');
    } else if (senderState === 'running') {
      // Pause transmission
      fetch(`${getApiUrl()}/pause`, { method: 'POST' });
      setStatus('Paused');
      setSenderState('paused');
    } else if (senderState === 'paused') {
      // Resume transmission
      fetch(`${getApiUrl()}/resume`, { method: 'POST' });
      setStatus('Sending frames...');
      setSenderState('running');
    }
  };

  /**
   * Handle reset button clicks
   * Resets the frame transmission to the beginning
   */
  const handleReset = (): void => {
    fetch(`${getApiUrl()}/reset`, { method: 'POST' });
    setCurrentFrame(0);
    setStatus('Ready');
  };

  /**
   * Handle configuration save button clicks
   * Saves the current configuration to the backend and updates all connected browsers
   */
  const handleSave = (): void => {
    const payload: ConfigData = { 
      total_frames: totalFrames, 
      frame_rate: frameRate 
    };
    
    console.log('Sending configuration payload:', payload);
    
    fetch(`${getApiUrl()}/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
      .then(res => res.json())
      .then((data: { success: boolean; error?: string }) => {
        console.log('Configuration save response:', data);
        if (data.success) {
          setStatus('Ready');
          setCurrentFrame(0);
          
          // Fetch the updated configuration to ensure UI reflects the saved values
          return fetch(`${getApiUrl()}/config`);
        } else {
          throw new Error(data.error || 'Unknown error');
        }
      })
      .then(res => res.json())
      .then((cfg: ConfigData) => {
        console.log('Updated configuration from server:', cfg);
        if (cfg.total_frames) setTotalFrames(cfg.total_frames);
        if (cfg.frame_rate) setFrameRate(cfg.frame_rate);
      })
      .catch((err: Error) => {
        console.error('Configuration save error:', err);
        setStatus('Config save error');
      });
  };

  // Generate the URL for the QR code
  const networkUrl = `http://${hostIP}:5173`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex flex-col items-center py-8">
      {/* Application Header */}
      <h1 className="text-4xl font-bold text-indigo-700 mb-6 drop-shadow">Conductor</h1>
      
      {/* QR Code and Network Access Information */}
      <div className="bg-indigo-100 rounded-lg px-4 py-2 mb-4 border border-indigo-200 flex flex-col items-center">
        {hostIP && (
          <div className="mb-2">
            <QRCodeSVG 
              value={networkUrl}
              size={128}
              level="M"
              includeMargin={true}
            />
          </div>
        )}
        <p className="text-sm text-indigo-700">
          http://<b>{hostIP}</b>:5173
        </p>
      </div>
      
      {/* Configuration Panel */}
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md mb-8">
        <h2 className="text-xl font-semibold text-indigo-600 mb-4">Configuration</h2>
        
        {/* Total Frames Input */}
        <label className="block mb-4">
          <span className="block text-sm font-medium text-gray-700 mb-1">Total Frames:</span>
          <input 
            type="number" 
            min={1} 
            max={65535} 
            value={totalFrames} 
            onChange={e => setTotalFrames(Number(e.target.value))} 
            className="w-full rounded border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400" 
          />
        </label>
        
        {/* Frame Rate Input */}
        <label className="block mb-4">
          <span className="block text-sm font-medium text-gray-700 mb-1">Frame Rate (fps):</span>
          <input 
            type="number" 
            min={1} 
            max={120} 
            value={frameRate} 
            onChange={e => setFrameRate(Number(e.target.value))} 
            className="w-full rounded border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-400" 
          />
        </label>
        
        {/* Save Configuration Button */}
        <button 
          onClick={handleSave} 
          className="w-full bg-indigo-500 hover:bg-indigo-600 text-white font-semibold py-2 px-4 rounded transition mb-2"
        >
          💾 Save Config
        </button>
      </div>
      
      {/* Status Display */}
      <div className="bg-white rounded-xl shadow p-6 w-full max-w-md mb-8">
        <h2 className="text-lg font-semibold text-indigo-600 mb-2">Status</h2>
        <div className="mb-1">Status: <b className="text-indigo-700">{status}</b></div>
        <div className="mb-1">Current Frame: <b>{currentFrame}</b></div>
        <div>Total Frames: <b>{totalFrames}</b></div>
      </div>
      
      {/* Control Buttons */}
      <div className="bg-white rounded-xl shadow p-6 w-full max-w-md mb-8 flex flex-col items-center">
        <h2 className="text-lg font-semibold text-indigo-600 mb-2">Controls</h2>
        <div className="flex gap-4 mb-2">
          <button
            onClick={handleToggle}
            disabled={status === 'Disconnected'}
            className="bg-green-500 hover:bg-green-600 text-white font-semibold py-2 px-6 rounded disabled:opacity-50 transition"
          >
            {senderState === 'stopped' ? '▶ Start' : (senderState === 'running' ? '⏸ Pause' : '▶ Resume')}
          </button>
          <button 
            onClick={handleReset} 
            className="bg-yellow-400 hover:bg-yellow-500 text-white font-semibold py-2 px-6 rounded transition"
          >
            🔄 Reset
          </button>
        </div>
      </div>
      
      {/* Progress Bar */}
      <div className="bg-white rounded-xl shadow p-6 w-full max-w-md flex flex-col items-center">
        <h2 className="text-lg font-semibold text-indigo-600 mb-2">Progress</h2>
        <progress 
          value={currentFrame} 
          max={totalFrames} 
          className="w-full h-4 mb-2" 
        />
        <div className="text-gray-700">{currentFrame} / {totalFrames} ({percent}%)</div>
      </div>
    </div>
  );
}

export default App;
