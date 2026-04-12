"""
CircuitMind AI - Launcher
Starts both the Flask server AND a public localhost.run tunnel simultaneously.
Run this file instead of app.py to get a public URL.
"""
import subprocess
import threading
import time
import sys
import os
import socket

PORT = 5000

# ── Find local IP ──────────────────────────────────────────────
def get_local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return '127.0.0.1'

# ── localhost.run SSH tunnel ──────────────────────────────────
public_url = None

def run_tunnel():
    global public_url
    print("  [tunnel] Connecting to localhost.run...")
    while True:
        try:
            proc = subprocess.Popen(
                ["ssh",
                 "-o", "StrictHostKeyChecking=no",
                 "-o", "ServerAliveInterval=30",
                 "-o", "ExitOnForwardFailure=yes",
                 "-R", f"80:localhost:{PORT}",
                 "nokey@localhost.run"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                # Match ONLY real tunnel URLs: *.lhr.life
                if ".lhr.life" in line:
                    for token in line.split():
                        t = token.rstrip(",.")
                        if t.startswith("https://") and ".lhr.life" in t:
                            public_url = t
                            print(f"\n  {'='*56}")
                            print(f"  PUBLIC URL (share with anyone):")
                            print(f"  >>> {public_url} <<<")
                            print(f"  {'='*56}\n")
                            break
            proc.wait()
        except FileNotFoundError:
            print("  [tunnel] ERROR: 'ssh' not found. OpenSSH must be installed.")
            break
        except Exception as e:
            print(f"  [tunnel] Disconnected ({e}). Reconnecting in 5s...")
        time.sleep(5)

# ── Flask server ──────────────────────────────────────────────
def run_flask():
    # Import app from app.py (same directory)
    sys.path.insert(0, os.path.dirname(__file__))
    from app import app
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

# ── Main ──────────────────────────────────────────────────────
if __name__ == '__main__':
    local_ip = get_local_ip()

    print()
    print("  +----------------------------------------------------------+")
    print("  |          CircuitMind AI  -  Starting...                  |")
    print("  +----------------------------------------------------------+")
    print(f"  |  Local  (you):        http://localhost:{PORT}               |")
    print(f"  |  Network (WiFi):      http://{local_ip}:{PORT}         |")
    print("  |  Public URL:          printing below when ready...      |")
    print("  +----------------------------------------------------------+")
    print()

    # Start tunnel in background
    tunnel_thread = threading.Thread(target=run_tunnel, daemon=True)
    tunnel_thread.start()

    # Start Flask (blocking — keeps process alive)
    run_flask()
