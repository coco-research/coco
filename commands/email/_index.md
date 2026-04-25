---
description: "Read, search, and manage Outlook emails via AppleScript. Subcommands: read, unread, search, today, thread, save, summary, reply-draft. Requires Legacy Outlook for Mac."
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

You manage Outlook email access via AppleScript (Legacy Outlook for Mac). Parse the user's argument to determine which subcommand to run.

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
