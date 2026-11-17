<purpose>
Triage and review all open GitHub issues and PRs against project contribution templates.
Produces a structured report showing compliance status for each item, flags missing
required fields, identifies label gaps, and optionally takes action (label, comment, close).
</purpose>

<required_reading>
Before starting, read these project files to understand the review criteria:
- `.github/ISSUE_TEMPLATE/feature_request.yml` — required fields for feature issues
- `.github/ISSUE_TEMPLATE/enhancement.yml` — required fields for enhancement issues
- `.github/ISSUE_TEMPLATE/chore.yml` — required fields for chore issues
- `.github/ISSUE_TEMPLATE/bug_report.yml` — required fields for bug reports
- `.github/PULL_REQUEST_TEMPLATE/feature.md` — required checklist for feature PRs
- `.github/PULL_REQUEST_TEMPLATE/enhancement.md` — required checklist for enhancement PRs
- `.github/PULL_REQUEST_TEMPLATE/fix.md` — required checklist for fix PRs
- `CONTRIBUTING.md` — the issue-first rule and approval gates
</required_reading>

<process>

<step name="preflight">
Verify prerequisites:

1. **`gh` CLI available and authenticated?**
   ```bash
   which gh && gh auth status 2>&1
   ```
   If not available: print setup instructions and exit.

2. **Detect repository:**
   If `--repo` flag provided, use that. Otherwise:
   ```bash
   gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null
   ```
   If no repo detected: error — must be in a git repo with a GitHub remote.

3. **Parse flags:**
   - `--issues` → set REVIEW_ISSUES=true, REVIEW_PRS=false
   - `--prs` → set REVIEW_ISSUES=false, REVIEW_PRS=true
   - `--label` → set AUTO_LABEL=true
   - `--close-incomplete` → set AUTO_CLOSE=true
   - Default (no flags): review both issues and PRs, report only (no auto-actions)
</step>

<step name="fetch_issues">
Skip if REVIEW_ISSUES=false.

Fetch all open issues:
```bash
gh issue list --state open --json number,title,labels,body,author,createdAt,updatedAt --limit 100
```

For each issue, classify by labels and body content:

| Label/Pattern | Type | Template |
|---|---|---|
| `feature-request` | Feature | feature_request.yml |
| `enhancement` | Enhancement | enhancement.yml |
| `bug` | Bug | bug_report.yml |
| `type: chore` | Chore | chore.yml |
| No matching label | Unknown | Flag for manual triage |

If an issue has no type label, attempt to classify from the body content:
- Contains "### Feature name" → likely Feature
- Contains "### What existing feature" → likely Enhancement
- Contains "### What happened?" → likely Bug
- Contains "### What is the maintenance task?" → likely Chore
- Cannot determine → mark as `needs-triage`
</step>

<step name="review_issues">
Skip if REVIEW_ISSUES=false.

For each classified issue, review against its template requirements.

**Feature Request Review Checklist:**
- [ ] Pre-submission checklist present (4 checkboxes)
- [ ] Feature name provided
- [ ] Type of addition selected
- [ ] Problem statement filled (not placeholder text)
- [ ] What is being added described with examples
- [ ] Full scope of changes listed (files created/modified/systems)
- [ ] User stories present (minimum 2)
- [ ] Acceptance criteria present (testable conditions)
- [ ] Applicable runtimes selected
- [ ] Breaking changes assessment present
- [ ] Maintenance burden described
- [ ] Alternatives considered (not empty)
- **Label check:** Has `needs-review` label? Has `approved-feature` label?
- **Gate check:** If PR exists linking this issue, does issue have `approved-feature`?

**Enhancement Review Checklist:**
- [ ] Pre-submission checklist present (4 checkboxes)
- [ ] What is being improved identified
- [ ] Current behavior described with examples
- [ ] Proposed behavior described with examples
- [ ] Reason and benefit articulated (not vague)
- [ ] Scope of changes listed
- [ ] Breaking changes assessed
- [ ] Alternatives considered
- [ ] Area affected selected
- **Label check:** Has `needs-review` label? Has `approved-enhancement` label?
- **Gate check:** If PR exists linking this issue, does issue have `approved-enhancement`?

**Bug Report Review Checklist:**
- [ ] GSD Version provided
- [ ] Runtime selected
- [ ] OS selected
- [ ] Node.js version provided
- [ ] Description of what happened
- [ ] Expected behavior described
- [ ] Steps to reproduce provided
- [ ] Frequency selected
- [ ] Severity/impact selected
- [ ] PII checklist confirmed
- **Label check:** Has `needs-triage` or `confirmed-bug` label?

**Chore Review Checklist:**
- [ ] Pre-submission checklist confirmed (no user-facing changes)
- [ ] Maintenance task described
- [ ] Type of maintenance selected
- [ ] Current state described with specifics
- [ ] Proposed work listed
- [ ] Acceptance criteria present
- [ ] Area affected selected
- **Label check:** Has `needs-triage` label?

**Scoring:** For each issue, calculate a completeness percentage:
- Count required fields present vs. total required fields
- Score = (present / total) * 100
- Status: COMPLETE (100%), MOSTLY COMPLETE (75-99%), INCOMPLETE (50-74%), REJECT (<50%)
</step>

<step name="fetch_prs">
Skip if REVIEW_PRS=false.

Fetch all open PRs:
```bash
gh pr list --state open --json number,title,labels,body,author,headRefName,baseRefName,isDraft,createdAt,reviewDecision,statusCheckRollup --limit 100
```

For each PR, classify by body content and linked issue:

| Body Pattern | Type | Template |
|---|---|---|
| Contains "## Feature PR" or "## Feature summary" | Feature PR | feature.md |
| Contains "## Enhancement PR" or "## What this enhancement improves" | Enhancement PR | enhancement.md |
| Contains "## Fix PR" or "## What was broken" | Fix PR | fix.md |
| Uses default template | Wrong Template | Flag — must use typed template |
| Cannot determine | Unknown | Flag for manual review |

Also check for linked issues:
```bash
gh pr view {number} --json body -q '.body' | grep -oE '(Closes|Fixes|Resolves) #[0-9]+'
```
</step>

<step name="review_prs">
Skip if REVIEW_PRS=false.

For each classified PR, review against its template requirements.

**Feature PR Review Checklist:**
- [ ] Uses feature PR template (not default)
- [ ] Issue linked with `Closes #NNN`
- [ ] Linked issue exists and has `approved-feature` label
- [ ] Feature summary present
- [ ] New files table filled
- [ ] Modified files table filled
- [ ] Implementation notes present
- [ ] Spec compliance checklist present (acceptance criteria from issue)
- [ ] Test coverage described
- [ ] Platforms tested checked (macOS, Windows, Linux)
- [ ] Runtimes tested checked
- [ ] Scope confirmation checked
- [ ] Full checklist completed
- [ ] Breaking changes section filled
- **CI check:** All status checks passing?
- **Review check:** Has review approval?

**Enhancement PR Review Checklist:**
- [ ] Uses enhancement PR template (not default)
- [ ] Issue linked with `Closes #NNN`
- [ ] Linked issue exists and has `approved-enhancement` label
- [ ] What is improved described
- [ ] Before/after provided
- [ ] Implementation approach described
- [ ] Verification method described
- [ ] Platforms tested checked
- [ ] Runtimes tested checked
- [ ] Scope confirmation checked
- [ ] Full checklist completed
- [ ] Breaking changes section filled
- **CI check:** All status checks passing?
