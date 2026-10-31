# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

---

## [1.11.0](https://github.com/coco-research/coco/compare/v1.10.0...v1.11.0) (2026-10-31)


### Features

* **adapter:** add Aider CLI adapter with AGENTS.md and .aider.conf.yml generation ([#148](https://github.com/coco-research/coco/issues/148)) ([9614b9e](https://github.com/coco-research/coco/commit/9614b9e6ed596acdfcdb37806dc8a43b8d6de818))
* **adapter:** add Amazon Q Developer adapter with rules and agents support ([#153](https://github.com/coco-research/coco/issues/153)) ([1649ad1](https://github.com/coco-research/coco/commit/1649ad1321716aa52febf1366f8bddc69f0e20f3))
* **adapter:** add Cline VS Code extension adapter with rules and agents support ([#151](https://github.com/coco-research/coco/issues/151)) ([c85fa49](https://github.com/coco-research/coco/commit/c85fa492af87f0af05185fe0fa89c47e4de7aa89))
* **adapter:** add GitHub Copilot CLI adapter with AGENTS.md and copilot-instructions generation ([#154](https://github.com/coco-research/coco/issues/154)) ([655467a](https://github.com/coco-research/coco/commit/655467ace46432472955ac6734fde1541c3ff065))
* **adapter:** add PI-Desktop — one command from clone to in-app ([#166](https://github.com/coco-research/coco/issues/166)) ([3b937ad](https://github.com/coco-research/coco/commit/3b937addba42818e62995f9c0763f8ad37fd91f1))
* **adapter:** add Roo Code VS Code extension adapter with rules and agents support ([#152](https://github.com/coco-research/coco/issues/152)) ([2f2eed4](https://github.com/coco-research/coco/commit/2f2eed49960ae6d230cb8670c1f5d9786f6e0458))
* **adapter:** add Windsurf (Codeium) adapter with skills, rules, agents, and systems support ([#147](https://github.com/coco-research/coco/issues/147)) ([2e88675](https://github.com/coco-research/coco/commit/2e88675769394a53ba627775fb90bb0aeeeb75ba))
* **adapter:** add Zed editor adapter with rules and agents support ([#149](https://github.com/coco-research/coco/issues/149)) ([5e4d29f](https://github.com/coco-research/coco/commit/5e4d29f22ac6dd68f33b64487638c1dff9f37899))
* **adapter:** complete VS Code Continue adapter with skills, agents, and rules support ([#150](https://github.com/coco-research/coco/issues/150)) ([d3110a4](https://github.com/coco-research/coco/commit/d3110a4b1f3b46db0accc16ca21a538e6d76e8f3))
* **adapters:** add Grok Build / Grok CLI adapter ([#126](https://github.com/coco-research/coco/issues/126)) ([3d026a0](https://github.com/coco-research/coco/commit/3d026a064095af09b569702db4a66f1e0b6c2e85))
* **adapters:** real VS Code adapter, replacing the Continue stub ([#107](https://github.com/coco-research/coco/issues/107)) ([52c217a](https://github.com/coco-research/coco/commit/52c217abdee6251b0430e25cc32d834604024207))
* add bootstrap installer with auto-detect and quick install ([73f0d0c](https://github.com/coco-research/coco/commit/73f0d0cab2b5a7a3f10b5ffe7fff333804153aaf))
* add Hermes Agent adapter ([#118](https://github.com/coco-research/coco/issues/118)) ([896e2c5](https://github.com/coco-research/coco/commit/896e2c53146b40bdf1e898e5e083c287df0d557d))
* **agent-self-eval:** add post-run quality scoring skill and /self-eval command ([#157](https://github.com/coco-research/coco/issues/157)) ([405d1dc](https://github.com/coco-research/coco/commit/405d1dcbdbdc5061baec961d0f6d0cf2d23f1020))
* **agents:** add prompt injection defense baseline to all core agents ([#143](https://github.com/coco-research/coco/issues/143)) ([eb73168](https://github.com/coco-research/coco/commit/eb73168d22c6c2424f72ce5d1cafdabcfa0424a2))
* **agents:** vendor 22 claude-code-templates agents with MIT attribution ([#94](https://github.com/coco-research/coco/issues/94)) ([1864fa9](https://github.com/coco-research/coco/commit/1864fa9c8785effca4324cc96953d7c0e1fbbb62))
* **brand:** rebrand to CoCo Super Intelligence; migrate to coco-research org ([#40](https://github.com/coco-research/coco/issues/40)) ([2b64538](https://github.com/coco-research/coco/commit/2b6453812a6e3a3989b676ef1bfc8b7799fd0421))
* **ci:** asset-count single source of truth (docs/asset-counts.json + drift gate) ([#122](https://github.com/coco-research/coco/issues/122)) ([0d76176](https://github.com/coco-research/coco/commit/0d76176bae127cfb692a9ad3c49d958024a9c91b))
* clarify and improve Codex AGENTS behavior ([9777dd4](https://github.com/coco-research/coco/commit/9777dd41d6152b7ec75f03aea41fbc5a0763f24b))
* **context-budget:** add token audit skill and /context-budget command ([#156](https://github.com/coco-research/coco/issues/156)) ([fb0fb63](https://github.com/coco-research/coco/commit/fb0fb633cb34a8055a01b87c7678d4bfe09a31ff))
* **counts:** derive persona, department and adapter counts, and gate them ([#179](https://github.com/coco-research/coco/issues/179)) ([617f2f6](https://github.com/coco-research/coco/commit/617f2f69e2b7d2f416dbe46a5ecd6b3b5c985b7c))
* **cursor:** --systems superintelligence writes SI commands to ~/.cursor/commands ([#124](https://github.com/coco-research/coco/issues/124)) ([74cc677](https://github.com/coco-research/coco/commit/74cc6775550a915d0133346f27b70acc7535abd3))
* **email:** triage + noise subcommands — rules-based inbox de-noising (salvaged from old working checkout) ([a59c19c](https://github.com/coco-research/coco/commit/a59c19c83f49b5df4a071d5ee88d74566a4d9b9a))
* **evals:** code-verification pilot skill with grader ([#367](https://github.com/coco-research/coco/issues/367)) ([6161a19](https://github.com/coco-research/coco/commit/6161a1956418b3f22be95f2816ff4f2e7bb951c4))
* **evals:** core of the skill improvement round (proposal checks, compose, dev and held-out gates) ([#360](https://github.com/coco-research/coco/issues/360)) ([1e54be4](https://github.com/coco-research/coco/commit/1e54be424c588d9954f5f365ab93beab4b6eccd0))
* **evals:** generate-tests and humanizer pilot skills with graders ([#365](https://github.com/coco-research/coco/issues/365)) ([4a60a1e](https://github.com/coco-research/coco/commit/4a60a1ea6b9e8520f91bfb3c5de9228a89566360))
* **evals:** improvement-round helpers (dev-only proposer workspace, round ledger, gates) ([#376](https://github.com/coco-research/coco/issues/376)) ([2f179b7](https://github.com/coco-research/coco/commit/2f179b7f18990772fe6074a9159247b95867d303))
* **evals:** paired bootstrap and FDR for candidate-vs-baseline decisions (RSI PR 3) ([46b82fc](https://github.com/coco-research/coco/commit/46b82fce3b8bf887977cf8e318e57e924255bd71))
* **evals:** paired bootstrap and FDR for RSI decisions ([#311](https://github.com/coco-research/coco/issues/311)) ([46b82fc](https://github.com/coco-research/coco/commit/46b82fce3b8bf887977cf8e318e57e924255bd71))
* **evals:** prd-generator, c4-architecture and writing-plans pilot skills with graders ([#359](https://github.com/coco-research/coco/issues/359)) ([037bd23](https://github.com/coco-research/coco/commit/037bd237d0f38a9614a5f559e2cc29b76b0eb5b0))
* **evals:** run one skill improvement round (run_round + CLI) ([#379](https://github.com/coco-research/coco/issues/379)) ([26935fa](https://github.com/coco-research/coco/commit/26935fa942fc660d611283a8b8f0c98216323f91))
* **evals:** skill eval harness with dev and held-out splits ([#351](https://github.com/coco-research/coco/issues/351)) ([08122a2](https://github.com/coco-research/coco/commit/08122a2d74cd2cc46cfa2164f8af7f0cb4beaee0))
* **evals:** T1 routing set and scorer for the SI router ([#307](https://github.com/coco-research/coco/issues/307)) ([cb9a5a6](https://github.com/coco-research/coco/commit/cb9a5a69410afa0a180d12cc8d1db63f7109ada4))
* **evals:** T1 routing set and scorer for the SI router (RSI week 1, PR 2) ([cb9a5a6](https://github.com/coco-research/coco/commit/cb9a5a69410afa0a180d12cc8d1db63f7109ada4))
* **goal:** add persistent goal skill and /coco:goal command ([#164](https://github.com/coco-research/coco/issues/164)) ([f838b81](https://github.com/coco-research/coco/commit/f838b814092e693bf3dc9f1780945bb7da999b7b))
* **hyperframes:** make media-use telemetry opt-in ([ac8a3b7](https://github.com/coco-research/coco/commit/ac8a3b78d460282d79b421f6b60bbb4d1c4b6a1a))
* **hyperframes:** make media-use telemetry opt-in ([#280](https://github.com/coco-research/coco/issues/280)) ([ac8a3b7](https://github.com/coco-research/coco/commit/ac8a3b78d460282d79b421f6b60bbb4d1c4b6a1a))
* **index:** record what each adapter actually delivers, and rebuild the stale arch index ([#169](https://github.com/coco-research/coco/issues/169)) ([c9d7023](https://github.com/coco-research/coco/commit/c9d7023e26fec0a7f660315a1ee5b9f4163ba87b))
* **install:** --uninstall removes only what the install recorded and restores originals ([#388](https://github.com/coco-research/coco/issues/388)) ([678823c](https://github.com/coco-research/coco/commit/678823cde74dfa090557d0812f9c785483b9fc12))
* **install:** --workflow links coco-gate and the workflow hooks, and prints the hook lines ([#403](https://github.com/coco-research/coco/issues/403)) ([95b3ddc](https://github.com/coco-research/coco/commit/95b3ddceb8ee8e96d9cf81f2e2ce3856ff89a600))
* **install:** JSON plan and manifest of every path the Claude Code installer writes ([#387](https://github.com/coco-research/coco/issues/387)) ([cddf10c](https://github.com/coco-research/coco/commit/cddf10c019e8b1f3f7282bd6ab8476da94cff562))
* **learning:** add Brain DB decisions sync for high-confidence instincts ([#162](https://github.com/coco-research/coco/issues/162)) ([ca77e3a](https://github.com/coco-research/coco/commit/ca77e3a73dd2634a5ecb070200df6617aac1845c))
* **learning:** add CLI interface and slash commands for learning system ([#160](https://github.com/coco-research/coco/issues/160)) ([cadd86d](https://github.com/coco-research/coco/commit/cadd86d39597628c4cffd15f882ca07195e13464))
* **learning:** add observation capture hook ([#158](https://github.com/coco-research/coco/issues/158)) ([09047c5](https://github.com/coco-research/coco/commit/09047c57c5aa9328c4282cf249a43f827431c00e))
* **learning:** add pattern detector and restore core learning modules ([#159](https://github.com/coco-research/coco/issues/159)) ([e4cb9d3](https://github.com/coco-research/coco/commit/e4cb9d3ef0a927e33c022d83728af5ff4559c16b))
* **learning:** add team feedback to instincts bridge ([#161](https://github.com/coco-research/coco/issues/161)) ([7a9e180](https://github.com/coco-research/coco/commit/7a9e180297bdadc108f3e725de08ae1baf01a42c))
* **learning:** add unified memory cross-agent context vault ([#163](https://github.com/coco-research/coco/issues/163)) ([d0888e5](https://github.com/coco-research/coco/commit/d0888e538d127007e3bff71db91c131e16b12be8))
* **local-llm:** local inference ops — mlx-dspark wiring, reasoning-hang fix, skill + command ([#110](https://github.com/coco-research/coco/issues/110)) ([b5222eb](https://github.com/coco-research/coco/commit/b5222eb441890b8cec5e946ef80f23ebca4496e9))
* **m0:** add M0 cross-tool agent memory as an opt-in bundle ([#88](https://github.com/coco-research/coco/issues/88)) ([4f73d1c](https://github.com/coco-research/coco/commit/4f73d1c38e247433fd6ce8d08f8518faaac5dae9))
* **mcp:** add MCP server catalog with 8 connector configurations ([#155](https://github.com/coco-research/coco/issues/155)) ([a6e4c8c](https://github.com/coco-research/coco/commit/a6e4c8c81acf705553f3b3d11931ddd9776c2ed9))
* **npm:** rename the package to cocosuperintelligence and publish unscoped ([#92](https://github.com/coco-research/coco/issues/92)) ([1c54719](https://github.com/coco-research/coco/commit/1c5471961ff3a586c71ae0f82753f08edc1928db))
* **packs:** add a content gate for pack files ([bf07637](https://github.com/coco-research/coco/commit/bf07637ce32aab8664ef057e70ba42de772bcdc5))
* **packs:** add a content gate for pack files ([#282](https://github.com/coco-research/coco/issues/282)) ([bf07637](https://github.com/coco-research/coco/commit/bf07637ce32aab8664ef057e70ba42de772bcdc5))
* **packs:** add pack.json to every installable bundle, with a schema gate ([#281](https://github.com/coco-research/coco/issues/281)) ([5ca3078](https://github.com/coco-research/coco/commit/5ca3078720c72ca9fecb94e568c42259d6ad5381))
* **packs:** add pack.json to every installable bundle, with a schema… ([5ca3078](https://github.com/coco-research/coco/commit/5ca3078720c72ca9fecb94e568c42259d6ad5381))
* **readme:** add hero demo GIF of a real /SI-Decide --debate run ([#34](https://github.com/coco-research/coco/issues/34)) ([c6aa7a2](https://github.com/coco-research/coco/commit/c6aa7a277c56e71e340c672694d587d4bd87ca25))
* **router:** record decision outcomes (rerouted, kept, overridden, bad) in the local log ([#353](https://github.com/coco-research/coco/issues/353)) ([1689866](https://github.com/coco-research/coco/commit/16898661f401170d451189c333efc1f1dbae0e07))
* **si:** add --debate deliberation mode to SI council generators ([c055813](https://github.com/coco-research/coco/commit/c055813cafc98a8e7a1244086e996e38810c5fcd))
* **si:** add Climate & Energy Super Intelligence team (25 personas) ([#137](https://github.com/coco-research/coco/issues/137)) ([110bd1e](https://github.com/coco-research/coco/commit/110bd1eeef1a36a183165839edd52e9cc664be9c))
* **si:** add Education & EdTech Super Intelligence team (25 personas) ([#136](https://github.com/coco-research/coco/issues/136)) ([783c181](https://github.com/coco-research/coco/commit/783c181c0ec952323be94ffd790fcfd11d4a2c9e))
* **si:** add Healthcare & Life Sciences Super Intelligence team (25 personas) ([#135](https://github.com/coco-research/coco/issues/135)) ([678e41e](https://github.com/coco-research/coco/commit/678e41e310609fbd2959ce0f3009d2d5a4db98d0))
* **si:** add Legal & IP Super Intelligence team (31 personas) ([#134](https://github.com/coco-research/coco/issues/134)) ([4c500de](https://github.com/coco-research/coco/commit/4c500de756688e7673a4f71ec4f43c97ba46ca7a))
* **si:** plain-English front door — /SI and /SI-&lt;Team&gt; infer the verb and dials from the prompt ([3f9ba03](https://github.com/coco-research/coco/commit/3f9ba03aaaef9298357caf6b04c5fb4e1813af54))
* **si:** schema, layer model and validator for the 37 team roles — and all 37 redefined ([#171](https://github.com/coco-research/coco/issues/171)) ([90daa58](https://github.com/coco-research/coco/commit/90daa58b66df726fba8e993215513df087d9aa87))
* **site:** add CoCo Ads as its 15th product, with a real 30s self-demo ([#105](https://github.com/coco-research/coco/issues/105)) ([455ad13](https://github.com/coco-research/coco/commit/455ad133b6fe889a878d70ee4b2f09bad555a946))
* **site:** add CoCo Connect screenshot to its product panel ([#104](https://github.com/coco-research/coco/issues/104)) ([5c34cfa](https://github.com/coco-research/coco/commit/5c34cfa8ef763c0503de5c83a49891d896e3ceef))
* **site:** add meta description + OG/Twitter tags, fix About nav label ([#106](https://github.com/coco-research/coco/issues/106)) ([e5f0560](https://github.com/coco-research/coco/commit/e5f056071205dd5befcbca7eecb470a10343c4cf))
* **site:** add product and sales contact addresses to the footer ([#101](https://github.com/coco-research/coco/issues/101)) ([ee7e60f](https://github.com/coco-research/coco/commit/ee7e60f82644bae78b0868c398957d3be5f1e817))
* **site:** add the launch film to the homepage flagship band ([#100](https://github.com/coco-research/coco/issues/100)) ([2d6af8a](https://github.com/coco-research/coco/commit/2d6af8a3e73e6efa4c4446dae0a9085b4614c1c4))
* **site:** org homepage at root, CoCo's deep dive moves to /coco/ ([#98](https://github.com/coco-research/coco/issues/98)) ([a97944c](https://github.com/coco-research/coco/commit/a97944c67b01e2751c541a4bc8e77e27b12f6863))
* **site:** publish cocoresearch.org landing page from repo root ([#97](https://github.com/coco-research/coco/issues/97)) ([23436fc](https://github.com/coco-research/coco/commit/23436fcb0bf0095bccdeaf26c5f970a061b011b8))
* **si:** wire 4 new departments into the registry and quality pipeline ([#138](https://github.com/coco-research/coco/issues/138)) ([a7a3775](https://github.com/coco-research/coco/commit/a7a3775727acdd1b7d442fe37db25db5a27a9db3))
* **skill-evolution:** add the loop's skill tree and move the counts ([#200](https://github.com/coco-research/coco/issues/200)) ([af82d37](https://github.com/coco-research/coco/commit/af82d37f505712537711eb4b89315d3e9f46e838))
* **skill-evolution:** plan task 2 - ledger.py ([#269](https://github.com/coco-research/coco/issues/269)) ([f0fd09c](https://github.com/coco-research/coco/commit/f0fd09c9ae02f769c0a8f020aa24577fb35ae8b1))
* **skills/goal:** persistent goal skill with continuous-execution loop semantics ([#123](https://github.com/coco-research/coco/issues/123)) ([383d656](https://github.com/coco-research/coco/commit/383d6567f6ab1e6ba6411aeb4e71378f555589eb))
* **skills:** add cli-anything methodology skill + coco-cli pilot wrapper (attribution: HKUDS/CLI-Anything) ([b0a47dd](https://github.com/coco-research/coco/commit/b0a47dd9a335889cf0ea2a16162f0bc78a7f325e))
* **skills:** add coco-diagram editorial diagram skill ([#95](https://github.com/coco-research/coco/issues/95)) ([7f2652c](https://github.com/coco-research/coco/commit/7f2652ce32e751ad5b679eeb599b482c3be691bc))
* **skills:** add HeyGen HyperFrames bundle (LICENSE + hyperframes skill, Apache-2.0) ([#58](https://github.com/coco-research/coco/issues/58)) ([8df96a4](https://github.com/coco-research/coco/commit/8df96a4750012776e7785f611a1cb7c80cdcb0dc))
* **skills:** add journey-map skill (owner's own; fix hardcoded path + stale X6 refs) ([#57](https://github.com/coco-research/coco/issues/57)) ([37c182d](https://github.com/coco-research/coco/commit/37c182dd934742145e2240235bebda84efcc5e1c))
* **skills:** c4-architecture edit kept by the improvement loop (held-out 0.132 to 0.879) ([#373](https://github.com/coco-research/coco/issues/373)) ([f561b6f](https://github.com/coco-research/coco/commit/f561b6fda1533c6fac7e61c61554536b0c741a80))
* **skills:** implement the declared domain taxonomy across every core skill ([#87](https://github.com/coco-research/coco/issues/87)) ([beb92a1](https://github.com/coco-research/coco/commit/beb92a1357e0a832e75b388764ed52aae53e04eb))
* **skills:** maker-mdap study notes (CC BY 4.0) ([#329](https://github.com/coco-research/coco/issues/329)) ([4b2b656](https://github.com/coco-research/coco/commit/4b2b6569bb6fabf54d289eb04c89f291b4678e75))
* **skills:** officecli skill and /officecli command for Office files ([#369](https://github.com/coco-research/coco/issues/369)) ([c22a882](https://github.com/coco-research/coco/commit/c22a88264b7c4f0b4ae160373a2747d7c9b94b85))
* **skills:** vendor embedded-captions skill (HeyGen HyperFrames bundle, Apache-2.0) ([#77](https://github.com/coco-research/coco/issues/77)) ([04d0fa5](https://github.com/coco-research/coco/commit/04d0fa515c1bea638044799c2a5ac051a7a6592f))
* **skills:** vendor faceless-explainer skill (HeyGen HyperFrames bundle) ([#72](https://github.com/coco-research/coco/issues/72)) ([250ef04](https://github.com/coco-research/coco/commit/250ef045f96ef468d13c1367b80562a7800a98db))
* **skills:** vendor figma skill (HeyGen HyperFrames bundle) ([#66](https://github.com/coco-research/coco/issues/66)) ([4cf137b](https://github.com/coco-research/coco/commit/4cf137b4ebe2d1e03798f44848e2ec538ac091d0))
* **skills:** vendor general-video skill (HeyGen HyperFrames bundle) ([#67](https://github.com/coco-research/coco/issues/67)) ([629c8f2](https://github.com/coco-research/coco/commit/629c8f29b4593cea3b90184d5f97c1527bc2a7dc))
* **skills:** vendor humanizer skill (MIT, blader/humanizer) ([#54](https://github.com/coco-research/coco/issues/54)) ([b095c67](https://github.com/coco-research/coco/commit/b095c6709da951da5e598dbfa7a3118af0842386))
* **skills:** vendor hyperframes-animation skill (HeyGen HyperFrames bundle) ([#61](https://github.com/coco-research/coco/issues/61)) ([ba4dff9](https://github.com/coco-research/coco/commit/ba4dff9513b54e740ccd52895427f4a90aa1d8f9))
* **skills:** vendor hyperframes-cli skill (HeyGen HyperFrames bundle) ([#60](https://github.com/coco-research/coco/issues/60)) ([7d99a28](https://github.com/coco-research/coco/commit/7d99a28e4b6a0b46ab639e94c21fbe2f1d52e757))
* **skills:** vendor hyperframes-core skill (HeyGen HyperFrames bundle) ([#59](https://github.com/coco-research/coco/issues/59)) ([e2c58d9](https://github.com/coco-research/coco/commit/e2c58d97777b35a842a08a1c1ec745f7c99ed074))
* **skills:** vendor hyperframes-creative skill (HeyGen HyperFrames bundle) ([#63](https://github.com/coco-research/coco/issues/63)) ([851847b](https://github.com/coco-research/coco/commit/851847b7bfd06713b9530d7973bf0b94165863f2))
* **skills:** vendor hyperframes-keyframes skill (HeyGen HyperFrames bundle) ([#62](https://github.com/coco-research/coco/issues/62)) ([63d9a83](https://github.com/coco-research/coco/commit/63d9a83bb30606effd37e471f939ab1e20985c98))
* **skills:** vendor hyperframes-registry skill (HeyGen HyperFrames bundle) ([#64](https://github.com/coco-research/coco/issues/64)) ([575bf25](https://github.com/coco-research/coco/commit/575bf25c532e260ecae0a80035392ba2d7e18320))
* **skills:** vendor karpathy-guidelines skill (MIT, multica-ai/andrej-karpathy-skills) ([#55](https://github.com/coco-research/coco/issues/55)) ([16e3306](https://github.com/coco-research/coco/commit/16e330698eddf94f7f5d3cecb2444ac2da567214))
* **skills:** vendor media-use skill (HeyGen HyperFrames bundle) ([#65](https://github.com/coco-research/coco/issues/65)) ([5041775](https://github.com/coco-research/coco/commit/50417750cd6975c448707b87d62b56022eda03ea))
* **skills:** vendor motion-graphics skill (HeyGen HyperFrames bundle) ([#68](https://github.com/coco-research/coco/issues/68)) ([67794b3](https://github.com/coco-research/coco/commit/67794b30d2402ee5a731e92bce2f8e9b398729fb))
* **skills:** vendor music-to-video skill (HeyGen HyperFrames bundle) ([#69](https://github.com/coco-research/coco/issues/69)) ([2c02b16](https://github.com/coco-research/coco/commit/2c02b16c35544180464a702d6a4733212feea8b9))
* **skills:** vendor pr-to-video skill (HeyGen HyperFrames bundle) ([#70](https://github.com/coco-research/coco/issues/70)) ([9ad5de7](https://github.com/coco-research/coco/commit/9ad5de7006013ef069a0d25911bd3689faf05d14))
* **skills:** vendor product-launch-video skill (HeyGen HyperFrames bundle) ([#71](https://github.com/coco-research/coco/issues/71)) ([44b058e](https://github.com/coco-research/coco/commit/44b058e68884068c35641b30a3842d03521ef8d2))
* **skills:** vendor remotion-to-hyperframes skill (HeyGen HyperFrames bundle) ([#75](https://github.com/coco-research/coco/issues/75)) ([d62bc6c](https://github.com/coco-research/coco/commit/d62bc6c06af7ff1f81dc2715f61795c7b187211c))
* **skills:** vendor slideshow skill (HeyGen HyperFrames bundle) ([#74](https://github.com/coco-research/coco/issues/74)) ([9d88b4d](https://github.com/coco-research/coco/commit/9d88b4d2d599a054dd414d79764091e010b59d57))
* **skills:** vendor talking-head-recut skill (HeyGen HyperFrames bundle) ([#73](https://github.com/coco-research/coco/issues/73)) ([f2b6565](https://github.com/coco-research/coco/commit/f2b65650a5e106b8d311d4f3d9cb4c2732149b5f))
* **skills:** vendor taste-skill design-taste-frontend + redesign-existing-projects (attribution: Leonxlnx/taste-skill) ([351f72b](https://github.com/coco-research/coco/commit/351f72bd08dc5288a018136349288c1f72de4f59))
* **skills:** vendor the reverse-skill bundle, defensive subset only ([#109](https://github.com/coco-research/coco/issues/109)) ([75045d1](https://github.com/coco-research/coco/commit/75045d1cf3b39d6d8cd7dc755c4f16ce4c206338))
* **skills:** vendor visual-explainer skill (MIT, nicobailon/visual-explainer) ([#56](https://github.com/coco-research/coco/issues/56)) ([f16cdc1](https://github.com/coco-research/coco/commit/f16cdc1f9f4456b461484767744851935513b03b))
* **skills:** vendor website-to-video skill (HeyGen HyperFrames bundle) [deprecated upstream] ([#76](https://github.com/coco-research/coco/issues/76)) ([eeca801](https://github.com/coco-research/coco/commit/eeca801b7896d8e0840d6065a3bf7fbdd4f173dc))
* Superintelligence bundle — a board of 185 world-class minds ([#18](https://github.com/coco-research/coco/issues/18)) ([bfc4dbb](https://github.com/coco-research/coco/commit/bfc4dbb1715c7323e3dc2bc6899b45399d776aef))
* **superintelligence:** expand board 185 -&gt; 389 across 9 teams + meta-orchestrator ([#21](https://github.com/coco-research/coco/issues/21)) ([84e3190](https://github.com/coco-research/coco/commit/84e319072232f1252730c61ff3aa3c9667fbc16a))
* **team-gate:** add four observe-mode hooks and their self-test ([785ee12](https://github.com/coco-research/coco/commit/785ee127e2826840c05b0651a3f02c5e356eaa87))
* **team-gate:** add gate_state receipt-chain library and fixtures ([d039522](https://github.com/coco-research/coco/commit/d0395220c305afccc8711980a1ee6c2c893087d7))
* **team-gate:** aggregators block a fourth build round unless overridden ([a6fadce](https://github.com/coco-research/coco/commit/a6fadce3065c972ebde72727347baaa4c83b0eeb))
* **team-gate:** arch_gate finds the arch-index scripts on any machine ([4f2ed83](https://github.com/coco-research/coco/commit/4f2ed83fbfd6993036ff531179270a1d4b118709))
* **team-gate:** arch_gate records a stage 1 baseline and gates the declared plan ([9c085d6](https://github.com/coco-research/coco/commit/9c085d684aada846ffb60930a631ee41bfabdfda))
* **team-gate:** arch_gate wraps arch_drift with a three-valued exit ([702ff47](https://github.com/coco-research/coco/commit/702ff473b5e29f85f3c799271514de8465a1cc47))
* **team-gate:** arm one hook at a time for the deny runs ([eee1144](https://github.com/coco-research/coco/commit/eee11444412971026d66da942884049ea1a53165))
* **team-gate:** brownfield_map writes the Stage 1 code map with a receipt ([c2600d3](https://github.com/coco-research/coco/commit/c2600d334749b5c7b89722858db135f9f543de52))
* **team-gate:** check_artifacts validates stage handoffs against the manifest ([5236b30](https://github.com/coco-research/coco/commit/5236b301a740d92fa16f21e30417b8df0b85eada))
* **team-gate:** claim_evidence checks PR claims against EVIDENCE.json ([4e6a803](https://github.com/coco-research/coco/commit/4e6a803790f3d1d67c20fa5e37b1088e7a598e2c))
* **team-gate:** claim_evidence flags merged, ci green and shipped without proof ([dda670f](https://github.com/coco-research/coco/commit/dda670f4115484606e1cb33646a82ec450192f96))
* **team-gate:** fix_gate aggregates the fix pipeline gates ([49afc2c](https://github.com/coco-research/coco/commit/49afc2ce22f7d21ad3fd4bc8fbdd6afd933c5cde))
* **team-gate:** fix_gate requires the brownfield map ([4a7b0bd](https://github.com/coco-research/coco/commit/4a7b0bd029ee77b57eb222ce96a0a5563b668d80))
* **team-gate:** latest receipt wins when a gate file is rewritten ([7e7c85d](https://github.com/coco-research/coco/commit/7e7c85da229b83ec8efe045b20ce6c4d5876e2fd))
* **team-gate:** prove_red proves each new test red then green ([3534db1](https://github.com/coco-research/coco/commit/3534db1a8c560d12589776b91d6ef06e47378945))
* **team-gate:** prove_red proves tests-only changes against stubbed implementations ([40d6dc9](https://github.com/coco-research/coco/commit/40d6dc94eab613edf167ba24608e90c10cecdb18))
* **team-gate:** run_gate discovers, runs and measures the CI commands ([44725c2](https://github.com/coco-research/coco/commit/44725c2cadb984e2e5e3252088d2b2c150530dd5))
* **team-gate:** run_gate reads unittest summaries ([ded7548](https://github.com/coco-research/coco/commit/ded7548883492a8e1fa959d6ac53943fbcda020e))
* **team-gate:** ship_gate aggregates the stage gates into the PR verdict ([7ad74f7](https://github.com/coco-research/coco/commit/7ad74f77892a69d580cceeeb876efb54a93c8916))
* **team-gate:** ship_gate requires the architecture baseline, plan and conformance gates ([40ea386](https://github.com/coco-research/coco/commit/40ea386bb49ac2669358c21b5abdced8d6c4a29a))
* **team-gate:** ship_gate requires the brownfield map at stage 1 ([5fccb2d](https://github.com/coco-research/coco/commit/5fccb2d0adc8dbc3428e13c9cabf55273a9660c6))
* **team-gate:** stage 2 cannot open without the brownfield map ([b3f4a6d](https://github.com/coco-research/coco/commit/b3f4a6d044406b3616203676a35c7bd9224c6f7e))
* **team-gate:** verify_independent stages a clean worktree and compares gates ([b706f84](https://github.com/coco-research/coco/commit/b706f84631ad123b40eba00c64bbb75c5d8329a0))
* **team:** add prompt injection defense to all 35 team role system prompts ([#145](https://github.com/coco-research/coco/issues/145)) ([07618a7](https://github.com/coco-research/coco/commit/07618a75da2d57f049920b438074b984bddbdbc0))
* **team:** architecture conformance gates — drift detection and built-as-declared ([#83](https://github.com/coco-research/coco/issues/83)) ([539ba27](https://github.com/coco-research/coco/commit/539ba2782c13ba74298fa671559fdedac66c4767))
* update-availability notifier + README accuracy fixes ([#24](https://github.com/coco-research/coco/issues/24)) ([1f5f9a2](https://github.com/coco-research/coco/commit/1f5f9a280b3a42706b47a676d73e1b6c327fc846))
* **workflow:** Claude Code hooks that hold code edits until the plan is signed ([#396](https://github.com/coco-research/coco/issues/396)) ([4f4d8e8](https://github.com/coco-research/coco/commit/4f4d8e83cfaa8b748bc904138bd858342c89809b))
* **workflow:** coco-gate githook install|remove, the git warning per repo, chain or skip, never overwrite ([#404](https://github.com/coco-research/coco/issues/404)) ([e389259](https://github.com/coco-research/coco/commit/e38925921b0cd97829410926c8db0b87d77797da))
* **workflow:** coco-workflow required check for signed PRD, architecture and plan ([#394](https://github.com/coco-research/coco/issues/394)) ([20033f5](https://github.com/coco-research/coco/commit/20033f5dfeb5e0d086ec4211adb58cb4c3823b9c))
* **workflow:** warn-only pre-commit hook and the show check ([#397](https://github.com/coco-research/coco/issues/397)) ([4305232](https://github.com/coco-research/coco/commit/43052320c191cf8ca071df3a46751f5faf868a99))


### Bug Fixes

* **adapters/grok:** link SI personas into ~/.grok/personas ([#201](https://github.com/coco-research/coco/issues/201)) ([228d8fc](https://github.com/coco-research/coco/commit/228d8fc96ee96f94e1a8f344191c10ef1ed39bc8))
* **adapters:** install the 13 SI team front doors, and default every adapter to its bundles ([#183](https://github.com/coco-research/coco/issues/183)) ([ffa5b48](https://github.com/coco-research/coco/commit/ffa5b485badc517631a0434ff366821a06266217))
* **aider:** checksum-guarded backups for AGENTS.md and .aider.conf.yml ([#256](https://github.com/coco-research/coco/issues/256)) ([#272](https://github.com/coco-research/coco/issues/272)) ([23cf839](https://github.com/coco-research/coco/commit/23cf839e71cd91c6073c9265bbe2e06598459251))
* **aider:** keep full agent descriptions in AGENTS.md ([#259](https://github.com/coco-research/coco/issues/259)) ([#303](https://github.com/coco-research/coco/issues/303)) ([1345dd0](https://github.com/coco-research/coco/commit/1345dd01dcda4abea062bd95da573d0adc9022d5))
* **aider:** keep full agent descriptions in AGENTS.md ([#259](https://github.com/coco-research/coco/issues/259)). ([1345dd0](https://github.com/coco-research/coco/commit/1345dd01dcda4abea062bd95da573d0adc9022d5))
* **aider:** write real aider option keys to .aider.conf.yml ([#255](https://github.com/coco-research/coco/issues/255)) ([#271](https://github.com/coco-research/coco/issues/271)) ([ee4ce67](https://github.com/coco-research/coco/commit/ee4ce67044c7c74e8fa5e8fcbe85b8c5668f6699))
* **assets:** re-render the social card from its source ([#348](https://github.com/coco-research/coco/issues/348)) ([a9892dd](https://github.com/coco-research/coco/commit/a9892dd5bc7a6b6f3d18cdf5508c17e4c46068b9))
* **bootstrap:** accept a ~/.coco that holds only the update cache ([#239](https://github.com/coco-research/coco/issues/239)) ([#302](https://github.com/coco-research/coco/issues/302)) ([e363e21](https://github.com/coco-research/coco/commit/e363e217039fc14a2d071ac070d53e4ef82d84eb))
* **bootstrap:** accept a ~/.coco that holds only the update cache ([#239](https://github.com/coco-research/coco/issues/239)). ([e363e21](https://github.com/coco-research/coco/commit/e363e217039fc14a2d071ac070d53e4ef82d84eb))
* **brain:** eliminate f-string SQL injection in update operations ([#140](https://github.com/coco-research/coco/issues/140)) ([4a4c27c](https://github.com/coco-research/coco/commit/4a4c27c95f58f64e3a59abe2e9f96d308de7e4f8))
* **brain:** replace inline code generation with stdin-based chroma_worker ([#141](https://github.com/coco-research/coco/issues/141)) ([2e36aff](https://github.com/coco-research/coco/commit/2e36affa6565796a77be8f846ef5a97d799b97ae))
* **captions:** validate bundled font licence contents ([#381](https://github.com/coco-research/coco/issues/381)) ([6756e4f](https://github.com/coco-research/coco/commit/6756e4fcae7a139983bb1ab8b3d2d49a5da08e2b))
* **ci:** accept unscoped cocosuperintelligence on npm publish ([#192](https://github.com/coco-research/coco/issues/192)) ([a85d543](https://github.com/coco-research/coco/commit/a85d543318bebe8c82351de98cc83a87ad04e59f))
* **ci:** derive the adapter smoke-test loop and add a general drift gate ([#180](https://github.com/coco-research/coco/issues/180)) ([30773d8](https://github.com/coco-research/coco/commit/30773d8b8b05c346dbe85feb06f24f283e28a6b7))
* **ci:** extend KNOWN_ADAPTERS to hermes/vscode, smoke-test hermes with exists-guard ([#119](https://github.com/coco-research/coco/issues/119)) ([0ede669](https://github.com/coco-research/coco/commit/0ede6693c37cf1bfcc4ec9612e2a639a50066a03))
* **ci:** make frontmatter lint run on a hosted runner and cover the whole tree ([#181](https://github.com/coco-research/coco/issues/181)) ([29068cc](https://github.com/coco-research/coco/commit/29068cc69097b43ca0e4d5049adc2be2bbfd82c2))
* **cli:** --help lists all 16 adapters, gated in CI ([#234](https://github.com/coco-research/coco/issues/234)) ([#310](https://github.com/coco-research/coco/issues/310)) ([b4064ad](https://github.com/coco-research/coco/commit/b4064ad1e926e65295b3fcf1058309476a46d907))
* **cli:** --help lists all 16 adapters, gated in CI ([#234](https://github.com/coco-research/coco/issues/234)). ([b4064ad](https://github.com/coco-research/coco/commit/b4064ad1e926e65295b3fcf1058309476a46d907))
* **cli:** closing hint names install, not update, for re-install ([#253](https://github.com/coco-research/coco/issues/253)) ([#287](https://github.com/coco-research/coco/issues/287)) ([d564160](https://github.com/coco-research/coco/commit/d564160b794a9de83ef8fd47de757f40733fe362))
* **cli:** reject unknown subcommands before cloning ([#268](https://github.com/coco-research/coco/issues/268)) ([#299](https://github.com/coco-research/coco/issues/299)) ([684f752](https://github.com/coco-research/coco/commit/684f75297173eaae408c51bb56a660e000c3ff40))
* **cli:** reject unknown subcommands before cloning ([#268](https://github.com/coco-research/coco/issues/268)). ([684f752](https://github.com/coco-research/coco/commit/684f75297173eaae408c51bb56a660e000c3ff40))
* **cli:** stop advertising the phantom team bundle in the CLI's own help ([#91](https://github.com/coco-research/coco/issues/91)) ([a89f634](https://github.com/coco-research/coco/commit/a89f63487d832cdb2d72e7a8fef51db579a538c4))
* **cli:** uninstall handles a symlinked clone dir and a symlinked ~/.claude ([#350](https://github.com/coco-research/coco/issues/350)) ([7392db8](https://github.com/coco-research/coco/commit/7392db88ebf1d37f0ed926ba566fef6f76567415))
* **cli:** uninstall matches link targets as paths, not globs, and resolves relative links ([#354](https://github.com/coco-research/coco/issues/354)) ([dfadb67](https://github.com/coco-research/coco/commit/dfadb67b5dc14d0b4ae553a9c85c53a8343a2a16))
* **cli:** uninstall removes ~/.coco/.update-check.json ([#264](https://github.com/coco-research/coco/issues/264)) ([#284](https://github.com/coco-research/coco/issues/284)) ([c7066e8](https://github.com/coco-research/coco/commit/c7066e88dd99cf5f6baebf39762c884b30ce3422))
* **cli:** uninstall, install and update only act on a real coco-research/coco clone ([#342](https://github.com/coco-research/coco/issues/342)) ([b8d42bd](https://github.com/coco-research/coco/commit/b8d42bd4fdec1d1163a5d481bb103a92c0f94a44))
* close the freshness gaps that let tonight's own counts go stale again ([#89](https://github.com/coco-research/coco/issues/89)) ([d32431a](https://github.com/coco-research/coco/commit/d32431ad5fd214467b959de6fab71a1acf6ab4d5))
* **coco-diagram:** WCAG accent, dangling citations, unshipped-script instructions, icon attribution ([#96](https://github.com/coco-research/coco/issues/96)) ([126eff9](https://github.com/coco-research/coco/commit/126eff9261ea5955c7ecdefc9c60af00ab211683))
* **codex:** AGENTS.md cites only files the install has, and keeps the /team router ([#261](https://github.com/coco-research/coco/issues/261), [#262](https://github.com/coco-research/coco/issues/262)) ([#421](https://github.com/coco-research/coco/issues/421)) ([9257e6f](https://github.com/coco-research/coco/commit/9257e6fbb2e391d49a4a55f340a47b3655591dd2))
* **docs:** correct the last count drift after the four-department Super Intelligence expansion ([#182](https://github.com/coco-research/coco/issues/182)) ([8a70d48](https://github.com/coco-research/coco/commit/8a70d48fcba7b1ea11c1ff9eb4727bfcf25faa05))
* **evals:** a slow skill executor exits with one line instead of a traceback; timeout configurable ([#358](https://github.com/coco-research/coco/issues/358)) ([21e1e94](https://github.com/coco-research/coco/commit/21e1e94ff18d3c2ca1a1df7aa75f007ace36d83a))
* **evals:** bound base-check git reads and handle failures ([#380](https://github.com/coco-research/coco/issues/380)) ([9a9a1e2](https://github.com/coco-research/coco/commit/9a9a1e2cd35843d3bc9b333bd8c83fbfbf4c00e4))
* **evals:** held-out gate split across life-time peeks; real-bootstrap tests; public paired helper ([#364](https://github.com/coco-research/coco/issues/364)) ([90cf4ab](https://github.com/coco-research/coco/commit/90cf4abb40447b030286e12dee65f8d8e6e3fa52))
* **evals:** prd-generator grader penalises restating the brief ([#368](https://github.com/coco-research/coco/issues/368)) ([79198ca](https://github.com/coco-research/coco/commit/79198ca3fae983fdb9071929bacc9c0da6b9c03e))
* **evals:** reject empty skill improvement scores ([#382](https://github.com/coco-research/coco/issues/382)) ([5f2eb30](https://github.com/coco-research/coco/commit/5f2eb3036131d1f911bdb51e2daee4d3727f8f42))
* **evals:** skill executor exits cleanly on a dropped connection and caps reply length ([#363](https://github.com/coco-research/coco/issues/363)) ([c382dcb](https://github.com/coco-research/coco/commit/c382dcb2250135fa5c5b007611ce16fffbf9de5e))
* **evals:** validate q in bh_fdr (lab-0162) ([#343](https://github.com/coco-research/coco/issues/343)) ([827e9a5](https://github.com/coco-research/coco/commit/827e9a5dcf3b44a30dd4e3e09ded43f78f6ae84a))
* **formula:** pin Homebrew sha256 to the v1.5.0 tarball ([#191](https://github.com/coco-research/coco/issues/191)) ([8c32189](https://github.com/coco-research/coco/commit/8c32189f9f2aefd0b3d410e2e65a0f0e274d3d7c))
* **formula:** set real sha256 for v1.0.0 tarball ([#30](https://github.com/coco-research/coco/issues/30)) ([bb396c1](https://github.com/coco-research/coco/commit/bb396c1d8f25c12e0bb66d4502fbb4ef17640a8a))
* **formula:** set real sha256 for v1.1.0 tarball ([#43](https://github.com/coco-research/coco/issues/43)) ([99dfba0](https://github.com/coco-research/coco/commit/99dfba09a00aef754a7d58e2ba7385c3f17596df))
* **formula:** set real sha256 for v1.2.0 tarball ([#52](https://github.com/coco-research/coco/issues/52)) ([d8336a7](https://github.com/coco-research/coco/commit/d8336a71d6efb7644cea3b5fa7c2034929532509))
* **funding:** point Sponsors at coco-research, not the reclaimed rkz91 username ([#47](https://github.com/coco-research/coco/issues/47)) ([15d16a3](https://github.com/coco-research/coco/commit/15d16a3e0a1ebc2562266c40a030325d9cb810df))
* **generic:** ship SI command family and front doors on first-run install ([#274](https://github.com/coco-research/coco/issues/274)) ([e0578bd](https://github.com/coco-research/coco/commit/e0578bd483f233a5be4b1a663a987496bd64a6d4)), closes [#273](https://github.com/coco-research/coco/issues/273) [#242](https://github.com/coco-research/coco/issues/242)
* **grok:** uninstall removes generated commands, MCP block and hooks ([#267](https://github.com/coco-research/coco/issues/267)) ([#314](https://github.com/coco-research/coco/issues/314)) ([2422b8f](https://github.com/coco-research/coco/commit/2422b8f9f822889d7e7bf3de0e6e477d6218fa77))
* **grok:** uninstall removes generated commands, MCP block and hooks ([#267](https://github.com/coco-research/coco/issues/267)). ([2422b8f](https://github.com/coco-research/coco/commit/2422b8f9f822889d7e7bf3de0e6e477d6218fa77))
* **gsd:** create missing autonomous workflow and update skill reference ([#139](https://github.com/coco-research/coco/issues/139)) ([df51c42](https://github.com/coco-research/coco/commit/df51c424a0586310612ebf0281daee9885c4521c))
* **hermes:** create the target profile instead of failing the install ([#175](https://github.com/coco-research/coco/issues/175)) ([eb45bd0](https://github.com/coco-research/coco/commit/eb45bd0e7da5a932ea19d3b59087b2714f10033c))
* **index:** make the generator count the whole tree and stop emitting dead links ([#84](https://github.com/coco-research/coco/issues/84)) ([24b8e0c](https://github.com/coco-research/coco/commit/24b8e0cfac58b573f83604229683955c76561786))
* **index:** read git-tracked files, not the working tree ([#167](https://github.com/coco-research/coco/issues/167)) ([ab2f5c3](https://github.com/coco-research/coco/commit/ab2f5c345a1cf3f6b04378dc8690ed297bd03691))
* **install:** --help no longer prints the shebang ([#247](https://github.com/coco-research/coco/issues/247)) ([#313](https://github.com/coco-research/coco/issues/313)) ([c271356](https://github.com/coco-research/coco/commit/c271356e10c22fe2f8e9e5a1cc89f4d6f96ff660))
* **install:** --help no longer prints the shebang ([#247](https://github.com/coco-research/coco/issues/247)). ([c271356](https://github.com/coco-research/coco/commit/c271356e10c22fe2f8e9e5a1cc89f4d6f96ff660))
* **installer:** add target prefix validation to prevent symlink traversal ([#142](https://github.com/coco-research/coco/issues/142)) ([47edb2f](https://github.com/coco-research/coco/commit/47edb2f26126f7cec3786eae21fb734e542a2853))
* **install:** every bundle by default except security tooling, which stays opt-in ([#170](https://github.com/coco-research/coco/issues/170)) ([90e53f5](https://github.com/coco-research/coco/commit/90e53f506148f913834c70d8d391ebe63162c3de))
* **install:** keep earlier rows in the manifest after a narrower re-install, so --uninstall stays complete ([#402](https://github.com/coco-research/coco/issues/402)) ([4978bb3](https://github.com/coco-research/coco/commit/4978bb3db15279b05c48228b1359e7e65bf67e0b))
* **install:** README counts match a measured install, gated in CI ([#277](https://github.com/coco-research/coco/issues/277)) ([988d767](https://github.com/coco-research/coco/commit/988d7679fa2dc660ee7767b57db2519944b61f3a))
* **licence:** remove Anthropic source-available skills and a docs scrape ([#82](https://github.com/coco-research/coco/issues/82)) ([32e4ba8](https://github.com/coco-research/coco/commit/32e4ba884da4bfbb3a2e62a1423a9ce808a6cea2))
* **local-llm:** measured throughput figures, and how to use the model efficiently ([#116](https://github.com/coco-research/coco/issues/116)) ([c60c479](https://github.com/coco-research/coco/commit/c60c47991c8e7da648658a33841287104884e477))
* **m0:** the m0 skills talk to the live daemon on :8000, not the retired :8787 server ([#285](https://github.com/coco-research/coco/issues/285)) ([a939c95](https://github.com/coco-research/coco/commit/a939c957b0d4158a9bb9198a71a7a50ddef713dd))
* **npm:** correct the bin path so the published command actually installs ([#93](https://github.com/coco-research/coco/issues/93)) ([b9415cc](https://github.com/coco-research/coco/commit/b9415cc1088dc81007a7795e249b13923ba3eccf))
* **packs:** content gate stores no internal names; reads them at scan time ([#317](https://github.com/coco-research/coco/issues/317)) ([2ee5abb](https://github.com/coco-research/coco/commit/2ee5abb1a7384f2274979967e2ba52df6fbe13c6))
* **packs:** harden content_exceptions handling in the content gate ([bf07637](https://github.com/coco-research/coco/commit/bf07637ce32aab8664ef057e70ba42de772bcdc5))
* **packs:** reject unknown keys in content_exceptions entries ([bf07637](https://github.com/coco-research/coco/commit/bf07637ce32aab8664ef057e70ba42de772bcdc5))
* **personas:** remove a minor's death and litigation details from noam-shazeer (lab-0054) ([de0454a](https://github.com/coco-research/coco/commit/de0454af17a74297c2d02f5020e6667bbfbc3ad3))
* **personas:** remove a minor's death and litigation details from noam-shazeer (lab-0054) ([#338](https://github.com/coco-research/coco/issues/338)) ([de0454a](https://github.com/coco-research/coco/commit/de0454af17a74297c2d02f5020e6667bbfbc3ad3))
* **release:** tag as vX.Y.Z, not cocosuperintelligence-vX.Y.Z ([#315](https://github.com/coco-research/coco/issues/315)) ([04a3683](https://github.com/coco-research/coco/commit/04a3683bf80627c462a3de1d1a5b6986adce4752))
* **router:** one shared local opener, '--' ends options, summary truncation flag, errors on stderr ([#370](https://github.com/coco-research/coco/issues/370)) ([5f8d153](https://github.com/coco-research/coco/commit/5f8d153147d1a630f9229f3279a5da24568f696f))
* **security:** close eval, rm-rf, uninstall-glob, and unpinned-clone holes ([#117](https://github.com/coco-research/coco/issues/117)) ([6bbf838](https://github.com/coco-research/coco/commit/6bbf838bab779f5dcf1938844c9c3a21f570f186))
* **security:** close the last contains-match uninstall glob and widen the gate ([#178](https://github.com/coco-research/coco/issues/178)) ([02b1967](https://github.com/coco-research/coco/commit/02b196731a0b4f51c8708e9fbacc66b1d6e48016))
* **si:** correct stale persona counts in the root registry ([#81](https://github.com/coco-research/coco/issues/81)) ([d81be2b](https://github.com/coco-research/coco/commit/d81be2bb9bbb2cf4c07b72f9fe11ca8e9b3c58a4))
* **si:** keyword Stage A fallback + COCO_SI_REPO on generate ([#172](https://github.com/coco-research/coco/issues/172)) ([0f9d4f2](https://github.com/coco-research/coco/commit/0f9d4f276d8b7d4c2284954e9e28cb1bc4a93d72))
* **si:** normalise all 13 roster front doors, drop hand-maintained counts ([#165](https://github.com/coco-research/coco/issues/165)) ([43be65a](https://github.com/coco-research/coco/commit/43be65a002eed9994202b7049c9a1db0d551b322))
* **si:** remove internal project references and make the build scripts portable ([#86](https://github.com/coco-research/coco/issues/86)) ([64354c3](https://github.com/coco-research/coco/commit/64354c30e7373935a46dc813b52bb653538dc241))
* **si:** repair 27 broken persona frontmatters and re-register them; add missing ROSTER.md files; team-aware validator ([b30b526](https://github.com/coco-research/coco/commit/b30b526475a130daea346157a5df453331c22474))
* **site:** Coco casing on cocoresearch.org and the new coco hero subhead ([#412](https://github.com/coco-research/coco/issues/412)) ([fb69a7a](https://github.com/coco-research/coco/commit/fb69a7a797f58d88348af4d3d7438ebd86ba88b8))
* **site:** correct published counts after the local-llm skill landed ([#112](https://github.com/coco-research/coco/issues/112)) ([eb6dbc1](https://github.com/coco-research/coco/commit/eb6dbc1c941170cf01f3a7b923cff3a7830974fc))
* **site:** finish closing out the Apple-methodology audit, remove owner's name ([#102](https://github.com/coco-research/coco/issues/102)) ([de877f9](https://github.com/coco-research/coco/commit/de877f988f8ac6e3266a13205403c3e97df50b1a))
* **site:** og-image says Coco without a persona count, and the stale 389 board image is gone ([#413](https://github.com/coco-research/coco/issues/413)) ([4dc28ab](https://github.com/coco-research/coco/commit/4dc28abe7c25d98cf6a20686a913933b2e3a5c70))
* **site:** release figures to 1.9.0; gate checks data-count spans on product pages ([#372](https://github.com/coco-research/coco/issues/372)) ([627e318](https://github.com/coco-research/coco/commit/627e318acee205e6fab1dcea6d0486d8116a2d06))
* **site:** replace Apple's exact accent color and logo gradient, add products overlay, fix sticky hash on refresh ([#99](https://github.com/coco-research/coco/issues/99)) ([b63dc92](https://github.com/coco-research/coco/commit/b63dc92045ab8fb539db29e9434be9e9dc98d075))
* **site:** taste-skill sweep — hero density, mobile nav, CTA dupes, em-dashes, tap targets, motion speed, CoCo Code copy ([#103](https://github.com/coco-research/coco/issues/103)) ([ddd01b2](https://github.com/coco-research/coco/commit/ddd01b2fa0460fcc3b3cccfe33924e862f4c3460))
* **site:** the counts line sits after the install figure, not inside it ([#415](https://github.com/coco-research/coco/issues/415)) ([0da6701](https://github.com/coco-research/coco/commit/0da6701c9aa84deb211f9b025cf0ba0c309bbd25))
* **si:** top up the 4 NEEDS-TOPUP gtm personas — every public_stance now cited, dead URLs replaced ([bac154b](https://github.com/coco-research/coco/commit/bac154b36bf03ee8cabe56d44eedbdf56af402fd))
* **superintelligence:** deliver full 242 SI command family on install + portable generators ([#23](https://github.com/coco-research/coco/issues/23)) ([052cfab](https://github.com/coco-research/coco/commit/052cfabcd493735b00490257470d7b1a705deb19))
* **team-gate:** arch_gate conformance records a non-current baseline in its gate file ([0a9d0b0](https://github.com/coco-research/coco/commit/0a9d0b0f9ab41885bd3dc4f52ebacf3d7b36c43d))
* **team-gate:** build the arch fixtures without the non-portable sed -i ([ddc4fce](https://github.com/coco-research/coco/commit/ddc4fce3584ee5c9cb78f43d3739abfbf061ba50))
* **team-gate:** claim_evidence reads run_gate's evidence shape and maps requirements through tests ([d3d1905](https://github.com/coco-research/coco/commit/d3d19057da3ae4f2fe19e0376442b0514ffd6f1a))
* **team-gate:** close the register follow-ups 5c, 5e, 5f, 12c and 12d ([3d1a96e](https://github.com/coco-research/coco/commit/3d1a96e3e14c32f22b42afc68cf27c89bce96fe3))
* **team-gate:** close three of the four prove_red ceilings in row 9b ([2fa2a00](https://github.com/coco-research/coco/commit/2fa2a002e388887714cba35f515e7ff875cb85c0))
* **team-gate:** gate_state self-test no longer depends on ignored files ([c5a2278](https://github.com/coco-research/coco/commit/c5a227827f80e5f3f7aa382a0b6866a798c664e9))
* **team-gate:** give the drift fixtures the repo's arch-index tools ([cc0c9d6](https://github.com/coco-research/coco/commit/cc0c9d6131a6ae140b6c1f4a815cc9a45ddccef7))
* **team-gate:** hooks self-test seeds the architecture gate files ship_gate now requires ([1cc7df0](https://github.com/coco-research/coco/commit/1cc7df080dbe0d41024ffd1703edd4788cde273f))
* **team-gate:** install.py writes hook paths that resolve in a consumer repository ([bfb0b11](https://github.com/coco-research/coco/commit/bfb0b11e595f2ee1f0be58ae5e53b16a47535edf))
* **team-gate:** lock append_receipt against concurrent writers ([6df8833](https://github.com/coco-research/coco/commit/6df8833d3c01bfca36143ec9aae84d05255c3ecc))
* **team-gate:** matrix grades a stub-proved test as met ([25f92bb](https://github.com/coco-research/coco/commit/25f92bbf7ba556292187ecbb2c04aa47b8f75716))
* **team-gate:** print a failing suite's output in the fixture runner ([bd9ae8b](https://github.com/coco-research/coco/commit/bd9ae8be455dac4e8aebff62409c1cb74c6e7825))
* **team-gate:** prove_red attributes assertions to the first worktree frame ([135b14f](https://github.com/coco-research/coco/commit/135b14f727103b3ff1063f564dde825a952c4278))
* **team-gate:** render_evidence reads the EVIDENCE.json shape run_gate writes ([a8ea411](https://github.com/coco-research/coco/commit/a8ea41149e9058a964ea952838d0effd11a97d73))
* **team-gate:** render_pr_body renders every override instruction ([4c23b63](https://github.com/coco-research/coco/commit/4c23b63d1c73898cf8184ed7ab6c0cf7e0ae11d3))
* **team-gate:** run_gate accepts its flags after the subcommand ([c3bd28b](https://github.com/coco-research/coco/commit/c3bd28b46f08df81fe8115fccc8ca219d26b6702))
* **team-gate:** ship_gate accepts an ancestor head for the gates that run before the build ([17c9990](https://github.com/coco-research/coco/commit/17c9990e32ee45292c7a5d0aa664425973f5c52f))
* **team-gate:** verify-chain resolves gate files named by receipts ([04465df](https://github.com/coco-research/coco/commit/04465df7f11e280a172a448c8c229bbd604a2269))
* **team:** companion-ref fix + evidence-based test-integrity gates ([#17](https://github.com/coco-research/coco/issues/17)) ([47eb7e8](https://github.com/coco-research/coco/commit/47eb7e892cf23cfa7056b112e279e394905a1ed6))
* **team:** use installed arch-index script path, ignore .team-ship ([bf532b7](https://github.com/coco-research/coco/commit/bf532b7712c9239401c2f14401d876d54e2d8a09))
* **team:** use the placeholder the tooling actually expands ([#189](https://github.com/coco-research/coco/issues/189)) ([50bf213](https://github.com/coco-research/coco/commit/50bf2135832aa97d02a212bfbf57d8d3b81d06f6))

## [1.10.0](https://github.com/coco-research/coco/compare/v1.9.1...v1.10.0) (2026-10-26)


### Features

* **install:** --uninstall removes only what the install recorded and restores originals ([#388](https://github.com/coco-research/coco/issues/388)) ([f99ef89](https://github.com/coco-research/coco/commit/f99ef89b6065408e7c7dc09b100b75e8c561ab80))
* **install:** JSON plan and manifest of every path the Claude Code installer writes ([#387](https://github.com/coco-research/coco/issues/387)) ([b7599fe](https://github.com/coco-research/coco/commit/b7599fe9bfc63f4c7c7269a5a3f6234bbeffcb30))
* **workflow:** coco-workflow required check for signed PRD, architecture and plan ([#394](https://github.com/coco-research/coco/issues/394)) ([bb40b58](https://github.com/coco-research/coco/commit/bb40b581e137c6b0f7cf9d9a210e622741406bca))


### Bug Fixes

* **install:** keep earlier rows in the manifest after a narrower re-install, so --uninstall stays complete ([#402](https://github.com/coco-research/coco/issues/402)) ([c52f91a](https://github.com/coco-research/coco/commit/c52f91a2d692683cce5ad7b9e4079c4b89f47575))

## [1.9.1](https://github.com/coco-research/coco/compare/v1.9.0...v1.9.1) (2026-10-23)


### Bug Fixes

* **captions:** validate bundled font licence contents ([#381](https://github.com/coco-research/coco/issues/381)) ([6d8e06e](https://github.com/coco-research/coco/commit/6d8e06e77b69d3bccd60c453b08ee42446ad508a))
* **evals:** bound base-check git reads and handle failures ([#380](https://github.com/coco-research/coco/issues/380)) ([f6a9040](https://github.com/coco-research/coco/commit/f6a90400540ab49ddf3a64fd61fe22b011caea20))
* **evals:** reject empty skill improvement scores ([#382](https://github.com/coco-research/coco/issues/382)) ([6f6308b](https://github.com/coco-research/coco/commit/6f6308bdd864f8329b49416d98f928f9b42ed2f9))
* **site:** release figures to 1.9.0; gate checks data-count spans on product pages ([#372](https://github.com/coco-research/coco/issues/372)) ([13d0129](https://github.com/coco-research/coco/commit/13d0129ecc3e238a0a6eefed01d219e24e47369d))

## [1.9.0](https://github.com/coco-research/coco/compare/v1.8.0...v1.9.0) (2026-10-21)


### Features

* **evals:** code-verification pilot skill with grader ([#367](https://github.com/coco-research/coco/issues/367)) ([49636ee](https://github.com/coco-research/coco/commit/49636ee6840747197787b33a8af2a01948d43a6c))
* **evals:** core of the skill improvement round (proposal checks, compose, dev and held-out gates) ([#360](https://github.com/coco-research/coco/issues/360)) ([1984a3d](https://github.com/coco-research/coco/commit/1984a3d30f403e459185a813fe6a410f744c634f))
* **evals:** generate-tests and humanizer pilot skills with graders ([#365](https://github.com/coco-research/coco/issues/365)) ([f0e2644](https://github.com/coco-research/coco/commit/f0e2644a1f84279d16479835dca0e946fd3fe7fe))
* **evals:** improvement-round helpers (dev-only proposer workspace, round ledger, gates) ([#376](https://github.com/coco-research/coco/issues/376)) ([d6312e4](https://github.com/coco-research/coco/commit/d6312e435d0c32d5dd88cb606a8eed73dd45225a))
* **evals:** prd-generator, c4-architecture and writing-plans pilot skills with graders ([#359](https://github.com/coco-research/coco/issues/359)) ([fdc4cc4](https://github.com/coco-research/coco/commit/fdc4cc45503aec4dd7e97d77e6a2c1b631095820))
* **evals:** run one skill improvement round (run_round + CLI) ([#379](https://github.com/coco-research/coco/issues/379)) ([cc8a3f2](https://github.com/coco-research/coco/commit/cc8a3f24a15fcede9c7b0fd97d6c192d30eed3c8))
* **skills:** c4-architecture edit kept by the improvement loop (held-out 0.132 to 0.879) ([#373](https://github.com/coco-research/coco/issues/373)) ([0726926](https://github.com/coco-research/coco/commit/07269261f64d03ac1363ee2adf14b7665dab62d5))
* **skills:** officecli skill and /officecli command for Office files ([#369](https://github.com/coco-research/coco/issues/369)) ([2c17c15](https://github.com/coco-research/coco/commit/2c17c155e6e1363ab922c0f14429a4889c5e4922))


### Bug Fixes

* **evals:** a slow skill executor exits with one line instead of a traceback; timeout configurable ([#358](https://github.com/coco-research/coco/issues/358)) ([460e284](https://github.com/coco-research/coco/commit/460e28471ad2552560b0a751b51051eae28019e0))
* **evals:** held-out gate split across life-time peeks; real-bootstrap tests; public paired helper ([#364](https://github.com/coco-research/coco/issues/364)) ([4656083](https://github.com/coco-research/coco/commit/46560839de52e1db11c2e2cd5d83c1934e18e242))
* **evals:** prd-generator grader penalises restating the brief ([#368](https://github.com/coco-research/coco/issues/368)) ([112c74b](https://github.com/coco-research/coco/commit/112c74bf1f3d07a15b0f59a2fd3facd8d8f1dbbb))
* **evals:** skill executor exits cleanly on a dropped connection and caps reply length ([#363](https://github.com/coco-research/coco/issues/363)) ([85559c8](https://github.com/coco-research/coco/commit/85559c8ef84e64f74641b433d616d1f113ba7358))
* **router:** one shared local opener, '--' ends options, summary truncation flag, errors on stderr ([#370](https://github.com/coco-research/coco/issues/370)) ([715e8ec](https://github.com/coco-research/coco/commit/715e8ec4f4552c4676034d7c8c2e3ddbadc599b6))

## [Unreleased]

### Added

- `officecli` skill and `/officecli` command, adapted from OfficeCLI (Apache-2.0) with the install section replaced by a Homebrew check and the update check disabled.

## [1.8.0](https://github.com/coco-research/coco/compare/v1.7.3...v1.8.0) (2026-10-17)


### Features

* **evals:** skill eval harness with dev and held-out splits ([#351](https://github.com/coco-research/coco/issues/351)) ([31c57de](https://github.com/coco-research/coco/commit/31c57debb95ee90e07ef3141c9134c03f378cfad))
* **router:** record decision outcomes (rerouted, kept, overridden, bad) in the local log ([#353](https://github.com/coco-research/coco/issues/353)) ([3433ba4](https://github.com/coco-research/coco/commit/3433ba42f449a66eee56418555c8cf9763851a98))

## [1.7.3](https://github.com/coco-research/coco/compare/v1.7.2...v1.7.3) (2026-10-17)


### Bug Fixes

* **cli:** uninstall matches link targets as paths, not globs, and resolves relative links ([#354](https://github.com/coco-research/coco/issues/354)) ([ee36e66](https://github.com/coco-research/coco/commit/ee36e6649630b8175a89278bcde996f618339591))

## [1.7.2](https://github.com/coco-research/coco/compare/v1.7.1...v1.7.2) (2026-10-17)


### Bug Fixes

* **cli:** uninstall handles a symlinked clone dir and a symlinked ~/.claude ([#350](https://github.com/coco-research/coco/issues/350)) ([6479205](https://github.com/coco-research/coco/commit/6479205f058447620c4f328b27093856a9369e44))

## [1.7.1](https://github.com/coco-research/coco/compare/v1.7.0...v1.7.1) (2026-10-16)


### Bug Fixes

* **assets:** re-render the social card from its source ([#348](https://github.com/coco-research/coco/issues/348)) ([21286b7](https://github.com/coco-research/coco/commit/21286b7d52614aa9b8a03b34c7376e93d3962d5b))
* **cli:** uninstall, install and update only act on a real coco-research/coco clone ([#342](https://github.com/coco-research/coco/issues/342)) ([1ac6cbb](https://github.com/coco-research/coco/commit/1ac6cbb59cbe766758b9036b79ce89234a36969f))
* **evals:** validate q in bh_fdr ([8e14567](https://github.com/coco-research/coco/commit/8e145676dbfec0d312b59947c5fbc00c4e1f69de))
* **grok:** uninstall removes generated commands, MCP block and hooks ([#267](https://github.com/coco-research/coco/issues/267)) ([eaa1110](https://github.com/coco-research/coco/commit/eaa111066f86ea8b75bafedb8811bf188936d4d9))
* **packs:** content gate stores no internal names; reads them at scan time ([#317](https://github.com/coco-research/coco/issues/317)) ([215df3c](https://github.com/coco-research/coco/commit/215df3c6573c2842d0163065fd0344b369404d65))

## [1.7.0](https://github.com/coco-research/coco/compare/v1.6.1...v1.7.0) (2026-10-13)


### Features

* **evals:** paired bootstrap and FDR for candidate-vs-baseline decisions (RSI PR 3) ([d0b2929](https://github.com/coco-research/coco/commit/d0b29297a44e1a13080215ee7b2ed54687bd75de))
* **evals:** paired bootstrap and FDR for RSI decisions ([#311](https://github.com/coco-research/coco/issues/311)) ([d0b2929](https://github.com/coco-research/coco/commit/d0b29297a44e1a13080215ee7b2ed54687bd75de))

## [1.6.1](https://github.com/coco-research/coco/compare/v1.6.0...v1.6.1) (2026-10-10)


### Bug Fixes

* **personas:** remove a minor's death and litigation details from noam-shazeer (lab-0054) ([41e7810](https://github.com/coco-research/coco/commit/41e7810cd93b497c8c9cf935498ea88571b1616c))
* **personas:** remove a minor's death and litigation details from noam-shazeer (lab-0054) ([#338](https://github.com/coco-research/coco/issues/338)) ([41e7810](https://github.com/coco-research/coco/commit/41e7810cd93b497c8c9cf935498ea88571b1616c))

## [1.6.0](https://github.com/coco-research/coco/compare/v1.5.1...v1.6.0) (2026-10-08)


### Features

* **skills:** maker-mdap study notes (CC BY 4.0) ([#329](https://github.com/coco-research/coco/issues/329)) ([8f6abd1](https://github.com/coco-research/coco/commit/8f6abd12417b3a172423f16cb1907d8a94368067))


### Bug Fixes

* **cli:** --help lists all 16 adapters, gated in CI ([#234](https://github.com/coco-research/coco/issues/234)) ([#310](https://github.com/coco-research/coco/issues/310)) ([20fb133](https://github.com/coco-research/coco/commit/20fb133eb7e22b9c52c664c8ac2493c9737635a5))
* **cli:** --help lists all 16 adapters, gated in CI ([#234](https://github.com/coco-research/coco/issues/234)). ([20fb133](https://github.com/coco-research/coco/commit/20fb133eb7e22b9c52c664c8ac2493c9737635a5))
* **install:** --help no longer prints the shebang ([#247](https://github.com/coco-research/coco/issues/247)) ([#313](https://github.com/coco-research/coco/issues/313)) ([2ddb559](https://github.com/coco-research/coco/commit/2ddb55987cf9471634673bf1c5382e63204340f2))
* **install:** --help no longer prints the shebang ([#247](https://github.com/coco-research/coco/issues/247)). ([2ddb559](https://github.com/coco-research/coco/commit/2ddb55987cf9471634673bf1c5382e63204340f2))

## [Unreleased]

- uninstall, install and update refuse a directory that is not a coco-research/coco clone.

## [1.5.1]

### Fixed

- **Aider adapter maintains checksum-guarded backups for `AGENTS.md` and `.aider.conf.yml`.** (#272)
- **Aider adapter writes real option keys to `.aider.conf.yml`.** (#271)
- **Installed the 13 Super Intelligence team front doors, and defaulting every adapter to its bundles.** (#183)
- **`/team` tools now use the placeholder the tooling actually expands.** (#189)

- **The README now says what an install delivers, and CI proves it.** The headline stays at 227 skills, the repository total, with a footnote giving the measured default install: 189 skills, 386 commands and 34 agents on Claude Code. The other 38 skills are the opt-in `reverse-skill` security pack (33) and five Cursor-only skills. `scripts/build-delivery-index.py` now writes `docs/delivered-counts.json` from a real install into a throwaway HOME, every "installed by default" figure in the README and on `coco/index.html` is gated against it, and CI fails if a fresh measurement differs from the committed file. Before this, every count gate compared against a walk of the repository, so nothing noticed that the README's "the totals above are what a plain `bash install.sh` delivers" was false.
- **Agents are 34, not 35.** `agents/PROMPT-DEFENSE.md` is the preamble every agent includes, not a subagent, and is no longer counted by `build-index.py`, the delivery index or the claude-code install receipt. The receipt also stops counting `skills/team-gate`, which has no `SKILL.md`.
- **Bundles are described as installed by default everywhere.** `package.json`, `.claude-plugin.json`, the README System Bundles section, `coco/index.html`, `docs/prd.md`, `docs/INDEX.md`, `docs/architecture.md` and the pi-desktop README still said "opt-in". The README also listed `/team` as a bundle (it is core), left HyperFrames, M0 and Cognee out of the bundle section, and its "full catalog" listed 66 of 75 core skills. The unverifiable "947 total assets" figure is gone; the persona row now says 98 cells, not 70.
- **The CLAUDE.md rules block can no longer damage the file.** A start marker without an end marker made the claude-code and hermes adapters delete everything after it; each install added a blank line; a symlinked `CLAUDE.md` was replaced by a copy; CRLF markers produced a second block. Both adapters now call `scripts/write-rules-block.sh`, which leaves an unterminated block untouched with a warning, is byte-identical on re-run, writes through symlinks, and keeps a `.coco-bak`. Gated by `tests/check-claude-md-block.sh`.
- **`--core-only` works for every adapter.** The root installer forwards it to any adapter whose manifest names bundles, and aider, amazon-q, cline, roo-code, zed and github-copilot-cli exited with "Unknown flag". `tests/smoke.sh` now runs `--core-only --dry-run` for all 16.
- **The windsurf and vscode-continue manifests list the six bundles they install**, which removes a false "-27" row from `adapters/INDEX.md`; that report also measures command shortfalls against the published 386 rather than grok's 389, so adapters delivering all 386 are no longer listed as short.
- **Removed a stale changelog claim** that `cocosuperintelligence` is unpublished; it is on npm at 1.5.0.

### Security

- **Add a content gate for bundle pack files.** (#282)

- **`generate_prd.sh` no longer `eval`s user input.** Interactive answers were assigned with `eval "$var_name='$input'"`, so a value containing a quote could run as shell. Assignment is now `printf -v` into an allow-listed variable name.
- **`stop-server.sh` no longer treats `/tmp/../…` as under `/tmp`.** The old `[[ $path == /tmp/* ]]` glob matched a traversal prefix and then `rm -rf` the directory. The path is canonicalized with `pwd -P` and compared against the real `/tmp` root; only a session directory under that root is deleted. PIDs must be numeric before `kill`.
- **Uninstall no longer glob-matches any path containing the clone name.** `find -lname '*${dir}*'` deleted links into `coco-research` / `coco-connect` when the clone was `coco`. The CLI and the docs now match the resolved clone path plus a trailing slash.
- **Skills no longer instruct `curl | sh` or `npx skills add -y`.** `browser-automation` and `ai-marketing-videos` fetch the inference.sh installer to a file for review; `find-skills` installs without `-y` and still requires an explicit yes that names the package.
- **CLI clone is pinned to the release tag, not floating `main`.** `bin/coco.js` and `bin/coco-bootstrap.sh` clone `v1.5.0` (kept in sync with `package.json`). Existing branch checkouts still `git pull --ff-only` so a tagged pin cannot downgrade a `main` tree.

### Added

- **Every installable bundle now ships a pack.json with a schema gate.** (#281)
- **Hyperframes media-use telemetry is now opt-in.** (#280)
- **Cinematic homepage.** (#279)
- **The loop's skill tree is now documented, with updated PRD counts.** (#200)
- **Completed the Repo Standard document set.** (#199)
- **Vendor the upstream MIT LICENSE verbatim for GSD.** (#283)

- **Local Superintelligence dogfood GIF.** A real `meta_select.py` Stage-A run on this Mac, linked from the README next to Install. Embedding was down (`Connection refused`), so the clip is labeled **degraded: keyword fallback** (`method: keyword`, `degraded: true`).

- **A Grok Build / Grok CLI adapter.** Wires Coco into `~/.grok/{skills,commands,agents,rules,hooks}` the same way the Claude Code adapter wires `~/.claude/`. Commands are flattened to `<ns>:<name>.md` because Grok, like Cursor, discovers user commands as flat `*.md` files and does not recurse. Rules are symlinked from Cursor `.mdc` sources as `*.md`, which is what Grok scans. `--systems` is supported, including Super Intelligence: per-team `SKILL.md` folders land as `si-<team>` skills and the 242 `/SI-*` commands are generated into `~/.grok/commands`. When `~/.coco/bin/coco-platform-mcp` is present, the adapter registers it in `~/.grok/config.toml` so native Grok config wins over Cursor's `~/.cursor/mcp.json` (which uses a relative `./backend` path and fails from a Grok session). When `~/.coco/bin/coco-m0-hook` is present, it writes `~/.grok/hooks/coco-m0.json`. The root installer auto-detects `~/.grok` after VS Code, and the smoke suite and CI dry-run loop cover the new adapter.

- **A real VS Code adapter, replacing the `vscode-continue` stub.** The stub assumed VS Code had no skills system of its own and deferred everything to the Continue extension, which is no longer true: VS Code reads agent skills, agent files and instruction files from `~/.copilot/{skills,agents,instructions}` by default (`chat.agentSkillsLocations`, `chat.agentFilesLocations`, `chat.instructionsFilesLocations`), and the Copilot CLI agent runtime reads the same folders, so one install now serves the editor and the terminal. Skills, agents and commands are symlinked and therefore never go stale. Commands become prompt files named `<ns>-<name>.prompt.md` rather than Claude's `<ns>:<name>.md`, because VS Code derives the slash-command name from the filename and a colon is not a portable filename — `/eng:anti-pattern` is `/eng-anti-pattern` here. Prompt files are the one artifact with no user-level default outside the VS Code profile, so they are installed into `<User>/prompts` and every `<User>/profiles/*/prompts` of every VS Code-family install found, which keeps commands from vanishing when a user switches profile or edition. Rules are the only generated output: VS Code requires the `.instructions.md` extension and an `applyTo` glob where the source is Cursor's `.mdc` with `globs` / `alwaysApply`, so they are compiled on every run. `--systems` is supported, including Super Intelligence, whose SI-* commands are generated into `~/.copilot/coco-generated/si-commands` before being linked. Two adapter-specific flags exist: `--source`, for linking a checkout other than the one the script lives in (running from a git worktree that may later be removed would otherwise leave every symlink dangling), and `--user-dir`, for a VS Code installation the detector cannot find. The root installer now auto-detects VS Code, after Claude Code and Cursor.

### Changed

- **The npm package is now `cocosuperintelligence`, published unscoped.** It was previously named `@coco-research/coco-cli` and had never been published, so no installed version of the old name exists anywhere and nothing downstream breaks. The new name matches the product as the README presents it, and shortens the install to `npx cocosuperintelligence`. Renamed across `package.json`, `bin/coco.js`, `README.md`, `install.sh`, `skills/coco-cli/SKILL.md`, `skills/cli-anything/SKILL.md`, `docs/distribution/npm-github-packages.md` and the publish workflow. `publishConfig.access` was dropped because it only applies to scoped packages; unscoped packages are public by default. Dated entries below that mention the old name are left as written, because they record what was true at the time.

### Fixed

- **`/team ship` no longer reconciles the architecture index mid-pipeline.** Stage 1 previously ran `/team arch build` or `/team arch drift` whenever the index was absent or behind HEAD, which meant every ship following a few commits silently paid for a full index reconciliation, with agents, before any product work began. Stage 1 now only records the pin alongside HEAD and continues, which costs nothing. Refreshing the index is a separate explicit act, and a stale baseline degrades the conformance gate to `UNVERIFIED`, which is the honest outcome.
- **Replaced an unimplementable escape hatch with a real flag.** The architecture gate previously said it could be skipped "on a repository where an index is not wanted", without defining how a pipeline was supposed to know that. `--no-arch` is now a documented flag with its own handling section, reported as `DISABLED (--no-arch)` and distinct from both a pass and `NOT APPLICABLE`. The router explicitly forbids inferring the intent from context, because a condition an agent has to guess at is not a condition.
- **Corrected how the conformance gate reads the pin after a build.** Stage 6 commits, so by the time the gate runs the pin is expected to be behind HEAD; that is precisely what makes `git diff <pin>..HEAD` the set of changes the ship made and any drift attributable to it. Currency is therefore judged once at Stage 1 rather than re-derived at gate time, and `team:architecture.md` documents this baseline convention so the two files cannot contradict each other.
- **The Cursor adapter installed no commands at all.** Its manifest covered only skills and rules, so `~/.cursor/commands/` was never touched and six symlinks left over from an earlier repository location dangled indefinitely. The adapter now installs commands, flattened to `<namespace>:<command>.md` because Cursor discovers user commands with the pattern `~/.cursor/commands/*.md` and does not recurse into subdirectories — a directory symlink resolves correctly while sitting one level too deep to be found. It also prunes command links that point outside the repository or at a directory.
- **Both installers now report skipped targets loudly.** `link_dir` leaves a real file in place rather than overwriting possible user work, which is correct, but it announced this with a quiet `Skip` line and no summary. The consequence observed in practice was an installed command set that went two months out of date while every re-install appeared to succeed. Skips are now prefixed `STALE:`, counted, and summarised with instructions at the end of the run.

- **Removed five phantom artifacts from the `/team ship` handoff table.** The table named `RESEARCH-BRIEF.md`, `ARCHITECTURE-DECISION.md`, `REVIEW-FINDINGS.md`, and `VERIFICATION-REPORT.md`, and no stage was ever instructed to write any of them. `ARCHITECTURE-DECISION.md` was the most consequential, because the single user-facing approval gate promised to present an architecture decision drawn from a file that had no producer anywhere in the repository. Every artifact in the table is now written to `.team-ship/` by the stage that owns it, and each stage body names the artifact it writes. The table also referred to a Verify stage that does not exist in the pipeline; verification is what Stages 7 through 13 are, and `EVIDENCE.md` is its artifact. Stage 14 now writes a real `SHIP-REPORT.md` on both the green and the blocked path.
- **Fixed a dangling tool pointer in the team toolkit registry.** The PRD Generation entry named `/pmstudio-prd`, which no skill declares; the skill identifies itself as `prd-generator`. An agent handed an unresolvable tool name silently falls back to the entry's `Alternative` line, which defeats the purpose of routing through the registry at all. The nine other `pmstudio-*` pointers in the registry were audited and do resolve, because those skills declare `pmstudio-*` names even though their directory names differ.
- **Stopped routing architecture documents to an infrastructure specialist.** The `/team document` type-detection branch for "architecture" and "design doc" sent the work to `senior-cloud-architect` or `senior-backend-eng` and reviewed the result only through `doc-quality`, `grammar-editor`, and `standards-reviewer` — a roster that checks structure, tone, and template conformance, and cannot assess whether the architecture described is sound. The branch now pairs `technical-writer` with the engineering role that owns the system, adds `domain-accuracy` to the review roster, and points at `/util:create-architecture-documentation` for formal published documents.
- **Corrected the asset counts in `.claude-plugin.json`,** which advertised 59 skills, 34 commands and 10 agents against a measured 179 skills, 37 in-repo commands and 34 agents, and understated the installable system bundles as three rather than 5.

### Added

- **A declare-then-verify architecture stage in `/team ship`.** Stage 3 now writes `.team-ship/ARCH-PLAN.json`, declaring the components this ship intends to build, the paths each will occupy, and the paths it must not touch. The declaration is shape-checked immediately and shown at the approval gate, so the intended architecture is something you can disagree with before any code is written. After Stage 6, a new built-as-declared gate checks that every declared path now exists and that nothing landed out of scope. A component declared and then silently dropped is a BLOCK, which no test gate can detect, because tests fail when behaviour breaks rather than when work is quietly abandoned. Implemented by `skills/arch-index/scripts/verify_arch_plan.py` with contract and rationale in `skills/arch-index/references/arch-plan.md`. Earlier analysis rejected forward architecture specifications on the grounds that path checking must be disabled for a system that does not exist yet; that holds only if the check runs at declaration time. Deferring it to after the build moves the check rather than weakening it, which is what makes the declaration enforceable.
- **`arch-index` skill and the `/team arch` action.** Together they produce and maintain `.arch/index.json`, a committed, commit-pinned map from each architectural component of the repository to the real directories and files that implement it. `scripts/validate_index.py` enforces twelve checks with a process exit code, the most important being that every claimed path resolves on disk. `scripts/arch_drift.py` performs a deterministic structural drift scan with no model calls at all, applying a deletion-first rule that removes a component when none of its primary paths survive. `scripts/repo_tree.py` emits a filtered tree whose depth is chosen by measuring the file count against a budget rather than by a fixed cap. The design is adapted from devildev by lak7 (Apache-2.0); the significant addition is that upstream stated its path-matching rule in prose, with a validation checklist of unchecked boxes, and never verified a single path in roughly thirteen hundred lines of code.
- **`team:architecture.md`, the Architecture Conformance Protocol.** Modelled on the Test Evidence Protocol, with the guiding principle "Paths or it does not exist." It carries an explicit list of the rules it does *not* mechanically enforce — currency, semantic drift, decomposition quality, and the exploration read budget — because a gate that overstates its reach is worse than one that does not exist.
- **Failure mode (e), architecture abandoned, in `/team verify`.** This is the reason the rest of the work exists. The four pre-existing failure modes are all test-evidence traps, so a build could satisfy every requirement and every test gate while having silently relocated, merged, or deleted the components it was built against. Tests do not fail when a component moves; they fail when behaviour changes. Failure mode (e) closes that gap with a shell script and no model call, and the Layer 4 verdict rule now spans (a) through (e).
- **Three roles: `solution-architect`, `architecture-reviewer`, and `repo-cartographer`.** All three carry the `all` domain tag, so no new tag was introduced — the tag vocabulary is duplicated in the router and `--roles` validates identifiers only, which means a role carrying an unlisted tag would be silently unselectable with no error. `architecture-reviewer` is the only Layer 3 role that evaluates decomposition; the existing six check structure, tone, template conformance, and factual accuracy, so an unsound architecture previously passed the review layer cleanly.
- **An architecture-conformance hard gate in `/team ship`,** alongside the existing seven. Because `.arch/` is committed rather than gitignored, this gate also runs inside the Stage 11 clean checkout; an untracked index would have made it silently unrunnable in the one path the pipeline designates as authoritative.
- **Registered six architecture-relevant assets in the team toolkit registry,** each of which existed in the repository but was invisible to every `/team` run because Layer 2 agents receive only registry excerpts and never browse the filesystem: `gsd-map-codebase` for codebase mapping, the gitnexus MCP for code-graph queries, `c4-architecture` for diagrams, `api-design-principles` for interface contracts, `/util:architecture-review` for audits, and `/util:create-architecture-documentation` for the formal document suite. Also clarified that the existing Architecture Review Decks entry is a presentation generator rather than an architecture tool.
- **Credited devildev by lak7 (Apache-2.0)** in `CREDITS.md` for the reverse-architecture design that the forthcoming `arch-index` skill builds on.

---

## [1.5.0] — 2026-09-16

### Changed

- **Release bump 1.2.0 → 1.5.0.** Package, plugin, CLI pin, README badge/clone/bootstrap text, and Spec Version now read 1.5.0. No product-feature delta in this cut.

---

## [1.2.0] — 2026-07-31

### Added

- **`coco-loop` skill.** Turns a plain-language goal into a readable charter that the person confirms, then arms and runs a bounded autonomous loop in propose-only mode. It never commits on its own. Requires the [coco-loops](https://github.com/coco-research/coco-loops) framework, which the skill now links with install instructions.
- **`scroll-world` skill.** Builds an immersive scroll-scrubbed landing page in which a pre-rendered camera flies from outside each scene into its interior and then on to the next with no cuts. Contributed upstream by cyw under the MIT license, with the original license retained at `skills/scroll-world/LICENSE`.

### Security

- **Corrected the funding pointer.** `.github/FUNDING.yml` still referenced `rkz91`, the account name used before the 2026-07-18 rename to `coco-research`. An unrelated third party had since registered the vacated username, so the repository's Sponsor configuration pointed at a stranger. No funds could have been misdirected, because that account has no Sponsors listing, but the window is now closed.
- **Removed the remaining stale account references from the installer.** The documented `curl`-pipe-to-`bash` command and the commit-verification link in `bin/coco-bootstrap.sh` both pointed at the reclaimed `rkz91` username, which would have resolved to third-party content had that account created a repository named `coco`.
- **Added a commit-verification gate to `bin/coco-bootstrap.sh`.** The installer now clones first, prints the commit hash, date, and message, and waits for explicit confirmation before running `install.sh`. The default is fail-closed. Only `COCO_BOOTSTRAP_YES=1` or `--yes` skips it; a previous form of this check treated any non-empty value, including `0`, as consent.
- **Pinned GitHub Actions to commit SHAs** and scoped the workflows to `permissions: contents: read`. Pins target `actions/setup-node` v7 and `actions/setup-python` v5, each verified to exist upstream and to match the commit its tag currently points to.
- **Fixed a DOM cross-site-scripting vector** in `skills/brainstorming/scripts/helper.js`, which built its selection indicator by concatenating a label into `innerHTML`. It now assigns `textContent`.
- **Hardened the Cursor adapter installer.** `link_dir()` could silently overwrite a real file, and an `A && B || C` pattern could execute a real command when the dry-run echo failed.
- **Added a Content-Security-Policy** to the generated diagram artifacts, and raised the floor versions of `@modelcontextprotocol/sdk`, `hono`, `vite`, and `wrangler` in the `openai-apps-mcp` template.
- **Added prompt-injection guidance** to `find-skills`, requiring the resolved package name to be surfaced and confirmed before an agent installs a skill on someone's behalf.

Security contributions in this release are by [@imachiever](https://github.com/imachiever) (Rajat Bhatia).

### Fixed

- **Corrected asset counts** for the two new skills. Skills 147 to **149** (core 64 to **66**), total addressable assets 865 to **867**, core install 124 to **126** active assets.

### Changed

- **Bumped Spec Version 1.1.0 to 1.2.0** so that it tracks the release version.

---

## [1.1.0] — 2026-07-18

### Changed

- **Rebranded to CoCo Super Intelligence.** The README now leads with the 389-persona advisory board as the hero capability, with the orchestration framework (skills, persistent state, portability) as the supporting layer. Added new brand lockups (`assets/logo-si.svg` / `logo-si-light.svg`) and a refreshed social card (`assets/og-image.svg`); the original `coco` mark (`logo.svg` / `logo-light.svg`) is preserved unchanged.
- **Repository migrated to the `coco-research` GitHub org.** All URLs, the npm scope (`@coco-research/coco-cli`), the Homebrew tap reference, and the publish workflows now point to `coco-research` instead of `rkz91`.
- **Relicensed to open-core.** The CoCo core stays MIT, but the Super Intelligence System (`systems/superintelligence/`) is now proprietary — source-available for reference, all rights reserved (see `systems/superintelligence/LICENSE`). The root `LICENSE` carves it out; `package.json`/`.claude-plugin.json` now declare `SEE LICENSE IN LICENSE`, the Homebrew formula uses `:cannot_represent`, and the README badge/labels read "Open-core." Bumped **Spec Version 1.0.0 → 1.1.0**. Note: MIT grants already made on prior releases of the Super Intelligence System remain valid for those snapshots; the change is forward-only.

### Fixed

- **Corrected asset counts.** Skills 146 → **147** (core 63 → 64 — `coco-ads` landed after the previous count fix), total addressable assets 864 → **865**, core install 123 → **124**. Replaced the stale `package.json` description ("59+ skills, 34+ commands") with accurate figures.
- **Expanded attribution.** Added CREDITS.md entries for Vercel and vercel-labs (web guidelines), plus reference sources for Apple (Liquid Glass), OpenAI, and Microsoft (Agent Lightning).

---

## [1.0.0] — 2026-06-07

First stable release. Establishes the Superintelligence board, the update notifier, and accurate docs.

### Added

- **Update notifier** — `npx @coco-research/coco-cli version` and `bash scripts/check-update.sh` report when a newer Coco is available. Checks the GitHub repo at most once per day, prints a one-line banner, sends no telemetry; opt out with `COCO_NO_UPDATE_CHECK=1`. The installer now prints the installed version and how to check for updates.
- **Superintelligence board expanded to 389 personas across 9 teams** (added Finance, Trading, Risk & Compliance, Strategy, Data & Analytics, GTM) plus the cross-team meta-orchestrator.

### Fixed

- **Full SI command family now generated on install.** The claude-code adapter now runs both `build_commands.py` (225 per-team) and `build_meta_commands.py` (17 cross-team), delivering all 242 SI commands instead of 225. The generators are now path-portable (derive the repo root from their own location; honor `COCO_SI_COMMANDS_DIR` / `COCO_SI_REPO`) instead of a hardcoded absolute path.
- **README accuracy** — clarified `/schedule` and `/loop` rely on the host CLI (not shipped by Coco), corrected the `vscode-continue` adapter status to experimental stub, and added Staying Current and Contributing sections.

---

## [0.1.0] — 2026-04-25

Initial public release.

### Added

- **59 skills** across foundational, PM, engineering, design, ops, meta domains
- **34 namespaced slash commands** — team, email, design, eng, pm, util
- **10 specialized subagents** at top level — code-reviewer, pm-advisor, mcp-specialist, refactoring-specialist, test-guardian, typescript-pro, ui-ux-designer, ai-engineer, data-specialist, database-architect
- **3 system bundles** — `gsd` (68 orchestration skills + 24 specialized GSD subagents), `brain` (6 knowledge skills), `team` (multi-agent pipelines)
- **claude-code adapter** wires `systems/<bundle>/agents/` and `systems/<bundle>/commands/` in addition to skills, when installed via `--systems`
- **4 IDE adapters** — `claude-code`, `cursor`, `codex`, `generic` (AGENTS.md)
- **Single-entry installer** — `bash install.sh` auto-detects target IDE
- **Frontmatter spec** — vendor-neutral artifact format ([`docs/architecture.md`](docs/architecture.md))
- **Full docs** — getting-started, install matrix, architecture, recommended-plugins
- **MIT license** — copyright Coco Inc

### Compatibility

- Stable: Claude Code, Cursor, Codex CLI, generic AGENTS.md
- Planned for v0.2: VS Code (via Continue), Antigravity (Google)

---

## Roadmap

### v0.2 (next)

- VS Code adapter (Continue integration)
- Antigravity adapter (experimental, format pending)
- CI: frontmatter linter
- Skill INDEX auto-generator
- Star history badge embed

### Backlog

- Asciinema demo casts
- Per-domain INDEX views (`docs/by-domain/<domain>.md`)
- Plugin distribution channel
- Web demo / playground
