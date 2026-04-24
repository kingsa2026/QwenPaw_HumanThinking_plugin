import os
import glob

assets_dir = "/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/assets"

# Check all JS files for human_thinking
print("Checking all JS files for human_thinking:")
for f in glob.glob(os.path.join(assets_dir, "*.js")):
    try:
        with open(f, "r", encoding="utf-8", errors="ignore") as ff:
            content = ff.read()
        if "human_thinking" in content:
            print(f"  ✓ {os.path.basename(f)} - FOUND")
        else:
            print(f"  ✗ {os.path.basename(f)} - NOT FOUND")
    except:
        pass

# Check if there's a backup file
print("\nChecking backup files:")
for f in glob.glob(os.path.join(assets_dir, "*.humanthinking.bak")):
    print(f"  {os.path.basename(f)}")
