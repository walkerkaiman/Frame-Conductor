import subprocess
import sys
import os
import shutil
import time
import socket

def wait_for_port(host, port, timeout=10):
    print(f"[DEBUG] Waiting for port {host}:{port} to become available (timeout={timeout}s)...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"[DEBUG] Port {host}:{port} is now available.")
                return True
        except Exception:
            time.sleep(0.5)
    print(f"[DEBUG] Timeout waiting for port {host}:{port}.")
    return False

def is_port_in_use(host, port):
    print(f"[DEBUG] Checking if port {host}:{port} is in use...")
    try:
        with socket.create_connection((host, port), timeout=1):
            print(f"[DEBUG] Port {host}:{port} is in use.")
            return True
    except Exception:
        print(f"[DEBUG] Port {host}:{port} is NOT in use.")
        return False

def run_pytest():
    print("\n=== Running pytest for Python tests ===")
    tests_dir = os.path.dirname(__file__)
    test_files = [f for f in os.listdir(tests_dir) if f.startswith('test_') and f.endswith('.py')]
    if not test_files:
        print("No Python test files found in Tests/.")
        return 0
    print(f"[DEBUG] Running pytest on files: {test_files}")
    result = subprocess.run([sys.executable, '-m', 'pytest'] + test_files, cwd=tests_dir, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode

def run_playwright():
    print("\n=== Running Playwright for frontend tests ===")
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    tests_dir = os.path.join(frontend_dir, 'tests')
    if not os.path.exists(tests_dir):
        print("No Playwright tests directory found.")
        return 0
    npx_cmd = 'npx'
    if os.name == 'nt':
        npx_cmd = shutil.which('npx') or 'npx.cmd'
    frontend_port = 5173
    frontend_hosts = ['127.0.0.1', 'localhost']
    # Check if frontend is already running on any host
    if any(is_port_in_use(host, frontend_port) for host in frontend_hosts):
        print(f"[DEBUG] Detected running frontend on {frontend_hosts} port {frontend_port}. Using existing server.")
        print(f"[DEBUG] Running Playwright tests against existing frontend...")
        result = subprocess.run([
            npx_cmd, 'playwright', 'test', 'tests/'
        ], cwd=frontend_dir, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if 'No tests found' in result.stdout or 'No tests found' in result.stderr:
            print("No Playwright tests were found or executed. Check your test file names and config.")
        print(f"[DEBUG] Playwright tests finished against existing frontend.")
        return result.returncode
    else:
        print(f"[ERROR] Frontend is NOT running on any of {frontend_hosts} port {frontend_port}. Please start the frontend (npm run dev) before running tests.")
        return 1

def main():
    py_status = run_pytest()
    pw_status = run_playwright()
    if py_status != 0 or pw_status != 0:
        print("\nSome tests failed.")
        sys.exit(1)
    print("\nAll tests passed.")

if __name__ == "__main__":
    main() 