# search-cli

A modern, fast command-line interface for querying the **Google Search Console Search Analytics API** and managing properties.

---

## Features

- 🔍 **Flexible Search Analytics Queries**: Multi-dimension grouping (`query`, `page`, `country`, `device`, `date`, `searchAppearance`).
- 🎯 **Expressive Filters**: Filter by dimension using intuitive syntax like `query contains "seo"`, `country == usa`, or regex `query regex ^top`.
- 🔐 **Dual Auth Support**:
  - **OAuth 2.0 User Flow**: Web browser login for personal/interactive usage with automatic token refresh.
  - **Service Account**: Headless authentication for automated scripts and CI/CD pipelines.
- 📊 **Multiple Output Formats**: Rich formatted terminal tables, CSV, TSV, and JSON.
- 🌐 **Property & Sitemap Management**: List verified sites, set a default property, check sitemaps status, and inspect URLs.

---

## Installation

### Prerequisites
- Python 3.9+

### Setup
```bash
# Clone or navigate to the directory
cd /path/to/search-cli

# Create a virtual environment & install in editable mode
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## Authentication Setup

### Option 1: OAuth 2.0 (Recommended for Personal / CLI Use)

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the **Google Search Console API** (Search Console API).
4. Go to **APIs & Services > Credentials** and create an **OAuth 2.0 Client ID** (Application type: *Desktop App*).
5. Download the JSON credentials file (`client_secrets.json`).
6. Run:
   ```bash
   search-cli auth login --credentials /path/to/client_secrets.json
   ```
   A browser window will open asking you to grant read access to your Search Console properties.

### Option 2: Service Account (Recommended for Headless / CI/CD)

1. In Google Cloud Console, create a **Service Account** and generate a JSON key.
2. Go to [Google Search Console](https://search.google.com/search-console) > Settings > Users and permissions.
3. Add the service account email (e.g. `service-account@project.iam.gserviceaccount.com`) as a user with **Full** or **Restricted** permissions on your property.
4. Run:
   ```bash
   search-cli auth service-account --key /path/to/service_account.json
   ```

---

## Usage Guide

### 1. View Auth Status
```bash
search-cli auth status
```

### 2. List Verified Properties
```bash
search-cli sites list
```

### 3. Set a Default Site
Avoid typing `--site` on every command:
```bash
search-cli sites default "sc-domain:example.com"
# or
search-cli sites default "https://example.com"
```

### 4. Query Search Analytics

#### Top Queries in the Last 28 Days
```bash
search-cli query --limit 20
```

#### Top Pages
```bash
search-cli query --dimension page --limit 20
```

#### Multi-Dimension Queries (Queries + Pages)
```bash
search-cli query --dimension query,page --limit 50
```

#### Date Ranges
```bash
# Last 7 days
search-cli query --days 7

# Custom date range
search-cli query --start-date 2026-01-01 --end-date 2026-01-31
```

#### Filtering
Filter syntax supports `contains`, `!contains`, `==`, `!=`, and `regex`:
```bash
# Query contains keyword
search-cli query --filter "query contains pricing"

# Query starts with "how to" using regex
search-cli query --filter "query regex ^how to"

# Exclude specific URL paths and filter by country
search-cli query \
  --dimension query,country \
  --filter "page !contains /tags/" \
  --filter "country == usa"
```

#### Search Types & Fresh Data
```bash
# Image search queries
search-cli query --search-type image

# Include fresh provisional data
search-cli query --data-state all
```

#### Sorting & Pagination
```bash
# Sort by CTR ascending or descending
search-cli query --sort-by ctr --asc
search-cli query --sort-by impressions --limit 50 --offset 50
```

#### Exporting (CSV / JSON / TSV)
```bash
# Export to CSV file
search-cli query --dimension query,page --format csv --output report.csv

# Output JSON for piping into jq
search-cli query --format json | jq '.rows[:5]'
```

### 5. Inspect a URL
Check index coverage, canonicalization, and crawl state:
```bash
search-cli inspect "https://example.com/blog/my-post"
```

### 6. View Sitemaps
```bash
search-cli sitemaps list
```

---

## Configuration

You can view and set configuration defaults at any time:
```bash
# View configuration
search-cli config list

# Set default site property
search-cli config set default_site "sc-domain:example.com"

# Clear credentials
search-cli auth logout
```

---

## Development & Testing

Run tests with pytest:
```bash
pytest
```
