---
description: "Read, search, and manage Outlook emails. Auto-detects Legacy Outlook (AppleScript) vs New Outlook (MIME/HxStore extraction). Subcommands: read, unread, search, today, thread, save, summary, reply-draft."
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

# /email — Outlook Email Commands

You manage Outlook email access. Parse the user's argument to determine which subcommand to run.

## Preflight: Detect Outlook variant (REQUIRED — run first)

Outlook for Mac has two incompatible variants. Detect which one is running before doing anything:

```bash
defaults read com.microsoft.Outlook IsRunningNewOutlook 2>/dev/null || echo 0
```

- Output `0` or unset → **Legacy Outlook** → use the AppleScript templates below.
- Output `1` → **New Outlook** → AppleScript is NOT supported (it will silently fail or error). Use **New Outlook (MIME) Mode** below instead. Do NOT attempt AppleScript.

If an AppleScript call errors with "Microsoft Outlook got an error" or the app is unscriptable, treat it as New Outlook and switch to MIME mode rather than retrying.

## CRITICAL: AppleScript Sender Pattern

The `sender` property in Legacy Outlook returns a **record**, not an object. Always access it like this:
```applescript
set s to sender of msg
set sName to name of s
set sAddr to address of s
```
NEVER use `name of sender of msg` directly — it will error.

## Subcommands

- **`read <name>`** — Show latest emails from a specific person
- **`unread`** — Show unread emails (count + top 20)
- **`search <keywords>`** — Search emails by subject/body keywords
- **`today`** — Show all emails received today
- **`this-week`** — Show emails from this week grouped by day
- **`thread <subject>`** — Show full email thread by subject
- **`save <name/subject> to <folder>`** — Save matching emails to a project folder
- **`summary`** — AI summary of today's/unread emails — key decisions, action items
- **`reply-draft <subject>`** — Draft a reply to a specific email
- **`folders`** — List all mail folders with message counts

If no subcommand given, default to `unread`.

---

## AppleScript Templates

### Base: Read messages with sender info
```applescript
tell application "Microsoft Outlook"
    set allMsgs to messages 1 thru {LIMIT} of {FOLDER}
    repeat with msg in allMsgs
        try
            set s to sender of msg
            set sName to name of s
            set sAddr to address of s
            set subj to subject of msg
            set msgDate to time received of msg
            set isRead to is read of msg
            -- filter logic here
        end try
    end repeat
end tell
```

### For reading body content
```applescript
set bodyText to plain text content of msg
```

### For checking recipients (sent items)
```applescript
set recipList to to recipients of msg
repeat with r in recipList
    set recipAddr to address of r
end repeat
```

### Folder references
- Inbox: `inbox` or `mail folder "Inbox" of default account`
- Sent: `mail folder "Sent Items" of default account`
- Archive: `mail folder "Archive" of default account`
- Deleted: `mail folder "Deleted Items" of default account`
- All folders: `mail folders of default account`

---

## Subcommand Details

### `read <name>`
1. Search inbox (first 1000 messages) for sender name/address containing `<name>`
2. Show up to 10 most recent matches as a table: Status | Date | From | Subject
3. Ask if user wants to read the full body of any specific email
4. If user says yes, fetch `plain text content of msg` and display

### `unread`
1. Count unread: iterate messages and count where `is read of msg` is false
2. Show first 20 unread messages as table: Date | From | Subject
3. Group by sender if many from same person
4. Offer to mark as read or read full content

### `search <keywords>`
1. Search inbox (first 2000 messages) — check `subject of msg` for keyword match
2. Also optionally search body (`plain text content`) for deeper matches (warn: slower)
3. Show results as table: Date | From | Subject
4. Limit to 20 results

### `today`
1. Get today's date
2. Iterate inbox messages, stop when `time received of msg` is before today
3. Show all today's emails as table grouped by hour
4. Include read/unread status

### `this-week`
1. Get date 7 days ago
2. Iterate inbox, collect all messages from this week
3. Group by day, show count per day + subjects
4. Limit to 50 most recent

### `thread <subject>`
1. Search inbox + sent items for messages where subject contains `<subject>`
2. Sort by date
3. Show full thread chronologically with sender and body excerpts

### `save <query> to <folder>`
1. Search for emails matching `<query>` (by sender name or subject keyword)
2. For each match, save to the specified project folder as `.txt` files:
   ```
   Subject: ...
   From: ...
   Date: ...
   ============================================================

   [body content]
   ```
3. Report how many saved
4. This triggers the cron's file detection → auto-update pipeline

### `summary`
1. Get today's emails (or unread if specified)
2. Read the body of each
3. Generate an AI summary:
   - Key decisions made
   - Action items for you
   - Meetings scheduled
   - FYIs / newsletters (skip detail)
4. Group by project relevance if possible

### `reply-draft <subject>`
1. Find the email by subject
2. Read its full content
3. Ask user what they want to say in reply
4. Draft a professional reply
5. Show the draft — user can copy/paste into Outlook

### `folders`
1. List all mail folders with message counts
2. Show as table: Folder | Messages | Unread

---

## New Outlook (MIME) Mode

New Outlook stores mail in a proprietary binary index (`HxStore.hxd`) with no AppleScript or local API. There is **no clean full-inbox read** — extract best-effort from the on-disk caches below, in priority order.

**Paths** (under `~/Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/Files/S0/4/`):
- `MimeFiles/` — full RFC822 messages (cleanest, but **often empty** — not every install populates it).
- `Attachments/0/*.eml` — received/forwarded messages saved as clean RFC822 `.eml` (reliable when present).
- `HxStore.hxd` (one level up, in `Main Profile/`) — the real store; binary, no per-message delimiters. `strings` + grep yields sender/subject fragments only (last resort, messy).

**Approach** (covers `read`, `search`, `today`, `this-week`, `thread`, `summary`, `save`):
```bash
P="$HOME/Library/Group Containers/UBF8T346G9.Office/Outlook/Outlook 15 Profiles/Main Profile/Files/S0/4"
# Tiers 1+2: clean RFC822 from MimeFiles + .eml attachments, most-recent first.
# Use find (not a glob) so it is portable across bash/zsh and survives an empty MimeFiles dir.
{ find "$P/MimeFiles" -type f -print0 2>/dev/null; find "$P/Attachments/0" -maxdepth 1 -name '*.eml' -print0 2>/dev/null; } \
  | xargs -0 ls -t 2>/dev/null | head -200 | while IFS= read -r f; do
  subj=$(grep -a -m1 -i '^Subject:' "$f"); [ -z "$subj" ] && continue
  from=$(grep -a -m1 -i '^From:' "$f"); date=$(grep -a -m1 -i '^Date:' "$f")
  printf '%s\t%s\t%s\t%s\n' "$date" "$from" "$subj" "$f"
done
# Tier 3 (only if the above returns nothing): subject/sender awareness from the binary store
#   strings "$P/../../HxStore.hxd" | grep -aiE '^(Subject|From):' | head -50
```
- Filter by sender (`read <name>`), keyword (`search`), or date (`today`/`this-week`). Body/`summary`: parse the matched file. `save <query> to <folder>`: copy the matched file into the target folder.

**Limitations on New Outlook (state honestly — do not guess):**
- This is **partial, not the full inbox**: `MimeFiles/` is frequently empty, and `.eml` attachments only cover received/forwarded messages. For complete access, use Legacy Outlook or the Microsoft Graph API — say so rather than implying full coverage.
- `unread` count / read state, `folders`, mark-as-read, and sending a `reply-draft` need the app API — unavailable. For `reply-draft`, still draft text for copy/paste.
- `HxStore.hxd` is binary; never present its raw `strings` dump as if it were clean email — use it only for awareness.

---

## Performance Notes

- AppleScript iteration is O(n) — searching 7000+ messages is slow
- Default search depth: 500 messages for quick commands, 2000 for `search`
- Always stop early when enough results found (exit repeat)
- For `today` and `this-week`, stop when date is older than target (messages are date-sorted)
- Use `messages 1 thru N` not `every message` to avoid loading entire mailbox

## Error Handling

- If Outlook is not running: `tell application "Microsoft Outlook" to activate` then retry
- If sender access fails: fall back to subject-only display
- If body is empty: try `content of msg` as fallback
- Timeout: 120 seconds per AppleScript call
