with open("/root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/console/index.html", "r") as f:
    content = f.read()
import re
js_files = re.findall(r'src="([^"]*\.js)"', content)
print("JS files in index.html:")
for f in js_files:
    print(f"  {f}")
