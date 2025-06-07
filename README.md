# Dutch RVO Content Sync

This project gathers public content from the Dutch RVO website and publishes it as a dataset on Hugging Face.

## Structure

Every item (blog, event, article, etc.) is represented by three separate dataset entries containing its title, summary and full content. Each entry is stored as JSON lines in the following format:

```json
{
  "url": "...",
  "content": "...",
  "source": "RVO Blogs | Evenementen | Nieuws | Onderwerpen | Overzichten | Praktijkverhalen | Subsidies en financiering"
}
```

## Running locally

```bash
pip install -r requirements.txt
python rvo_content_sync.py
```

Set the `HF_TOKEN` and optionally `HF_DATASET_REPO` environment variables to upload the data to your Hugging Face account.

## GitHub Actions

The repository contains a workflow that synchronizes the content every two days and uploads the dataset to Hugging Face.
