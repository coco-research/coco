#!/bin/bash
# Check if @openai/agents and @openai/agents-realtime are at recommended versions

echo "Checking OpenAI Agents SDK package versions..."
echo ""

# Expected versions
EXPECTED_AGENTS="0.2.1"
EXPECTED_REALTIME="0.2.1"
EXPECTED_ZOD="3"

# Check @openai/agents
echo "Checking @openai/agents..."
AGENTS_VERSION=$(npm view @openai/agents version 2>/dev/null)
if [ -z "$AGENTS_VERSION" ]; then
  echo "❌ @openai/agents not found on npm registry"
else
  echo "✅ Latest @openai/agents: $AGENTS_VERSION"
  if [ "$AGENTS_VERSION" != "$EXPECTED_AGENTS" ]; then
    echo "⚠️  Expected version: $EXPECTED_AGENTS"
    echo "   Consider updating skill templates if breaking changes exist"
  fi
fi
echo ""

# Check @openai/agents-realtime
echo "Checking @openai/agents-realtime..."
REALTIME_VERSION=$(npm view @openai/agents-realtime version 2>/dev/null)
if [ -z "$REALTIME_VERSION" ]; then
  echo "❌ @openai/agents-realtime not found on npm registry"
else
  echo "✅ Latest @openai/agents-realtime: $REALTIME_VERSION"
  if [ "$REALTIME_VERSION" != "$EXPECTED_REALTIME" ]; then
    echo "⚠️  Expected version: $EXPECTED_REALTIME"
    echo "   Consider updating skill templates if breaking changes exist"
  fi
fi
echo ""

# Check zod (peer dependency)
echo "Checking zod (peer dependency)..."
ZOD_VERSION=$(npm view zod version 2>/dev/null)
if [ -z "$ZOD_VERSION" ]; then
  echo "❌ zod not found on npm registry"
else
  echo "✅ Latest zod: $ZOD_VERSION"
  ZOD_MAJOR=$(echo "$ZOD_VERSION" | cut -d. -f1)
  if [ "$ZOD_MAJOR" != "$EXPECTED_ZOD" ]; then
    echo "⚠️  Expected major version: $EXPECTED_ZOD.x"
    echo "   Skill requires zod@3.x for schema validation"
  fi
fi
echo ""

echo "Version check complete!"
echo ""
echo "To update skill documentation:"
echo "  1. Update metadata.packages in SKILL.md frontmatter"
echo "  2. Update shared/package.json dependencies"
echo "  3. Re-test all templates"
echo "  4. Update metadata.last_verified date"
