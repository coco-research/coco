#!/usr/bin/env bash
set -euo pipefail

PKG_VER=$(python3 -c "import json; print(json.load(open('package.json'))['version'])")
PLUGIN_VER=$(python3 -c "import json; print(json.load(open('.claude-plugin.json'))['version'])")
MANIFEST_VER=$(python3 -c "import json; print(json.load(open('.release-please-manifest.json'))['.'])")

BOOTSTRAP_VER=$(grep 'PINNED_TAG=' bin/coco-bootstrap.sh | sed -E 's/.*PINNED_TAG="v([^"]+)".*/\1/')
README_VER=$(grep '<!-- x-release-please-version -->' README.md | sed -E 's/.*`v([^`]+)`.*/\1/')

if [ "$PKG_VER" != "$PLUGIN_VER" ] || [ "$PKG_VER" != "$MANIFEST_VER" ] || [ "$PKG_VER" != "$BOOTSTRAP_VER" ] || [ "$PKG_VER" != "$README_VER" ]; then
    echo "Version mismatch:"
    echo "package.json: $PKG_VER"
    echo ".claude-plugin.json: $PLUGIN_VER"
    echo ".release-please-manifest.json: $MANIFEST_VER"
    echo "bin/coco-bootstrap.sh: $BOOTSTRAP_VER"
    echo "README.md: $README_VER"
    exit 1
fi

echo "All version pins agree: $PKG_VER"
