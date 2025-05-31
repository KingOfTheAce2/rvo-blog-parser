import requests
import json
from datetime import datetime
from pathlib import Path

BASE_URL = "https://www.rvo.nl"
BLOG_FEED_URL = "https://www.rvo.nl/api/v1/search?fq=type:blog&rows=100"

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
DATA_FILE = DATA_DIR / "rvo_blogs.jsonl"
SOURCE = "RVO-Blogs"

def fetch_blogs():
    response = requests.get(BLOG_FEED_URL)
    response.raise_for_status()
    return response.json()["items"]

def extract_entries(blog):
    url = BASE_URL + blog["url"]
    entries = []
    for field in ["title", "intro", "id"]:  # id is used for optional full content
        if field == "id":
            content = fetch_full_content(blog["url"])  # optional, often intro only
            field_name = "content"
        else:
            content = blog[field]
            field_name = "title" if field == "title" else "summary"
        entries.append({
            "url": url,
            "content": content.strip(),
            "source": SOURCE,
            "type": field_name
        })
    return entries

def fetch_full_content(relative_url):
    # In a real case, scrape the full article if needed
    return ""  # Placeholder

def save_entries(entries):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def main():
    blogs = fetch_blogs()
    all_entries = []
    for blog in blogs:
        entries = extract_entries(blog)
        all_entries.extend(entries)
    save_entries(all_entries)

if __name__ == "__main__":
    main()
