# HyperFrames — Video & Motion Skill Bundle

Vendored skill bundle from HeyGen's [`hyperframes`](https://github.com/heygen-com/hyperframes) project (npm `hyperframes`). Twenty skills covering the HyperFrames HTML-composition engine plus the video-authoring workflows built on it: explainer/promo/launch videos, motion graphics, caption and overlay treatments, slideshows, and Figma/Remotion interop.

## License

This entire bundle (`systems/hyperframes/`) is vendored third-party code, **not** part of Coco's MIT core. It is licensed under **Apache License 2.0**, Copyright 2026 HeyGen, Inc. — see [`LICENSE`](LICENSE) in this directory, which governs every file under `systems/hyperframes/skills/`. Upstream: <https://github.com/heygen-com/hyperframes>.

## Install

```bash
bash adapters/<your-ide>/install.sh --systems hyperframes
```

This wires the 20 HyperFrames skills into your IDE's skill location.

## What's in the bundle

**HyperFrames engine (7)** — `hyperframes` (entry point/router), `hyperframes-core` (composition contract), `hyperframes-cli` (dev-loop commands), `hyperframes-animation` (motion + runtime adapters), `hyperframes-keyframes` (seek-safe keyframe authoring), `hyperframes-creative` (design/brand/audio direction), `hyperframes-registry` (component/block registry).

**HeyGen core skills (2)** — `media-use` (media resolution/generation OS), `figma` (Figma → HyperFrames import).

**Video suite (11)** — `general-video`, `motion-graphics`, `music-to-video`, `pr-to-video`, `product-launch-video`, `faceless-explainer`, `talking-head-recut`, `embedded-captions`, `slideshow`, `remotion-to-hyperframes`, `website-to-video`.

## Known upstream deprecation

`website-to-video` was folded into `product-launch-video` upstream as of `hyperframes` v0.7.59 — its input handling now lives inside `product-launch-video`. It is kept here in full per Coco's standing "vendor faithfully, never delete" convention, so contributors can still see and use the standalone flow. Treat `website-to-video` as deprecated upstream; prefer `product-launch-video` for new work that targets a URL.

## Why a separate system

All 20 skills come from one upstream (`heygen-com/hyperframes`) under one license. Bundling them under `systems/hyperframes/` — rather than 20 individual entries under `skills/` — keeps the vendor boundary explicit, lets one `LICENSE` file unambiguously govern the whole set, and matches the opt-in `--systems <bundle>` install pattern already used for `gsd`, `brain`, and `team`.
