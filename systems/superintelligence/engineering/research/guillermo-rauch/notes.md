# Guillermo Rauch — Research Notes

**Slug:** guillermo-rauch
**Cell:** web-and-frontend (engineering team)
**Researched:** 2026-05-30
**Researcher:** Claude (engineering Super Intelligence Team build, Wave E7)

Raw, dated findings with quotes and URLs. Saved so future re-syntheses do not re-crawl.

---

## Identity confirmation

- **Real name:** Guillermo Rauch.
- **Born:** December 10, 1990, Lanús, Buenos Aires, Argentina. Father an industrial engineer; first computer at age seven.
  - Source: https://en.everybodywiki.com/Guillermo_Rauch ; https://medium.com/history-of-vercel/history-of-vercel-1990-2009-guillermo-rauch-childhood-and-first-steps-in-programming-1dbf038ddf9a
- **Founder & CEO of Vercel.** Creator/steward of Next.js; creator of Socket.IO, Mongoose; author of the SWR data-fetching library. Confirmed identity — confidence high. No disambiguation issue (single well-known public figure under this name).

## Career timeline (verified)

- Joined the **MooTools** core team as a teenager; first full-time job as a frontend engineer at 18, relocated to San Francisco.
- Created open-source projects **Socket.IO** (real-time WebSocket abstraction) and **Mongoose** (MongoDB ODM for Node.js).
- Co-founded **LearnBoost**; CTO of **Cloudup** (file-sharing startup), acquired by **Automattic** (WordPress parent) in 2013.
- Founded **ZEIT** in 2015; **rebranded to Vercel in 2020**. Front-end-focused cloud integrated with Next.js.
- **Next.js** created in 2016 by Rauch and team — React framework introducing SSR, SSG, file-based routing. Became the most popular React framework; adopted by Netflix, TikTok, Hulu, Nike, Washington Post.
  - Sources: https://rauchg.com/about ; https://en.wikipedia.org/wiki/Vercel ; https://startupintros.com/people/guillermo-rauch

> CORRECTION TO ASSUMPTIONS: The task brief lists "SWR" among his creations. This is correct — SWR is a Vercel/Rauch-authored React hooks library for data fetching ("stale-while-revalidate"). No correction needed, but noting it is a library (not a framework) and is less central to his 2025-2026 public signal than Next.js, v0, and the AI Cloud.

---

## RECENT SIGNALS (all dated AFTER 2025-05-30, verified)

### 1. Next.js 16 release — 2025-10-21
- Released Tuesday, October 21, 2025. Turbopack now **stable** as the default bundler (5-10x faster Fast Refresh, 2-5x faster builds). Introduces **Cache Components** (explicit caching model built on Partial Pre-Rendering + `use cache`), **Next.js Devtools MCP** (Model Context Protocol integration for debugging), and **Proxy** replacing Middleware.
- Announced at Next.js Conf 25 opening keynote (October 2025), Rauch presenting.
- Sources: https://nextjs.org/blog/next-16 ; https://www.infoq.com/news/2025/12/nextjs-16-release/ ; https://www.youtube.com/watch?v=myjrQS_7zNk

### 2. "Learn to ship" — X post, ~2025-10-26
- Tweet ID 1982476318639079784 (snowflake decodes to late October 2025). Cross-posted to LinkedIn (activity 7388342462555119616).
- Full text: "Learn to ship. Shipping is a skill distinct from coding. Shipping is designing, coding, QAing, story-telling, teaching, marketing, selling, pivoting, iterating… It used to be that coding dominated in importance because of coding ability scarcity. AI will push you to go further."
- Sources: https://x.com/rauchg/status/1982476318639079784 ; https://www.linkedin.com/posts/rauchg_learn-to-ship-shipping-is-a-skill-distinct-activity-7388342462555119616-Ha2B

### 3. "Introducing the new v0" — Vercel blog, 2026-02-03
- v0 rebuilt from the ground up to close the prototype-to-production gap for "vibe coding." New: GitHub repo import, Git workflow panel (branch/PR/deploy-on-merge for non-engineers), database integrations (Snowflake, AWS), enterprise security, sandbox-based full-stack runtime, token-based billing (replaced fixed credits).
- Key line: "2026 will be the year of agents. Soon, you'll be able to build end-to-end agentic workflows in v0, AI models included, and deploy them on Vercel's self-driving infrastructure."
- Source: https://vercel.com/blog/introducing-the-new-v0 ; coverage https://www.infoworld.com/article/4126837/vercel-revamps-ai-powered-v0-development-platform.html

### 4. Sequoia "Training Data" podcast — generative web — 2025-11
- "The web is evolving from dynamic to generative." Software becomes ephemeral and personalized; predicts within 3-5 years major internet companies adapt or collapse.
- v0 at 3M users (Nov 2025). "AI products come with natural feedback loops." Natural language "opens up the top of funnel to every person on the planet." Builder population goes "from millions of traditional developers to hundreds of millions." Users have "zero patience for errors." ChatGPT became Vercel's fastest-growing acquisition channel (LLM recommendations).
- Source: https://sequoiacap.com/podcast/training-data-guillermo-rauch/

### 5. IPO-readiness + ARR surge — TechCrunch, 2026-04-13 (HumanX conference, SF)
- ARR run rate: $100M (start of 2024) → $340M (end of Feb 2026) — a ~240% surge over the period.
- 30% of apps on Vercel's platform already came from agents. "Agents are very prolific at deploying."
- IPO: "Vercel is very much a work-in-public company." "There's no perfect timeline or quarter I can give. The company's ready and getting more ready for it every day." "The total addressable market of infrastructure has now grown, and it simply has no ceiling." "All of that software … it needs to go somewhere, and we think it's going to be Vercel."
- "When I started this company, only tens of millions of people could deploy. Now we're seeing that everybody in the world can create an app."
- As of March 2026, **v0 has over 6 million developers**.
- Sources: https://techcrunch.com/2026/04/13/vercel-ceo-guillermo-rauch-signals-ipo-readiness-as-ai-agents-fuel-revenue-surge/ ; https://finance.yahoo.com/markets/stocks/articles/vercel-ceo-guillermo-rauch-signals-152229505.html

### 6. Series F funding — September 2025
- Raised **$300M Series F** co-led by Accel and GIC; valued at **$9.3B**.
- Sources: https://en.wikipedia.org/wiki/Vercel ; TechCrunch (above).

---

## PUBLIC STANCES (each cited)

1. **Generative web** — "the web is evolving from dynamic to generative"; software becomes ephemeral, personalized, generated on demand.
   - https://sequoiacap.com/podcast/training-data-guillermo-rauch/
2. **Shipping > coding** — "Shipping is a skill distinct from coding… AI will push you to go further."
   - https://x.com/rauchg/status/1982476318639079784
3. **The AI Cloud / Fluid compute** — serverless reinvented for AI: eliminate cold starts, manual scaling, overprovisioning; Active CPU pricing (pay only when code actively executing); up to 90% cost reduction for high-idle AI workloads. "AI Cloud has dual meaning": full autonomy of security/infra ops, AND the best cloud to ship AI products.
   - https://rauchg.com/2025/the-ai-cloud ; https://vercel.com/blog/the-ai-cloud-a-unified-platform-for-ai-workloads ; https://x.com/rauchg/status/1969459262758809996
4. **Natural language as the new interface / democratized creation** — "opens up the top of funnel to every person on the planet because all you need to know is to use your natural language"; builders go from millions to hundreds of millions.
   - https://sequoiacap.com/podcast/training-data-guillermo-rauch/
5. **Team Web** — "Team Web where everything is instantaneous"; mission "let's make the web platform the best that it can be"; instant access (ChatGPT.com, v0.dev) without install friction.
   - https://www.antoinebuteau.com/lessons-from-guillermo-rauch-founder-and-ceo-of-vercel/
6. **Quality is non-negotiable for AI products** — users have "zero patience for errors"; invest heavily in fine-tuning / custom model training for "production-grade outputs"; close the prototype-to-production gap.
   - https://sequoiacap.com/podcast/training-data-guillermo-rauch/ ; https://vercel.com/blog/introducing-the-new-v0
7. **Make shipping addictive / build in public / incremental delivery of bold visions** — "Make it work, make it right, make it fast"; ship frequently, build in public.
   - https://www.accel.com/podcast-episodes/vercels-guillermo-rauch-on-bold-visions-for-the-future-delivered-incrementally

---

## PRODUCTIVE CONFLICT (ROSTER.md slugs)

- **dhh** (David Heinemeier Hansson, architecture-testing-craft cell) — DHH champions the "majestic monolith," is anti-serverless and anti-cloud (famously moved 37signals OFF the cloud). Rauch is the serverless/frontend-cloud thesis incarnate. Rauch on CDN/monolith migration: "One of the largest consumer household goods companies in the world just migrated from monolith+Cloudflare to Vercel. No more orange cloud." Direct serverless-vs-monolith / cloud-vs-on-prem axis.
   - https://x.com/rauchg/status/1839313153496330351 ; DHH's public anti-cloud stance is canonical.
- **ryan-carniato** (SolidJS) and **evan-you** (Vue/Vite/VoidZero), **dan-abramov** (React) — framework-design disagreements (React Server Components / Next.js coupling debates) but same cell; less of a sharp axis than DHH. Use DHH as the primary conflict.

## PAIRS WELL WITH (from brief, verified plausible)

- **rich-harris** (Svelte/SvelteKit; works AT Vercel — direct colleague). https://vercel.com/
- **adam-wathan** (Tailwind CSS — ubiquitous in v0 output; aesthetic + DX alignment).
- **michael-truell** (Cursor/Anysphere CEO — AI-assisted coding frontier; v0 and Cursor are sibling theses on AI codegen).

---

## ADDITIONAL DATED X SIGNALS (supporting, late 2025)

- Vercel Sandbox for agents: "cloud computers purpose-built for agents… clone & launch millions of agents with 1 API." https://x.com/rauchg/status/2014441058869117005
- AI Gateway production data: "Google is king of production scale, Anthropic dominates in coding & spend, OpenAI is growing fast since 5.4, OSS continues to gain ground. The AI race is a lot more fluid than it looks." https://x.com/rauchg/status/2054671803264757957
- AI coding agent for Vercel/web: "We've been building an AI coding agent optimized for Vercel and web technologies… unusually 'slow' in its rollout." https://x.com/rauchg/status/1957888264905621757
- "time to deploy URL" → "time to intelligence" framing on AI SDK Gateway. https://x.com/rauchg/status/1924899244156055958

## CANONICAL WORKS

- Next.js (framework) — https://nextjs.org/
- v0 — https://v0.app/ ; "Introducing the new v0" https://vercel.com/blog/introducing-the-new-v0
- Socket.IO — real-time engine. SWR — React data fetching. Mongoose — MongoDB ODM.
- "The AI Cloud" essay — https://rauchg.com/2025/the-ai-cloud
- AI SDK — https://github.com/vercel/ai ; v0 Platform API https://vercel.com/blog/build-your-own-ai-app-builder-with-the-v0-platform-api
- Personal site / writing — https://rauchg.com/about

## BLIND SPOTS (inferred from stance pattern)

- Cost transparency at scale: serverless/consumption pricing is his thesis, but DHH-style critics argue managed cloud bills surprise at scale; Rauch underweights the on-prem TCO argument.
- Vendor lock-in: Next.js + Vercel coupling (RSC, edge, ISR features that shine on Vercel) draws repeated community concern; he tends to frame it as DX, not lock-in.
- Backend/data-systems depth: his center of gravity is the frontend/edge/render layer; deep DB/storage/consistency tradeoffs are not his native turf.
- "Everyone can build" optimism can underweight maintenance, security, and long-term ownership burden of AI-generated apps.

## SOURCES (>=8, real URLs; >=3 recent)

1. https://rauchg.com/about
2. https://en.wikipedia.org/wiki/Vercel
3. https://techcrunch.com/2026/04/13/vercel-ceo-guillermo-rauch-signals-ipo-readiness-as-ai-agents-fuel-revenue-surge/ (recent)
4. https://nextjs.org/blog/next-16 (recent)
5. https://vercel.com/blog/introducing-the-new-v0 (recent)
6. https://sequoiacap.com/podcast/training-data-guillermo-rauch/ (recent)
7. https://rauchg.com/2025/the-ai-cloud (recent)
8. https://x.com/rauchg/status/1982476318639079784 (recent)
9. https://vercel.com/blog/the-ai-cloud-a-unified-platform-for-ai-workloads
10. https://x.com/rauchg/status/1839313153496330351
11. https://www.accel.com/podcast-episodes/vercels-guillermo-rauch-on-bold-visions-for-the-future-delivered-incrementally
12. https://startupintros.com/people/guillermo-rauch
