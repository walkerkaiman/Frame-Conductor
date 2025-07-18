from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import asyncio
import json
import os
from utils.sacn_sender import SACNSender
import logging

CONFIG_FILE = 'sacn_sender_config.json'
# Backend now runs on port 9000 (set in main.py)

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State ---
config_lock = threading.RLock()
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        config = json.load(f)
else:
    config = {
        'total_frames': 1000,
        'frame_rate': 30,
        'universe': 999,
        'frame_length': 512
    }
sender = SACNSender(
    universe=config.get('universe', 999),
    frame_length=config.get('frame_length', 512)
)
progress_state = {
    'frame': 0,
    'total_frames': config.get('total_frames', 1000),
    'status': 'Ready',
    'percent': 0
}
ws_clients = set()

# --- Helper Functions ---
logging.basicConfig(level=logging.INFO)
logging.info(f"Backend working directory: {os.getcwd()}")
logging.info(f"Config file path: {os.path.abspath(CONFIG_FILE)}")

def save_config():
    with config_lock:
        try:
            logging.info(f"save_config: About to open {CONFIG_FILE} for writing")
            with open(CONFIG_FILE, 'w') as f:
                logging.info("save_config: File opened for writing")
                json.dump(config, f, indent=2)
                logging.info("save_config: json.dump complete")
                f.flush()
                logging.info("save_config: flush complete")
                os.fsync(f.fileno())
                logging.info("save_config: fsync complete")
            logging.info(f"save_config: File closed after writing")
            logging.info(f"Config saved to {os.path.abspath(CONFIG_FILE)}: {config}")
            logging.info(f"save_config: About to open {CONFIG_FILE} for reading")
            with open(CONFIG_FILE, 'r') as f:
                logging.info("save_config: File opened for reading")
                logging.info(f"Config file contents after save: {f.read()}")
        except Exception as e:
            logging.error(f"Error saving config: {e}", exc_info=True)

def update_progress(frame=None, status=None):
    if frame is not None:
        progress_state['frame'] = frame
    if status is not None:
        progress_state['status'] = status
    progress_state['total_frames'] = config.get('total_frames', 1000)
    if progress_state['total_frames'] > 0:
        progress_state['percent'] = int((progress_state['frame'] / progress_state['total_frames']) * 100)
    else:
        progress_state['percent'] = 0

# --- HTTP Endpoints ---
@app.get("/api/config")
async def get_config():
    with config_lock:
        return config

@app.post("/api/config")
async def update_config(request: Request):
    logging.info("update_config endpoint called")
    try:
        data = await request.json()
        logging.info(f"Received config update: {data}")
        need_to_stop = False
        logging.info("Attempting to acquire config_lock for update...")
        with config_lock:
            logging.info("config_lock acquired.")
            logging.info("Updating in-memory config...")
            config.update(data)
            logging.info(f"Config after update: {config}")
            logging.info("Saving config to file...")
            save_config()
            logging.info("Config saved to file.")
            logging.info("Updating sender universe and frame_length...")
            sender.universe = config.get('universe', 999)
            sender.frame_length = config.get('frame_length', 512)
            logging.info(f"Sender updated: universe={sender.universe}, frame_length={sender.frame_length}")
            if sender.is_running:
                need_to_stop = True
        logging.info("config_lock released.")
        if need_to_stop:
            logging.info("Stopping sender after config update...")
            await asyncio.to_thread(sender.stop_sending)
            update_progress(0, 'Ready')
            logging.info("Sender stopped.")
        logging.info("update_config endpoint completed successfully.")
        return {"success": True}
    except Exception as e:
        logging.error(f"Exception in update_config: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@app.post("/api/start")
async def start_sender():
    total_frames = config.get('total_frames', 1000)
    frame_rate = config.get('frame_rate', 30)
    sender.universe = config.get('universe', 999)
    sender.frame_length = config.get('frame_length', 512)
    sender.stop_sending()
    sender.set_frame_callback(lambda frame: update_progress(frame, 'Sending frames...'))
    sender.start_sending(total_frames, frame_rate)
    update_progress(0, 'Sending frames...')
    return {"success": True}

@app.post("/api/pause")
async def pause_sender():
    if sender.is_running:
        if sender.is_paused:
            sender.resume()
            update_progress(status='Sending frames...')
        else:
            sender.pause()
            update_progress(status='Paused')
    return {"success": True}

@app.post("/api/reset")
async def reset_sender():
    sender.stop_sending()
    update_progress(0, 'Ready')
    return {"success": True}

# --- WebSocket Endpoint ---
@app.websocket("/ws/progress")
async def websocket_progress(websocket: WebSocket):
    await websocket.accept()
    ws_clients.add(websocket)
    try:
        while True:
            await websocket.send_json(progress_state)
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        ws_clients.discard(websocket) 