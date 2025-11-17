
import subprocess
import sys
import os

# Assumes the backend code is in a sibling directory. Adjust path as needed.
BACKEND_SCRIPT_PATH = os.path.abspath("../mdjourney-backend/main.py")

def start_backend_process_local(port: int) -> int:
    """Starts a backend process locally using the host's Python executable."""
    command = [sys.executable, BACKEND_SCRIPT_PATH, "--port", str(port)]
    process = subprocess.Popen(command)
    print(f"INFO: Gateway started local backend on port {port} with PID {process.pid}")
    return process.pid

def stop_backend_process_local(pid: int):
    """Stops a local backend process by its PID."""
    print(f"INFO: Gateway stopping local backend with PID {pid}")
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
    else:
        subprocess.run(["kill", str(pid)], check=True)
