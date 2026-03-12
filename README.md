# Research Agent CLI

A minimal CLI tool that generates structured market research briefs by combining Brave Search results with LLM analysis.

## Setup

```bash
pip install -r requirements.txt
export BRAVE_API_KEY="your-brave-api-key"
```

## Usage

```bash
python research_agent.py --company "Acme Corp" --industry "cloud computing" --audience "enterprise CTOs"
```

This produces a `research_brief.md` file with:

- **Market Overview** — market size and growth rate with sources
- **Key Industry Trends** — 3-5 relevant trends
- **Competitive Landscape** — 3 competitors with positioning
- **Relevant Statistics** — 3-5 data points with sources

### Options

| Flag | Required | Description |
|------|----------|-------------|
| `--company` | Yes | Company name to research |
| `--industry` | Yes | Industry or sector |
| `--audience` | Yes | Target audience |
| `--search-count` | No | Number of Brave search results to fetch per query (default: `10`) |
| `--save-search-json` | No | Save the raw search data payload as pretty JSON |
| `--output` | No | Output file path (default: `research_brief.md`) |

### Examples

```bash
# SaaS startup targeting SMBs
python research_agent.py --company "Notion" --industry "productivity software" --audience "small business teams"

# Custom output path
python research_agent.py --company "Stripe" --industry "fintech" --audience "developers" --output stripe_brief.md

# Increase Brave result count per query
python research_agent.py --company "Datadog" --industry "observability" --audience "platform engineers" --search-count 15

# Save raw search evidence for auditing
python research_agent.py --company "HubSpot" --industry "CRM software" --audience "marketing teams" --save-search-json /tmp/research-search-data.json
```

## How It Works

1. Takes company name, industry, and target audience as inputs
2. Performs 4 Brave Search API queries (market size, trends, competitors, statistics) using the configured result count
3. Passes all search results to an LLM for structured extraction
4. Optionally writes the raw search data payload to JSON for auditing
5. Writes the resulting markdown brief to a file
