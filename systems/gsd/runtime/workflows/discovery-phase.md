<purpose>
Execute discovery at the appropriate depth level.
Produces DISCOVERY.md (for Level 2-3) that informs PLAN.md creation.

Called from plan-phase.md's mandatory_discovery step with a depth parameter.

NOTE: For comprehensive ecosystem research ("how do experts build this"), use /gsd:plan-phase --research-phase instead, which produces RESEARCH.md.
</purpose>

<depth_levels>
**This workflow supports three depth levels:**

| Level | Name         | Time      | Output                                       | When                                      |
| ----- | ------------ | --------- | -------------------------------------------- | ----------------------------------------- |
| 1     | Quick Verify | 2-5 min   | No file, proceed with verified knowledge     | Single library, confirming current syntax |
| 2     | Standard     | 15-30 min | DISCOVERY.md                                 | Choosing between options, new integration |
| 3     | Deep Dive    | 1+ hour   | Detailed DISCOVERY.md with validation gates  | Architectural decisions, novel problems   |

**Depth is determined by plan-phase.md before routing here.**
</depth_levels>

<source_hierarchy>
**MANDATORY: Context7 BEFORE WebSearch**

Claude's training data is 6-18 months stale. Always verify.

1. **Context7 MCP FIRST** - Current docs, no hallucination
2. **Official docs** - When Context7 lacks coverage
3. **WebSearch LAST** - For comparisons and trends only

See ~/.claude/get-shit-done/templates/discovery.md `<discovery_protocol>` for full protocol.
</source_hierarchy>

<process>

<step name="determine_depth">
Check the depth parameter passed from plan-phase.md:
- `depth=verify` → Level 1 (Quick Verification)
- `depth=standard` → Level 2 (Standard Discovery)
- `depth=deep` → Level 3 (Deep Dive)

Route to appropriate level workflow below.
</step>

<step name="level_1_quick_verify">
**Level 1: Quick Verification (2-5 minutes)**

For: Single known library, confirming syntax/version still correct.

**Process:**

1. Resolve library in Context7:

   ```
   mcp__context7__resolve-library-id with libraryName: "[library]"
   ```

2. Fetch relevant docs:

   ```
   mcp__context7__get-library-docs with:
   - context7CompatibleLibraryID: [from step 1]
   - topic: [specific concern]
   ```

3. Verify:

   - Current version matches expectations
   - API syntax unchanged
   - No breaking changes in recent versions

4. **If verified:** Return to plan-phase.md with confirmation. No DISCOVERY.md needed.

5. **If concerns found:** Escalate to Level 2.

**Output:** Verbal confirmation to proceed, or escalation to Level 2.
</step>

<step name="level_2_standard">
**Level 2: Standard Discovery (15-30 minutes)**

For: Choosing between options, new external integration.

**Process:**

1. **Identify what to discover:**

   - What options exist?
   - What are the key comparison criteria?
   - What's our specific use case?

2. **Context7 for each option:**

   ```
   For each library/framework:
   - mcp__context7__resolve-library-id
   - mcp__context7__get-library-docs (mode: "code" for API, "info" for concepts)
   ```

3. **Official docs** for anything Context7 lacks.

4. **WebSearch** for comparisons:

   - "[option A] vs [option B] {current_year}"
   - "[option] known issues"
   - "[option] with [our stack]"

5. **Cross-verify:** Any WebSearch finding → confirm with Context7/official docs.

6. **Create DISCOVERY.md** using ~/.claude/get-shit-done/templates/discovery.md structure:

   - Summary with recommendation
   - Key findings per option
   - Code examples from Context7
   - Confidence level (should be MEDIUM-HIGH for Level 2)

7. Return to plan-phase.md.

**Output:** `.planning/phases/XX-name/DISCOVERY.md`
</step>

<step name="level_3_deep_dive">
**Level 3: Deep Dive (1+ hour)**

For: Architectural decisions, novel problems, high-risk choices.

