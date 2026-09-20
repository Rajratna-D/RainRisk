"""
RainRisk: Production Web Application One-Click Launcher

Starts the high-performance FastAPI server serving both the REST API and
the compiled React/Vite frontend bundle, and automatically opens your default browser.
"""

import os
import sys
import webbrowser
import uvicorn

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from backend.main import app

def main():
    port = 8008
    url = f"http://localhost:{port}"
    print("=" * 70)
    print("  RainRisk: Climate Risk Intelligence Platform (React + FastAPI)")
    print("=" * 70)
    print(f"  [+] Serving interactive web platform at: {url}")
    print("  [+] Press CTRL+C to terminate.")
    print("=" * 70)

    webbrowser.open(url)
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    main()
