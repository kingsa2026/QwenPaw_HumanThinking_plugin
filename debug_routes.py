import sys
sys.path.insert(0, "/root/.qwenpaw/venv/lib/python3.12/site-packages")

try:
    from qwenpaw.app._app import app
    print("Routes registered in app:")
    for route in app.routes:
        if hasattr(route, 'path'):
            if 'human' in route.path.lower() or 'plugin' in route.path.lower():
                print(f"  {route.path}")
except Exception as e:
    print(f"Error: {e}")
