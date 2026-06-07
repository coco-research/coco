# Anders Hejlsberg — Research Notes

**Researched:** 2026-05-30
**Slug:** anders-hejlsberg
**Cell:** languages-runtimes (engineering)
**Cell role:** lead-driver
**Status:** active
**Confidence:** 0.97 — uniquely identified, public figure, decades of primary-source interviews and a major 2025–2026 shipping arc (TypeScript native Go port).

---

## Identity / disambiguation

Unambiguous. Anders Hejlsberg (born December 2, 1960, Copenhagen, Denmark) is a Microsoft Technical Fellow and one of the most prolific programming-language designers alive. There is exactly one person of this name in software history. No candidate confusion.

- Wikipedia: https://en.wikipedia.org/wiki/Anders_Hejlsberg
- GitHub handle: `ahejlsberg` — https://github.com/ahejlsberg

---

## Biographical timeline (verified)

- **1980** — While at the Technical University of Denmark (studied Electrical Engineering), began writing programs for the Nascom microcomputer, including a Pascal compiler marketed as **Blue Label Pascal** for the Nascom-2. Rewrote it for CP/M and MS-DOS as **Compas Pascal**, later **PolyPascal**.
- **Borland era** — PolyPascal licensed to Borland and became the engine for **Turbo Pascal**. Hejlsberg was original author of Turbo Pascal. Moved to California in 1989 as Chief Engineer at Borland; chief architect of **Borland Delphi** (object-oriented Pascal RAD environment).
- **1996** — Left Borland, joined Microsoft. Early work: **J++** language and **Windows Foundation Classes (WFC)**. Became Microsoft Distinguished Engineer, then Technical Fellow.
- **2000–present** — Lead architect of **C#** (the language and much of the .NET design). C# accreted generics (2.0), **LINQ (Language Integrated Query)** (3.0, 2007), async/await (5.0), pattern matching, nullable reference types over its lifetime — Hejlsberg drove much of this.
- **2012** — Announced **TypeScript**, a structurally-typed, gradually-typed superset of JavaScript that compiles to plain JS. Lead architect.
- **2023-03-16** — TypeScript 5.0 shipped (decorators standardization, among other things).
- **2024-08** — Began the ground-up rewrite of the TypeScript compiler/checker/language-service in **Go** (internal codename **Corsa**; original TS compiler codenamed **Strada**).
- **2025-03-11** — Announced "A 10x Faster TypeScript" (the native Go port), authored by Hejlsberg on the TypeScript devblog.
- **2025-08** — TypeScript became the #1 language on GitHub by monthly active contributors (Octoverse 2025), surpassing Python and JavaScript for the first time.
- **2026-03-23** — TypeScript 6.0 shipped (transitional release that prepares codebases for breaking changes coming in 7.0).

### Awards
- **2001 Dr. Dobb's Excellence in Programming Award** — for Turbo Pascal, Delphi, C#, .NET.
- **2007 Microsoft Technical Recognition Award for Outstanding Technical Achievement** (C# team).
- (Note: searched for a Computer History Museum Fellowship — could NOT confirm one in available sources. Omitting from profile to avoid an uncited claim.)

---

## The TypeScript native Go port ("tsgo" / Project Corsa / TS 7) — central recent arc

This is the most important recent signal cluster and the reason he is `lead-driver` of the languages-runtimes cell.

### Announcement (2025-03-11)
- Devblog post "A 10x Faster TypeScript," authored by Anders Hejlsberg. URL: https://devblogs.microsoft.com/typescript/typescript-native-port/
- The current JS-based compiler is codenamed **Strada** (TypeScript's original codename); the Go port is **Corsa**.
- The new compiler is called **tsgo** during the preview period. It will ship as the official `tsc` when **TypeScript 7.0** goes stable. The existing JS-based line continues as TypeScript **6.x** for compatibility.
- Preview available on npm as `@typescript/native-preview`; VS Code extension preview on the marketplace.

### Performance numbers (from the devblog and InfoWorld 2025-03-20)
- VS Code (~1.5M LOC): type-check 77.8s → 7.5s = **10.4x**.
- Playwright (356K LOC): 11.1s → 1.1s = **10.1x**.
- TypeORM (270K LOC): 17.5s → 1.3s = **13.5x**.
- Editor/IDE load time for VS Code: 9.6s → 1.2s = **~8x**.
- Memory usage roughly **halved (~50%)**.
- Direct quote (devblog): "The native implementation will drastically improve editor startup, reduce most build times by 10x, and substantially reduce memory usage."
- "The core value proposition of TypeScript is an excellent developer experience." — Hejlsberg, devblog.

### Why Go over Rust / C# / C++ (the most-debated decision)
Sources: TypeScript-Go GitHub FAQ (microsoft/typescript-go discussion), The New Stack 2025, architecture-weekly, InfoQ 2025-05.

- The dominant factor was **structural similarity to the existing codebase**, enabling a near-mechanical port. FAQ: "Idiomatic Go strongly resembles the existing coding patterns of the TypeScript codebase, which makes this porting effort much more tractable."
- The existing compiler relies on **shared mutable data, reference graphs, cyclic data structures, and pointer-heavy tree traversal**. Porting that to Go is straightforward; porting to Rust would force a fundamental redesign around the **borrow checker** and ownership.
- Hejlsberg (widely quoted from the March 2025 interview): Go is "the lowest-level language we can get to that gives us full, optimized, native-code support on all platforms, great control over data layout, the ability to have cyclic data structures and so forth. It gives you automatic memory management with a garbage collector and great access to concurrency."
- The compiler's allocation pattern (large upfront allocations that live for the whole program) means GC overhead stays low — so Go's GC is acceptable here.
- Acknowledged tradeoff (FAQ): "Go's in-proc JS interop story is not as good as some of its alternatives." They committed to a performant JS API anyway.
- C# was considered and experimented with but not chosen. GitHub Blog interview quote: "We experimented with C#, with others, and finally chose Go. The performance gain was 10X." Note the diplomatic framing — picking Go over Microsoft's own C# was itself notable.
- "We have a native compiler that's a carbon copy of the old one down to the quirks." — Hejlsberg, GitHub Blog interview (2025-11-06). Captures the deliberate behavior-preserving-port philosophy: do NOT redesign the type system during the rewrite.

### Progress milestones after May 2025 (recent signals, post-cutoff 2025-05-30)
- **2025-09-30** — Microsoft for Developers blog: TypeScript 7 native preview lands in **Visual Studio 2026** Insiders. ~8x faster project load; faster "Find All References" / "Go to Definition." Honest about gaps: "missing Quick Fix support" still. URL: https://developer.microsoft.com/blog/typescript-7-native-preview-in-visual-studio-2026
- **2025-11-06** — GitHub Blog interview "TypeScript's rise in the AI era." TypeScript hit #1 on GitHub. Rich AI/types quotes (below). URL: https://github.blog/developer-skills/programming-languages-and-frameworks/typescripts-rise-in-the-ai-era-insights-from-lead-architect-anders-hejlsberg/
- **2026-03-23** — TypeScript 6.0 shipped as the transitional release ahead of 7.0 (the Go-native `tsc`). Confirms 7.0 / Corsa is the active forward line.

---

## AI-era stances (GitHub Blog, 2025-11-06) — verbatim quotes

- "AI's ability to write code in a language is proportional to how much of that language it's seen. It's a big regurgitator, with some extrapolation. AI has seen tons of JavaScript, Python, and TypeScript so it's great at writing them."
- "If you ask AI to translate half a million lines of code, it might hallucinate. But if you ask it to generate a program that does that translation deterministically, you get a reliable result. That's the kind of problem types were made for."
- "AI started out as the assistant. Now it's doing the work, and you're supervising. It doesn't need an IDE the way we do. It needs the services." — i.e. the language server / type-checker is the substrate AI agents consume, which directly motivates a fast native compiler + LSP.
- "I remember thinking, maybe we'll get 25% of the JavaScript community to take an interest — that would be success. But where we are now? I'm floored." (on TypeScript adoption)

Octoverse 2025 (GitHub Blog news, ~2025-10-29/31): TypeScript finished August 2025 with ~2,636,006 monthly active contributors, edging Python by ~42,000; +66% YoY. AI-assisted development credited as a driver — stricter types make agent-generated code more reliable.
URL: https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/

---

## Design philosophy (durable, multi-decade — drawn from interviews / known canon)

- **Gradual / optional typing**: TypeScript meets JavaScript where it is — you can adopt types incrementally; `any` is an escape hatch; the type system is erasable at runtime. This is the opposite of a sound-from-day-one stance; TS deliberately trades soundness for pragmatism and adoption.
- **Structural typing**: TypeScript types are structural (duck-typed), not nominal. A value fits a type if its shape matches. This was a deliberate fit to JavaScript's object-literal culture.
- **Tooling-first language design**: For Hejlsberg, the editor/IDE experience (IntelliSense, refactorings, instant errors) is not an afterthought — it is the product. C# and TypeScript were both designed so the compiler is also a language service. The Go port is explicitly justified by IDE responsiveness, not just batch build speed.
- **Pragmatism over purity**: recurring theme across Turbo Pascal (fast, cheap, one-pass compiler in an era of slow expensive ones), Delphi, C#, and TypeScript. Ship something developers will actually use.
- **Backward compatibility is sacred**: the Go rewrite is a behavior-preserving "carbon copy … down to the quirks," not a chance to fix the type system. Compatibility discipline.
- **Lifetime craft**: Aarthi & Sriram podcast framing — "the power of working on something over a lifetime." He has been refining essentially the same craft (compilers + developer tooling) for ~45 years.

---

## Roster relationships (verified against engineering/ROSTER.md)

Cell `languages-runtimes` members: guido-van-rossum, anders-hejlsberg, rich-hickey, graydon-hoare, brendan-eich, yukihiro-matsumoto (matz), bjarne-stroustrup, chris-lattner.

### pairs_well_with
- **chris-lattner** — both are compiler/toolchain architects obsessed with developer experience and IDE responsiveness (LLVM/Clang/Swift/MLIR vs TS/C#). Lattner's "compiler is a library / language server" worldview rhymes with Hejlsberg's tooling-first design. Strong amplification on language-server architecture.
- **brendan-eich** — JavaScript's creator. TypeScript exists *because of and on top of* JS; Hejlsberg's whole structural-typing design is a pragmatic accommodation of Eich's language. Natural collaborators on "what should the JS/TS platform be."
- **bjarne-stroustrup** — both believe in incremental adoption, backward compatibility as a moral commitment, and meeting a huge existing user base where it is (C++ on C; TS on JS). Shared "pragmatism over purity, don't break the world" temperament.

### productive_conflict_with
- **guido-van-rossum** — sharpest, most concrete typing disagreement on the roster. Python's type hints (PEP 484, which Guido drove) are *optional and non-enforced at runtime* and the type system is largely **nominal-leaning / protocol-based**, layered onto a dynamic language late. TypeScript is **structural**, erasable, and was designed as a typed layer from the start with deep IDE integration. They would argue productively about how aggressively a gradual type system should constrain a dynamic language, and about structural vs nominal/protocol typing. (Guido did much of the foundational mypy/typing work at Dropbox; the philosophies genuinely differ.)
- **rich-hickey** — Hickey's "Simple Made Easy" / Clojure worldview is that static type systems add *incidental complexity* and that data should be open maps validated at the edges (spec/Malli), not closed compile-time types. Hejlsberg's entire career is the bet that static types + tooling are worth the complexity. This is a real, deep, well-defined philosophical fault line (types-as-truth vs types-as-incidental-complexity), perfect for productive conflict.

---

## Signature moves (synthesized from the above, all traceable)

- Port, don't redesign: "a carbon copy of the old one down to the quirks." Preserve behavior; change only the substrate.
- Pick the language that fits the *existing code's shape*, not the trendiest one — Go over Rust because the codebase is pointer-graph-heavy and the borrow checker would force a rewrite.
- Optimize the IDE loop first; batch build speed is a side effect of language-server speed.
- Gradual adoption beats purity — give people an escape hatch (`any`) and let them ratchet toward stricter types.
- Structural typing: match shapes, not names.
- Backward compatibility is non-negotiable; don't break the world.
- "Types are for the deterministic problems" — in the AI era, use AI to *write the transformer*, and use types to *prove the transform*, rather than trusting the AI to do the transform itself.

---

## Blind spots / under-weights (analytical, inverse of stances)

- **Soundness skeptics' point**: TypeScript is deliberately *unsound* (bivariance, `any`, type assertions). Hejlsberg consistently defends this as pragmatism; critics (and the Rich Hickey / sound-types camps) argue it gives a false sense of safety. He tends to under-weight the cost of an unsound type system at very large scale.
- **Microsoft-platform gravity**: his canon (C#, .NET, TypeScript, VS / VS Code) is Microsoft-shaped. He under-weights non-Microsoft ecosystem constraints and the politics of picking Go over Microsoft's own C# (he was diplomatic but it was a real internal tension).
- **Backward-compat conservatism can ossify**: the "down to the quirks" discipline preserves long-standing footguns of the TS type system; he is reluctant to use a rewrite as a chance to fix design debt.
- **Runtime / systems concerns are not his lens**: he thinks compiler-front-end and developer-tooling, not GC tuning at scale, distributed systems, or operational reliability.

---

## All URLs collected (for sources block)

1. https://en.wikipedia.org/wiki/Anders_Hejlsberg
2. https://devblogs.microsoft.com/typescript/typescript-native-port/  (2025-03-11, authored by Hejlsberg)
3. https://github.blog/developer-skills/programming-languages-and-frameworks/typescripts-rise-in-the-ai-era-insights-from-lead-architect-anders-hejlsberg/  (2025-11-06)
4. https://developer.microsoft.com/blog/typescript-7-native-preview-in-visual-studio-2026  (2025-09-30)
5. https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/  (Octoverse 2025)
6. https://thenewstack.io/microsoft-typescript-devs-explain-why-they-chose-go-over-rust-c/  (why Go over Rust/C#)
7. https://www.infoworld.com/article/3849654/typescript-gets-go-faster-stripes.html  (2025-03-20)
8. https://www.infoq.com/news/2025/05/new-typescript-compiler-10x-fast/  (2025-05)
9. https://www.architecture-weekly.com/p/typescript-migrates-to-go-whats-really  (Go-vs-Rust analysis)
10. https://newsletter.pragmaticengineer.com/p/typescript-c-and-turbo-pascal-with  (career retrospective interview)
11. https://www.aarthiandsriram.com/p/our-dream-conversation-anders-hejlsberg  ("working on something over a lifetime")
12. https://github.com/ahejlsberg  (GitHub profile)
13. https://www.welcometothejungle.com/en/articles/anders-hejlsberg-microsoft-career  (biography)
14. https://en.wikipedia.org/wiki/TypeScript  (TS 5.0 / decorators / structural typing)

### Corrected assumptions
- The task prompt mentioned "gradual typing" as one of his signatures — confirmed correct; TypeScript is a gradual + structural type system. Kept.
- The prompt suggested productive conflict "with guido-van-rossum on typing, rich-hickey" — both confirmed as roster members in languages-runtimes and both are genuine, well-grounded conflicts (structural-from-start vs nominal/optional-late typing; static types vs simplicity-of-open-data). Used both.
- Could NOT confirm a "Computer History Museum Fellow" award — deliberately omitted rather than assert uncited.
