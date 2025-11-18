#!/usr/bin/env python3
"""
Process manager for the FAIR metadata automation system.
Handles starting, monitoring, and stopping system services.
"""

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Optional

from app.core.config import find_config_file, get_monitor_path, initialize_config


class ProcessManager:
    """Manages system processes for the FAIR metadata automation system."""

    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\nReceived signal {signum}. Shutting down all services...")
        self.shutdown()
        sys.exit(0)

    def start_monitor(self) -> Optional[subprocess.Popen]:
        """Start the folder monitor."""
        try:
            print("Starting Folder Monitor...")

            # --- Load the configuration to find the correct path ---
            config_file = find_config_file()
            if not config_file or not initialize_config(str(config_file)):
                print("Error: Could not load configuration. Monitor cannot start.")
                # As a fallback, you could default to 'data/', but failing is better.
                # monitor_path_to_use = "data/"
                return None

            monitor_path_to_use = get_monitor_path()
            print(f"Found monitor path from config: {monitor_path_to_use}")
            # --------------------------------------------------------

            monitor_module = "app.monitors.folder_monitor"

            # Use the path from the config file instead of a hardcoded value
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    monitor_module,
                    "--path",
                    str(monitor_path_to_use),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=Path.cwd(),  # Ensure it runs from project root
            )

            # Wait a moment to see if it starts successfully
            time.sleep(2)
            if process.poll() is None:
                print("Folder Monitor started successfully")
                return process
            else:
                print("Folder Monitor failed to start")
                return None

        except Exception as e:
            print(f"Error starting Folder Monitor: {e}")
            return None

    def start_api(
        self, host: str = "0.0.0.0", port: int = 8000, reload: bool = True
    ) -> Optional[subprocess.Popen]:
        """Start the API server."""
        try:
            print("Starting API Server...")

            # Check if uvicorn is available
            try:
                import uvicorn
            except ImportError:
                print(
                    "Error: uvicorn not installed. Install with: pip install 'mdjourney[api]'"
                )
                return None

            # Run uvicorn from project root with proper module path
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "api.main:app",
                    "--host",
                    host,
                    "--port",
                    str(port),
                    "--reload" if reload else "--no-reload",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=Path.cwd(),  # Ensure it runs from project root
            )

            # Wait a moment to see if it starts successfully
            time.sleep(3)
            if process.poll() is None:
                print("API Server started successfully")
                return process
            else:
                print("API Server failed to start")
                # Capture and display the error output
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    if stdout:
                        print(f"API Server output: {stdout}")
                    if stderr:
                        print(f"API Server error: {stderr}")
                except subprocess.TimeoutExpired:
                    pass
                return None

        except Exception as e:
            print(f"Error starting API Server: {e}")
            return None

    def start_frontend(self) -> Optional[subprocess.Popen]:
        """Start the frontend development server."""
        try:
            print("Starting Frontend Development Server...")
            frontend_dir = Path("frontend")
            if not frontend_dir.exists():
                print(f"Frontend directory not found at {frontend_dir}")
                return None

            # Check if node_modules exists
            node_modules = frontend_dir / "node_modules"
            if not node_modules.exists():
                print("Installing frontend dependencies...")
                subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)

            process = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Wait a moment to see if it starts successfully
            time.sleep(5)
            if process.poll() is None:
                print("Frontend Development Server started successfully")
                return process
            else:
                print("Frontend Development Server failed to start")
                return None

        except Exception as e:
            print(f"Error starting Frontend: {e}")
            return None

    def monitor_process(self, process: subprocess.Popen, name: str):
        """Monitor a process and print its output."""
        try:
            for line in iter(process.stdout.readline, ""):
                if not self.running:
                    break
                if line:
                    print(f"[{name}] {line.rstrip()}")
        except Exception as e:
            print(f"Error monitoring {name}: {e}")

    def start_all_services(
        self,
        monitor: bool = True,
        api: bool = True,
        frontend: bool = True,
        api_host: str = "0.0.0.0",
        api_port: int = 8000,
        api_reload: bool = True,
    ):
        """Start all or specific services."""
        print("Starting FAIR Metadata System...")
        print("=" * 50)

        # Start components based on flags
        if monitor:
            monitor_process = self.start_monitor()
            if monitor_process:
                self.processes.append(monitor_process)
                # Start monitoring thread
                monitor_thread = threading.Thread(
                    target=self.monitor_process, args=(monitor_process, "MONITOR")
                )
                monitor_thread.daemon = True
                monitor_thread.start()

        if api:
            api_process = self.start_api(api_host, api_port, api_reload)
            if api_process:
                self.processes.append(api_process)
                # Start monitoring thread
                api_thread = threading.Thread(
                    target=self.monitor_process, args=(api_process, "API")
                )
                api_thread.daemon = True
                api_thread.start()

        if frontend:
            frontend_process = self.start_frontend()
            if frontend_process:
                self.processes.append(frontend_process)
                # Start monitoring thread
                frontend_thread = threading.Thread(
                    target=self.monitor_process, args=(frontend_process, "FRONTEND")
                )
                frontend_thread.daemon = True
                frontend_thread.start()

        if self.processes:
            print("\n" + "=" * 50)
            print("System started successfully!")
            print("\nService URLs:")
            if api:
                print(f"   API Server: http://{api_host}:{api_port}")
                print(f"   API Docs: http://{api_host}:{api_port}/docs")
            if frontend:
                print("   Frontend: http://localhost:5173")
            print("\nPress Ctrl+C to stop all services")
            print("=" * 50)

            # Keep the main thread alive
            try:
                while self.running and any(p.poll() is None for p in self.processes):
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutdown requested by user...")
                self.shutdown()
        else:
            print("No services started successfully")

    def shutdown(self):
        """Shutdown all running processes."""
        self.running = False
        print("\nShutting down all services...")

        for process in self.processes:
            if process.poll() is None:  # Process is still running
                print(f"Stopping {process.args[0]}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"Force killing {process.args[0]}...")
                    process.kill()
                except Exception as e:
                    print(f"Error stopping {process.args[0]}: {e}")

        print("All services stopped")


def start_all_services(
    monitor: bool = True,
    api: bool = True,
    frontend: bool = True,
    api_host: str = "0.0.0.0",
    api_port: int = 8000,
    api_reload: bool = True,
):
    """Convenience function to start all services."""
    manager = ProcessManager()
    manager.start_all_services(monitor, api, frontend, api_host, api_port, api_reload)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start the FAIR Metadata System")
    parser.add_argument(
        "--monitor-only", action="store_true", help="Start only the folder monitor"
    )
    parser.add_argument(
        "--api-only", action="store_true", help="Start only the API server"
    )
    parser.add_argument(
        "--frontend-only", action="store_true", help="Start only the frontend"
    )
    parser.add_argument("--api-host", default="0.0.0.0", help="API server host")
    parser.add_argument("--api-port", type=int, default=8000, help="API server port")
    parser.add_argument(
        "--no-reload", action="store_true", help="Disable API auto-reload"
    )

    args = parser.parse_args()

    # Validate arguments
    if sum([args.monitor_only, args.api_only, args.frontend_only]) > 1:
        print("Error: Only one --*-only flag can be used at a time")
        sys.exit(1)

    # Determine which services to start
    monitor = not args.api_only and not args.frontend_only
    api = not args.monitor_only and not args.frontend_only
    frontend = not args.monitor_only and not args.api_only

    start_all_services(
        monitor=monitor,
        api=api,
        frontend=frontend,
        api_host=args.api_host,
        api_port=args.api_port,
        api_reload=not args.no_reload,
    )
