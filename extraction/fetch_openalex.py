import requests
import json
import os
from urllib.parse import quote

OUT_DIR = "raw_papers"
os.makedirs(OUT_DIR, exist_ok=True)

BASE_URL = "https://api.openalex.org/works"


def fetch_papers(query, max_results=5):
    """
    Fetch papers from OpenAlex based on a topic search.
    Saves each paper into raw_papers/ as paper_1.json, paper_2.json, ...
    """

    encoded = quote(query)
    url = f"{BASE_URL}?search={encoded}&per-page={max_results}"
    print(f"[OpenAlex] Fetching: {url}")

    response = requests.get(url)

    if response.status_code != 200:
        print(f"[ERROR] OpenAlex returned status code {response.status_code}")
        return

    data = response.json()
    results = data.get("results", [])

    print(f"[OpenAlex] Found {len(results)} papers")

    paper_count = 0
    for i, paper in enumerate(results):
        abstract = rebuild_abstract(paper.get("abstract_inverted_index"))
        
        # Skip papers without abstracts
        if not abstract or len(abstract.strip()) == 0:
            print(f"[OpenAlex] Skipping paper {i+1} - no abstract available")
            continue

        cleaned = {
            "id": paper.get("id"),
            "title": paper.get("title"),
            "abstract": abstract,
            "year": paper.get("publication_year"),
            "authors": [a["author"]["display_name"] for a in paper.get("authorships", [])],
            "doi": paper.get("doi"),
            "concepts": [c["display_name"] for c in paper.get("concepts", [])],
        }

        paper_count += 1
        out_path = os.path.join(OUT_DIR, f"paper_{paper_count}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)

        print(f"[OpenAlex] Saved {out_path} (title: {paper.get('title', '')[:60]}...)")


def rebuild_abstract(inverted_index):
    """
    Convert OpenAlex's inverted index abstract format into normal text.
    """
    if not inverted_index:
        return ""

    # Find total length of abstract
    max_pos = max(pos for positions in inverted_index.values() for pos in positions)
    words = [""] * (max_pos + 1)

    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word

    return " ".join(words)


if __name__ == "__main__":
    # EXAMPLE QUERY — YOU CAN CHANGE THIS.
    fetch_papers("battery state of health machine learning", max_results=5)

