import sys
sys.path.insert(0, "/root/.qwenpaw/venv/lib/python3.12/site-packages")
from qwenpaw.app._app import app

print("All routes:")
for r in app.routes:
    path = getattr(r, 'path', str(r))
    if 'human' in str(path).lower() or 'plugin' in str(path).lower():
        print(f"  {path}")
