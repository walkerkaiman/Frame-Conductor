"""
Frame Conductor - FastAPI Backend Server

This module provides the FastAPI backend for the Frame Conductor application.
It handles sACN frame transmission, configuration management, and real-time
communication with the React frontend via HTTP APIs and WebSocket.

Features:
- RESTful API endpoints for configuration and control
- WebSocket for real-time progress updates
- sACN frame transmission management
- Configuration persistence with file-based storage
- Multi-client WebSocket support for real-time synchronization

API Endpoints:
- GET /api/config - Retrieve current configuration
- POST /api/config - Update configuration
- POST /api/start - Start frame transmission
- POST /api/pause - Pause/resume transmission
- POST /api/reset - Reset to frame 0
- WebSocket /ws/progress - Real-time progress updates

Configuration:
    The server automatically creates and manages a JSON configuration file
    (sacn_sender_config.json) that persists settings between sessions.

Threading:
    Uses threading.RLock for thread-safe configuration access and
    asyncio for WebSocket communication and async operations.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import asyncio
import json
import os
from utils.sacn_sender import SACNSender
import logging
from typing import Dict, Any, Set
import socket

# Configuration constants
CONFIG_FILE = 'sacn_sender_config.json'
DEFAULT_CONFIG = {
    'total_frames': 1000,
    'frame_rate': 30,
    'universe': 999,
    'frame_length': 512
}

# Initialize FastAPI application
app = FastAPI(
    title="Frame Conductor API",
    description="Backend API for sACN frame transmission control",
    version="1.0.0"
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State ---
config_lock = threading.RLock()
ws_clients: Set[WebSocket] = set()

# Load configuration from file or use defaults
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    except Exception as e:
        logging.error(f"Error loading config file: {e}")
        config = DEFAULT_CONFIG.copy()
else:
    config = DEFAULT_CONFIG.copy()

# Initialize sACN sender
sender = SACNSender(
    universe=config.get('universe', 999),
    frame_length=config.get('frame_length', 512)
)

# State for WebSocket progress updates
progress_state = {
    'frame': 0,
    'total_frames': config.get('total_frames', 1000),
    'status': 'Ready',
    'percent': 0
}

# State for configuration updates
config_state = {
    'type': 'config_update',
    'config': config.copy()
}

# --- Helper Functions ---
logging.basicConfig(level=logging.INFO)
logging.info(f"Backend working directory: {os.getcwd()}")
logging.info(f"Config file path: {os.path.abspath(CONFIG_FILE)}")


def save_config() -> bool:
    """
    Save the current configuration to the JSON file.
    
    This function saves the in-memory configuration to the config file
    with proper error handling and file system synchronization.
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    with config_lock:
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk
            logging.info(f"Configuration saved to {os.path.abspath(CONFIG_FILE)}")
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {e}", exc_info=True)
            return False


def update_progress(frame: int | None = None, status: str | None = None) -> None:
    """
    Update the progress state for WebSocket broadcasting.
    
    This function updates the progress state that is continuously
    broadcast to all connected WebSocket clients.
    
    Args:
        frame (int, optional): Current frame number
        status (str, optional): Current status ('Ready', 'Sending frames...', 'Paused', etc.)
    """
    if frame is not None:
        progress_state['frame'] = frame
    if status is not None:
        progress_state['status'] = status
    
    # Update total frames from current config
    progress_state['total_frames'] = config.get('total_frames', 1000)
    
    # Calculate percentage
    if progress_state['total_frames'] > 0:
        progress_state['percent'] = int((progress_state['frame'] / progress_state['total_frames']) * 100)
    else:
        progress_state['percent'] = 0


async def broadcast_config_update() -> None:
    """
    Broadcast configuration updates to all connected WebSocket clients.
    
    This function sends the current configuration to all connected
    WebSocket clients to keep them synchronized.
    """
    if ws_clients:
        # Create a copy to avoid modification during iteration
        clients = list(ws_clients)
        for client in clients:
            try:
                await client.send_json(config_state)
            except Exception:
                # Remove disconnected clients
                ws_clients.discard(client)


# --- HTTP Endpoints ---
@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.
    
    Returns:
        Dict[str, Any]: Current configuration including total_frames, frame_rate, universe, and frame_length
    """
    with config_lock:
        return config.copy()


@app.post("/api/config")
async def update_config(request: Request) -> Dict[str, Any]:
    """
    Update the configuration.
    
    This endpoint accepts configuration updates and:
    1. Updates the in-memory configuration
    2. Saves the configuration to file
    3. Updates the sACN sender settings
    4. Broadcasts the update to all WebSocket clients
    5. Stops the sender if it's currently running (to apply new settings)
    
    Args:
        request (Request): FastAPI request object containing JSON configuration data
        
    Returns:
        Dict[str, Any]: Success status and optional error message
    """
    logging.info("Configuration update requested")
    try:
        data = await request.json()
        logging.info(f"Received configuration update: {data}")
        
        need_to_stop = False
        
        with config_lock:
            # Update configuration
            config.update(data)
            logging.info(f"Configuration updated: {config}")
            
            # Save to file
            if not save_config():
                return {"success": False, "error": "Failed to save configuration"}
            
            # Update sACN sender settings
            sender.universe = config.get('universe', 999)
            sender.frame_length = config.get('frame_length', 512)
            logging.info(f"sACN sender updated: universe={sender.universe}, frame_length={sender.frame_length}")
            
            # Update config state for WebSocket broadcasting
            config_state['config'] = config.copy()
            
            # Broadcast update to all clients
            asyncio.create_task(broadcast_config_update())
            
            # Stop sender if running to apply new settings
            if sender.is_running:
                need_to_stop = True
        
        # Stop sender outside of lock to avoid deadlock
        if need_to_stop:
            logging.info("Stopping sender to apply new configuration")
            await asyncio.to_thread(sender.stop_sending)
            update_progress(0, 'Ready')
            logging.info("Sender stopped")
        
        logging.info("Configuration update completed successfully")
        return {"success": True}
        
    except Exception as e:
        logging.error(f"Exception in configuration update: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/start")
async def start_sender() -> Dict[str, Any]:
    """
    Start sACN frame transmission.
    
    This endpoint starts the sACN sender with the current configuration
    and sets up the frame callback for progress updates.
    
    Returns:
        Dict[str, Any]: Success status
    """
    try:
        total_frames = config.get('total_frames', 1000)
        frame_rate = config.get('frame_rate', 30)
        
        # Update sender settings
        sender.universe = config.get('universe', 999)
        sender.frame_length = config.get('frame_length', 512)
        
        # Stop any existing transmission
        sender.stop_sending()
        
        # Set up frame callback for progress updates
        sender.set_frame_callback(lambda frame: update_progress(frame, 'Sending frames...'))
        
        # Start transmission
        if sender.start_sending(total_frames, frame_rate):
            update_progress(0, 'Sending frames...')
            logging.info(f"Started sACN transmission: {total_frames} frames at {frame_rate} fps")
            return {"success": True}
        else:
            logging.error("Failed to start sACN transmission")
            return {"success": False, "error": "Failed to start sACN transmission"}
            
    except Exception as e:
        logging.error(f"Exception starting sender: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/pause")
async def pause_sender() -> Dict[str, Any]:
    """
    Pause sACN frame transmission.
    
    This endpoint explicitly pauses the sACN sender if it's currently running.
    
    Returns:
        Dict[str, Any]: Success status
    """
    try:
        if sender.is_running and not sender.is_paused:
            sender.pause()
            update_progress(status='Paused')
            logging.info("sACN transmission paused")
            return {"success": True}
        else:
            logging.warning("Cannot pause: sender is not running or already paused")
            return {"success": False, "error": "Sender is not running or already paused"}
            
    except Exception as e:
        logging.error(f"Exception in pause: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/resume")
async def resume_sender() -> Dict[str, Any]:
    """
    Resume sACN frame transmission.
    
    This endpoint explicitly resumes the sACN sender if it's currently paused.
    
    Returns:
        Dict[str, Any]: Success status
    """
    try:
        if sender.is_running and sender.is_paused:
            sender.resume()
            update_progress(status='Sending frames...')
            logging.info("sACN transmission resumed")
            return {"success": True}
        else:
            logging.warning("Cannot resume: sender is not running or not paused")
            return {"success": False, "error": "Sender is not running or not paused"}
            
    except Exception as e:
        logging.error(f"Exception in resume: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.post("/api/reset")
async def reset_sender() -> Dict[str, Any]:
    """
    Reset sACN frame transmission.
    
    This endpoint stops the current transmission and resets the
    progress state to ready.
    
    Returns:
        Dict[str, Any]: Success status
    """
    try:
        sender.stop_sending()
        update_progress(0, 'Ready')
        logging.info("sACN transmission reset")
        return {"success": True}
        
    except Exception as e:
        logging.error(f"Exception in reset: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@app.get("/api/local_ip")
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return {"ip": IP}


@app.get("/api/state")
async def get_sender_state() -> Dict[str, Any]:
    """
    Get the current state of the sACN sender.
    
    Returns:
        Dict[str, Any]: Current state information including status and available actions
    """
    try:
        if not sender.is_running:
            state = "stopped"
            available_actions = ["start"]
        elif sender.is_paused:
            state = "paused"
            available_actions = ["resume", "reset"]
        else:
            state = "running"
            available_actions = ["pause", "reset"]
        
        return {
            "state": state,
            "available_actions": available_actions,
            "current_frame": progress_state.get('frame', 0),
            "total_frames": progress_state.get('total_frames', 0)
        }
        
    except Exception as e:
        logging.error(f"Exception getting sender state: {e}", exc_info=True)
        return {"state": "error", "available_actions": [], "error": str(e)}


# --- WebSocket Endpoint ---
@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    """
    WebSocket endpoint for real-time progress updates.
    
    This endpoint:
    1. Accepts WebSocket connections
    2. Sends initial state (progress and config)
    3. Continuously broadcasts progress updates at ~60fps
    4. Handles client disconnections gracefully
    
    Args:
        websocket (WebSocket): WebSocket connection object
    """
    await websocket.accept()
    ws_clients.add(websocket)
    logging.info(f"WebSocket client connected. Total clients: {len(ws_clients)}")
    
    try:
        # Send initial state
        await websocket.send_json(progress_state)
        await websocket.send_json(config_state)
        
        # Keep connection alive with frequent updates for smooth visual feedback
        while True:
            await asyncio.sleep(0.016)  # ~60fps for smooth updates
            await websocket.send_json(progress_state)
            
    except WebSocketDisconnect:
        logging.info("WebSocket client disconnected")
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        ws_clients.discard(websocket)
        logging.info(f"WebSocket client removed. Total clients: {len(ws_clients)}") 