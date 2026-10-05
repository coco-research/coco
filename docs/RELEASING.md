# Releasing a product

Use this when any CoCo Research product gets a new version or changes stage.

1. Tag the commit and publish a GitHub Release with notes.
2. Update that product's row in `data/products.json` (the version and the stage tag). Run `python3 scripts/render-site-products.py`. Open the pull request with `data/products.json` and `index.html`.
3. If the release changes how many skills, commands, or personas ship, run the count gates with `bash tests/check-asset-counts.sh` and include the generated count files they compare against.
4. Add an entry to `CHANGELOG.md`.
