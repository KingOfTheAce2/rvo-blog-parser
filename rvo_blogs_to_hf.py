import requests
import json
from datasets import Dataset
from huggingface_hub import login

# Always flush print so GitHub Actions logs show up live
print = lambda *args, **kwargs: __builtins__.print(*args, **kwargs, flush=True)

HF_REPO = "vGassen/Dutch-RVO-blogs"
API_URL = "https://www.rvo.nl/api/v1/opendata/blogs"
BASE_URL = "https://www.rvo.nl"

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
        "summary": blog.get("intro"),
        "date": blog.get("created"),
        "url": BASE_URL + blog.get("url", ""),
        "content": None,
        "author": None
    }

def save_to_jsonl(data, path="rvo_blogs.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def main():
    print("[INFO] Starting RVO blog sync...")

    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable not set")
    login(token=hf_token)

    blogs = fetch_rvo_blogs()
    cleaned = [clean_blog(b) for b in blogs]
    print(f"[INFO] Cleaned {len(cleaned)} blogs")
    save_to_jsonl(cleaned)

    dataset = Dataset.from_json("rvo_blogs.jsonl")
    print("[INFO] Uploading dataset to HuggingFace...")
    dataset.push_to_hub(HF_REPO)
    print("[✅] Upload complete.")

if __name__ == "__main__":
    import os
    main()
