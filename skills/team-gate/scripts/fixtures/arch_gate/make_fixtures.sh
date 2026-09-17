#!/bin/bash
# Create or update test fixtures for arch_gate.py
# This script is idempotent: it can be run multiple times safely.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Fixture 1: remove-verdict
# A repo where a component claims a path that no longer exists (all primary paths gone)
echo "Setting up remove-verdict fixture..."
REMOVE_ROOT="$SCRIPT_DIR/remove-verdict"
mkdir -p "$REMOVE_ROOT/.arch"

cd "$REMOVE_ROOT"

# Initialize git if needed
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"
fi

# Create a component that claims a path
mkdir -p src/deleted-component
echo "// This will be deleted" > src/deleted-component/main.rs

# Create minimal index.json with component claiming the deleted path
HEAD=$(git rev-parse HEAD 2>/dev/null || echo "placeholder")
cat > .arch/index.json << EOF
{
  "schemaVersion": "1.0",
  "pinnedCommit": "$HEAD",
  "ecosystem": {
    "treeTruncated": false
  },
  "components": [
    {
      "id": "deleted-component",
      "title": "Deleted Component",
      "codeOwnership": {
        "primary": {
          "directories": ["src/deleted-component"],
          "rationale": "This path will be deleted"
        }
      }
    }
  ]
}
EOF

# Make initial commit if not exists
if ! git rev-parse HEAD > /dev/null 2>&1; then
    git add .
    git commit -m "Initial commit"
    # Update pinnedCommit in index to actual HEAD
    HEAD=$(git rev-parse HEAD)
    sed -i.bak "s/\"pinnedCommit\": \"placeholder\"/\"pinnedCommit\": \"$HEAD\"/" .arch/index.json
    rm -f .arch/index.json.bak
    git add .arch/index.json
    git commit -m "Pin to HEAD"
fi

# Now delete the component's path
rm -rf src/deleted-component
git add -A
git commit -m "Delete component path" 2>/dev/null || true

# Fixture 2: prune-verdict
# A repo where some paths of a component exist, some don't (PRUNE verdict)
echo "Setting up prune-verdict fixture..."
PRUNE_ROOT="$SCRIPT_DIR/prune-verdict"
mkdir -p "$PRUNE_ROOT/.arch"

cd "$PRUNE_ROOT"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"
fi

# Create a component with multiple paths
mkdir -p src/component-a src/component-b
echo "// A" > src/component-a/main.rs
echo "// B" > src/component-b/main.rs

HEAD=$(git rev-parse HEAD 2>/dev/null || echo "placeholder")
cat > .arch/index.json << EOF
{
  "schemaVersion": "1.0",
  "pinnedCommit": "$HEAD",
  "ecosystem": {
    "treeTruncated": false
  },
  "components": [
    {
      "id": "multi-path",
      "title": "Multi-path Component",
      "codeOwnership": {
        "primary": {
          "directories": ["src/component-a", "src/component-b"],
          "rationale": "This component spans two directories"
        }
      }
    }
  ]
}
EOF

if ! git rev-parse HEAD > /dev/null 2>&1; then
    git add .
    git commit -m "Initial commit"
    HEAD=$(git rev-parse HEAD)
    sed -i.bak "s/\"pinnedCommit\": \"placeholder\"/\"pinnedCommit\": \"$HEAD\"/" .arch/index.json
    rm -f .arch/index.json.bak
    git add .arch/index.json
    git commit -m "Pin to HEAD"
fi

# Delete one of the paths (creating a PRUNE verdict)
rm -rf src/component-b
git add -A
git commit -m "Delete one path" 2>/dev/null || true

# Fixture 3: clean
# A repo where everything passes (all paths exist, no drift)
echo "Setting up clean fixture..."
CLEAN_ROOT="$SCRIPT_DIR/clean"
mkdir -p "$CLEAN_ROOT/.arch"

cd "$CLEAN_ROOT"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"
fi

# Create components with existing paths
mkdir -p src/comp-a src/comp-b
echo "// A" > src/comp-a/main.rs
echo "// B" > src/comp-b/main.rs

HEAD=$(git rev-parse HEAD 2>/dev/null || echo "placeholder")
cat > .arch/index.json << EOF
{
  "schemaVersion": "1.0",
  "pinnedCommit": "$HEAD",
  "ecosystem": {
    "treeTruncated": false
  },
  "components": [
    {
      "id": "component-a",
      "title": "Component A",
      "codeOwnership": {
        "primary": {
          "directories": ["src/comp-a"],
          "rationale": "Component A owns comp-a"
        }
      },
      "connections": ["component-b"]
    },
    {
      "id": "component-b",
      "title": "Component B",
      "codeOwnership": {
        "primary": {
          "directories": ["src/comp-b"],
          "rationale": "Component B owns comp-b"
        }
      },
      "connections": ["component-a"]
    }
  ]
}
EOF

if ! git rev-parse HEAD > /dev/null 2>&1; then
    git add .
    git commit -m "Initial commit"
    HEAD=$(git rev-parse HEAD)
    sed -i.bak "s/\"pinnedCommit\": \"placeholder\"/\"pinnedCommit\": \"$HEAD\"/" .arch/index.json
    rm -f .arch/index.json.bak
    git add .arch/index.json
    git commit -m "Pin to HEAD"
fi

# Fixture 4: stale-pin
# A repo where pinned-commit is not HEAD (stale index)
echo "Setting up stale-pin fixture..."
STALE_ROOT="$SCRIPT_DIR/stale-pin"
mkdir -p "$STALE_ROOT/.arch"

cd "$STALE_ROOT"

if ! git rev-parse --git-dir > /dev/null 2>&1; then
    git init
    git config user.email "test@example.com"
    git config user.name "Test User"
fi

# Create components
mkdir -p src/comp-x
echo "// X" > src/comp-x/main.rs

# Make first commit
git add .
git commit -m "First commit"
FIRST_COMMIT=$(git rev-parse HEAD)

# Create index pinned to first commit
cat > .arch/index.json << EOF
{
  "schemaVersion": "1.0",
  "pinnedCommit": "$FIRST_COMMIT",
  "ecosystem": {
    "treeTruncated": false
  },
  "components": [
    {
      "id": "component-x",
      "title": "Component X",
      "codeOwnership": {
        "primary": {
          "directories": ["src/comp-x"],
          "rationale": "Component X"
        }
      }
    }
  ]
}
EOF

git add .arch/index.json
git commit -m "Add index"

# Make another commit to move HEAD away from pin
echo "// More code" >> src/comp-x/main.rs
git add src/comp-x/main.rs
git commit -m "Make HEAD diverge from pin"

echo "Fixtures created successfully."
