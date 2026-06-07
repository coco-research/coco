# Engineering Super Intelligence Team — Locked Roster

**Status:** Phase 4B — roster locked 2026-05-30, build in progress.
**Team ID:** `engineering-super-intelligence`
**Native personas:** 70 across 11 cells. **Cross-listed from AI:** 9 (no new research).
**Quality bar:** matches AI team — ≥8 source URLs, ≥3 recent signals (post-2025-05-28), every `public_stance` carries an `evidence_url`. Full English prose (never caveman). Exemplar: `superintelligence/ai/personas/andrej-karpathy.md`.

Patch applied 2026-05-30 (from `/ultra-think` on the roster): added Lamport, Lattner, Torvalds, Liskov, Perlman; reclassified Ghemawat as `archetype`; split the former `devops-platform-ai-coding` mega-cell into `devops-platform` + `ai-assisted-coding`. Liskov→craft and Perlman→cloud-architecture also break two previously all-male cells.

---

## Cells and personas

### 1. cloud-architecture (8)
Cloud-scale system design, infra primitives, the build-vs-managed lens.

| Slug | Name | Anchor |
|---|---|---|
| `james-hamilton` | James Hamilton | AWS distinguished engineer; datacenter + Nitro economics |
| `werner-vogels` | Werner Vogels | AWS CTO; "everything fails all the time," eventual consistency |
| `adrian-cockcroft` | Adrian Cockcroft | ex-Netflix/ex-AWS; microservices + cloud migration canon |
| `marc-brooker` | Marc Brooker | AWS senior PE; formal methods, serverless, retries/timeouts |
| `brendan-burns` | Brendan Burns | Kubernetes co-creator; Microsoft Azure CVP |
| `eric-brewer` | Eric Brewer | CAP theorem; Google VP infrastructure |
| `colm-maccarthaigh` | Colm MacCárthaigh | AWS VP/DE; s2n, load balancing, networking, formal verification |
| `radia-perlman` | Radia Perlman | "Mother of the Internet"; spanning tree, network protocol design |

### 2. reliability-sre-obs (7)
SRE practice, observability, incident response, resilience.

| Slug | Name | Anchor |
|---|---|---|
| `ben-treynor-sloss` | Ben Treynor Sloss | Google VP; coined "SRE" |
| `betsy-beyer` | Betsy Beyer | Google; SRE Book editor |
| `charity-majors` | Charity Majors | Honeycomb co-founder/CTO; observability, "test in prod" |
| `cindy-sridharan` | Cindy Sridharan | distributed systems / observability writing |
| `liz-fong-jones` | Liz Fong-Jones | Honeycomb field CTO; SLOs, OpenTelemetry |
| `nora-jones` | Nora Jones | Jeli founder; chaos engineering, incident analysis |
| `tammy-butow` | Tammy Butow | chaos engineering (Gremlin); reliability practice |

### 3. data-and-storage (8)
Databases, distributed data, consistency, storage engines, distributed-systems theory.

| Slug | Name | Anchor |
|---|---|---|
| `martin-kleppmann` | Martin Kleppmann | DDIA; CRDTs, local-first |
| `jeff-dean` | Jeff Dean | Google chief scientist; MapReduce, Bigtable, Spanner |
| `sanjay-ghemawat` | Sanjay Ghemawat | Google senior fellow; GFS/MapReduce — **archetype** (private; persistent_signals) |
| `pat-helland` | Pat Helland | Salesforce; "Life Beyond Distributed Transactions," immutability |
| `michael-stonebraker` | Michael Stonebraker | Postgres/Vertica/VoltDB; Turing laureate |
| `andy-pavlo` | Andy Pavlo | CMU; OtterTune, self-driving DBs, DB systems teaching |
| `joe-hellerstein` | Joe Hellerstein | Berkeley; query optimization, dataflow, Hydro |
| `leslie-lamport` | Leslie Lamport | Paxos, logical clocks, TLA+; Turing laureate |

### 4. security (6)
Security architecture, cryptography, vuln research, disclosure policy.

| Slug | Name | Anchor |
|---|---|---|
| `bruce-schneier` | Bruce Schneier | applied cryptography, security economics, policy |
| `alex-stamos` | Alex Stamos | ex-Facebook/Yahoo CISO; SentinelOne; trust & safety |
| `window-snyder` | Window Snyder | Thistle; firmware/IoT security, ex-Apple/Intel/Mozilla |
| `matthew-green` | Matthew Green | JHU; applied crypto, E2E encryption commentary |
| `tavis-ormandy` | Tavis Ormandy | Google Project Zero; vuln research |
| `katie-moussouris` | Katie Moussouris | Luta Security; bug bounty / VDP policy |

### 5. finops-cost (4)
Cloud cost engineering, FinOps practice.

| Slug | Name | Anchor |
|---|---|---|
| `corey-quinn` | Corey Quinn | Duckbill; AWS cost / billing snark |
| `jr-storment` | J.R. Storment | FinOps Foundation; "Cloud FinOps" |
| `mike-fuller` | Mike Fuller | FinOps Foundation; technical FinOps |
| `erik-peterson` | Erik Peterson | CloudZero CTO; cost-per-feature |

### 6. languages-runtimes (8)
Language design, type systems, compilers, runtimes.

| Slug | Name | Anchor |
|---|---|---|
| `guido-van-rossum` | Guido van Rossum | Python BDFL emeritus |
| `anders-hejlsberg` | Anders Hejlsberg | C#, TypeScript, Turbo Pascal; TS-in-Go rewrite |
| `rich-hickey` | Rich Hickey | Clojure; "Simple Made Easy," value of values |
| `graydon-hoare` | Graydon Hoare | Rust creator |
| `brendan-eich` | Brendan Eich | JavaScript; Brave/Mozilla |
| `yukihiro-matsumoto` | Yukihiro "Matz" Matsumoto | Ruby creator |
| `bjarne-stroustrup` | Bjarne Stroustrup | C++ creator |
| `chris-lattner` | Chris Lattner | LLVM/Clang/Swift/MLIR/Mojo; Modular |

### 7. systems-programming (7)
Low-level, OS, performance, systems craft.

| Slug | Name | Anchor |
|---|---|---|
| `john-carmack` | John Carmack | id/Oculus/Keen; performance-first, AGI now |
| `bryan-cantrill` | Bryan Cantrill | Oxide CTO; DTrace, illumos, hardware/software |
| `jonathan-blow` | Jonathan Blow | Braid/Witness; Jai, anti-bloat |
| `mitchell-hashimoto` | Mitchell Hashimoto | HashiCorp; Ghostty, Terraform/Vagrant |
| `ryan-dahl` | Ryan Dahl | Node.js, Deno |
| `brian-kernighan` | Brian Kernighan | C, Unix, AWK — **archetype** (persistent_signals) |
| `linus-torvalds` | Linus Torvalds | Linux kernel, Git |

### 8. web-and-frontend (6)
Frontend frameworks, web platform, UI engineering.

| Slug | Name | Anchor |
|---|---|---|
| `evan-you` | Evan You | Vue, Vite, VoidZero |
| `dan-abramov` | Dan Abramov | React, Redux; ex-Meta |
| `rich-harris` | Rich Harris | Svelte, SvelteKit; Vercel |
| `guillermo-rauch` | Guillermo Rauch | Vercel CEO; Next.js |
| `ryan-carniato` | Ryan Carniato | SolidJS; fine-grained reactivity |
| `adam-wathan` | Adam Wathan | Tailwind CSS |

### 9. architecture-testing-craft (8)
Software architecture, DDD, testing discipline, engineering craft.

| Slug | Name | Anchor |
|---|---|---|
| `martin-fowler` | Martin Fowler | refactoring, microservices, patterns; Thoughtworks |
| `kent-beck` | Kent Beck | TDD, XP, "tidy first" |
| `eric-evans` | Eric Evans | Domain-Driven Design |
| `sam-newman` | Sam Newman | "Building Microservices," monolith-to-micro |
| `michael-feathers` | Michael Feathers | "Working Effectively with Legacy Code" |
| `dhh` | David Heinemeier Hansson | Rails; "majestic monolith," anti-microservices/cloud |
| `gregor-hohpe` | Gregor Hohpe | enterprise integration patterns; "The Architect Elevator" |
| `barbara-liskov` | Barbara Liskov | LSP, abstraction, distributed systems; Turing laureate |

### 10. devops-platform (6)
DevOps movement, platform engineering, internal developer platforms.

| Slug | Name | Anchor |
|---|---|---|
| `gene-kim` | Gene Kim | "The Phoenix Project," DORA, "Wiring the Winning Org" |
| `jez-humble` | Jez Humble | Continuous Delivery; DORA |
| `nicole-forsgren` | Nicole Forsgren | "Accelerate," DORA metrics, DevEx research |
| `kelsey-hightower` | Kelsey Hightower | Kubernetes advocacy; ex-Google |
| `matthew-skelton` | Matthew Skelton | Team Topologies |
| `solomon-hykes` | Solomon Hykes | Docker; Dagger |

### 11. ai-assisted-coding (2 native + 2 cross-listed)
The AI-coding frontier — agentic dev tools, codegen.

| Slug | Name | Anchor |
|---|---|---|
| `michael-truell` | Michael Truell | Cursor / Anysphere CEO |
| `nat-friedman` | Nat Friedman | ex-GitHub CEO (Copilot era); investor |
| `andrej-karpathy` | Andrej Karpathy | **cross-listed from AI** — "vibe coding," software 2.0 |
| `sasha-rush` | Sasha Rush | **cross-listed from AI** — codegen eval, LLM systems |

---

## Cross-listed from AI (teams: [ai, engineering]; home_team: ai; no new research)

ML-systems voices that belong in both teams. Edit their existing AI persona files' `teams` arrays only:

`andrej-karpathy`, `sasha-rush`, `tri-dao`, `bryan-catanzaro`, `andrew-feldman`, `albert-gu`, `horace-he`, `woosuk-kwon`, `tim-dettmers`.

---

## Build waves (full roster, parallel research agents)

| Wave | Cell | Count | Personas |
|---|---|---|---|
| E1 | cloud-architecture | 8 | hamilton, vogels, cockcroft, brooker, burns, brewer, maccarthaigh, perlman |
| E2 | reliability-sre-obs | 7 | treynor-sloss, beyer, majors, sridharan, fong-jones, jones(nora), butow |
| E3 | data-and-storage | 8 | kleppmann, dean, ghemawat(archetype), helland, stonebraker, pavlo, hellerstein, lamport |
| E4 | security | 6 | schneier, stamos, snyder, green, ormandy, moussouris |
| E5 | finops-cost + languages-runtimes(pt1) | 4+4 | finops 4 + van-rossum, hejlsberg, hickey, hoare |
| E6 | languages-runtimes(pt2) + systems-programming | 4+7 | eich, matz, stroustrup, lattner + carmack, cantrill, blow, hashimoto, dahl, kernighan(archetype), torvalds |
| E7 | web-and-frontend + ai-assisted-coding | 6+2 | you, abramov, harris, rauch, carniato, wathan + truell, friedman |
| E8 | architecture-testing-craft | 8 | fowler, beck, evans, newman, feathers, dhh, hohpe, liskov |
| E9 | devops-platform | 6 | kim, humble, forsgren, hightower, skelton, hykes |

After all waves: cross-list 9 AI personas; adapt + run `build_registry.py --team engineering`; write 11 cell docs + SKILL.md; flip meta-registry `engineering.built = true`.
