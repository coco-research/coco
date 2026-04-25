# Agent Orchestration Patterns

This reference explains different approaches to coordinating multiple agents in OpenAI Agents SDK.

---

## Pattern 1: LLM-Based Orchestration

**What**: Let the LLM autonomously decide how to route tasks and execute tools.

**When to Use**:
- Requirements are complex and context-dependent
- You want adaptive, intelligent routing
- Task decomposition benefits from reasoning

**How It Works**:
1. Create a "manager" agent with instructions and tools/handoffs
2. LLM plans task execution based on instructions
3. LLM decides which tools to call or agents to delegate to
4. Self-critique and improvement loops possible

**Example**:
```typescript
const managerAgent = Agent.create({
  name: 'Project Manager',
  instructions: `You coordinate project work. You have access to:
  - Database agent for data operations
  - API agent for external integrations
  - UI agent for frontend tasks

  Analyze the request and route to appropriate agents.`,
  handoffs: [databaseAgent, apiAgent, uiAgent],
});
```

**Best Practices**:
- Write clear, detailed instructions
- Define tool/handoff descriptions precisely
- Implement monitoring and logging
- Create evaluation frameworks
- Iterate based on observed failures

**Pros**:
- Flexible and adaptive
- Handles complex scenarios
- Can self-improve with feedback

**Cons**:
- Less predictable
- Higher token usage
- Requires good prompt engineering

---

## Pattern 2: Code-Based Orchestration

**What**: Use explicit programming logic to control agent execution flow.

**When to Use**:
- Workflow is deterministic and well-defined
- You need guaranteed execution order
- Debugging and testing are priorities
- Cost control is important

**How It Works**:
1. Define agents for specific tasks
2. Use code to sequence execution
3. Pass outputs as inputs to next steps
4. Implement conditional logic manually

**Example**:
```typescript
// Sequential execution
const summary = await run(summarizerAgent, article);
const sentiment = await run(sentimentAgent, summary.finalOutput);
const recommendations = await run(recommenderAgent, sentiment.finalOutput);

// Conditional routing
if (sentiment.finalOutput.score < 0.3) {
  await run(escalationAgent, article);
} else {
  await run(responseAgent, article);
}

// Parallel execution
const [summary, keywords, entities] = await Promise.all([
  run(summarizerAgent, article),
  run(keywordAgent, article),
  run(entityAgent, article),
]);

// Feedback loops
let result = await run(writerAgent, prompt);
let quality = await run(evaluatorAgent, result.finalOutput);

while (quality.finalOutput.score < 8) {
  result = await run(writerAgent, `Improve: ${result.finalOutput}`);
  quality = await run(evaluatorAgent, result.finalOutput);
}
```

**Best Practices**:
- Break complex tasks into discrete steps
- Use structured outputs for reliable routing
- Implement error handling at each step
- Log execution flow for debugging

**Pros**:
- Predictable and deterministic
- Easy to debug and test
- Full control over execution
- Lower token usage

**Cons**:
- Less flexible
- Requires upfront planning
- Manual routing logic

---

## Pattern 3: Agents as Tools

**What**: Wrap agents as tools for a manager LLM, which decides when to invoke them.

**When to Use**:
- You want LLM routing but keep the manager in control
- Sub-agents produce specific outputs (data, not conversation)
- You need manager to summarize/synthesize results

**How It Works**:
1. Create specialist agents with `outputType`
2. Convert agents to tools
3. Manager agent calls them as needed
4. Manager synthesizes final response

**Example**:
```typescript
const weatherAgent = new Agent({
  name: 'Weather Service',
  instructions: 'Return weather data',
  outputType: z.object({
    temperature: z.number(),
    conditions: z.string(),
  }),
});

// Convert to tool
const weatherTool = tool({
  name: 'get_weather',
  description: 'Get weather data',
  parameters: z.object({ city: z.string() }),
  execute: async ({ city }) => {
    const result = await run(weatherAgent, city);
    return result.finalOutput;
  },
});

const managerAgent = new Agent({
  name: 'Assistant',
  instructions: 'Help users with various tasks',
  tools: [weatherTool, /* other agent-tools */],
});
```

**Pros**:
- Manager maintains conversation control
- Clean separation of concerns
- Reusable specialist agents

**Cons**:
- Extra layer of complexity
- Slightly higher latency

---

## Pattern 4: Parallel Execution

**What**: Run multiple agents concurrently and select/combine results.

**When to Use**:
- Independent tasks can run simultaneously
- You want to generate multiple options
- Time to result matters

**Example Use Cases**:
- Generate 3 marketing copy variants
- Parallel research tasks (summary, pros/cons, stats, quotes)
- Quality voting (best result selection)

**See Templates**:
- `templates/text-agents/agent-parallel.ts`

---

## Pattern 5: Human-in-the-Loop

**What**: Require human approval for specific actions.

**When to Use**:
- High-stakes actions (payments, deletions, emails)
- Compliance requirements
- Building trust in AI systems

**How It Works**:
1. Mark tools with `requiresApproval: true`
2. Handle `ToolApprovalItem` interruptions
3. Prompt user for approval
4. Resume with approve/reject

**See Templates**:
- `templates/text-agents/agent-human-approval.ts`

---

## Choosing a Pattern

| Requirement | Recommended Pattern |
|-------------|---------------------|
| Adaptive routing | LLM-Based |
| Deterministic flow | Code-Based |
| Cost control | Code-Based |
| Complex reasoning | LLM-Based |
| Multiple options | Parallel |
| Safety requirements | Human-in-the-Loop |
| Manager + specialists | Agents as Tools |

---

## Combining Patterns

You can mix patterns:

```typescript
// Code-based orchestration with parallel execution and HITL
const [research1, research2] = await Promise.all([
  run(researchAgent1, topic),
  run(researchAgent2, topic),
]);

// LLM-based synthesis
const synthesis = await run(synthesizerAgent, {
  research1: research1.finalOutput,
  research2: research2.finalOutput,
});

// Human approval for final output
const approved = await requestApproval(synthesis.finalOutput);
if (approved) {
  await run(publishAgent, synthesis.finalOutput);
}
```

---

**Last Updated**: 2025-10-26
**Source**: [OpenAI Agents Docs - Multi-Agent Guide](https://openai.github.io/openai-agents-js/guides/multi-agent)
