# Thinking Partner Integration

Conditional extended thinking at workflow decision points. Activates when `features.thinking_partner: true` in `.planning/config.json` (default: false).

---

## Tradeoff Detection Signals

The thinking partner activates when developer responses contain specific signals indicating competing priorities:

**Keyword signals:**
- "or" / "versus" / "vs" connecting two approaches
- "tradeoff" / "trade-off" / "tradeoffs"
- "on one hand" / "on the other hand"
