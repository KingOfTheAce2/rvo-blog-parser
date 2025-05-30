import requests
import json
from datasets import Dataset
from huggingface_hub import login
from datetime import datetime

HF_REPO = "vGassen/rvo-blogs"
API_URL = "https://www.rvo.nl/api/v1/opendata/blogs"
BASE_URL = "https://www.rvo.nl"

def clean_blog(blog):
    return {
        "id": blog.get("id"),
        "title": blog.get("title"),
        "summary": blog.get("intro"),
        "date": blog.get("created"),
        "url": BASE_URL + blog.get("url", ""),
    }

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
