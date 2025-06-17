import json
import os
from pathlib import Path
from typing import List, Dict
import urllib.request
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from huggingface_hub import HfApi
except Exception:  # huggingface_hub might not be available
    HfApi = None

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

# Configure your Hugging Face dataset repo
HF_DATASET_REPO = os.environ.get("HF_DATASET_REPO") or "vGassen/Dutch-RVO-blogs"
HF_TOKEN = os.environ.get("HF_TOKEN")
HF_DATASET_VERSION = os.environ.get("HF_DATASET_VERSION") or "1.0.0"

def clean_html_content(content: str) -> str:
    """Remove HTML tags and clean up text content."""
    if not content:
        return ""
    soup = BeautifulSoup(content, 'html.parser')
    # Remove script and style elements
    for element in soup(["script", "style"]):
        element.decompose()
    text = soup.get_text(separator=' ').strip()
    # Normalize whitespace
    return ' '.join(text.split())

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_items(url: str) -> List[Dict]:
    """Fetch JSON items from the given endpoint with retry logic."""
    try:
        with urllib.request.urlopen(url) as response:
            data = json.load(response)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Request failed: {exc}") from exc

    # Some endpoints may nest results inside "items" or "data"
    if isinstance(data, dict):
        return data.get("items") or data.get("data") or []
    return data

def make_entries(item: Dict, source: str) -> List[Dict]:
    """Convert one API item into dataset entries with cleaned content."""
    entries = []
    url = item.get("url") or item.get("link") or ""
    if url and not url.startswith("http"):
        url = BASE_URL + url

    title = clean_html_content(item.get("title") or "")
    summary = clean_html_content(item.get("intro") or item.get("summary") or "")
    content = clean_html_content(item.get("body") or item.get("content") or "")

    for text, content_type in [(title, "title"), (summary, "summary"), (content, "full_content")]:
        if text:
            entries.append({
                "url": url,
                "content": text,
                "source": source,
                "content_type": content_type
            })
    return entries

def load_existing() -> set:
    """Load existing (url, content) pairs to avoid duplicates."""
    seen = set()
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    seen.add((entry["url"], entry["content"]))
                except json.JSONDecodeError:
                    print(f"Warning: Skipping invalid JSON line in {DATA_FILE}")
    return seen

def append_entries(new_entries: List[Dict]) -> None:
    """Append new entries to the dataset file, avoiding duplicates."""
    seen = load_existing()
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        for entry in new_entries:
            key = (entry["url"], entry["content"])
            if key not in seen:
                try:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    seen.add(key)
                except Exception as e:
                    print(f"Warning: Failed to write entry {entry['url']}: {e}")

def push_to_hf() -> None:
    """Upload the dataset to Hugging Face with metadata."""
    if not HF_TOKEN:
        print("HF_TOKEN not set; skipping upload")
        return
    if HfApi is None:
        print("huggingface_hub not installed; skipping upload")
        return

    api = HfApi(token=HF_TOKEN)
    
    # Prepare dataset metadata
    metadata = {
        "language": "nl",
        "license": "cc-by-4.0",
        "tags": ["dutch", "government", "rvo"],
        "version": HF_DATASET_VERSION,
        "description": "Dutch RVO (Netherlands Enterprise Agency) content dataset",
        "sources": list(ENDPOINTS.keys())
    }
    
    try:
        # Upload the dataset file
        print(f"Uploading dataset to {HF_DATASET_REPO}...")
        api.upload_file(
            path_or_fileobj=str(DATA_FILE),
            path_in_repo=DATA_FILE.name,
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
            commit_message=f"Update dataset to version {HF_DATASET_VERSION}"
        )
        
        # Upload metadata
        print("Uploading dataset metadata...")
        api.upload_file(
            path_or_fileobj=json.dumps(metadata, indent=2, ensure_ascii=False).encode(),
            path_in_repo="dataset-metadata.json",
            repo_id=HF_DATASET_REPO,
            repo_type="dataset",
            commit_message=f"Update metadata for version {HF_DATASET_VERSION}"
        )
        
        print("Upload completed successfully")
    except Exception as e:
        print(f"Failed to upload to HuggingFace: {e}")
        raise

def main() -> None:
    """Main function to fetch and process RVO content."""
    print("Starting RVO content synchronization...")
    all_new_entries = []
    
    for source, url in ENDPOINTS.items():
        print(f"Fetching {source} data...")
        try:
            items = fetch_items(url)
            print(f"Retrieved {len(items)} items from {source}")
            
            for item in items:
                try:
                    entries = make_entries(item, source)
                    all_new_entries.extend(entries)
                except Exception as e:
                    print(f"Warning: Failed to process item from {source}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error fetching {source}: {e}")
            continue

    print(f"Processing {len(all_new_entries)} new entries...")
    append_entries(all_new_entries)
    print("Content synchronization completed")
    
    print("Starting HuggingFace upload...")
    push_to_hf()
    print("Process completed successfully")

if __name__ == "__main__":
    main()
