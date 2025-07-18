def print_headless_instructions():
    """Print instructions for headless mode keyboard controls."""
    print("\nFrame Conductor (Headless Mode)")
    print("================================")
    print("Keyboard commands:")
    print("  p : Play/Pause")
    print("  r : Reset")
    print("  q : Quit")
    print("--------------------------------")


def headless_progress_bar(current, total, status, bar_length=30):
    """Display a real-time progress bar in the terminal for headless mode."""
    percent = (current / total) if total else 0
    filled = int(bar_length * percent)
    bar = "=" * filled + ">" + " " * (bar_length - filled - 1)
    percent_disp = int(percent * 100)
    print(f"\r[{bar}] {percent_disp:3d}%  (Frame {current}/{total})  Status: {status}   ", end="", flush=True) 