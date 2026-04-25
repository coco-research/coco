---
name: browser-automation
description: Browser automation for AI agents. Two providers — agent-browser (local CLI with Playwright) and agentic-browser (cloud via inference.sh). Both use the same @e ref-based workflow for navigating pages, filling forms, clicking buttons, taking screenshots, extracting data, and automating browser tasks.
allowed-tools: Bash(agent-browser:*), Bash(infsh *)
---

# Browser Automation

Browser automation for AI agents with two provider options. Both share the same core workflow: navigate, snapshot, interact using `@e` refs, re-snapshot after changes.

| Provider | Runtime | Best For |
|----------|---------|----------|
| agent-browser | Local (Playwright CLI) | Local testing, iOS Simulator, file:// URLs |
| agentic-browser | Cloud (inference.sh) | Video recording, cloud execution, parallel sessions |

---

## Core Workflow (Both Providers)

Every browser automation follows this pattern:

1. **Navigate** — Open a URL
2. **Snapshot** — Get `@e` refs for interactive elements
3. **Interact** — Use refs to click, fill, select
4. **Re-snapshot** — After navigation or DOM changes, get fresh refs

**Important: Refs are invalidated after navigation.** Always re-snapshot after clicking links/buttons, form submissions, or dynamic content loading.

---

## Provider 1: agent-browser (Local CLI)

### Quick Start

```bash
agent-browser open https://example.com/form
agent-browser snapshot -i
# Output: @e1 [input type="email"], @e2 [input type="password"], @e3 [button] "Submit"

agent-browser fill @e1 "user@example.com"
agent-browser fill @e2 "password123"
agent-browser click @e3
agent-browser wait --load networkidle
agent-browser snapshot -i  # Check result
```

### Essential Commands

```bash
# Navigation
agent-browser open <url>              # Navigate
agent-browser close                   # Close browser

# Snapshot
agent-browser snapshot -i             # Interactive elements with refs
agent-browser snapshot -i -C          # Include cursor-interactive elements
agent-browser snapshot -s "#selector" # Scope to CSS selector

# Interaction (use @refs from snapshot)
agent-browser click @e1               # Click element
agent-browser fill @e2 "text"         # Clear and type text
agent-browser type @e2 "text"         # Type without clearing
agent-browser select @e1 "option"     # Select dropdown option
agent-browser check @e1               # Check checkbox
agent-browser press Enter             # Press key
agent-browser scroll down 500         # Scroll page

# Get information
agent-browser get text @e1            # Get element text
agent-browser get url                 # Get current URL
agent-browser get title               # Get page title

# Wait
agent-browser wait @e1                # Wait for element
agent-browser wait --load networkidle # Wait for network idle
agent-browser wait --url "**/page"    # Wait for URL pattern
agent-browser wait 2000               # Wait milliseconds

# Capture
agent-browser screenshot              # Screenshot to temp dir
agent-browser screenshot --full       # Full page screenshot
agent-browser pdf output.pdf          # Save as PDF
```

### Authentication with State Persistence

```bash
# Login once and save state
agent-browser open https://app.example.com/login
agent-browser snapshot -i
agent-browser fill @e1 "$USERNAME"
agent-browser fill @e2 "$PASSWORD"
agent-browser click @e3
agent-browser wait --url "**/dashboard"
agent-browser state save auth.json

# Reuse in future sessions
agent-browser state load auth.json
agent-browser open https://app.example.com/dashboard
```

### Parallel Sessions

```bash
agent-browser --session site1 open https://site-a.com
agent-browser --session site2 open https://site-b.com
agent-browser session list
```

### Visual / Debugging

```bash
agent-browser --headed open https://example.com
agent-browser highlight @e1
agent-browser record start demo.webm
```

### Local Files

```bash
agent-browser --allow-file-access open file:///path/to/document.pdf
agent-browser --allow-file-access open file:///path/to/page.html
agent-browser screenshot output.png
```

### iOS Simulator (Mobile Safari)

```bash
# List available iOS simulators
agent-browser device list

# Launch Safari on a specific device
agent-browser -p ios --device "iPhone 16 Pro" open https://example.com

# Same workflow — snapshot, interact, re-snapshot
agent-browser -p ios snapshot -i
agent-browser -p ios tap @e1
agent-browser -p ios fill @e2 "text"
agent-browser -p ios swipe up
agent-browser -p ios screenshot mobile.png
agent-browser -p ios close
```

**Requirements:** macOS with Xcode, Appium (`npm install -g appium && appium driver install xcuitest`)

### Semantic Locators (Alternative to Refs)

```bash
agent-browser find text "Sign In" click
agent-browser find label "Email" fill "user@test.com"
agent-browser find role button click --name "Submit"
agent-browser find placeholder "Search" type "query"
agent-browser find testid "submit-btn" click
```

---

## Provider 2: agentic-browser (Cloud via inference.sh)

### Quick Start

```bash
# Install CLI
curl -fsSL https://cli.inference.sh | sh && infsh login

# Open a page
infsh app run agentic-browser --function open --input '{"url": "https://example.com"}' --session new
```

### Core Functions

| Function | Description |
|----------|-------------|
| `open` | Navigate to URL, configure browser (viewport, proxy, video) |
| `snapshot` | Re-fetch page state with `@e` refs after DOM changes |
| `interact` | Perform actions using `@e` refs |
| `screenshot` | Take page screenshot (viewport or full page) |
| `execute` | Run JavaScript code on the page |
| `close` | Close session, returns video if recording enabled |

### Interact Actions

| Action | Description | Required Fields |
|--------|-------------|-----------------|
| `click` | Click element | `ref` |
| `dblclick` | Double-click | `ref` |
| `fill` | Clear and type text | `ref`, `text` |
| `type` | Type without clearing | `text` |
| `press` | Press key (Enter, Tab) | `text` |
| `select` | Select dropdown option | `ref`, `text` |
| `hover` | Hover over element | `ref` |
| `check` / `uncheck` | Toggle checkbox | `ref` |
| `drag` | Drag and drop | `ref`, `target_ref` |
| `upload` | Upload file(s) | `ref`, `file_paths` |
| `scroll` | Scroll page | `direction`, `scroll_amount` |
| `back` | Go back in history | - |
| `wait` | Wait milliseconds | `wait_ms` |
| `goto` | Navigate to URL | `url` |

### Full Example

```bash
# Start session
RESULT=$(infsh app run agentic-browser --function open --session new --input '{
  "url": "https://example.com/login"
}')
SESSION_ID=$(echo $RESULT | jq -r '.session_id')

# Fill and submit
infsh app run agentic-browser --function interact --session $SESSION_ID --input '{
  "action": "fill", "ref": "@e1", "text": "user@example.com"
}'
infsh app run agentic-browser --function interact --session $SESSION_ID --input '{
  "action": "fill", "ref": "@e2", "text": "password123"
}'
infsh app run agentic-browser --function interact --session $SESSION_ID --input '{
  "action": "click", "ref": "@e3"
}'

# Re-snapshot after navigation
infsh app run agentic-browser --function snapshot --session $SESSION_ID --input '{}'

# Close when done
infsh app run agentic-browser --function close --session $SESSION_ID --input '{}'
```

### Video Recording

```bash
# Start with recording enabled
SESSION=$(infsh app run agentic-browser --function open --session new --input '{
  "url": "https://example.com",
  "record_video": true,
  "show_cursor": true
}' | jq -r '.session_id')

# ... perform actions ...

# Close to get the video file
infsh app run agentic-browser --function close --session $SESSION --input '{}'
# Returns: {"success": true, "video": <File>}
```

### Proxy Support

```bash
infsh app run agentic-browser --function open --session new --input '{
  "url": "https://example.com",
  "proxy_url": "http://proxy.example.com:8080",
  "proxy_username": "user",
  "proxy_password": "pass"
}'
```

### File Upload

```bash
infsh app run agentic-browser --function interact --session $SESSION --input '{
  "action": "upload",
  "ref": "@e5",
  "file_paths": ["/path/to/file.pdf"]
}'
```

### JavaScript Execution

```bash
infsh app run agentic-browser --function execute --session $SESSION --input '{
  "code": "document.querySelectorAll(\"h2\").length"
}'
# Returns: {"result": "5", "screenshot": <File>}
```

---

## Common Patterns (Both Providers)

### Form Submission
1. Open the form URL
2. Snapshot to get element refs
3. Fill each field using refs
4. Click submit button
5. Wait for navigation/network idle
6. Re-snapshot to verify result

### Data Extraction
1. Navigate to target page
2. Snapshot interactive elements
3. Get text from specific elements
4. Optionally use JSON output for parsing

### Authentication Flow
1. Navigate to login page
2. Fill credentials
3. Handle 2FA if prompted
4. Save session state for reuse
5. Load saved state in future sessions

---

## Deep-Dive Documentation

| Reference | Description |
|-----------|-------------|
| `references/commands.md` | Full command reference with all options |
| `references/snapshot-refs.md` | Ref lifecycle, invalidation rules, troubleshooting |
| `references/session-management.md` | Parallel sessions, state persistence |
| `references/authentication.md` | Login flows, OAuth, 2FA handling |
| `references/video-recording.md` | Recording workflows for debugging |
| `references/proxy-support.md` | Proxy configuration, geo-testing |

## Ready-to-Use Templates

| Template | Description |
|----------|-------------|
| `templates/form-automation.sh` | Form filling with validation |
| `templates/authenticated-session.sh` | Login once, reuse state |
| `templates/capture-workflow.sh` | Content extraction with screenshots |
