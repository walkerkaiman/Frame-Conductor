#!/usr/bin/env python3
"""
Frame Conductor - Main Entry Point

A standalone application for sending sACN frame numbers to Universe 1.
This application can be run independently of the Interaction framework.

Usage:
    python main.py [--headless] [--target-frame N] [--fps X]
"""

import argparse
import sys
import threading
import time
import tkinter as tk
from gui import FrameConductorGUI
from sacn_sender import SACNSender


def run_gui():
    """Main function to run the Frame Conductor GUI application."""
    root = tk.Tk()
    app = FrameConductorGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


def print_headless_instructions():
    print("\nFrame Conductor (Headless Mode)")
    print("================================")
    print("Keyboard commands:")
    print("  p : Play/Pause")
    print("  r : Reset")
    print("  q : Quit")
    print("--------------------------------")


def headless_progress_bar(current, total, status, bar_length=30):
    percent = (current / total) if total else 0
    filled = int(bar_length * percent)
    bar = "=" * filled + ">" + " " * (bar_length - filled - 1)
    percent_disp = int(percent * 100)
    print(f"\r[{bar}] {percent_disp:3d}%  (Frame {current}/{total})  Status: {status}   ", end="", flush=True)


def run_headless(target_frame, fps):
    sender = SACNSender(universe=1)
    status = "Paused"
    running = False
    paused = True
    reset_requested = False
    quit_requested = False
    current_frame = 0
    lock = threading.Lock()

    def on_frame_sent(frame):
        nonlocal current_frame
        with lock:
            current_frame = frame

    sender.set_frame_callback(on_frame_sent)

    def sender_thread_func():
        nonlocal running, paused, reset_requested, status
        while not quit_requested:
            if running and not paused:
                if sender.is_running:
                    # Already running, just wait
                    time.sleep(0.05)
                else:
                    # Start sending
                    sender.start_sending(target_frame, fps)
                    status = "Running"
            elif reset_requested:
                sender.stop_sending()
                status = "Reset"
                with lock:
                    nonlocal current_frame
                    current_frame = 0
                reset_requested = False
                paused = True
                running = False
            else:
                if sender.is_running:
                    sender.pause_sending()
                    status = "Paused"
                time.sleep(0.05)
        sender.stop_sending()
        status = "Stopped"

    thread = threading.Thread(target=sender_thread_func, daemon=True)
    thread.start()

    print_headless_instructions()
    print("Starting in Paused state. Press 'p' to Play.")

    try:
        while not quit_requested:
            with lock:
                frame = current_frame
            headless_progress_bar(frame, target_frame, status)
            if sys.platform == "win32":
                import msvcrt
                if msvcrt.kbhit():
                    key = msvcrt.getwch().lower()
                    if key == "p":
                        if not running:
                            running = True
                            paused = False
                            status = "Running"
                        else:
                            paused = not paused
                            status = "Paused" if paused else "Running"
                    elif key == "r":
                        reset_requested = True
                        status = "Reset"
                    elif key == "q":
                        quit_requested = True
                        print("\nExiting.")
                        break
            else:
                # Unix: use select for non-blocking input
                import select
                import termios
                import tty
                dr, dw, de = select.select([sys.stdin], [], [], 0)
                if dr:
                    key = sys.stdin.read(1).lower()
                    if key == "p":
                        if not running:
                            running = True
                            paused = False
                            status = "Running"
                        else:
                            paused = not paused
                            status = "Paused" if paused else "Running"
                    elif key == "r":
                        reset_requested = True
                        status = "Reset"
                    elif key == "q":
                        quit_requested = True
                        print("\nExiting.")
                        break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        quit_requested = True
    finally:
        sender.stop_sending()
        print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(description="Frame Conductor - sACN Frame Sender")
    parser.add_argument("--headless", action="store_true", help="Run in headless (no-GUI) mode")
    parser.add_argument("--target-frame", type=int, default=1000, help="Target frame number (default: 1000)")
    parser.add_argument("--fps", type=int, default=30, help="Frame rate (default: 30)")
    args = parser.parse_args()

    if args.headless:
        run_headless(args.target_frame, args.fps)
    else:
        run_gui()

if __name__ == "__main__":
    main() 