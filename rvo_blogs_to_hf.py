import requests
import json
from datasets import Dataset
from huggingface_hub import HfApi
from datetime import datetime

# Print with flush for GitHub logs
print = lambda *args, **kwargs: __builtins__.print(*args, **kwargs, flush=True)

HF_REPO = "vGassen/Dutch-RVO-blogs"
API_URL = "https://www.rvo.nl/api/v1/opendata/blogs"


def fetch_blog_data():
    print("[INFO] Fetching all RVO blogs with pagination...")
    all_blogs = []
    page = 1
    page_size = 100

    while True:
        print(f"[INFO] Fetching page {page}...")
        resp = requests.get(f"{API_URL}?page={page}&pageSize={page_size}")
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch page {page}: {resp.status_code}")
        data = resp.json()
        if not data:
            break
        all_blogs.extend(data)
        page += 1

    print(f"[INFO] Total blogs fetched: {len(all_blogs)}")
    return all_blogs


def normalize_blog(blog):
    return {
        "id": blog.get("id"),
        "title": blog.get("title"),
        "summary": blog.get("intro"),
        "date": blog.get("created"),
        "url": f"https://www.rvo.nl{blog.get('url')}" if blog.get("url") else None,
    }


def save_to_jsonl(data, path="rvo_blogs.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[INFO] Saved {len(data)} entries to {path}")


def main():
    print("[INFO] Starting RVO sync...")
    raw_blogs = fetch_blog_data()
    parsed_blogs = [normalize_blog(b) for b in raw_blogs if b.get("title") and b.get("intro")]

    if not parsed_blogs:
        print("[ERROR] No valid blog data found.")
        return

    save_to_jsonl(parsed_blogs)

    print("[INFO] Uploading to Hugging Face...")
    dataset = Dataset.from_json("rvo_blogs.jsonl")
    dataset.push_to_hub(HF_REPO)
    print("[INFO] Upload complete.")


if __name__ == "__main__":
    main()
