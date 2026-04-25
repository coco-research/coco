# /team communicate — Communications Pipeline

> Called by team.md router when action is `communicate`.
> Creates stakeholder communications: emails, announcements, status updates.

## Role Selection Bias

| Layer | Preferred Roles | Count |
|-------|----------------|-------|
| L1 | business-analyst | 1-2 |
| L2 | comms-specialist, marketing-specialist (if launch/announcement) | 2-3 |
| L3 | grammar-editor, standards-reviewer | 2-3 |
| L4 | principal-pm | 1 |

### Communication Type Detection

Parse scope to detect type:
- "launch" / "announcement" / "go-to-market" → marketing-specialist + comms-specialist
- "status" / "update" / "progress" → comms-specialist
- "email" → comms-specialist
- "incident" / "outage" → comms-specialist + sre-devops in L2
- "onboard" / "welcome" → comms-specialist + technical-writer
- Default → comms-specialist lead

## Pipeline Customization

### Layer 1: Audience & Context
L1 agents determine:
- Who are the recipients? (executives, technical team, end users, external)
- What is the key message and call to action?
- What tone is appropriate?
- What context do recipients already have?

### Layer 2: Draft Creation
- **Mode:** `default`
- Comms specialist drafts the communication
- Marketing specialist (if present) adds positioning and impact framing

**Toolkit integration:**
- Check team-toolkit.md for "Stakeholder Communications" entry
- If /pmstudio-comms recommended → use it, then apply quality notes
- Apply feedback: "shorten subject lines", "add TL;DR for long emails"

### Layer 3: Quality Review (Heavy)
- **grammar-editor** → Tone calibration, readability, active voice
- **standards-reviewer** → Format compliance, branding

### Layer 4: Final Review
Principal checks:
- Will this land with the audience?
- Is the CTA clear and actionable?
- Is the tone right for the relationship?
- Should this be sent as-is or does it need human review first?

## GSD Integration

N/A — Communications are project-context-independent.
