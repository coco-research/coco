---
name: OpenAI Apps MCP
description: |
  Build ChatGPT apps with MCP servers on Cloudflare Workers. Extend ChatGPT with custom tools and interactive widgets (HTML/JS UI).

  Use when: developing ChatGPT extensions, implementing MCP servers, or troubleshooting CORS, widget 404s, MIME types, ASSETS binding errors, Next.js integration issues, or edge platform limitations.
user-invocable: true
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

# Building OpenAI Apps with Stateless MCP Servers

**Status**: Production Ready
**Last Updated**: 2026-01-21
**Dependencies**: `cloudflare-worker-base`, `hono-routing` (optional)
**Latest Versions**: @modelcontextprotocol/sdk@1.25.3, hono@4.11.3, zod@4.3.5, wrangler@4.58.0

---

## Overview

Build **ChatGPT Apps** using **MCP (Model Context Protocol)** servers on Cloudflare Workers. Extends ChatGPT with custom tools and interactive widgets (HTML/JS UI rendered in iframe).

**Architecture**: ChatGPT → MCP endpoint (JSON-RPC 2.0) → Tool handlers → Widget resources (HTML)

**Status**: Apps available to Business/Enterprise/Edu (GA Nov 13, 2025). MCP Apps Extension (SEP-1865) formalized Nov 21, 2025.

---

## Quick Start

### 1. Scaffold & Install

```bash
npm create cloudflare@latest my-openai-app -- --type hello-world --ts --git --deploy false
cd my-openai-app
npm install @modelcontextprotocol/sdk@1.25.3 hono@4.11.3 zod@4.3.5
npm install -D @cloudflare/vite-plugin@1.17.1 vite@7.2.4
```

### 2. Configure wrangler.jsonc

```jsonc
{
  "name": "my-openai-app",
  "main": "dist/index.js",
  "compatibility_flags": ["nodejs_compat"],  // Required for MCP SDK
  "assets": {
    "directory": "dist/client",
    "binding": "ASSETS"  // Must match TypeScript
  }
}
```

### 3. Create MCP Server (`src/index.ts`)

```typescript
import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';

const app = new Hono<{ Bindings: { ASSETS: Fetcher } }>();

// CRITICAL: Must allow chatgpt.com
app.use('/mcp/*', cors({ origin: 'https://chatgpt.com' }));

const mcpServer = new Server(
  { name: 'my-app', version: '1.0.0' },
  { capabilities: { tools: {}, resources: {} } }
);

// Tool registration
mcpServer.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: 'hello',
    description: 'Use this when user wants to see a greeting',
    inputSchema: {
      type: 'object',
      properties: { name: { type: 'string' } },
      required: ['name']
    },
    annotations: {
      openai: { outputTemplate: 'ui://widget/hello.html' }  // Widget URI
    }
  }]
}));

// Tool execution
mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === 'hello') {
    const { name } = request.params.arguments as { name: string };
    return {
      content: [{ type: 'text', text: `Hello, ${name}!` }],
      _meta: { initialData: { name } }  // Passed to widget
    };
  }
  throw new Error(`Unknown tool: ${request.params.name}`);
});

app.post('/mcp', async (c) => {
  const body = await c.req.json();
  const response = await mcpServer.handleRequest(body);
  return c.json(response);
});

app.get('/widgets/*', async (c) => c.env.ASSETS.fetch(c.req.raw));

export default app;
```

### 4. Create Widget (`src/widgets/hello.html`)

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { margin: 0; padding: 20px; font-family: system-ui; }
  </style>
</head>
<body>
  <div id="greeting">Loading...</div>
  <script>
    if (window.openai && window.openai.getInitialData) {
      const data = window.openai.getInitialData();
      document.getElementById('greeting').textContent = `Hello, ${data.name}! 👋`;
    }
  </script>
</body>
</html>
```

### 5. Deploy

```bash
npm run build
npx wrangler deploy
npx @modelcontextprotocol/inspector https://my-app.workers.dev/mcp
```

---

## Critical Requirements

**CORS**: Must allow `https://chatgpt.com` on `/mcp/*` routes
**Widget URI**: Must use `ui://widget/` prefix (e.g., `ui://widget/map.html`)
**MIME Type**: Must be `text/html+skybridge` for HTML resources
**Widget Data**: Pass via `_meta.initialData` (accessed via `window.openai.getInitialData()`)
**Tool Descriptions**: Action-oriented ("Use this when user wants to...")
**ASSETS Binding**: Serve widgets from ASSETS, not bundled in worker code
**SSE**: Send heartbeat every 30s (100s timeout on Workers)

---

## Known Issues Prevention

This skill prevents **14** documented issues:

### Issue #1: CORS Policy Blocks MCP Endpoint
**Error**: `Access to fetch blocked by CORS policy`
**Fix**: `app.use('/mcp/*', cors({ origin: 'https://chatgpt.com' }))`

### Issue #2: Widget Returns 404 Not Found
**Error**: `404 (Not Found)` for widget URL
**Fix**: Use `ui://widget/` prefix (not `resource://` or `/widgets/`)
```typescript
annotations: { openai: { outputTemplate: 'ui://widget/map.html' } }
```

### Issue #3: Widget Displays as Plain Text
**Error**: HTML source code visible instead of rendered widget
**Fix**: MIME type must be `text/html+skybridge` (not `text/html`)
```typescript
server.setRequestHandler(ListResourcesRequestSchema, async () => ({
  resources: [{ uri: 'ui://widget/map.html', mimeType: 'text/html+skybridge' }]
}));
```

### Issue #4: ASSETS Binding Undefined
**Error**: `TypeError: Cannot read property 'fetch' of undefined`
**Fix**: Binding name in wrangler.jsonc must match TypeScript
```jsonc
{ "assets": { "binding": "ASSETS" } }  // wrangler.jsonc
```
```typescript
type Bindings = { ASSETS: Fetcher };  // index.ts
```

### Issue #5: SSE Connection Drops After 100 Seconds
**Error**: SSE stream closes unexpectedly
**Fix**: Send heartbeat every 30s (Workers timeout at 100s inactivity)
```typescript
const heartbeat = setInterval(async () => {
  await stream.writeSSE({ data: JSON.stringify({ type: 'heartbeat' }), event: 'ping' });
}, 30000);
```

### Issue #6: ChatGPT Doesn't Suggest Tool
**Error**: Tool registered but never appears in suggestions
**Fix**: Use action-oriented descriptions
```typescript
// ✅ Good: 'Use this when user wants to see a location on a map'
// ❌ Bad: 'Shows a map'
```

### Issue #7: Widget Can't Access Initial Data
**Error**: `window.openai.getInitialData()` returns `undefined`
**Fix**: Pass data via `_meta.initialData`
```typescript
return {
  content: [{ type: 'text', text: 'Here is your map' }],
  _meta: { initialData: { location: 'SF', zoom: 12 } }
};
```

### Issue #8: Widget Scripts Blocked by CSP
**Error**: `Refused to load script (CSP directive)`
**Fix**: Use inline scripts or same-origin scripts. Third-party CDNs blocked.
```html
<!-- ✅ Works --> <script>console.log('ok');</script>
<!-- ❌ Blocked --> <script src="https://cdn.example.com/lib.js"></script>
```

### Issue #9: Hono Global Response Override Breaks Next.js (v1.25.0-1.25.2)
**Error**: `No response is returned from route handler` (Next.js App Router)
**Source**: [GitHub Issue #1369](https://github.com/modelcontextprotocol/typescript-sdk/issues/1369)
**Affected Versions**: v1.25.0 to v1.25.2
**Fixed In**: v1.25.3
**Why It Happens**: Hono (MCP SDK dependency) overwrites `global.Response`, breaking frameworks that extend it (Next.js, Remix, SvelteKit). NextResponse instanceof check fails.
**Prevention**:
- **Upgrade to v1.25.3+** (recommended)
- **Before fix**: Use `webStandardStreamableHTTPServerTransport` instead
- **Or**: Run MCP server on separate port from Next.js/Remix/SvelteKit app

```typescript
// ✅ v1.25.3+ - Fixed
const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
});

// ✅ v1.25.0-1.25.2 - Workaround
import { webStandardStreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/index.js';
const transport = webStandardStreamableHTTPServerTransport({
  sessionIdGenerator: undefined,
});
```

### Issue #10: Elicitation (User Input) Fails on Cloudflare Workers
**Error**: `EvalError: Code generation from strings disallowed`
**Source**: [GitHub Issue #689](https://github.com/modelcontextprotocol/typescript-sdk/issues/689)
**Why It Happens**: Internal AJV v6 validator uses prohibited APIs on edge platforms
**Prevention**: Avoid `elicitInput()` on edge platforms (Cloudflare Workers, Vercel Edge, Deno Deploy)

**Workaround**:
```typescript
// ❌ Don't use on Cloudflare Workers
const userInput = await server.elicitInput({
  prompt: "What is your name?",
  schema: { type: "string" }
});

// ✅ Use tool parameters instead
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name } = request.params.arguments as { name: string };
  // User provides via tool call, not elicitation
});
```

**Status**: Requires MCP SDK v2 to fix properly. Track [PR #844](https://github.com/modelcontextprotocol/typescript-sdk/pull/844).

### Issue #11: SSE Transport Statefulness Breaks Serverless Deployments
**Error**: `400: No transport found for sessionId`
**Source**: [GitHub Issue #273](https://github.com/modelcontextprotocol/typescript-sdk/issues/273)
**Why It Happens**: `SSEServerTransport` relies on in-memory session storage. In serverless environments (AWS Lambda, Cloudflare Workers), the initial `GET /sse` request may be handled by Instance A, but subsequent `POST /messages` requests land on Instance B, which lacks the in-memory state.
**Prevention**: Use **Streamable HTTP transport** (added in v1.24.0) instead of SSE for serverless deployments
**Solution**: For stateful SSE, deploy to non-serverless environments (VPS, long-running containers)

**Official Status**: Fixed by introducing Streamable HTTP (v1.24+) - now the **recommended standard** for serverless.

### Issue #12: OAuth Configuration Requires TWO Separate Apps
**Source**: [Cloudflare Remote MCP Server Docs](https://developers.cloudflare.com/agents/guides/remote-mcp-server/)
**Why It Happens**: OAuth providers validate redirect URLs strictly. Localhost and production have different URLs, so they need separate OAuth client registrations.
**Prevention**:
```bash
# Development OAuth App
Callback URL: http://localhost:8788/callback

# Production OAuth App
Callback URL: https://my-mcp-server.workers.dev/callback
```

**Additional Requirements**:
- KV namespace for auth state storage (create manually)
- `COOKIE_ENCRYPTION_KEY` env var: `openssl rand -hex 32`
- Client restart required after config changes

### Issue #13: Widget State Over 4k Tokens Causes Performance Issues (Community-sourced)
**Source**: [OpenAI Apps SDK - ChatGPT UI](https://developers.openai.com/apps-sdk/build/chatgpt-ui/)
**Why It Happens**: Widget state persists only to a single widget instance tied to one conversation message. State is reset when users submit via the main chat composer instead of widget controls.
**Prevention**: Keep state payloads under **4k tokens** for optimal performance

```typescript
// ✅ Good - Lightweight state
window.openai.setWidgetState({ selectedId: "item-123", view: "grid" });

// ❌ Bad - Will cause performance issues
window.openai.setWidgetState({
  items: largeArray,           // Don't store full datasets
  history: conversationLog,    // Don't store conversation history
  cache: expensiveComputation  // Don't cache large results
});
```

**Best Practice**:
- Store only UI state (selected items, view mode, filters)
- Fetch data from MCP server on widget mount
- Use tool calls to persist important data

### Issue #14: Widget-Initiated Tool Calls Fail Without Permission Flag (Community-sourced)
**Source**: [OpenAI Apps SDK - ChatGPT UI](https://developers.openai.com/apps-sdk/build/chatgpt-ui/)
**Why It Happens**: Components initiating tool calls via `window.openai.callTool()` require the tool marked as "able to be initiated by the component" on the MCP server. Without this flag, calls fail silently.
**Prevention**: Mark tools as `widgetCallable: true` in annotations

```typescript
// MCP Server - Mark tool as widget-callable
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: 'update_item',
    description: 'Update an item',
    inputSchema: { /* ... */ },
    annotations: {
      openai: {
        outputTemplate: 'ui://widget/item.html',
        // ✅ Required for widget-initiated calls
        widgetCallable: true
      }
    }
  }]
}));

// Widget - Now allowed to call tool
window.openai.callTool({
  name: 'update_item',
  arguments: { id: itemId, status: 'completed' }
});
```

---

## Widget Development Best Practices

### File Upload Limitations (Community-sourced)
**Source**: [OpenAI Apps SDK - ChatGPT UI](https://developers.openai.com/apps-sdk/build/chatgpt-ui/)

`window.openai.uploadFile()` only supports 3 image formats: `image/png`, `image/jpeg`, and `image/webp`. Other formats fail silently.

```typescript
// ✅ Supported
window.openai.uploadFile({ accept: 'image/png,image/jpeg,image/webp' });

// ❌ Not supported (fails silently)
window.openai.uploadFile({ accept: 'application/pdf' });
window.openai.uploadFile({ accept: 'text/csv' });
```

**Alternative for Other File Types**:
1. Use base64 encoding in tool arguments
2. Request user paste text content
3. Use external upload service (S3, R2) and pass URL

### Tool Performance Targets (Community-sourced)
**Source**: [OpenAI Apps SDK - Troubleshooting](https://developers.openai.com/apps-sdk/deploy/troubleshooting)

Tool calls exceeding "a few hundred milliseconds" cause UI sluggishness in ChatGPT. Official docs recommend profiling backends and implementing caching for slow operations.

**Performance Targets**:
- **< 200ms**: Ideal response time
- **200-500ms**: Acceptable but noticeable
- **> 500ms**: Sluggish, needs optimization

**Optimization Strategies**:
```typescript
// 1. Cache expensive computations
const cache = new Map();
if (cache.has(key)) return cache.get(key);
const result = await expensiveOperation();
cache.set(key, result);

// 2. Use KV/D1 for pre-computed data
const cached = await env.KV.get(`result:${id}`);
if (cached) return JSON.parse(cached);

// 3. Paginate large datasets
return {
  content: [{ type: 'text', text: 'First 20 results...' }],
  _meta: { hasMore: true, nextPage: 2 }
};

// 4. Move slow work to async tasks
// Return immediately, update via follow-up
```

---

## MCP SDK 1.25.x Updates (December 2025)

**Breaking Changes** from @modelcontextprotocol/sdk@1.24.x → 1.25.x:
- Removed loose type exports (Prompts, Resources, Roots, Sampling, Tools) - use specific schemas
- ES2020 target required (previous: ES2018)
- `setRequestHandler` is now typesafe - incorrect schemas throw type errors

**New Features**:
- **Tasks** (v1.24.0+): Long-running operations with progress tracking
- **Sampling with Tools** (v1.24.0+): Tools can request model sampling
- **OAuth Client Credentials** (M2M): Machine-to-machine authentication

**Migration**: If using loose type imports, update to specific schema imports:
```typescript
// ❌ Old (removed in 1.25.0)
import { Tools } from '@modelcontextprotocol/sdk/types.js';

// ✅ New (1.25.1+)
import { ListToolsRequestSchema, CallToolRequestSchema } from '@modelcontextprotocol/sdk/types.js';
```

---

## Zod 4.0 Migration Notes (MAJOR UPDATE - July 2025)

**Breaking Changes** from zod@3.x → 4.x:
- `.default()` now expects input type (not output type). Use `.prefault()` for old behavior.
- ZodError: `error.issues` (not `error.errors`)
- `.merge()` and `.superRefine()` deprecated
- Optional properties with defaults now always apply

**Performance**: 14x faster string parsing, 7x faster arrays, 6.5x faster objects

**Migration**: Update validation code:
```typescript
// Zod 4.x
try {
  const validated = schema.parse(data);
} catch (error) {
  if (error instanceof z.ZodError) {
    return { content: [{ type: 'text', text: error.issues.map(e => e.message).join(', ') }] };
  }
}
```

---

## Dependencies

```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.25.3",
    "hono": "^4.11.3",
    "zod": "^4.3.5"
  },
  "devDependencies": {
    "@cloudflare/vite-plugin": "^1.17.1",
    "@cloudflare/workers-types": "^4.20260103.0",
    "vite": "^7.2.4",
    "wrangler": "^4.54.0"
  }
}
```

## Official Documentation

- **MCP Specification**: https://modelcontextprotocol.io/ (Latest: 2025-11-25)
- **MCP SDK**: https://github.com/modelcontextprotocol/typescript-sdk
- **OpenAI Apps SDK**: https://developers.openai.com/apps-sdk
- **MCP Apps Extension (SEP-1865)**: http://blog.modelcontextprotocol.io/posts/2025-11-21-mcp-apps/
- **Context7 Library ID**: /modelcontextprotocol/typescript-sdk

## Production Reference

**Open Source Example**: https://github.com/jezweb/chatgpt-app-sdk (portfolio carousel widget)
- **Live in Production**: Rendering in ChatGPT Business
- **MCP Server**: Full JSON-RPC 2.0 implementation with tools + resources (~310 lines)
- **Widget Integration**: WordPress API → `window.openai.toolOutput` → React carousel
- **Database**: D1 (SQLite) for contact form submissions
- **Stack**: Hono 4 + React 19 + Tailwind v4 + Drizzle ORM
- **Key Files**:
  - `/src/lib/mcp/server.ts` - Complete MCP handler
  - `/src/server/tools/portfolio.ts` - Tool with widget annotations
  - `/src/widgets/PortfolioWidget.tsx` - Data access pattern
- **Verified**: All 14 known issues prevented, zero errors in production

---

## Community Resources

### Deployment Tools

**Cloudflare One-Click Deploy**: Deploy MCP servers to Cloudflare Workers with pre-built templates and auto-configured CI/CD. Includes OAuth wrapper and Python support.
- Docs: https://developers.cloudflare.com/agents/guides/remote-mcp-server/
- Blog: https://blog.cloudflare.com/model-context-protocol/

### Frameworks

**Skybridge** (Community): React-focused framework with HMR support for widgets and enhanced MCP server helpers. Unofficial but actively maintained.
- GitHub: https://github.com/alpic-ai/skybridge
- Docs: https://www.skybridge.tech/

> **Note**: Community frameworks are not officially supported. Use at your own discretion
