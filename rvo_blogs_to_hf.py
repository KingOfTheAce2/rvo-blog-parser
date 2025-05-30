import requests
from bs4 import BeautifulSoup
import json
from datasets import Dataset
from huggingface_hub import HfFolder
import os
import sys

# ✅ Force Python to flush output for GitHub Actions logs
print = lambda *args, **kwargs: __builtins__.print(*args, **kwargs, flush=True)

HF_REPO = "vGassen/rvo-blogs"
SITEMAP_URL = "https://www.rvo.nl/sitemap/blogs/1"

def fetch_blog_urls():
    resp = requests.get(SITEMAP_URL)
    if resp.status_code != 200:
        raise Exception(f"Failed to fetch sitemap: {resp.status_code}")
    soup = BeautifulSoup(resp.content, "xml")
    return [loc.text for loc in soup.find_all("loc")]

def scrape_blog(url):
    print(f"[INFO] Scraping: {url}")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[WARN] Failed to fetch {url}: {e}")
        return None

    page = BeautifulSoup(r.text, "html.parser")
    title = page.find("h1")
    date = page.find("meta", {"property": "article:published_time"})
    article = page.find("article")

    return {
        "url": url,
        "title": title.get_text(strip=True) if title else None,
        "date": date["content"] if date else None,
        "text": article.get_text(separator="\n", strip=True) if article else None
    }

def save_to_jsonl(data, path="rvo_blogs.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[INFO] Saved {len(data)} entries to {path}")

def main():
    print("[INFO] Starting RVO sync...")

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise ValueError("HF_TOKEN environment variable not set")
    HfFolder.save_token(hf_token)

    urls = fetch_blog_urls()
    print(f"[INFO] Found {len(urls)} blog URLs")

    blogs = []
    for url in urls:
        blog = scrape_blog(url)
        if blog and blog["text"]:
            blogs.append(blog)

    if not blogs:
        print("[WARN] No blogs with content were fetched. Aborting upload.")
        return

    save_to_jsonl(blogs)

    print("[INFO] Uploading to Hugging Face...")
    dataset = Dataset.from_json("rvo_blogs.jsonl")
    dataset.push_to_hub(HF_REPO)

if __name__ == "__main__":
    main()
