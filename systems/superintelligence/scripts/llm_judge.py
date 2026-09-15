#!/usr/bin/env python3
"""
Tier 2 LLM-judge semantic review for SI personas.
Evaluates voice fidelity, factual accuracy, schema compliance, recency, and cross-team coherence.

Requires either:
  - Local LM Studio running at localhost:1234 (default)
  - AI gateway key at ~/.coco/.ai-gateway-key

Usage:
    python3 llm_judge.py --team ai --slug andrej-karpathy
    python3 llm_judge.py --team finance --threshold 70
    python3 llm_judge.py --all --dry-run  # show what would be judged without calling LLM
"""
from __future__ import annotations
import argparse, json, os, pathlib, re, sys, urllib.request
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

SI_ROOT = pathlib.Path(__file__).resolve().parents[1]
TEAMS = ["ai", "engineering", "product-design", "finance", "trading",
         "risk-compliance", "strategy", "data-analytics", "gtm"]

RUBRIC = """You are an expert evaluator of AI persona profiles that simulate real-world thought leaders.
Score each dimension 0-100 and provide specific revision instructions for any score below 80.

DIMENSIONS:
1. Voice Fidelity (weight: 25): Does the persona's signature_moves, public_stances, and narrative
   body authentically capture how this person actually speaks, thinks, and argues? Are the quotes
   and paraphrases consistent with their known public communication style?

2. Factual Accuracy (weight: 30): Are affiliations, publications, career history, and claims
   verifiable against public records? Are there any hallucinated URLs, invented publications,
   or incorrect dates? Every factual claim should be traceable to a real source.

3. Schema Compliance (weight: 15): Does the markdown body follow the expected structure?
   Are all required frontmatter fields present and correctly typed? Is the YAML valid?

4. Recency & Relevance (weight: 15): Are recent_signal_12mo entries actually from the last
   12 months and materially relevant to the persona's domain? Do they reflect genuine
   public activity (talks, papers, interviews) rather than filler?

5. Cross-team Coherence (weight: 15): If the persona appears in multiple teams, is their
   role, cell assignment, and expertise description consistent across all listings?
   Does the archetype description align with their actual domain contributions?

OUTPUT FORMAT (JSON only, no commentary):
{
  "voice_fidelity": {"score": <0-100>, "notes": "<specific feedback>"},
  "factual_accuracy": {"score": <0-100>, "notes": "<specific feedback>"},
  "schema_compliance": {"score": <0-100>, "notes": "<specific feedback>"},
  "recency_relevance": {"score": <0-100>, "notes": "<specific feedback>"},
  "cross_team_coherence": {"score": <0-100>, "notes": "<specific feedback>"},
  "weighted_total": <0-100>,
  "verdict": "PASS" | "NEEDS-REVISION" | "FAIL",
  "revision_instructions": ["<actionable item 1>", "<actionable item 2>", ...]
}

VERDICT RULES:
- weighted_total >= 80 → PASS
- weighted_total >= 60 → NEEDS-REVISION
- weighted_total < 60 → FAIL
"""


def load_persona(team: str, slug: str) -> tuple[str, dict]:
    path = SI_ROOT / team / "personas" / f"{slug}.md"
    if not path.exists():
        return None, None
    text = path.read_text()
    if not text.startswith("---"):
        return text, None
    end = text.find("\n---\n", 4)
    if end < 0:
        end = text.find("\n---", 4)
    try:
        fm = yaml.safe_load(text[4:end]) if end > 0 else None
    except Exception:
        fm = None
    return text, fm


def call_llm(prompt: str, system: str, model: str = "qwen3.6", max_tokens: int = 4096) -> str:
    """Try LM Studio first, then AI gateway."""
    # Try LM Studio
    lm_payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.1
    }).encode()

    try:
        req = urllib.request.Request(
            "http://localhost:1234/v1/chat/completions",
            data=lm_payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception:
        pass

    # Try AI gateway
    key_path = pathlib.Path.home() / ".coco" / ".ai-gateway-key"
    if key_path.exists():
        key = key_path.read_text().strip()
        gw_payload = json.dumps({
            "model": "gpt-5.4-nano-2026-03-17",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "max_completion_tokens": max_tokens
        }).encode()
        try:
            req = urllib.request.Request(
                "https://YOUR_AI_GATEWAY_HOST/YOUR_PROJECT_ID/v1/chat/completions",
                data=gw_payload,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return json.dumps({"error": f"gateway failed: {e}"})

    return json.dumps({"error": "No LLM endpoint available. Start LM Studio or configure AI gateway."})


def judge_persona(team: str, slug: str, dry_run: bool = False) -> dict:
    text, fm = load_persona(team, slug)
    if text is None:
        return {"slug": slug, "team": team, "error": "file not found"}
    if fm is None:
        return {"slug": slug, "team": team, "error": "frontmatter parse failed"}

    if dry_run:
        return {"slug": slug, "team": team, "dry_run": True, "persona_size": len(text)}

    prompt = f"Evaluate this persona profile:\n\n```\n{text[:12000]}\n```"
    raw = call_llm(prompt, RUBRIC)

    # Extract JSON from response
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group())
            result["slug"] = slug
            result["team"] = team
            return result
        except json.JSONDecodeError:
            pass

    return {"slug": slug, "team": team, "error": "LLM response not valid JSON", "raw": raw[:500]}


def main():
    ap = argparse.ArgumentParser(description="Tier 2 LLM-judge semantic review")
    ap.add_argument("--team", help="Team to evaluate")
    ap.add_argument("--all", action="store_true", help="Evaluate all teams")
    ap.add_argument("--slug", help="Evaluate only this slug")
    ap.add_argument("--dry-run", action="store_true", help="List personas without calling LLM")
    ap.add_argument("--output", help="Write results to JSON file")
    args = ap.parse_args()

    teams = TEAMS if args.all else ([args.team] if args.team else [])
    if not teams:
        ap.error("Specify --team <name> or --all")

    results = []
    for team in teams:
        personas_dir = SI_ROOT / team / "personas"
        if not personas_dir.is_dir():
            continue
        slugs = sorted(f.stem for f in personas_dir.glob("*.md"))
        if args.slug:
            slugs = [s for s in slugs if s == args.slug]
        for slug in slugs:
            print(f"Judging {team}/{slug}...", flush=True)
            result = judge_persona(team, slug, dry_run=args.dry_run)
            results.append(result)
            if not args.dry_run and "error" not in result:
                verdict = result.get("verdict", "?")
                total = result.get("weighted_total", "?")
                print(f"  → {verdict} ({total})")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults written to {args.output}")
    else:
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
