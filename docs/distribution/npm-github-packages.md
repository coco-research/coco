# Publishing to GitHub Packages (npm)

Reference: https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-npm-registry

## What was set up

| File | Purpose |
|------|---------|
| `package.json` | Renamed package to `@coco-research/coco-cli`; added `publishConfig.registry` pointing to `https://npm.pkg.github.com` |
| `.npmrc` | Tells npm to use GitHub Packages registry for the `@coco-research` scope |
| `.github/workflows/publish-npm.yml` | CI workflow that publishes on `release: published` (or manual trigger) |

## How to publish a new version

### Option A — automatic via release

```bash
# Bump version
npm version patch    # or minor / major
git push && git push --tags

# Create a GitHub Release on the new tag
gh release create v0.1.1 --title "v0.1.1" --generate-notes
```

The `publish-npm.yml` workflow fires on the release event and publishes to GitHub Packages using the auto-provided `GITHUB_TOKEN`.

### Option B — manual trigger

Push a commit, then:

```bash
gh workflow run publish-npm.yml --repo coco-research/coco
```

### Option C — local publish

```bash
# Auth: create a personal access token with `write:packages` scope
# https://github.com/settings/tokens
export GITHUB_TOKEN=ghp_yourtoken
npm publish
```

## How users install

```bash
# Configure registry for the @coco-research scope (one-time)
echo "@coco-research:registry=https://npm.pkg.github.com" >> ~/.npmrc

# Auth: GitHub Packages requires authentication even for public packages
# Create a token at https://github.com/settings/tokens with `read:packages` scope
echo "//npm.pkg.github.com/:_authToken=ghp_yourtoken" >> ~/.npmrc

# Install
npm install -g @coco-research/coco-cli
coco install
```

## Differences vs npm registry (`npmjs.com`)

| | GitHub Packages | npm registry |
|---|---|---|
| Auth required for install | yes (even public) | no (public packages) |
| Scope | `@<org-or-user>/<pkg>` required | optional |
| Token | GitHub PAT with `read:packages` | npm token |
| Discoverability | github.com/<user>/coco/packages | npmjs.com/package/<pkg> |

## When to also publish to npmjs.com

GitHub Packages is great for internal/scoped distribution. For maximum discoverability and frictionless install (no auth), also publish to npm registry:

1. Create npm account at https://www.npmjs.com/signup
2. Create access token: `npm token create`
3. Add as `NPM_TOKEN` secret in repo settings
4. Add a parallel workflow that publishes to npmjs.com (omit `publishConfig` or override at publish time)

For Coco's scope:
- v0.1.0 → GitHub Packages (this setup) — gates installs to people willing to authenticate
- v0.2.0+ → also publish to npmjs.com for `npx coco-cli` to work without auth

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `403 Forbidden` on publish | Check workflow has `permissions: packages: write` |
| `404 Not Found` on install | Verify scope name matches GH user (`@coco-research`) |
| `EAUTH` on install | Token needs `read:packages` scope |
| Workflow doesn't fire | Confirm release event triggered (`gh release list`) |
