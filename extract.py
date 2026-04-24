import zipfile
import os

zip_path = "/tmp/HumanThinking.zip"
extract_to = "/root/.qwenpaw/plugins/HumanThinking"

os.makedirs(extract_to, exist_ok=True)
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(extract_to)

print("Extracted files:")
for root, dirs, files in os.walk(extract_to):
    for f in files:
        print(os.path.join(root, f))
