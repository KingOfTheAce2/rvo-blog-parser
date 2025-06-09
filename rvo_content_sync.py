import json
import os
from pathlib import Path
from typing import List, Dict

import requests
from huggingface_hub import HfApi

# Mapping of content sources to their Open Data API endpoints
ENDPOINTS = {
    "RVO Blogs": "https://www.rvo.nl/api/v1/opendata/blogs",
    "Evenementen": "https://www.rvo.nl/api/v1/opendata/events",
    "Nieuws": "https://www.rvo.nl/api/v1/opendata/articles",
    "Onderwerpen": "https://www.rvo.nl/api/v1/opendata/subjects",
    "Overzichten": "https://www.rvo.nl/api/v1/opendata/summary",
    "Praktijkverhalen": "https://www.rvo.nl/api/v1/opendata/showcases",
    "Subsidies en financiering": "https://www.rvo.nl/api/v1/opendata/subsidies",
}

BASE_URL = "https://www.rvo.nl"
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "rvo_content.jsonl"

# Configure your Hugging Face dataset repo. Treat an empty environment variable
# as if it was not provided so the default is used. The default repository is
# ``vGassen/Dutch-RVO-blogs``.
HF_DATASET_REPO = os.environ.get("HF_DATASET_REPO") or "vGassen/Dutch-RVO-blogs"
HF_TOKEN = os.environ.get("HF_TOKEN")


def fetch_items(url: str) -> List[Dict]:
    """Fetch JSON items from the given endpoint."""
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    # Some endpoints may nest results inside "items"
    if isinstance(data, dict):
        return data.get("items") or data.get("data") or []
    return data


def make_entries(item: Dict, source: str) -> List[Dict]:
    """Convert one API item into up to three dataset entries."""
    entries = []
    url = item.get("url") or item.get("link") or ""
    if url and not url.startswith("http"):
        url = BASE_URL + url

    title = item.get("title") or ""
    summary = item.get("intro") or item.get("summary") or ""
    content = item.get("body") or item.get("content") or ""

    for text in [title, summary, content]:
        if text:
            entries.append({"url": url, "content": text.strip(), "source": source})
    return entries


def load_existing() -> set:
    """Load existing (url, content) pairs to avoid duplicates."""
    seen = set()
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                seen.add((entry["url"], entry["content"]))
    return seen


def append_entries(new_entries: List[Dict]) -> None:
    seen = load_existing()
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        for entry in new_entries:
            key = (entry["url"], entry["content"])
            if key not in seen:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                seen.add(key)


def push_to_hf() -> None:
    """Upload the JSONL file to Hugging Face."""
    if not HF_TOKEN:
        print("HF_TOKEN not set; skipping upload")
        return
    api = HfApi(token=HF_TOKEN)
    api.upload_file(
        path_or_fileobj=str(DATA_FILE),
        path_in_repo=DATA_FILE.name,
        repo_id=HF_DATASET_REPO,
        repo_type="dataset",
    )


def main() -> None:
    all_new_entries = []
    for source, url in ENDPOINTS.items():
        try:
            items = fetch_items(url)
        except Exception as e:
            print(f"Failed to fetch {source}: {e}")
            continue
        for item in items:
            all_new_entries.extend(make_entries(item, source))

    append_entries(all_new_entries)
    push_to_hf()


if __name__ == "__main__":
    main()
