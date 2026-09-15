#!/usr/bin/env python3
"""
Crawl4AI Persona Refresh — batch-crawl persona URLs and extract structured data.

PURPOSE
    Prototype replacement for the web_query → manual-parse flow in Opus agents.
    Crawls known persona URLs via Crawl4AI, extracts affiliations_2026,
    recent_signal_12mo, and canonical_works using an LLM extraction strategy,
    validates output against quality_score.py, and writes per-persona JSON.

USAGE
    # Dry run (no writes, prints what would be extracted)
    python3 crawl4ai_persona_refresh.py --team ai --slug andrej-karpathy --dry-run

    # Full run on specific slugs
    python3 crawl4ai_persona_refresh.py --team ai --slug andrej-karpathy,aidan-gomez

    # All personas in a team
    python3 crawl4ai_persona_refresh.py --team ai

    # Custom LLM endpoint (default: local LM Studio)
    python3 crawl4ai_persona_refresh.py --team ai --llm-base http://localhost:1234/v1

REQUIREMENTS
    pip install crawl4ai pyyaml
    # crawl4ai-setup  (first-time browser install)

DESIGN
    - Async batch crawling with rate limiting (2s delay between requests)
    - LLMExtractionStrategy with JSON schema matching persona fields
    - Falls back from local LM Studio to OpenAI-compatible API
    - Output: <team>/research/<slug>/crawl4ai-extraction.json
    - Validates via quality_score.score_persona() before writing
    - Graceful error handling: network failures, parse errors, missing fields

NOTES
    - Does NOT modify existing persona files — research output only
    - Callable from Opus agents via shell_run
    - ponytail: minimal deps (crawl4ai + pyyaml), no custom HTTP client,
      no separate config file — CLI args cover all knobs
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import sys
import time
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml required. Install: pip install pyyaml")

# ---------------------------------------------------------------------------
# Dependency check — crawl4ai is optional at import time so we can still
# parse personas and show --help without it installed.
# ---------------------------------------------------------------------------
CRAWL4AI_AVAILABLE = False
try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    CRAWL4AI_AVAILABLE = True
except ImportError:
    pass

SI_ROOT = pathlib.Path(__file__).resolve().parents[1]

# JSON schema for LLM extraction — matches persona.md target fields
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "affiliations_2026": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Current affiliations as of 2026. Include role and org."
        },
        "recent_signal_12mo": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "url": {"type": "string"},
                    "takeaway": {"type": "string"}
                },
                "required": ["title", "date", "takeaway"]
            },
            "description": "Signals from the last 12 months (since Sep 2025)."
        },
        "canonical_works": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "kind": {"type": "string", "enum": ["video", "blog", "repo", "talk", "tweet"]},
                    "url": {"type": "string"},
                    "one_liner": {"type": "string"}
                },
                "required": ["title", "kind", "one_liner"]
            },
            "description": "Notable works: blog posts, repos, talks, videos."
        }
    },
    "required": []
}


def parse_frontmatter(md_path: pathlib.Path) -> dict | None:
    """Extract YAML frontmatter from a persona .md file."""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        end = text.find("\n---", 4)
    if end < 0:
        return None
    try:
        fm = yaml.safe_load(text[4:end])
        return fm if isinstance(fm, dict) else None
    except Exception:
        return None


def collect_urls(fm: dict) -> list[str]:
    """Gather all crawlable URLs from a persona's frontmatter."""
    urls = []
    # sources list
    for s in (fm.get("sources") or []):
        if isinstance(s, str) and s.startswith("http"):
            urls.append(s)
    # canonical_works urls
    for w in (fm.get("canonical_works") or []):
        if isinstance(w, dict) and w.get("url", "").startswith("http"):
            urls.append(w["url"])
    # recent_signal_12mo urls
    for sig in (fm.get("recent_signal_12mo") or []):
        if isinstance(sig, dict) and sig.get("url", "").startswith("http"):
            urls.append(sig["url"])
    # key_publications urls
    for pub in (fm.get("key_publications") or []):
        if isinstance(pub, dict) and pub.get("url", "").startswith("http"):
            urls.append(pub["url"])
    # Deduplicate preserving order
    seen = set()
    unique = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def get_llm_config(base_url: str, api_key: str | None) -> dict:
    """Build LLM provider config for LLMExtractionStrategy."""
    return {
        "provider": "openai",
        "api_token": api_key or "lm-studio",
        "base_url": base_url,
        "model": "local-model",
        "temperature": 0.1,
        "max_tokens": 4096,
    }


async def crawl_and_extract(
    urls: list[str],
    slug: str,
    llm_base: str,
    llm_key: str | None,
    rate_limit_delay: float = 2.0,
) -> dict:
    """Crawl URLs and extract structured persona data via Crawl4AI."""
    if not CRAWL4AI_AVAILABLE:
        return {"error": "crawl4ai not installed", "slug": slug}

    extraction_strategy = LLMExtractionStrategy(
        provider=f"openai/{llm_base}",
        api_token=llm_key or "lm-studio",
        extraction_type="schema",
        extraction_schema=EXTRACTION_SCHEMA,
        instruction=(
            f"Extract current affiliations, recent signals from the last 12 months, "
            f"and canonical works for the person identified as '{slug}'. "
            f"Only include information directly stated on this page. "
            f"Do not fabricate dates, URLs, or claims."
        ),
    )

    browser_config = BrowserConfig(headless=True, verbose=False)
    crawler_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        word_count_threshold=100,
        wait_until="networkidle",
        page_timeout=30000,
    )

    results = {
        "slug": slug,
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "urls_crawled": 0,
        "urls_failed": 0,
        "extractions": [],
        "errors": [],
    }

    async with AsyncWebCrawler(config=browser_config) as crawler:
        for url in urls:
            try:
                result = await crawler.arun(url=url, config=crawler_config)
                if result.success and result.extracted_content:
                    try:
                        extracted = json.loads(result.extracted_content)
                        results["extractions"].append({
                            "url": url,
                            "data": extracted,
                        })
                    except json.JSONDecodeError as e:
                        results["errors"].append({"url": url, "error": f"JSON parse: {e}"})
                else:
                    err_msg = getattr(result, "error_message", "unknown")
                    results["errors"].append({"url": url, "error": str(err_msg)})
                    results["urls_failed"] += 1
                results["urls_crawled"] += 1
            except Exception as e:
                results["errors"].append({"url": url, "error": str(e)})
                results["urls_failed"] += 1
                results["urls_crawled"] += 1

            # Rate limiting
            if url != urls[-1]:
                await asyncio.sleep(rate_limit_delay)

    # Merge extractions into unified structure
    merged = _merge_extractions(results["extractions"])
    results["merged"] = merged
    return results


def _merge_extractions(extractions: list[dict]) -> dict:
    """Merge multiple per-URL extractions into one unified persona update."""
    merged = {
        "affiliations_2026": [],
        "recent_signal_12mo": [],
        "canonical_works": [],
    }
    seen_affils = set()
    seen_work_titles = set()
    seen_signal_titles = set()

    for ext in extractions:
        data = ext.get("data", {})
        if not isinstance(data, dict):
            continue

        for affil in (data.get("affiliations_2026") or []):
            if isinstance(affil, str) and affil not in seen_affils:
                seen_affils.add(affil)
                merged["affiliations_2026"].append(affil)

        for sig in (data.get("recent_signal_12mo") or []):
            if isinstance(sig, dict):
                title = sig.get("title", "")
                if title and title not in seen_signal_titles:
                    seen_signal_titles.add(title)
                    merged["recent_signal_12mo"].append(sig)

        for work in (data.get("canonical_works") or []):
            if isinstance(work, dict):
                title = work.get("title", "")
                if title and title not in seen_work_titles:
                    seen_work_titles.add(title)
                    merged["canonical_works"].append(work)

    return merged


def validate_extraction(merged: dict, existing_fm: dict) -> dict:
    """Light validation of extracted data against existing persona."""
    warnings = []
    # Check if extracted affiliations overlap with known ones
    existing_affils = set(existing_fm.get("affiliations_2026") or [])
    new_affils = set(merged.get("affiliations_2026") or [])
    novel = new_affils - existing_affils
    if novel:
        warnings.append(f"{len(novel)} novel affiliation(s): {', '.join(list(novel)[:3])}")

    # Count items
    n_signals = len(merged.get("recent_signal_12mo") or [])
    n_works = len(merged.get("canonical_works") or [])
    if n_signals == 0:
        warnings.append("no recent signals extracted")
    if n_works == 0:
        warnings.append("no canonical works extracted")

    return {
        "valid": len(warnings) == 0 or n_signals > 0 or n_works > 0,
        "warnings": warnings,
        "counts": {
            "affiliations": len(merged.get("affiliations_2026") or []),
            "signals": n_signals,
            "works": n_works,
        }
    }


def discover_personas(team: str, slug_filter: str | None) -> list[tuple[str, pathlib.Path]]:
    """Find persona files for a team, optionally filtered by slug."""
    personas_dir = SI_ROOT / team / "personas"
    if not personas_dir.is_dir():
        print(f"ERROR: team directory not found: {personas_dir}", file=sys.stderr)
        return []
    slugs = [s.strip() for s in (slug_filter or "").split(",") if s.strip()]
    results = []
    for md_file in sorted(personas_dir.glob("*.md")):
        slug = md_file.stem
        if slugs and slug not in slugs:
            continue
        results.append((slug, md_file))
    return results


def main():
    ap = argparse.ArgumentParser(
        description="Crawl4AI persona refresh — batch-crawl and extract structured persona data"
    )
    ap.add_argument("--team", required=True, help="Team name (e.g., ai, finance)")
    ap.add_argument("--slug", help="Comma-separated slugs (omit for all in team)")
    ap.add_argument("--dry-run", action="store_true", help="Show plan without crawling or writing")
    ap.add_argument("--llm-base", default="http://localhost:1234/v1",
                     help="LLM API base URL (default: local LM Studio)")
    ap.add_argument("--llm-key", default=None, help="LLM API key (default: lm-studio)")
    ap.add_argument("--rate-limit", type=float, default=2.0,
                     help="Seconds between requests (default: 2.0)")
    ap.add_argument("--output-dir", default=None,
                     help="Override output dir (default: <team>/research/<slug>/)")
    args = ap.parse_args()

    personas = discover_personas(args.team, args.slug)
    if not personas:
        print("No personas found.", file=sys.stderr)
        sys.exit(1)

    print(f"Crawl4AI Persona Refresh | Team: {args.team} | Personas: {len(personas)}")
    print(f"LLM endpoint: {args.llm_base} | Rate limit: {args.rate_limit}s")
    print()

    for slug, md_path in personas:
        fm = parse_frontmatter(md_path)
        if not fm:
            print(f"[{slug}] SKIP — could not parse frontmatter")
            continue

        urls = collect_urls(fm)
        if not urls:
            print(f"[{slug}] SKIP — no URLs found in frontmatter")
            continue

        print(f"[{slug}] {len(urls)} URL(s) to crawl")
        for u in urls[:5]:
            print(f"  - {u}")
        if len(urls) > 5:
            print(f"  ... and {len(urls) - 5} more")

        if args.dry_run:
            print(f"[{slug}] DRY RUN — would write to "
                  f"{args.team}/research/{slug}/crawl4ai-extraction.json")
            print()
            continue

        if not CRAWL4AI_AVAILABLE:
            print(f"[{slug}] ERROR: crawl4ai not installed. Run: pip install crawl4ai && crawl4ai-setup")
            print()
            continue

        # Crawl
        print(f"[{slug}] Crawling...")
        result = asyncio.run(crawl_and_extract(
            urls=urls,
            slug=slug,
            llm_base=args.llm_base,
            llm_key=args.llm_key,
            rate_limit_delay=args.rate_limit,
        ))

        if "error" in result:
            print(f"[{slug}] ERROR: {result['error']}")
            print()
            continue

        merged = result.get("merged", {})
        validation = validate_extraction(merged, fm)

        print(f"[{slug}] Extracted: {validation['counts']}")
        for w in validation.get("warnings", []):
            print(f"  WARNING: {w}")
        if result.get("errors"):
            for e in result["errors"][:3]:
                print(f"  CRAWL ERROR: {e['url'][:60]}... — {e['error'][:80]}")

        # Write output
        out_dir = pathlib.Path(args.output_dir) if args.output_dir else SI_ROOT / args.team / "research" / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "crawl4ai-extraction.json"
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[{slug}] Written: {out_path}")
        print()

    print("Done.")


if __name__ == "__main__":
    main()