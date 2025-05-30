import requests
import json
from datasets import Dataset
from huggingface_hub import login
from bs4 import BeautifulSoup
import os

print = lambda *args, **kwargs: __builtins__.print(*args, **kwargs, flush=True)

HF_REPO = "vGassen/Dutch-RVO-blogs"
API_URL = "https://www.rvo.nl/api/v1/opendata/blogs"
BASE_URL = "https://www.rvo.nl"

def fetch_rvo_blogs():
    print("[INFO] Fetching all RVO blogs with pagination...")
    page = 1
    all_blogs = []

    while True:
        url = f"{API_URL}?page={page}"
        response = requests.get(url)
        response.raise_for_status()
        batch = response.json()

        if not batch:
            break

        print(f"[INFO] Fetched page {page} with {len(batch)} blogs")
        all_blogs.extend(batch)
        page += 1

    print(f"[INFO] Total blogs fetched: {len(all_blogs)}")
    return all_blogs

def extract_full_text(slug):
    try:
        r = requests.get(BASE_URL + slug)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")
        article = soup.find("div", class_="rte") or soup.find("article")
        return article.get_text(separator="\n").strip() if article else None
    except Exception as e:
        print(f"[WARN] Failed to extract full text: {e}")
        return None

def clean_blog(blog):
    return {
        "id": blog.get("id"),
        "title": blog.get("title"),
        "summary": blog.get("intro"),
        "date": blog.get("created"),
        "url": BASE_URL + blog.get("url", ""),
        "text": extract_full_text(blog.get("url", ""))
    }

def save_to_jsonl(data, path="rvo_blogs.jsonl"):
    print(f"[INFO] Saving {len(data)} entries to {path}")
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            json.dump(item, f, ensure_ascii=False)
            f.write("\n")

def main():
    print("[INFO] Starting RVO sync...")
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN is not set")
    login(token=hf_token)

    blogs = fetch_rvo_blogs()
    cleaned = [clean_blog(b) for b in blogs]
    save_to_jsonl(cleaned)

    print("[INFO] Uploading to Hugging Face...")
    dataset = Dataset.from_json("rvo_blogs.jsonl")
    dataset.push_to_hub(HF_REPO)
    print("[✅] Done")

if __name__ == "__main__":
    main()
