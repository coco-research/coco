# User Profiling: Detection Heuristics Reference

This reference document defines detection heuristics for behavioral profiling across 8 dimensions. The gsd-user-profiler agent applies these rules when analyzing extracted session messages. Do not invent dimensions or scoring rules beyond what is defined here.

## How to Use This Document

1. The gsd-user-profiler agent reads this document before analyzing any messages
2. For each dimension, the agent scans messages for the signal patterns defined below
3. The agent applies the detection heuristics to classify the developer's pattern
4. Confidence is scored using the thresholds defined per dimension
5. Evidence quotes are curated using the rules in the Evidence Curation section
6. Output must conform to the JSON schema in the Output Schema section

---

## Dimensions

### 1. Communication Style

`dimension_id: communication_style`

**What we're measuring:** How the developer phrases requests, instructions, and feedback -- the structural pattern of their messages to Claude.

**Rating spectrum:**

| Rating | Description |
|--------|-------------|
| `terse-direct` | Short, imperative messages with minimal context. Gets to the point immediately. |
| `conversational` | Medium-length messages mixing instructions with questions and thinking-aloud. Natural, informal tone. |
| `detailed-structured` | Long messages with explicit structure -- headers, numbered lists, problem statements, pre-analysis. |
| `mixed` | No dominant pattern; style shifts based on task type or project context. |

**Signal patterns:**

1. **Message length distribution** -- Average word count across messages. Terse < 50 words, conversational 50-200 words, detailed > 200 words.
2. **Imperative-to-interrogative ratio** -- Ratio of commands ("fix this", "add X") to questions ("what do you think?", "should we?"). High imperative ratio suggests terse-direct.
3. **Structural formatting** -- Presence of markdown headers, numbered lists, code blocks, or bullet points within messages. Frequent formatting suggests detailed-structured.
4. **Context preambles** -- Whether the developer provides background/context before making a request. Preambles suggest conversational or detailed-structured.
5. **Sentence completeness** -- Whether messages use full sentences or fragments/shorthand. Fragments suggest terse-direct.
6. **Follow-up pattern** -- Whether the developer provides additional context in subsequent messages (multi-message requests suggest conversational).

**Detection heuristics:**

1. If average message length < 50 words AND predominantly imperative mood AND minimal formatting --> `terse-direct`
2. If average message length 50-200 words AND mix of imperative and interrogative AND occasional formatting --> `conversational`
