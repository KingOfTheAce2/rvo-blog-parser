# Dutch RVO Blog Scraper

This project pulls all Dutch public RVO blog posts and prepares them for integration with Hugging Face Datasets.

## Structure

Each blog post is split into three dataset entries:
- `title`
- `summary`
- `content` (currently empty unless full scraping is added)

Each entry is stored as:
```json
{
  "url": "...",
  "content": "...",
  "source": "RVO-Blogs",
  "type": "title" | "summary" | "content"
}
```

## Running locally

```bash
pip install -r requirements.txt
python rvo_blog_sync.py
```

## GitHub Actions

This repo is configured to automatically fetch new blog posts every Monday.

To trigger manually, go to GitHub → Actions → *Weekly RVO Blog Sync* → Run workflow.
