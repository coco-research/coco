---
name: source-fetch
description: "Use before writing anything that cites a web source, including persona research, competitive write-ups, and cited summaries. Fetches each public URL to a local markdown file and records URL, status, fetch time and title in sources.json so every citation is checkable."
domain: foundational
---

# Source Fetch Skill

Fetch first, write second. A citation is only worth what is in the file on disk. If the page was never fetched, it cannot be cited.

## When to use

Use this skill when the deliverable will name a URL, quote a person, or assert a recent fact about an organization or product. Triggers:

- persona or expert research that fills an affiliations, works, or "recent signal" field
- a write-up whose claims need source links
- a factual answer where the user asks "where did that come from"
- a refresh of facts that may have changed since they were last recorded

Skip it for material the user handed over directly, and for pages already fetched into the same folder this session. Re-fetch only when the old copy is stale or missing.

## Step 1: name the folder

Ask the user where the sources go, or take the path they already gave. One folder per job:

```
<folder>/sources/<slug>.md
<folder>/sources/sources.json
```

`<slug>` is a kebab-case form of the page name, not the raw URL, and two pages from one host must not overwrite each other. Nothing gets written outside that folder.

## Step 2: fetch each URL

Preferred, when available:

1. `pip install crawl4ai`
2. `crawl4ai-setup`

Both are optional. They install a browser, which handles JavaScript-rendered pages.

Fall back to `curl` for plain pages. Most article, blog, and documentation pages are plain HTML underneath and convert fine:

```
curl -sSL --max-time 30 -o page.html <url>
```

Then convert the HTML body to markdown and keep the `<title>` tag. A fetch that returns a login wall, a cookie notice, or an empty body did not fetch the page: record it as failed and do not guess at the contents.

## Step 3: write sources.json

One entry per URL, written at the end of every batch:

```json
[
  {
    "url": "https://example.com/post",
    "file": "sources/example-post.md",
    "http_status": 200,
    "fetched_at": "<ISO 8601 UTC timestamp>",
    "title": "The actual page title"
  }
]
```

- `http_status` is the real status code, not an assumption. A 403, 404 or 429 stays in the record with its number.
- `fetched_at` is UTC, ISO 8601.
- `title` is copied from the page. Do not retitle it for tidiness.
- A failed fetch gets an entry with its status and `"file": null`.

`sources.json` is the index. If an entry is not in it, the source does not exist for citation purposes.

## Step 4: cite only what you fetched

Before writing any citation, check two things:

1. The `file` named in `sources.json` exists on disk.
2. Its `title` matches the page you are about to describe.

If either check fails, drop the citation. Do not cite the URL from memory, from a search result snippet, or from a different session.

Quotes are stricter than citations:

- A quote must appear character for character in the fetched file. Verbatim means verbatim.
- If it is close but not identical, or if you are compressing the author's point, write it without quotation marks and mark it `[paraphrase]`.
- Never reconstruct a sentence you believe someone said. A paraphrase with no quote marks is always available; an invented quote is never acceptable.

Numbers, dates, roles, and funding figures follow the same rule. Either the fetched file states it, or the claim does not go in the document.

## Hard rules

- No private, paywalled, or login-only pages. If a page needs a session, it is out of scope, even with credentials supplied.
- Respect `robots.txt`. Read it before the first request to a host and skip disallowed paths.
- At most one request per second per host. Sleep between requests; do not fire a batch in parallel at one host.
- Store raw markdown, not a summary. The fetch exists so a later reader can re-check the claim against the source.
- Keep failures in the record. A source that 403s is data; silently deleting it hides the gap in the evidence.

## How the persona refresh script uses the same flow

`systems/superintelligence/scripts/crawl4ai_persona_refresh.py` is the batch version of this skill, and worth reading before writing a new fetcher:

- it collects URLs from the persona frontmatter (`sources`, `canonical_works`, `key_publications`, `recent_signal_12mo`)
- it deduplicates them before any request goes out
- it spaces requests with a configurable delay, defaulting to two seconds
- it records per-URL errors instead of aborting the batch
- it writes one JSON file per persona under the team's research folder, timestamped in UTC
- it only extracts from pages it actually retrieved, and the extraction prompt forbids inventing dates and URLs

Use that script when the job is persona research. Use this skill's manual flow when the job is a handful of pages feeding a written document, or when the crawler is not installed.

## Done check

- Every cited URL has an entry in `sources.json` with a real status code, and every 200 points at a file that exists.
- Every quote in the draft appears in its fetched file.
- Anything softened is marked `[paraphrase]`.
- No request went to a host more than once per second.
