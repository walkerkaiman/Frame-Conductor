#!/usr/bin/env python3
"""
Frame Conductor - Main Entry Point

A standalone application for sending sACN frame numbers to Universe 1.
This application can be run independently of the Interaction framework.

Usage:
    python main.py [--headless] [--target-frame N] [--fps X]
"""

import subprocess
import sys
import time
import argparse
import webbrowser
import os
# from gui import FrameConductorGUI  # Removed old GUI
# from utils.sacn_sender import SACNSender  # Only needed for headless mode
# from utils.headless_utils import print_headless_instructions, headless_progress_bar  # Only needed for headless mode

BACKEND_PORT = 9000
FRONTEND_PORT = 5173  # Default Vite dev server port
FRONTEND_DEV = True  # Set to True to launch React dev server automatically


def start_backend():
    # Start FastAPI server with uvicorn
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api_server:app",
        "--host", "0.0.0.0", "--port", str(BACKEND_PORT)
    ])

def start_frontend():
    # Use full path to npm.cmd for Windows compatibility
    npm_path = r"C:\Program Files\nodejs\npm.cmd"
    if not os.path.exists(npm_path):
        npm_path = "npm"  # Fallback to system PATH
    return subprocess.Popen([npm_path, "run", "dev"], cwd="frontend")


def main():
    parser = argparse.ArgumentParser(description="Frame Conductor - sACN Frame Sender")
    parser.add_argument("--headless", action="store_true", help="Run in headless (no-GUI) mode")
    parser.add_argument("--target-frame", type=int, default=1000, help="Total frames (default: 1000)")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")
    args = parser.parse_args()

    backend_proc = start_backend()
    frontend_proc = None
    if FRONTEND_DEV:
        frontend_proc = start_frontend()
    time.sleep(2)  # Give servers time to start

    # Open the web GUI in the default browser
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")

    try:
        if args.headless:
            print("Headless mode not implemented in this scaffold.")
        else:
            print(f"Web GUI launched at http://localhost:{FRONTEND_PORT}")
        # Wait for interrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Exiting.")
    finally:
        backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        backend_proc.wait()
        if frontend_proc:
            frontend_proc.wait()
        print("All processes terminated. Goodbye!")

if __name__ == "__main__":
    main() 