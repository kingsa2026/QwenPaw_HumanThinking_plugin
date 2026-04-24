import sys
sys.path.insert(0, "/root/.qwenpaw/venv/lib/python3.12/site-packages")

from qwenpaw.app._app import app

print("Routes with 'human' or 'plugin':")
for route in app.routes:
    path = getattr(route, "path", "")
    if "human" in path.lower() or "plugin" in path.lower():
        print(f"  {path}")
