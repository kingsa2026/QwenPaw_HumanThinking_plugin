import os
import glob

assets_dir = "/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets"
for f in glob.glob(os.path.join(assets_dir, "*.js")):
    try:
        with open(f, "r", encoding="utf-8", errors="ignore") as ff:
            content = ff.read()
        if "human_thinking" in content:
            print(f"Found in: {os.path.basename(f)}")
    except:
        pass
