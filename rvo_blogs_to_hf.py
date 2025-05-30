import requests
import json
from datasets import Dataset
from huggingface_hub import login
from bs4 import BeautifulSoup
import os

# Force print flushing for GitHub Action logs
print = lambda *args, **kwargs: __builtins__.print(*args, **kwargs, flush=True)

HF_REPO = "vGassen/rvo-blogs"
API_URL = "https://www.rvo.nl/api/v1/opendata/blogs"
BASE_URL = "https://www.rvo.nl"

def fetch_rvo_blogs():
    print("[INFO] Fetching blogs from RVO API...")
    response = requests.get(API_URL)
    response.raise_for_status()
    data = response.json()
    print(f"[INFO] Received {len(data)} blogs")
    return data

def extract_full_text(slug):
    full_url = BASE_URL + slug
    try:
        r = requests.get(full_url)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "html.parser")

        # Look for content area (RVO uses class "rte" for main body)
        article = soup.find("div", class_="rte")
        if not article:
            article = soup.find("article")
        if not article:
            print(f"[WARN] No main content found at {full_url}")
            return None

        return article.get_text(separator="\n").strip()
    except Exception as e:
        print(f"[WARN] Failed to extract full text from {full_url}: {e}")
        return None

def clean_blog(blog):
    slug = blog.get("url", "")
    full_text = extract_full_text(slug)

    return {
        "id": blog.get("id"),
        "title": blog.get("title"),
        "summary": blog.get("intro"),
        "date": blog.get("created"),
        "url": BASE_URL + slug,
        "text": full_text
    }

def save_to_jsonl(data, path="rvo_blogs.jsonl"):
    print(f"[INFO] Saving {len(data)} blogs to {path}")
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
    cleaned = [clean_blog(b) for b in blogs if b.get("url")]
    save_to_jsonl(cleaned)

    print("[INFO] Uploading dataset to HuggingFace...")
    dataset = Dataset.from_json("rvo_blogs.jsonl")
    dataset.push_to_hub(HF_REPO)
    print("[✅] Upload complete.")

if __name__ == "__main__":
    main()
