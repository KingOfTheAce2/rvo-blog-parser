import requests
import json
from datasets import Dataset
from huggingface_hub import login
from datetime import datetime

HF_REPO = "vGassen/rvo-blogs"
API_URL = "https://www.rvo.nl/api/v1/opendata/blogs"

def fetch_rvo_blogs():
    print("[INFO] Fetching blogs from RVO...")
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    print(f"[INFO] Received {len(data)} blogs")
    return data

def clean_blog(blog):
    return {
        "id": blog.get("id"),
        "title": blog.get("title"),
        "summary": blog.get("summary"),
        "content": blog.get("content"),
        "author": blog.get("author"),
        "date": blog.get("date")
    }

def save_to_jsonl(data, path="rvo_blogs.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def main():
    print("[INFO] Starting RVO blog sync...")
    blogs = fetch_rvo_blogs()
    cleaned = [clean_blog(b) for b in blogs]
    save_to_jsonl(cleaned)

    dataset = Dataset.from_json("rvo_blogs.jsonl")
    dataset.push_to_hub(HF_REPO)
    print("[INFO] Upload complete.")

if __name__ == "__main__":
    main()
