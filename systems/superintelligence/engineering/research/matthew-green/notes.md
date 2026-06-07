# Matthew Green — research notes

**Slug:** matthew-green
**Researched:** 2026-05-30
**Cell:** security (engineering-super-intelligence)
**Status:** active

Raw findings, dated quotes, and source URLs gathered for the persona synthesis. Saved so future re-syntheses do not re-crawl.

---

## Identity confirmation (high confidence)

- **Full name:** Matthew Daniel Green. Born 1976, Hanover, New Hampshire.
- **Current title:** Associate Professor of Computer Science, Johns Hopkins University, at the Information Security Institute (ISI). (Wikipedia; JHU faculty page — note `isi.jhu.edu/~mgreen/` returned HTTP 403 to the fetch tool but is referenced consistently across sources.)
- **Blog:** "A Few Thoughts on Cryptographic Engineering" — https://blog.cryptographyengineering.com/ (tagline: "Some random thoughts about crypto. Notes from a course I teach. Pictures of my dachshunds.")
- **Social:** Twitter/X handle is `@matthew_d_green` (https://x.com/matthew_d_green). Multiple sources note he has "mostly migrated to BlueSky" as of recent years, but the X account remains the canonical historical handle. The prompt's `@matthew_d_green` is correct.
- Identity is unambiguous. Confidence high.

## Education
- B.S. Computer Science, Oberlin College.
- B.M. Electronic Music, Oberlin College.
- M.S. Computer Science, Johns Hopkins University.
- Ph.D. Computer Science, Johns Hopkins University. Dissertation: "Cryptography for Secure and Private Databases."

## Career history
- **1999–2005:** AT&T Laboratories, Florham Park, NJ (audio coding, content distribution, streaming video).
- **2005–2011:** Co-founder and CTO, Independent Security Evaluators (with Avi Rubin).
- Co-founder of crypto companies: Zeutro, Sealance.
- Advisory roles: Linux Foundation Core Infrastructure Initiative; Mozilla Cybersecurity Delphi.
- **2005–present:** Johns Hopkins faculty.

## Notable research & discoveries
- **Zerocoin / Zerocash:** co-developer of the anonymous-cryptocurrency protocols that became the basis of Zcash. Influential contributor to Zcash.
- **TLS attacks:** involved in analysis around Logjam (2015) and the broader export-grade-crypto attack family. (Logjam's headline authors are Adrian et al.; Green is associated with the applied-crypto critique and commentary around these. See correction note below — verify attribution before stating Green is a named Logjam author.)
- **Dual EC DRBG backdoor:** Green's blog analysis of the NSA Dual_EC_DRBG backdoor and RSA Security's BSAFE usage of the backdoored CSPRNG was widely cited in mainstream media. This is a signature piece of his public work.
- **Hardware/protocol security:** exposed flaws in RSA BSAFE, Speedpass, E-ZPass, automotive immobilizer systems, satellite television piracy systems.
- **Open Crypto Audit Project:** co-founded; ran the public audit of TrueCrypt.

## The 2013 JHU / NSA blog takedown incident
- September 2013: Johns Hopkins' dean (Whiting School of Engineering) requested removal of Green's blog post discussing NSA encryption-weakening, citing "classified material" concerns. The university later apologized and the post was restored. This is a defining episode in his public-intellectual identity — academic freedom vs. institutional pressure on security research.

---

## CORRECTIONS / wrong-assumption log

1. **"Bugs in our Pockets" — Green is NOT an author.** The prompt and common association might suggest Green co-authored the canonical 2021/2024 client-side-scanning paper "Bugs in our Pockets: The Risks of Client-Side Scanning." He did **not**. The author list is: H. Abelson, R. Anderson, S. M. Bellovin, J. Benaloh, M. Blaze, J. Callas, W. Diffie, S. Landau, P. G. Neumann, R. L. Rivest, J. I. Schiller, B. Schneier, V. Teague, C. Troncoso. (arXiv 2110.07450; Journal of Cybersecurity vol 10 iss 1, 2024.) Green's anti-client-side-scanning position is documented in his **own blog posts** and his NYT op-ed, NOT in this paper. Persona key_publications must NOT list "Bugs in our Pockets" under Green. It can be cited in notes as the allied-community canon (his co-conspirators Schneier, Anderson, etc.), and supports the `pairs_well_with: bruce-schneier` link.

2. **Logjam authorship:** Green is closely associated with the export-grade-crypto attack discourse and commentary, but the primary Logjam academic paper ("Imperfect Forward Secrecy") is led by David Adrian et al. Do not assert Green as a named first-tier author of Logjam in the persona without a confirming citation. Persona attributes "applied-crypto attack commentary / TLS attack analysis" to him via his blog rather than claiming paper authorship.

3. **Title precision:** He is an **Associate** Professor (not full Professor as sometimes loosely stated). Frontmatter uses "Associate Professor."

---

## Public stances (each with evidence URL)

### Stance 1 — EU Chat Control is the most dangerous mass-surveillance design proposed in the free world
- Tweet (2023-03-09): "The EU's 'chat control' legislation is the most alarming proposal I've ever read. Taken in context, it is essentially a design for the most powerful text and image-based mass surveillance system the free world has ever seen."
  - https://x.com/matthew_d_green/status/1634252397919739921
- Blog "Remarks on 'Chat Control'" (2023-03-23): calls the Commission's Impact Assessment "deeply naive and alarming"; says regulators are "asking technology providers to deploy systems that none of them know how to build safely."
  - https://blog.cryptographyengineering.com/2023/03/23/remarks-on-chat-control/

### Stance 2 — Client-side scanning fundamentally breaks the privacy guarantee of E2EE ("confidential with an asterisk")
- Blog "Remarks on 'Chat Control'" (2023-03-23): client-side scanning creates "an exception to the privacy guarantees of encrypted systems" where data becomes confidential "with an asterisk." "Model extraction is a real possibility in all proposed client-side scanning systems today." Apple's 2021 proposal "failed" when "users were able to extract this code" within two weeks, enabling collision and evasion attacks.
  - https://blog.cryptographyengineering.com/2023/03/23/remarks-on-chat-control/

### Stance 3 — Apple's on-device CSAM scanning (NeuralHash) was "a really bad idea" and a step toward surveillance of encrypted messaging
- Tweet (2021-08-04): "I've had independent confirmation from multiple people that Apple is releasing a client-side tool for CSAM scanning tomorrow. This is a really bad idea."
  - https://x.com/matthew_d_green/status/1423071186616000513
- NYT op-ed with Alex Stamos (Aug 2021): "Apple Wants to Protect Children. But It's Creating Serious Privacy Risks." — urged Apple to pause until outside researchers could study the system; criticized lack of transparency.
  - Referenced via Wikipedia and 9to5Mac coverage (see sources). The op-ed is paywalled at nytimes.com.

### Stance 4 — "Ghost user" / exceptional-access proposals weaken security for everyone by exploiting an authentication vulnerability rather than fixing it
- Blog "On Ghost Users and Messaging Backdoors" (2018-12-17): the GCHQ ghost proposal "exploits a security vulnerability rather than fixing it, and it opens all users of the system to exploitation of that same vulnerability by others." Making the backdoor work "requires changing both the cloud computers ... and the client program on everyone's phone and computer, and that change makes all of those systems less secure."
  - https://blog.cryptographyengineering.com/2018/12/17/on-ghost-users-and-messaging-backdoors/

### Stance 5 — Extraordinary claims that a vendor secretly reads E2EE messages need extraordinary, forensically-visible evidence (skeptic in BOTH directions)
- Blog "WhatsApp Encryption, a Lawsuit, and a Lot of Noise" (2026-02-02): "I cannot definitively tell you that this is not the case. I can, however, tell you that if WhatsApp did this, they (1) would get caught, (2) the evidence would almost certainly be visible in WhatsApp's application code..." and "If you're going to (metaphorically) commit a crime, doing it in a forensically-detectable manner is very stupid." Recommends Signal for those who distrust Meta but rejects unsubstantiated backdoor conspiracy.
  - https://blog.cryptographyengineering.com/2026/02/02/whatsapp-encryption-a-lawsuit-and-a-lot-of-noise/

### Stance 6 — If you bother to encrypt something (e.g. LLM reasoning state), encrypt it properly; half-measures invite replay and side-channel leakage
- Blog "Let's talk about encrypted reasoning" (2026-05-29): "If you think reasoning state is worth encrypting, then properly encrypt it. It should not be replayable across sessions or accounts." "If I can convince a model to do secret-dependent reasoning, then there is almost certain to be leakage." (Timing / token-count side channels on encrypted LLM reasoning blobs.)
  - https://blog.cryptographyengineering.com/2026/05/29/fooling-around-with-encrypted-reasoning-blobs/

---

## Recent signal (12 months — all dated AFTER 2025-05-30)

1. **"Let's talk about encrypted reasoning"** — 2026-05-29 — encrypted LLM reasoning blobs are replayable + leak via timing/token side channels; "encrypt it properly." https://blog.cryptographyengineering.com/2026/05/29/fooling-around-with-encrypted-reasoning-blobs/
2. **"Anonymous credentials: an illustrated primer (Part 2)"** — 2026-04-17 — real-world anonymous-credential / Privacy Pass deployments; privacy-preserving alternatives to age-verification mandates. https://blog.cryptographyengineering.com/2026/04/17/anonymous-credentials-an-illustrated-primer-part-2/
3. **"Anonymous credentials: an illustrated primer"** — 2026-03-02 — foundational primer; positions anonymous auth as the privacy-preserving answer to age-verification legislation. https://blog.cryptographyengineering.com/2026/03/02/anonymous-credentials-an-illustrated-primer/
4. **"WhatsApp Encryption, a Lawsuit, and a Lot of Noise"** — 2026-02-02 — debunks the claim that Meta secretly reads WhatsApp plaintext; demands forensic evidence. https://blog.cryptographyengineering.com/2026/02/02/whatsapp-encryption-a-lawsuit-and-a-lot-of-noise/

(Note: blog also active on E2EE / EU scanning context in early-2026 posts; "state of encryption in early 2026" theme recurs — Meta E2EE friction with US/UK/AU/IN/EU governments.)

---

## Pairs / conflicts (verified against ROSTER.md security cell)

Security cell slugs: `bruce-schneier`, `alex-stamos`, `window-snyder`, `matthew-green`, `tavis-ormandy`, `katie-moussouris`.

- **pairs_well_with: bruce-schneier** — aligned anti-backdoor / anti-client-side-scanning policy voice; Schneier is a "Bugs in our Pockets" author and a long-time ally in the exceptional-access debate. Both treat security as economics + policy, not just math.
- **productive_conflict_with: alex-stamos** — they co-wrote the 2021 NYT op-ed but diverge on the broader encryption-vs-platform-safety tradeoff: Stamos is "constantly torn" and emphasizes the scale of real-world harm enabled by E2EE, advocating multi-stakeholder nuance and platform trust-and-safety investment; Green is closer to an encryption-absolutist who treats any scanning exception as a fatal architectural compromise. This is the canonical "encryption-vs-platform-safety" axis named in the build brief.
- **productive_conflict_with: katie-moussouris** (secondary) — Green's "extraordinary claims need forensic evidence / vendors would get caught" posture can undervalue the disclosure-and-incentive machinery Moussouris builds; she emphasizes structured VDP and the messy human/organizational reality of getting vulns fixed, vs. Green's "the code would reveal it" confidence.

---

## Signature moves observed
- Long-form "illustrated primer" explainers that make hard crypto (anonymous credentials, zero-knowledge, CSS) legible to non-cryptographers.
- Reads a security proposal and asks "what does this break that the proposer hasn't modeled?" — model extraction, collision/evasion, ghost-user auth weakening.
- "Forensic-detectability" test: would a secret backdoor be visible in the client code / would they get caught? Uses it to debunk both government backdoor demands AND backdoor conspiracy theories.
- Distinguishes "confidential" from "confidential with an asterisk" — the exception is the whole problem.
- Grounds policy arguments in concrete prior failures (Apple NeuralHash code extracted in two weeks; Dual EC DRBG).

## Voice style observed
- Wry, plain-spoken, slightly weary academic-blogger register. Self-deprecating ("Pictures of my dachshunds"). Uses hedging honestly ("I cannot definitively tell you that this is not the case") then lands a sharp practical conclusion. Comfortable saying a proposal is "naive," "alarming," or "a really bad idea" in plain words. Explains by analogy and worked example, not jargon dumps.

---

## Sources (collected)
1. https://blog.cryptographyengineering.com/ — main blog
2. https://blog.cryptographyengineering.com/author/matthewdgreen/ — author index (post list + dates)
3. https://en.wikipedia.org/wiki/Matthew_D._Green — bio
4. https://blog.cryptographyengineering.com/2026/05/29/fooling-around-with-encrypted-reasoning-blobs/ — recent (2026-05-29)
5. https://blog.cryptographyengineering.com/2026/04/17/anonymous-credentials-an-illustrated-primer-part-2/ — recent (2026-04-17)
6. https://blog.cryptographyengineering.com/2026/03/02/anonymous-credentials-an-illustrated-primer/ — recent (2026-03-02)
7. https://blog.cryptographyengineering.com/2026/02/02/whatsapp-encryption-a-lawsuit-and-a-lot-of-noise/ — recent (2026-02-02)
8. https://blog.cryptographyengineering.com/2023/03/23/remarks-on-chat-control/ — Chat Control remarks
9. https://blog.cryptographyengineering.com/2018/12/17/on-ghost-users-and-messaging-backdoors/ — ghost users / exceptional access
10. https://x.com/matthew_d_green/status/1634252397919739921 — Chat Control "most alarming proposal" tweet (2023-03-09)
11. https://x.com/matthew_d_green/status/1423071186616000513 — Apple CSAM "really bad idea" tweet (2021-08-04)
12. https://arxiv.org/abs/2110.07450 — "Bugs in our Pockets" (allied canon; Green NOT an author — see corrections)
13. https://9to5mac.com/2021/08/10/apple-child-protection-controversy-alex-stamos/ — Stamos nuance / Green–Stamos op-ed context
14. https://engineering.jhu.edu/faculty/matthew-green/ — JHU faculty page
