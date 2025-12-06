import os
import json

EXTRACTED_DIR = "extracted"
pool = {
    "claims": [],
    "methods": [],
    "evidence": [],
    "explicit_limitations": [],
    "implicit_limitations": [],
    "datasets": [],
    "contradictions": []
}

files = [f for f in os.listdir(EXTRACTED_DIR) if f.endswith("_structured.json")]

for fname in files:
    with open(os.path.join(EXTRACTED_DIR, fname), "r") as f:
        data = json.load(f)

    for key in pool.keys():
        items = data.get(key, [])
        pool[key].extend(items)

with open("curated_pool.json", "w") as f:
    json.dump(pool, f, indent=2)

print("[Merge] Combined all extracted information into curated_pool.json")

