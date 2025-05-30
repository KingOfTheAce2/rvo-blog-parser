import os
import json
import requests
from datasets import Dataset
from huggingface_hub import HfFolder, login

HF_REPO = "vGassen/Dutch-RVO-blogs"  # ← change to your actual repo
HF_TOKEN = os.getenv("HF_TOKEN")

def fetch_rvo_blogs():
    """Simulate RVO blog API fetching with pagination."""
    all_blogs = []
    page = 1

    print("[INFO] Starting RVO sync...")
    print("[INFO] Fetching all RVO blogs with pagination...")

    while True:
        print(f"[INFO] Fetching page {page}...")
        # Simulated API call — replace this with real logic
        response = {"blogs": []}  # ← placeholder response
        blogs = response.get("blogs", [])

        if not blogs:
            break

        all_blogs.extend(blogs)
        page += 1

    print(f"[INFO] Total blogs fetched: {len(all_blogs)}")
    return all_blogs

def save_jsonl(data, path):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def main():
    # Set token
    if HF_TOKEN:
        HfFolder.save_token(HF_TOKEN)
        login(token=HF_TOKEN)

    blogs = fetch_rvo_blogs()

    if not blogs:
        print("[WARN] No blogs found. Skipping upload.")
        return

    jsonl_path = "rvo_blogs.jsonl"
    save_jsonl(blogs, jsonl_path)

    if os.path.getsize(jsonl_path) == 0:
        print("[WARN] JSONL file is empty. Skipping dataset creation.")
        return

    print("[INFO] Uploading to Hugging Face...")

    dataset = Dataset.from_json(jsonl_path)
    dataset.push_to_hub(HF_REPO)
    print("[INFO] Upload complete.")

if __name__ == "__main__":
    main()
