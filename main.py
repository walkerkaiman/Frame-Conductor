#!/usr/bin/env python3
"""
Frame Conductor - Main Entry Point

A modern web application for sending sACN frame numbers to Universe 999.
This application provides a React frontend with FastAPI backend for real-time
control and monitoring of sACN frame transmission.

Features:
- Web-based interface accessible from any browser
- Network accessibility for multi-device control
- Real-time progress updates via WebSocket
- Configuration persistence and multi-browser synchronization
- Network-wide singleton protection (only one instance per network)

Usage:
    python main.py [--headless] [--target-frame N] [--fps X]

Arguments:
    --headless: Run in headless mode (not implemented in current version)
    --target-frame N: Set total frames to send (default: 1000)
    --fps X: Set frame rate in frames per second (default: 30)

Network Access:
    The application automatically detects your local IP address and provides
    URLs for both local and network access. Other devices on your network
    can access the interface using the displayed network URL.

Network Singleton:
    Only one instance of Frame Conductor can run on the network at a time.
    If another instance is detected, the application will exit with an error.
"""

import subprocess
import sys
import time
import argparse
import webbrowser
import os
import socket
import shutil
from utils.network_singleton import NetworkSingleton

# Configuration constants
BACKEND_PORT = 9000
FRONTEND_PORT = 5173  # Default Vite dev server port
FRONTEND_DEV = True  # Set to True to launch React dev server automatically





def start_backend() -> subprocess.Popen:
    """
    Start the FastAPI backend server using uvicorn.
    
    Returns:
        subprocess.Popen: Process object for the backend server
        
    Note:
        The backend is configured to bind to all network interfaces (0.0.0.0)
        to allow access from other devices on the network.
    """
    return subprocess.Popen([
        sys.executable, "-m", "uvicorn", "api_server:app",
        "--host", "0.0.0.0", "--port", str(BACKEND_PORT)
    ])


def start_frontend() -> subprocess.Popen:
    """
    Start the React frontend development server using npm.
    
    Returns:
        subprocess.Popen: Process object for the frontend server
        
    Note:
        Attempts to find npm in PATH, with fallbacks for common Windows locations.
        The frontend is configured to bind to all network interfaces for network access.
    """
    npm_path = shutil.which('npm')
    if not npm_path:
        # Fallback to common Windows npm locations
        npm_path = r"C:\Program Files\nodejs\npm.cmd"
        if not os.path.exists(npm_path):
            npm_path = "npm"  # Final fallback
    print(f"[DEBUG] Using npm path: {npm_path}")
    return subprocess.Popen([npm_path, "run", "dev"], cwd="frontend")


def check_port(host: str, port: int, timeout: int = 2) -> bool:
    """
    Check if a port is open and accepting connections.
    
    Args:
        host (str): Hostname or IP address to check
        port (int): Port number to check
        timeout (int): Connection timeout in seconds
        
    Returns:
        bool: True if port is open, False otherwise
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except:
        return False


def get_local_ip() -> str:
    """
    Get the local IP address for network access.
    
    This function determines the local IP address by attempting to connect
    to a remote address (8.8.8.8:80) and reading the local socket address.
    
    Returns:
        str: Local IP address, or "localhost" if detection fails
    """
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "localhost"


def main() -> int:
    """
    Main application entry point.
    
    This function:
    1. Parses command line arguments
    2. Starts the network singleton mechanism
    3. Starts the backend FastAPI server
    4. Starts the frontend React development server (if enabled)
    5. Waits for servers to start and verifies they're running
    6. Opens the web interface in the default browser
    7. Displays network access information
    8. Waits for user interruption (Ctrl+C)
    9. Gracefully shuts down all processes
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(description="Frame Conductor - sACN Frame Sender")
    parser.add_argument("--headless", action="store_true", help="Run in headless (no-GUI) mode")
    parser.add_argument("--target-frame", type=int, default=1000, help="Total frames (default: 1000)")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")
    parser.add_argument("--no-singleton", action="store_true", help="Disable network singleton protection")
    args = parser.parse_args()

    # Initialize network singleton (unless disabled)
    singleton = None
    if not args.no_singleton:
        def on_conflict(instance_id: str):
            print(f"[ERROR] Another Frame Conductor instance is already running on the network")
            print(f"[ERROR] Only one instance is allowed per network")
        
        singleton = NetworkSingleton(on_conflict_callback=on_conflict)
        if not singleton.start():
            return 1
    else:
        print("[WARNING] Network singleton protection disabled")

    try:
        print(f"[DEBUG] Starting backend on port {BACKEND_PORT}...")
        backend_proc = start_backend()
        
        frontend_proc = None
        if FRONTEND_DEV:
            print(f"[DEBUG] Starting frontend on port {FRONTEND_PORT}...")
            frontend_proc = start_frontend()
        
        print("[DEBUG] Waiting for servers to start...")
        time.sleep(3)  # Give servers more time to start
        
        # Check if servers are running
        local_ip = get_local_ip()
        backend_running = check_port(local_ip, BACKEND_PORT)
        frontend_running = check_port(local_ip, FRONTEND_PORT)
        
        print(f"[DEBUG] Backend running: {backend_running}")
        print(f"[DEBUG] Frontend running: {frontend_running}")
        
        if not backend_running:
            print(f"[ERROR] Backend failed to start on port {BACKEND_PORT}")
            return 1
        
        if not frontend_running:
            print(f"[WARNING] Frontend may not be running on port {FRONTEND_PORT}")
            print("[INFO] You may need to manually start the frontend with: cd frontend && npm run dev")

        # Open the web GUI in the default browser
        if frontend_running:
            webbrowser.open(f"http://{local_ip}:{FRONTEND_PORT}")
            print(f"Web GUI launched at http://{local_ip}:{FRONTEND_PORT}")
            print(f"Other computers can access the GUI at: http://{local_ip}:{FRONTEND_PORT}")
        else:
            print(f"Backend API available at http://{local_ip}:{BACKEND_PORT}")
            print(f"Other computers can access the API at: http://{local_ip}:{BACKEND_PORT}")

        try:
            if args.headless:
                print("Headless mode not implemented in this version.")
                print("Please use the web interface or implement headless mode.")
            else:
                print("Press Ctrl+C to stop the servers")
            # Wait for interrupt
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Exiting.")
        finally:
            print("[DEBUG] Terminating processes...")
            backend_proc.terminate()
            if frontend_proc:
                frontend_proc.terminate()
            backend_proc.wait()
            if frontend_proc:
                frontend_proc.wait()
            print("All processes terminated. Goodbye!")
        
        return 0
        
    finally:
        # Clean up singleton
        if singleton:
            singleton.stop()


if __name__ == "__main__":
    sys.exit(main()) 