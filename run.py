"""
MahaRainRisk: Unified Platform Launcher
Boots the FastAPI backend, serves the Dribbble-inspired Obsidian-Emerald dashboard,
with Smart Port Routing that automatically detects and avoids occupied ports.
"""

import os
import sys
import socket
import webbrowser
import threading
import time

# Ensure Windows terminal handles Unicode cleanly
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def find_smart_port(preferred_ports=(8008, 8080, 8888, 5000, 3000)) -> int:
    """
    Smart Port Router:
    1. Checks the $PORT environment variable (e.g. Render / Cloud).
    2. Probes preferred ports in sequence (8008, 8080, 8888, etc.), avoiding 8000.
    3. If any port is occupied, it automatically reroutes to the next open port.
    4. Fallback to OS-assigned ephemeral open port if all are occupied.
    """
    if "PORT" in os.environ:
        try:
            return int(os.environ["PORT"])
        except ValueError:
            pass

    for port in preferred_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                print(f" [!] Port {port} is occupied. Automatically checking next available port...")

    # Dynamic OS fallback: bind to 0 to ask kernel for an available open port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def open_browser_after_delay(url: str):
    time.sleep(1.8)
    print(f"\n[*] Launching MahaRainRisk Dashboard in your browser: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    import uvicorn

    is_cloud = "PORT" in os.environ or "RENDER" in os.environ or os.environ.get("ENVIRONMENT") == "production"
    host = "0.0.0.0" # Bind to all interfaces so phones on local Wi-Fi can access
    port = find_smart_port()
    server_url = f"http://localhost:{port}"

    print("=" * 76)
    print(" 🌾  MAHARAINRISK: MAHARASHTRA AGRITECH DROUGHT EARLY WARNING PLATFORM")
    print("=" * 76)
    print(" ✔  Ground Truth Telemetry : 194 Talukas • 36 Districts (2014-2026)")
    print(" ✔  Mode 1 ML Diagnostic   : 250-Tree Random Forest (98% Test Accuracy)")
    print(" ✔  Mode 2 ML Forecaster   : 30-Day Early Warning Forecaster (77% Accuracy)")
    print(" ✔  University Advisories  : MPKV Rahuri, VNMKV, Dr. PDKV, Dr. BSKKV")
    print(" ✔  Design Inspiration     : Dribbble AI Greenhouse (Obsidian-Emerald)")
    print("-" * 76)
    print(f" 🚀 Server running at       : {server_url}")
    print(f" 📖 Interactive API Docs   : {server_url}/docs")
    print(f" ℹ️  Host / Port            : Binding to {host}:{port}")
    print("=" * 76)

    # Launch browser only in local interactive mode
    if not is_cloud and os.environ.get("NO_BROWSER", "0") != "1":
        threading.Thread(target=open_browser_after_delay, args=(f"http://127.0.0.1:{port}",), daemon=True).start()

    uvicorn.run("backend.main:app", host=host, port=port, log_level="info", reload=False)
