# Tavis Ormandy — Research Notes

**Slug:** tavis-ormandy
**Cell:** security (cell_role: specialist)
**Home team:** engineering
**Compiled:** 2026-05-30
**Researcher:** Engineering Super Intelligence Team build, Wave E4

These are raw, dated research excerpts gathered via WebSearch / WebFetch so that
future re-syntheses do not need to re-crawl. Every claim that lands in the persona
frontmatter is sourced here.

---

## Identity confirmation (high confidence)

- **Real name:** Tavis Ormandy. English computer-security white-hat hacker.
- **Current status (2026):** Independent vulnerability researcher. Left Google on
  **2025-10-10** after nearly 20 years. He announced this himself on X:
  "A personal update... after nearly 20 years at Google, today is my last day!
  I'm going to be working on independent research for the foreseeable future,
  then who knows!"
  URL: https://x.com/taviso/status/1976724463103426860
- **Location:** San Francisco Bay Area (currently); originally from England.
- **Contact / presence:** taviso@gmail.com; GitHub github.com/taviso; X @taviso;
  Mastodon social.sdf.org/@taviso; personal site lock.cmpxchg8b.com; older blog
  blog.cmpxchg8b.com.
- Source: https://en.wikipedia.org/wiki/Tavis_Ormandy and https://lock.cmpxchg8b.com/

### CORRECTION TO TASK BRIEF
The task brief described him as a current "Google Project Zero vulnerability
researcher." This is **out of date**. As of 2025-10-10 he is **independent** —
no longer at Google or Project Zero. The persona `affiliations_2026` reflects
the independent status, with Google/Project Zero moved to `past_affiliations`.
His most recent work (39C3 talk, uMatrix post) is published under the independent
banner / his own site. Logged here per the "correct wrong assumptions" instruction.

---

## Employment history

- **Google (2009 – 2025-10-10):** ~20 years. Joined Google's security team in 2009.
- **Project Zero (2014 – 2025):** Founding-era member of Google Project Zero, the
  elite bug-hunting team launched July 2014 with its signature 90-day disclosure
  deadline and public bug tracker.
  Source: https://en.wikipedia.org/wiki/Project_Zero
- Before Google he was associated with the Gentoo Linux security team / full-disclosure
  community (the blog.cmpxchg8b.com "Security Debianisms" / ctypes.sh era).
- Now: **independent vulnerability researcher** (since 2025-10-10).

---

## Signature findings (chronological)

### Antivirus / security-software attack surface (2012 – 2016+)
The defining thesis of his career: **security software is itself a vast, highly
privileged attack surface.**

- **Sophos (2012):** "Sophail: Applied attacks against Sophos Antivirus." Concluded
  Sophos was "ill-equipped to handle the output of one co-operative security
  researcher." PDF: https://lock.cmpxchg8b.com/Sophail.pdf
- Quote (his recurring framing): "By design, antivirus products introduce a vast
  attack surface to a hostile environment" and vendors "have a responsibility to
  uphold the highest secure development standards possible to minimize the potential
  for harm caused by their software."
  Source: https://en.wikipedia.org/wiki/Tavis_Ormandy
- **FireEye (2015, with Natalie Silvanovich):** severe RCE.
- **Kaspersky (2015):** "Kaspersky: Mo Unpackers, Mo Problems." AV unpackers run
  attacker-controlled code at high privilege.
  Source: https://googleprojectzero.blogspot.com/2015/09/kaspersky-mo-unpackers-mo-problems.html
- **Symantec / Norton (2016):** wormable RCE across the entire Symantec product line,
  including kernel-level unpackers.
- **Trend Micro Password Manager (2016):** node.js debugger exposed; arbitrary command
  execution from any website. ("anyone on the internet can steal all of your
  passwords completely silently.")
- **Avast / ESET / Comodo / Malwarebytes (2016):** repeated emulator / unpacker bugs.
  ESET emulator flaw: https://www.pcworld.com/article/428235/critical-flaw-in-eset-products-shows-why-spy-groups-are-interested-in-antivirus-programs.html
- Cultural impact: "Antivirus Software Is 'Increasingly Useless' and May Make Your
  Computer Less Safe."
  Source: https://it.slashdot.org/story/16/07/08/145245/antivirus-software-is-increasingly-useless-and-may-make-your-computer-less-safe

### LastPass (2016 – 2017)
- Made testing LastPass a "pet project." Found multiple remote-credential-theft bugs
  in the Firefox / browser add-on (2016, July 2016) and three more in 2017 that could
  allow password theft from a previously visited site.
  Source: https://threatpost.com/lastpass-fixes-bug-that-leaks-credentials/148378/
- Reinforces the password-manager / browser-extension attack-surface theme.

### Cloudbleed (2017-02) — Cloudflare
- Disclosed by Project Zero on 2017-02-17. Ormandy noticed **corrupted web pages**
  returned through Cloudflare and realized memory was leaking.
- Cloudflare's HTML parser (Ragel-generated) buffer-overran, leaking adjacent memory:
  HTTP cookies, auth tokens, POST bodies, private messages — leaked to ANY Cloudflare
  customer and **cached by search engines.** Leaked >1,000,000 (some sources 18M+)
  times; could have started 2016-09-22.
- Cloudflare disabled the vulnerable features within hours; fully patched within ~3 days.
- Sources:
  - https://en.wikipedia.org/wiki/Cloudbleed
  - https://blog.cloudflare.com/incident-report-on-memory-leak-caused-by-cloudflare-parser-bug/
  - https://thehackernews.com/2017/02/cloudflare-vulnerability.html

### Zenbleed (2023-07) — AMD Zen 2, CVE-2023-20593
- Reported to AMD 2023-05-15; published ~2023-07-24.
- Root cause: mishandling of the `vzeroupper` instruction during speculative
  execution / mispredict recovery. Incorrect management of the z-bit in the Register
  Allocation Table lets data leak from the **shared vector register file** across
  isolation boundaries.
- His quote: "It doesn't matter if they're happening in other virtual machines,
  sandboxes, containers, processes, whatever!" and "It turns out that memory
  management is hard, even in silicon." On methodology: "It turns out that
  mispredicting on purpose is difficult to optimize!"
- Discovery method: **fuzzing + performance counters + "Oracle Serialization"** —
  compares a randomly generated program's execution against its serialized oracle to
  detect speculative inconsistencies.
- Leak rate: ~30 KB / core / second — fast enough to capture credentials in real time.
- Affects all Zen 2: Ryzen 3000/4000/5000U, Threadripper 3000, EPYC "Rome."
- Mitigation: microcode / AGESA update, or set chicken bit DE_CFG[9] (perf penalty).
- Write-up: https://lock.cmpxchg8b.com/zenbleed.html (July 2023)
- Sources:
  - https://thehackernews.com/2023/07/zenbleed-new-flaw-in-amd-zen-2.html
  - https://www.bleepingcomputer.com/news/security/zenbleed-attack-leaks-sensitive-data-from-amd-zen2-processors/

### Reptar (2023-11) — Intel, CVE-2023-23583
- "What happens when a CPU goes wrong" — write-up Nov 2023.
- Intel-side analogue: redundant prefix decoding (`rep movsb` + REX) caused machine
  state corruption / privilege escalation / DoS on Intel CPUs.
- Write-up: https://lock.cmpxchg8b.com/reptar.html

### EntrySign (2025-03) — AMD Zen 1–5 microcode, CVE-2024-56161
- AMD microcode **signature verification** weakness: the verification algorithm used
  AES-CMAC as a *hash* function. CMAC is a MAC, not a collision-resistant hash, so the
  team could forge valid signatures and load **arbitrary custom microcode** onto Zen
  1–5 cores.
- Disclosure timeline: 2025-01-21 Ormandy emailed oss-sec after an **Asus update page
  leaked the patch early** for a then-undisclosed "AMD Microcode Signature Verification
  Vulnerability"; full details + tooling 2025-03-05.
- Tool: **zentool** (and the AMD CPU "jailbreak" toolchain) — examine, author, sign,
  resign, and load microcode patches.
- Credited team: Josh Eads, Matteo Rizzo, Kristoffer Janke, Eduardo Vela Nava,
  Tavis Ormandy, Sophie Schmieg (Google Hardware Security Team).
- "You can now jailbreak your AMD CPU! We've just released a full microcode toolchain,
  with source code and tutorials." — https://x.com/taviso/status/1897333770644336774 (2025-03-05)
- Sources:
  - https://seclists.org/oss-sec/2025/q1/176
  - https://github.com/google/security-research/blob/master/pocs/cpus/entrysign/zentool/README.md
  - https://www.theregister.com/2025/01/23/asus_amd_processor_fix/
- NOTE: Some secondary sources conflate EntrySign with CVE-2024-36347 (a separate AMD
  Zen microcode loading issue). The canonical EntrySign signature-verification CVE is
  **CVE-2024-56161**. Persona cites CVE-2024-56161.

---

## RECENT SIGNAL (>= 3, all dated AFTER 2025-05-30)

1. **2025-08-20 — "Why are anime catgirls blocking my access to the Linux kernel?"**
   (Anubis critique). Argues Anubis's SHA-256 proof-of-work anti-AI-scraper gate is
   security theatre: an AI vendor "will have a datacenter full of compute capacity" and
   can solve the challenges for ~$0, while resource-constrained legitimate users (and
   accessibility tools) eat the cost. "This… makes no sense to me." Mining tokens for
   all ~11,500 Anubis-protected sites costs approximately zero dollars.
   - Blog: https://lock.cmpxchg8b.com/anubis.html
   - X: https://x.com/taviso/status/1958181778595909706
   - Coverage: https://hackaday.com/2025/08/22/this-week-in-security-anime-catgirls-illegal-adblock-and-disputed-research/
   - HN: https://news.ycombinator.com/item?id=44962529

2. **2025-10-10 — Departure from Google / Project Zero, going independent.**
   "after nearly 20 years at Google, today is my last day! I'm going to be working on
   independent research for the foreseeable future."
   - https://x.com/taviso/status/1976724463103426860

3. **2025-12-29 — 39C3 talk "The Angry Path to Zen: AMD Zen Microcode Tools and
   Insights."** Deep dive on the EntrySign microcode work, the microcode ROM, the
   tooling built, and how to write/test your own microcode on Zen 1–5. Tools under
   github.com/AngryUEFI. His first major public talk as an independent.
   - Fahrplan: https://fahrplan.events.ccc.de/congress/2025/fahrplan/event/the-angry-path-to-zen-amd-zen-microcode-tools-and-insights
   - Video: https://media.ccc.de/v/39c3-the-angry-path-to-zen-amd-zen-microcode-tools-and-insights
   - YouTube: https://www.youtube.com/watch?v=GrBSH2N5-lc

4. **2026-05 — "I miss the uMatrix Chrome extension"** (matrix³ prototype). Rebuilds
   uMatrix-style per-origin request control under Chrome MV3 using `declarativeNetRequest`
   + Content Security Policy + reporting endpoints. "You can't do *everything* that was
   possible in a callback declaratively… but practically the rules are flexible enough
   for everything I would ever want." A pragmatic counter to the "MV3 killed content
   blocking" narrative.
   - https://lock.cmpxchg8b.com/umatrix.html

---

## Public stances (each cited)

1. **Security software is a vast, highly privileged attack surface — often it makes you
   less safe.** "By design, antivirus products introduce a vast attack surface to a
   hostile environment."
   - https://en.wikipedia.org/wiki/Tavis_Ormandy
   - https://it.slashdot.org/story/16/07/08/145245/antivirus-software-is-increasingly-useless-and-may-make-your-computer-less-safe

2. **Full-disclosure-leaning / hard deadlines force vendor accountability.** Built his
   reputation releasing details on the Full Disclosure list when vendors stalled;
   aligned with Project Zero's 90-day deadline + public tracker.
   - https://fortune.com/2017/06/23/google-project-zero-hacker-swat-team/
   - https://en.wikipedia.org/wiki/Project_Zero

3. **Hardware/microcode is not a trust anchor — silicon has the same bugs as software.**
   Zenbleed, Reptar, EntrySign. "It turns out that memory management is hard, even in
   silicon." Microcode signature verification using CMAC-as-hash was forgeable.
   - https://lock.cmpxchg8b.com/zenbleed.html
   - https://seclists.org/oss-sec/2025/q1/176

4. **Proof-of-work / "clever" gates are usually security theatre when the threat model
   is wrong.** Anubis penalizes the wrong party (humans, not datacenters).
   - https://lock.cmpxchg8b.com/anubis.html

5. **Public PoCs and tooling are legitimate research output.** Ships working exploits
   (Zenbleed PoC) and full toolchains (zentool) so defenders and researchers can verify
   and reproduce, not just read prose.
   - https://x.com/taviso/status/1897333770644336774
   - https://github.com/google/security-research/blob/master/pocs/cpus/entrysign/zentool/README.md

6. **Browser-extension and password-manager surfaces deserve the same scrutiny as
   kernels.** LastPass / Trend Micro password-manager RCEs; the uMatrix MV3 rebuild.
   - https://threatpost.com/lastpass-fixes-bug-that-leaks-credentials/148378/
   - https://lock.cmpxchg8b.com/umatrix.html

---

## Productive conflict — full disclosure vs coordinated / bounty

`katie-moussouris` (Luta Security; architected Microsoft's bug bounty + the
international VDP/ISO 29147 & 30111 standards) is the natural foil. Moussouris champions
*structured, incentive-aligned, coordinated* disclosure and the economics of bug bounties;
Ormandy is temperamentally full-disclosure / hard-deadline and skeptical of bounty
programs as a substitute for vendors fixing root-cause engineering problems. Both are in
the engineering `security` cell (confirmed in ROSTER.md). This is the canonical pairing
the task brief flagged.

Secondary conflict: `alex-stamos` (security cell) — a more diplomacy- and
trust-&-safety-oriented, vendor-relationship-preserving posture vs Ormandy's blunt,
adversarial, "ship the PoC" style.

## Pairs well with (real ROSTER.md slugs)

- `bryan-cantrill` (systems-programming) — hardware/software boundary, blunt voice,
  DTrace-style observability of "what the machine actually does."
- `matthew-green` (security) — applied-crypto rigor; the CMAC-is-not-a-hash EntrySign
  finding is exactly Green's wheelhouse.
- `colm-maccarthaigh` (cloud-architecture) — TLS/networking attack surface, formal
  reasoning about protocol behavior; Cloudbleed-style edge-proxy memory safety.
- `john-carmack` (systems-programming) — performance/microarchitecture intuition,
  reading what silicon actually does on the mispredict path.

All four slugs verified present in ROSTER.md.

---

## Sources (master list)

- https://en.wikipedia.org/wiki/Tavis_Ormandy
- https://lock.cmpxchg8b.com/
- https://lock.cmpxchg8b.com/zenbleed.html
- https://lock.cmpxchg8b.com/reptar.html
- https://lock.cmpxchg8b.com/anubis.html
- https://lock.cmpxchg8b.com/umatrix.html
- https://lock.cmpxchg8b.com/Sophail.pdf
- https://x.com/taviso/status/1976724463103426860 (departure, 2025-10-10)
- https://x.com/taviso/status/1958181778595909706 (Anubis, 2025-08-20)
- https://x.com/taviso/status/1897333770644336774 (zentool release, 2025-03-05)
- https://seclists.org/oss-sec/2025/q1/176 (EntrySign oss-sec)
- https://github.com/google/security-research/blob/master/pocs/cpus/entrysign/zentool/README.md
- https://fahrplan.events.ccc.de/congress/2025/fahrplan/event/the-angry-path-to-zen-amd-zen-microcode-tools-and-insights
- https://media.ccc.de/v/39c3-the-angry-path-to-zen-amd-zen-microcode-tools-and-insights
- https://www.youtube.com/watch?v=GrBSH2N5-lc
- https://en.wikipedia.org/wiki/Cloudbleed
- https://blog.cloudflare.com/incident-report-on-memory-leak-caused-by-cloudflare-parser-bug/
- https://thehackernews.com/2023/07/zenbleed-new-flaw-in-amd-zen-2.html
- https://googleprojectzero.blogspot.com/2015/09/kaspersky-mo-unpackers-mo-problems.html
- https://it.slashdot.org/story/16/07/08/145245/antivirus-software-is-increasingly-useless-and-may-make-your-computer-less-safe
- https://threatpost.com/lastpass-fixes-bug-that-leaks-credentials/148378/
- https://fortune.com/2017/06/23/google-project-zero-hacker-swat-team/
- https://en.wikipedia.org/wiki/Project_Zero
- https://hackaday.com/2025/08/22/this-week-in-security-anime-catgirls-illegal-adblock-and-disputed-research/
