
import subprocess
import sys
import os
import time

# Correctly determine the paths
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "..", "mdjourney-backend")
backend_script_path = os.path.join(backend_dir, "main.py")
# The repository root is two levels up from the gateway script's directory
repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

def start_backend_process_local(port: int, config_path: str) -> int:
    """Starts a backend process locally, passing the config file path."""
    command = [
        sys.executable,
        "-u", # Unbuffered output
        backend_script_path,
        "--port", str(port),
        "--config-file", config_path
    ]

    # Create a new environment for the subprocess to set PYTHONPATH
    proc_env = os.environ.copy()
    python_path = proc_env.get("PYTHONPATH", "")
    proc_env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{python_path}"

    print(f"INFO: Gateway starting backend with command: {' '.join(command)}")
    print(f"INFO: Setting CWD for backend to: {backend_dir}")
    print(f"INFO: Setting PYTHONPATH for backend to: {proc_env['PYTHONPATH']}")

    # Set the current working directory to the backend's directory
    process = subprocess.Popen(
        command,
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=proc_env
    )

    # Give the process a moment to start and print output
    time.sleep(2)

    # Read and print the output
    stdout, stderr = process.communicate()
    if stdout:
        print(f"Backend stdout:\n{stdout.decode()}")
    if stderr:
        print(f"Backend stderr:\n{stderr.decode()}")

    return process.pid

def stop_backend_process_local(pid: int):
    """Stops a local backend process by its PID."""
    print(f"INFO: Gateway stopping local backend with PID {pid}")
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=True)
    else:
        subprocess.run(["kill", str(pid)], check=True)
