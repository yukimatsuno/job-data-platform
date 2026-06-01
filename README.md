# job-data-platform

A Python project for scraping job listings, transforming them into structured job data, storing them in MongoDB, and serving a web UI with FastAPI.

## What this project does

- Scrapes job posting data from sources such as HERP and saves results as CSV/JSON.
- Loads and serves job data from MongoDB in a searchable web interface.
- Uses FastAPI with Jinja2 templates for list and detail pages.
- Supports optional Azure OpenAI enrichment for normalization and classification.

## Project structure

- `app/` - FastAPI application code and MongoDB connection.
- `templates/` - HTML templates for job list, job details, and about pages.
- `static/` - CSS and static assets.
- `*.py` and `*.ipynb` - scraping, transformation, and import scripts.

## Requirements

- Python 3.10+
- MongoDB access
- `requirements.txt`

## Setup

1. Create a `.env` file in the project root.

Example `.env`:

```env
MONGO_URI=your_mongo_connection_string
DB_NAME=job_data_platform
COLLECTION_NAME=herp
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
```

2. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

3. Populate MongoDB with scraped data.
   - Use the notebook and scripts in the repository to scrape job listings.
   - The app reads from the configured MongoDB collection.

4. Start the FastAPI server:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5. Open the app in your browser:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/about`

## Notes

- `.gitignore` already excludes `.env`, so credentials are not pushed to GitHub.
- `app/db.py` loads environment variables with `python-dotenv`.
- `05_llm_transform_batch.py` requires Azure OpenAI credentials when used.

## Optional scripts

- `01_herp_scraper.ipynb` - scraping notebook.
- `03_scrape_job_url.py` - scrape job URLs.
- `04_batch_scrape_job_cards.py` - scrape job card details in batch.
- `05_llm_transform_batch.py` - normalize and classify job data with Azure OpenAI.
- `06_import_llm_outputs_to_mongo.py` - import transformed results into MongoDB.
