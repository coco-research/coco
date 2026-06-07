#!/usr/bin/env python3
"""
Free, key-free retriever for local persona grounding.
Multi-query DuckDuckGo (text + dated news) -> fetch top pages -> trafilatura
extract real article text. Returns a context block + the real URL allowlist
so the generator can be told "cite ONLY from these".
"""
from __future__ import annotations
import concurrent.futures as cf
from ddgs import DDGS
import trafilatura


def search(name: str, anchor: str, cell: str, max_pages: int = 20):
    cell_words = cell.replace("-", " ")
    text_queries = [f"{name} {anchor}", f"{name} 2026", f"{name} interview",
                    f"{name} {cell_words}", f"{name} book OR paper"]
    news_queries = [name, f"{name} {cell_words}"]
    text_hits: dict[str, dict] = {}
    news: list[dict] = []
    with DDGS() as d:
        for q in text_queries:
            try:
                for r in d.text(q, max_results=10):
                    u = r.get("href") or r.get("url")
                    if u and u not in text_hits:
                        text_hits[u] = {"title": r.get("title", ""), "snippet": (r.get("body") or "")[:200]}
            except Exception:
                pass
        for q in news_queries:
            try:
                for r in d.news(q, max_results=10, timelimit="y"):
                    u = r.get("url") or r.get("href")
                    if u:
                        news.append({"date": r.get("date", ""), "title": r.get("title", ""),
                                     "url": u, "snippet": (r.get("body") or "")[:160]})
            except Exception:
                pass

    urls = list(text_hits)[:max_pages]

    def fx(u):
        try:
            dl = trafilatura.fetch_url(u)
            if not dl:
                return None
            t = trafilatura.extract(dl, include_comments=False, include_tables=False) or ""
            return (u, t[:2200]) if t.strip() else None
        except Exception:
            return None

    pages = []
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        for res in ex.map(fx, urls):
            if res:
                pages.append(res)
    return pages, news


def context_block(pages, news):
    lines = ["SOURCES (real URLs with extracted article text — use these for `sources` and stance evidence_url; cite ONLY these):"]
    for u, txt in pages:
        lines.append(f"### {u}\n{txt}\n")
    lines.append("RECENT NEWS (real, dated — use for recent_signal_12mo; KEEP ONLY items dated after 2025-06-01):")
    for n in news:
        lines.append(f"- {n['date']} :: {n['title']} :: {n['url']} :: {n['snippet']}")
    allow = [u for u, _ in pages] + [n["url"] for n in news]
    return "\n".join(lines), allow


if __name__ == "__main__":
    import sys
    p, n = search(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "", sys.argv[3] if len(sys.argv) > 3 else "")
    print(f"pages fetched: {len(p)} | news: {len(n)}")
    for u, t in p:
        print(f"  PAGE {u} ({len(t)}c)")
    for x in n[:15]:
        print(f"  NEWS {x['date']} {x['url']}")
