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
    npm_cmd = 'npm'
    if os.name == 'nt':
        npm_cmd = shutil.which('npm') or 'npm.cmd'
    frontend_port = 5173
    frontend_hosts = ['127.0.0.1', 'localhost']
    
    # Check if frontend is already running on any host
    frontend_running = any(is_port_in_use(host, frontend_port) for host in frontend_hosts)
    frontend_process = None
    
    if frontend_running:
        print(f"[DEBUG] Detected running frontend on {frontend_hosts} port {frontend_port}. Using existing server.")
    else:
        print(f"[DEBUG] Frontend not running. Starting frontend development server...")
        try:
            frontend_process = subprocess.Popen([npm_cmd, 'run', 'dev'], cwd=frontend_dir, 
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Wait for frontend to start
            if not wait_for_port('localhost', frontend_port, timeout=30):
                print(f"[ERROR] Frontend failed to start within 30 seconds.")
                if frontend_process:
                    frontend_process.terminate()
                return 1
            print(f"[DEBUG] Frontend started successfully on port {frontend_port}.")
        except Exception as e:
            print(f"[ERROR] Failed to start frontend: {e}")
            if frontend_process:
                frontend_process.terminate()
            return 1
    
    try:
        print(f"[DEBUG] Running Playwright tests against frontend...")
        result = subprocess.run([
            npx_cmd, 'playwright', 'test', 'tests/'
        ], cwd=frontend_dir, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        if 'No tests found' in result.stdout or 'No tests found' in result.stderr:
            print("No Playwright tests were found or executed. Check your test file names and config.")
        print(f"[DEBUG] Playwright tests finished.")
        return result.returncode
    finally:
        # Clean up frontend process if we started it
        if frontend_process:
            print(f"[DEBUG] Terminating frontend process...")
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
            print(f"[DEBUG] Frontend process terminated.")

def main():
    py_status = run_pytest()
    pw_status = run_playwright()
    if py_status != 0 or pw_status != 0:
        print("\nSome tests failed.")
        sys.exit(1)
    print("\nAll tests passed.")

if __name__ == "__main__":
    main() 