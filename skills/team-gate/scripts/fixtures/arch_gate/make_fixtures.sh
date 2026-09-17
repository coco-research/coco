#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATES="$SCRIPT_DIR/templates"
BUILD="$SCRIPT_DIR/_build"

[ "$1" = "clean" ] && rm -rf "$BUILD"

build_fixture() {
    local name="$1"
    local stale="$2"
    local root="$BUILD/$name"

    # Clean previous fixture to ensure idempotency
    rm -rf "$root"
    mkdir -p "$root"
    cp -r "$TEMPLATES/$name/src" "$root/src" 2>/dev/null || true
    mkdir -p "$root/.arch"
    cp "$TEMPLATES/$name/index.json" "$root/.arch/index.json"

    cd "$root"
    git init > /dev/null
    git config user.email "test@example.com"
    git config user.name "Test"
    git add . && git commit -q -m "Initial"

    PIN=$(git rev-parse HEAD)
    sed -i '' "s/PLACEHOLDER/$PIN/" .arch/index.json

    if [ "$stale" = "1" ]; then
        # Stale: diverge after setting pin
        echo "more" >> src/x/main.rs
        git add src/x/main.rs && git commit -q -m "Diverge"
        echo "$PIN" > .arch/pinned-commit
    else
        # Clean/Drift: delete files if needed, then update index+pin to current HEAD
        if [ "$name" = "remove-verdict" ] && [ -d src/deleted ]; then
            rm -rf src/deleted
        fi

        # Stage index and any deletions, commit all changes
        git add -A && git commit -q -m "Reconcile" || true

        # Get final HEAD
        FINAL=$(git rev-parse HEAD)
        echo "$FINAL" > .arch/pinned-commit
    fi
}

build_fixture "remove-verdict" 0
build_fixture "prune-verdict" 0
build_fixture "clean" 0
build_fixture "stale-pin" 1
