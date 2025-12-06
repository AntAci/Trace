import os
import json
from extract_groq import extract_structure

RAW_DIR = "raw_papers"
OUT_DIR = "extracted"

os.makedirs(OUT_DIR, exist_ok=True)

papers = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]

for filename in papers:
    print(f"\n[Extract] Processing {filename}")

    with open(os.path.join(RAW_DIR, filename), "r") as f:
        paper = json.load(f)

    title = paper.get("title", "")
    abstract = paper.get("abstract", "")

    if not abstract or len(abstract.strip()) == 0:
        print(f"[Extract] Skipping {filename} - no abstract available")
        continue

    structured = extract_structure(abstract, title)

    out_file = os.path.join(OUT_DIR, filename.replace(".json", "_structured.json"))
    with open(out_file, "w") as f:
        json.dump(structured, f, indent=2)

    print(f"[Extract] Saved to {out_file}")

