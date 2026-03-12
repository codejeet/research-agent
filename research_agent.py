#!/usr/bin/env python3
"""Minimal research agent CLI that generates structured market research briefs."""

import argparse
import json
import os
import sys

import requests


BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
LLM_BASE_URL = "http://127.0.0.1:3456/v1"
LLM_MODEL = "claude-opus-4"
SEARCH_DATA_KEYS = ("market_size", "trends", "competitors", "statistics")


def brave_search(query, api_key, count=10):
    """Perform a web search using the Brave Search API."""
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    }
    params = {"q": query, "count": count}
    resp = requests.get(BRAVE_SEARCH_URL, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "description": item.get("description", ""),
        })
    return results


def call_llm(prompt):
    """Send a prompt to the OpenAI-compatible LLM API and return the response."""
    resp = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers={"Content-Type": "application/json", "Authorization": "Bearer not-needed"},
        json={
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def build_search_queries(company, industry, audience):
    """Build the 4 structured search queries."""
    return {
        "market_size": f"{industry} market size growth rate {audience} 2024 2025",
        "trends": f"{industry} industry trends {audience} 2024 2025",
        "competitors": f"{company} competitors {industry} {audience}",
        "statistics": f"{industry} statistics data {audience} market research",
    }


def format_search_results(results):
    """Format search results into a readable string for the LLM."""
    lines = []
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. [{r['title']}]({r['url']})")
        lines.append(f"   {r['description']}")
    return "\n".join(lines)


def normalize_search_data(search_data):
    """Return search data with the expected top-level keys in a stable order."""
    return {key: search_data.get(key, []) for key in SEARCH_DATA_KEYS}


def save_search_data(path, search_data):
    """Persist raw search data as pretty JSON for auditing."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(normalize_search_data(search_data), f, indent=2)
        f.write("\n")


def build_llm_prompt(company, industry, audience, search_data):
    """Build the prompt for the LLM to generate the research brief."""
    prompt = f"""You are a market research analyst. Based on the search results below, create a structured research brief for the company "{company}" in the "{industry}" industry targeting "{audience}".

## Search Results

### Market Size & Growth
{format_search_results(search_data['market_size'])}

### Industry Trends
{format_search_results(search_data['trends'])}

### Competitors
{format_search_results(search_data['competitors'])}

### Statistics & Data
{format_search_results(search_data['statistics'])}

## Instructions

Generate a markdown research brief with EXACTLY these sections:

# Research Brief: {company}

## Market Overview
Summarize the market size and growth rate. Include specific numbers and cite sources with URLs.

## Key Industry Trends
List 3-5 key trends in the {industry} industry relevant to {audience}. Each trend should have a brief explanation.

## Competitive Landscape
Identify 3 competitors to {company} and describe their positioning. Include what differentiates each.

## Relevant Statistics
List 3-5 specific data points with sources (URLs). Focus on statistics relevant to {audience} in the {industry} space.

Use only information from the search results above. Cite sources with URLs where possible. Be concise and factual."""
    return prompt


def main():
    parser = argparse.ArgumentParser(
        description="Research agent that generates structured market research briefs."
    )
    parser.add_argument("--company", required=True, help="Company name to research")
    parser.add_argument("--industry", required=True, help="Industry/sector")
    parser.add_argument("--audience", required=True, help="Target audience")
    parser.add_argument(
        "--search-count",
        type=int,
        default=10,
        help="Number of Brave search results to fetch per query (default: 10)",
    )
    parser.add_argument(
        "--save-search-json",
        help="Optional path to save raw search data as pretty JSON",
    )
    parser.add_argument(
        "--output", default="research_brief.md", help="Output file (default: research_brief.md)"
    )
    args = parser.parse_args()

    api_key = os.environ.get("BRAVE_API_KEY")
    if not api_key:
        print("Error: BRAVE_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    queries = build_search_queries(args.company, args.industry, args.audience)
    search_data = {key: [] for key in SEARCH_DATA_KEYS}

    for label, query in queries.items():
        print(f"Searching: {query}")
        try:
            search_data[label] = brave_search(query, api_key, count=args.search_count)
        except requests.RequestException as e:
            print(f"Warning: Search failed for '{label}': {e}", file=sys.stderr)
            search_data[label] = []

    if args.save_search_json:
        save_search_data(args.save_search_json, search_data)
        print(f"Search data saved to {args.save_search_json}")

    prompt = build_llm_prompt(args.company, args.industry, args.audience, search_data)

    print("Generating research brief...")
    try:
        brief = call_llm(prompt)
    except requests.RequestException as e:
        print(f"Error: LLM request failed: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(brief)

    print(f"Research brief saved to {args.output}")


if __name__ == "__main__":
    main()
