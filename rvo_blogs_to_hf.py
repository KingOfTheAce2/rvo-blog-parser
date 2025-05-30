import requests
import json
from datasets import Dataset
from bs4 import BeautifulSoup
from huggingface_hub import HfApi
from datetime import datetime
import time

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


def scrape_article_text(url):
    if not url:
        return None
    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            print(f"[WARNING] Failed to fetch article content at {url}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")
        article = soup.find("article")
        if not article:
            return None

        # Join all paragraph text inside article
        text = "\n".join([p.get_text(strip=True) for p in article.find_all("p")])
        return text.strip() if text else None
    except Exception as e:
        print(f"[ERROR] Exception while scraping {url}: {e}")
        return None


def normalize_blog(blog):
    url = f"https://www.rvo.nl{blog.get('url')}" if blog.get("url") else None
    article = scrape_article_text(url)
    return {
        "id": blog.get("id"),
        "title": blog.get("title"),
        "summary": blog.get("intro"),
        "date": blog.get("created"),
        "url": url,
        "article": article,
    }


def save_to_jsonl(data, path="rvo_blogs.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[INFO] Saved {len(data)} entries to {path}")


def main():
    print("[INFO] Starting RVO sync...")
    raw_blogs = fetch_blog_data()
    parsed_blogs = []

    for blog in raw_blogs:
        if blog.get("title") and blog.get("intro"):
            parsed = normalize_blog(blog)
            parsed_blogs.append(parsed)
            print(f"[INFO] Processed blog: {parsed['title']}")
            time.sleep(0.5)  # Be polite with scraping

    if not parsed_blogs:
        print("[WARNING] No valid blog data found, but continuing anyway.")

    save_to_jsonl(parsed_blogs)

    print("[INFO] Uploading to Hugging Face...")
    dataset = Dataset.from_json("rvo_blogs.jsonl")
    dataset.push_to_hub(HF_REPO)
    print("[INFO] Upload complete.")


if __name__ == "__main__":
    main()
