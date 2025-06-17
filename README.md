# Dutch RVO Content Sync

This project gathers public content from the Dutch RVO website and publishes it as a dataset on Hugging Face.

## Structure

Each public item from RVO is converted into one or more simple entries. For every
source (blogs, events, news, etc.) we create a row for the title, the summary
and the full text.  Every row only contains the URL of the item, the extracted
text and the source name.  The dataset therefore consists of many short
snippets rather than a single object per page.

Entries are stored in a JSON Lines file with the following format:

```json
{
  "url": "...",
  "content": "...",
  "source": "RVO Blogs | Evenementen | Nieuws | Onderwerpen | Overzichten | Praktijkverhalen | Subsidies en financiering"
}
```

## Running locally

```bash
pip install -r requirements.txt  # optional: only needed for upload features
python rvo_content_sync.py
```

Set the `HF_TOKEN` environment variable to enable uploading to Hugging Face.
By default the data is pushed to `vGassen/Dutch-RVO-blogs`, even though it
contains more than just blogs.  You can override the destination by setting the
`HF_DATASET_REPO` environment variable.

## GitHub Actions

The repository contains a workflow that synchronizes the content every two days and uploads the dataset to Hugging Face.
