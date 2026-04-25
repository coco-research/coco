# User Story Examples & Best Practices

A comprehensive guide to writing effective user stories with real-world examples across different domains.

---

## Table of Contents

1. [User Story Format](#user-story-format)
2. [Anatomy of Good User Stories](#anatomy-of-good-user-stories)
3. [Examples by Domain](#examples-by-domain)
4. [Acceptance Criteria Patterns](#acceptance-criteria-patterns)
5. [Common Mistakes](#common-mistakes)
6. [Story Splitting](#story-splitting)

---

## User Story Format

### Standard Template

```
As a [user type/persona],
I want to [perform action/use feature],
So that [achieve benefit/value].
```

### Alternative Formats

**Job Story (Jobs-to-be-Done):**
```
When [situation],
I want to [motivation],
So I can [expected outcome].
```

**Feature-Driven:**
```
In order to [receive benefit],
As a [user type],
I want [feature/capability].
```

---

## Anatomy of Good User Stories

### INVEST Criteria

Good user stories are:

- **Independent:** Can be developed and delivered separately
- **Negotiable:** Details can be discussed and adjusted
- **Valuable:** Delivers clear value to users or business
- **Estimable:** Can be sized/estimated by the team
- **Small:** Can be completed in one iteration/sprint
- **Testable:** Has clear acceptance criteria

### Key Components

1. **User Type:** Who is the user? Be specific.
2. **Action:** What do they want to do? One clear action.
3. **Value:** Why do they want it? The benefit or outcome.
4. **Acceptance Criteria:** How do we know it's done? Testable conditions.

---

## Examples by Domain

### E-Commerce

#### Example 1: Product Search

**User Story:**
```
As a online shopper,
I want to filter products by price range,
So that I can find items within my budget.
```

**Acceptance Criteria:**
- [ ] Given I'm on the product listing page, when I set a minimum and maximum price, then only products within that range are displayed
- [ ] Given I've applied a price filter, when I clear the filter, then all products are shown again
- [ ] Given I set an invalid price range (min > max), when I apply the filter, then I see an error message
- [ ] Price filter persists when I navigate between pages of results
- [ ] Filter displays count of products matching the criteria

**Priority:** Must Have (P0)
**Story Points:** 5

---

#### Example 2: Guest Checkout

**User Story:**
```
As a first-time customer,
I want to checkout without creating an account,
So that I can complete my purchase quickly.
```

**Acceptance Criteria:**
- [ ] Given I have items in cart, when I click checkout, then I see options for "Guest Checkout" and "Sign In"
- [ ] Given I choose guest checkout, when I enter shipping and payment info, then I can complete the order
- [ ] Given I complete a guest checkout, when the order is placed, then I receive a confirmation email
- [ ] After guest checkout, I see an option to create an account with my order information
- [ ] Guest checkout flow takes no more than 3 screens

**Priority:** Must Have (P0)
**Story Points:** 8

---

### SaaS / B2B Platform

#### Example 3: Team Collaboration

**User Story:**
```
As a project manager,
I want to assign tasks to team members,
So that everyone knows their responsibilities.
```

**Acceptance Criteria:**
- [ ] Given I'm viewing a task, when I click "Assign", then I see a list of team members
- [ ] Given I select a team member, when I confirm the assignment, then they receive a notification
- [ ] Given a task is assigned, when I view the task list, then I can see who is assigned to each task
- [ ] Given I'm a team member, when I'm assigned a task, then it appears in my "My Tasks" view
- [ ] I can assign multiple people to a single task
- [ ] I can change or remove task assignments

**Priority:** Must Have (P0)
**Story Points:** 5

---

#### Example 4: Usage Analytics

**User Story:**
```
As a SaaS administrator,
I want to view team usage analytics,
So that I can optimize our subscription plan.
```

**Acceptance Criteria:**
- [ ] Given I have admin permissions, when I navigate to analytics, then I see usage metrics for the last 30 days
- [ ] Dashboard shows: active users, feature usage, API calls, and storage used
- [ ] Given I select a date range, when I apply the filter, then metrics update accordingly
- [ ] I can export analytics data as CSV
- [ ] Metrics update in real-time (max 5-minute delay)

**Priority:** Should Have (P1)
**Story Points:** 8

---

### Mobile App

#### Example 5: Push Notifications

**User Story:**
```
As a mobile app user,
I want to customize which notifications I receive,
So that I only see relevant updates.
```

**Acceptance Criteria:**
- [ ] Given I'm in settings, when I navigate to notifications, then I see toggle switches for each notification type
- [ ] Notification types include: messages, mentions, updates, promotions
- [ ] Given I disable a notification type, when that event occurs, then I don't receive a push notification
- [ ] Settings sync across devices using the same account
- [ ] Default settings are: messages ON, mentions ON, updates ON, promotions OFF

**Priority:** Must Have (P0)
**Story Points:** 5

---

#### Example 6: Offline Mode

**User Story:**
```
As a mobile user with unreliable connectivity,
I want to access my recently viewed content offline,
So that I can continue using the app without internet.
```

**Acceptance Criteria:**
- [ ] Given I've viewed content while online, when I go offline, then I can still access the last 50 items viewed
- [ ] Given I'm offline, when I try to access new content, then I see a "No connection" message with cached content
- [ ] Given I'm offline and make changes, when I reconnect, then changes sync automatically
- [ ] Offline indicator appears in the app when connectivity is lost
- [ ] Cached content is automatically cleared after 7 days

**Priority:** Should Have (P1)
**Story Points:** 13

---

### Authentication & Security

#### Example 7: Two-Factor Authentication

**User Story:**
```
As a security-conscious user,
I want to enable two-factor authentication,
So that my account is protected from unauthorized access.
```

**Acceptance Criteria:**
- [ ] Given I'm in security settings, when I enable 2FA, then I can choose between SMS and authenticator app
- [ ] Given I choose authenticator app, when I scan the QR code, then I must enter a verification code to activate
- [ ] Given 2FA is enabled, when I log in, then I'm prompted for my second factor
- [ ] I receive backup codes when activating 2FA
- [ ] I can disable 2FA with my current password + 2FA code

**Priority:** Must Have (P0)
**Story Points:** 13

---

#### Example 8: Password Reset

**User Story:**
```
As a user who forgot my password,
I want to reset it via email,
So that I can regain access to my account.
```

**Acceptance Criteria:**
- [ ] Given I click "Forgot Password", when I enter my email, then I receive a reset link within 5 minutes
- [ ] Reset link expires after 24 hours
- [ ] Given I click the reset link, when I enter a new password, then it must meet password requirements (shown on screen)
- [ ] After successful reset, I'm logged in automatically
- [ ] If email doesn't exist in system, show generic message (don't reveal if account exists)

**Priority:** Must Have (P0)
**Story Points:** 5

---

### Content & Media

#### Example 9: Video Upload

**User Story:**
```
As a content creator,
I want to upload videos with progress tracking,
So that I know when my upload is complete.
```

**Acceptance Criteria:**
- [ ] Given I select a video file, when I click upload, then I see a progress bar showing percentage complete
- [ ] Supported formats: MP4, MOV, AVI (max 2GB)
- [ ] Given upload is in progress, when I navigate away, then upload continues in background
- [ ] Given upload completes, when processing is done, then I receive a notification
- [ ] Given upload fails, when error occurs, then I see specific error message and can retry

**Priority:** Must Have (P0)
**Story Points:** 8

---

### Admin & Configuration

#### Example 10: User Permissions

**User Story:**
```
As an administrator,
I want to assign role-based permissions to users,
So that team members have appropriate access levels.
```

**Acceptance Criteria:**
- [ ] Given I'm viewing a user profile, when I click "Change Role", then I see available roles: Admin, Editor, Viewer
- [ ] Given I assign a role, when I save, then user immediately gains/loses associated permissions
- [ ] Admin: full access; Editor: create/edit content; Viewer: read-only
- [ ] I can create custom roles with specific permission combinations
- [ ] Audit log records all permission changes with timestamp and admin who made the change

**Priority:** Must Have (P0)
**Story Points:** 13

---

## Acceptance Criteria Patterns

### Given-When-Then Format

Most structured format, excellent for complex logic:

```
Given [initial context/state],
When [action/event],
Then [expected outcome].
```

**Example:**
```
Given I'm a logged-in user with items in my cart,
When I apply a 20% discount code,
Then the cart total is reduced by 20% and displays the discount.
```

### Checklist Format

Simpler, good for straightforward requirements:

```
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Edge case handling
```

### Table Format

Great for multiple scenarios:

| Condition | Action | Expected Result |
|-----------|--------|----------------|
| Valid email | Click "Send" | Confirmation message |
| Invalid email | Click "Send" | Error message |
| Empty field | Click "Send" | "Required field" error |

---

## Common Mistakes to Avoid

### ❌ Too Technical

**Bad:**
```
As a user,
I want the system to use Redis caching with 10-minute TTL,
So that page loads are fast.
```

**Good:**
```
As a user,
I want pages to load in under 2 seconds,
So that I can browse efficiently.
```

**Why:** User stories focus on user value, not implementation. Let engineers choose the solution.

---

### ❌ Too Vague

**Bad:**
```
As a user,
I want the app to be fast,
So that I have a good experience.
```

**Good:**
```
As a user,
I want search results to appear in under 1 second,
So that I can quickly find what I need.
```

**Why:** "Fast" is subjective. Be specific and measurable.

---

### ❌ Missing the "Why"

**Bad:**
```
As a user,
I want to upload profile pictures.
```

**Good:**
```
As a user,
I want to upload a profile picture,
So that other users can recognize me in the community.
```

**Why:** Understanding the "why" helps the team make better decisions.

---

### ❌ Multiple Actions in One Story

**Bad:**
```
As a user,
I want to create an account, set up my profile, and invite team members,
So that I can start using the platform.
```

**Good:** Split into three stories:
```
Story 1: As a user, I want to create an account...
Story 2: As a user, I want to set up my profile...
Story 3: As an account owner, I want to invite team members...
```

**Why:** Stories should be small and focused on one capability.

---

### ❌ No Acceptance Criteria

**Bad:**
```
As a user,
I want to search for products,
So that I can find what I need.
```

**Good:** Add specific criteria:
```
Acceptance Criteria:
- [ ] Search works on product name and description
- [ ] Results display in under 2 seconds
- [ ] Displays "No results found" when no matches
- [ ] Shows top 20 results with pagination
```

**Why:** Acceptance criteria define "done" and enable testing.

---

## Story Splitting Techniques

When a story is too large, use these techniques to split it:

### 1. By Workflow Steps

**Large Story:**
```
As a user, I want to book a flight online.
```

**Split Stories:**
- Search for flights
- Select flight
- Enter passenger details
- Choose seat
- Make payment
- Receive confirmation

---

### 2. By User Persona

**Large Story:**
```
As a user, I want to manage my subscriptions.
```

**Split Stories:**
- As a free user, I want to view available plans
- As a paid user, I want to upgrade my plan
- As an admin, I want to manage team subscriptions

---

### 3. By Business Rules

**Large Story:**
```
As a user, I want to apply discount codes.
```

**Split Stories:**
- Apply percentage discount (e.g., 20% off)
- Apply fixed amount discount (e.g., $10 off)
- Apply free shipping discount
- Handle expired discount codes
- Limit one discount per order

---

### 4. By Data Variations

**Large Story:**
```
As a user, I want to import contacts.
```

**Split Stories:**
- Import from CSV file
- Import from Google Contacts
- Import from Microsoft Outlook
- Import from LinkedIn

---

### 5. By CRUD Operations

**Large Story:**
```
As a user, I want to manage my projects.
```

**Split Stories:**
- Create a new project
- View project details
- Update project settings
- Delete a project

---

### 6. By Happy Path / Edge Cases

**MVP Story (Happy Path):**
```
As a user, I want to upload a profile photo (JPG, < 5MB).
```

**Follow-up Stories:**
- Support additional formats (PNG, GIF)
- Handle files larger than 5MB with error message
- Auto-crop/resize images
- Allow photo deletion

---

## Story Sizing Guidelines

### Story Points Reference

**1-2 Points (Few hours):**
- Simple UI change
- Copy update
- Minor configuration

**3-5 Points (1-2 days):**
- New form with validation
- Simple API endpoint
- Basic feature toggle

**8 Points (3-5 days):**
- Complex form with business logic
- Integration with third-party service
- New database schema with migration

**13+ Points (1+ weeks):**
- Too large! Split the story
- Consider as an Epic

---

## Templates for Common Scenarios

### Registration/Sign-Up

```
As a new visitor,
I want to create an account with my email,
So that I can access personalized features.

Acceptance Criteria:
- [ ] Email and password required (password: min 8 chars, 1 number, 1 special char)
- [ ] Email validation and duplicate check
- [ ] Confirmation email sent upon registration
- [ ] Automatically logged in after email confirmation
- [ ] Option to sign up with Google/Apple (social auth)
```

### Data Export

```
As a user,
I want to export my data as CSV,
So that I can analyze it in Excel.

Acceptance Criteria:
- [ ] Export button in settings
- [ ] Includes all user data (specify fields)
- [ ] File downloads immediately (or email if > 10MB)
- [ ] Filename format: "export_[username]_[date].csv"
- [ ] Respects data privacy regulations (only user's own data)
```

### Error Handling

```
As a user,
I want to see helpful error messages,
So that I know how to fix issues.

Acceptance Criteria:
- [ ] Error messages are specific (not generic "Error occurred")
- [ ] Suggest actionable next steps
- [ ] Display in user's language
- [ ] Don't expose technical details (stack traces)
- [ ] Log errors for debugging (backend)
```

---

## Best Practices Summary

1. **Write from user perspective**, not system perspective
2. **Focus on value/benefit**, not just functionality
3. **Keep stories small** (completable in one sprint)
4. **Make acceptance criteria testable**
5. **Use consistent format** across your team
6. **Include edge cases** in acceptance criteria
7. **Collaborate** with engineers and designers when writing
8. **Refine regularly** based on new learnings
9. **Link to mockups/designs** when relevant
10. **Prioritize ruthlessly** (must/should/nice-to-have)

---

## Additional Resources

### User Story Template

```
Title: [Concise feature name]

As a [specific user type],
I want to [action/capability],
So that [benefit/value].

Acceptance Criteria:
- [ ] [Testable criterion 1]
- [ ] [Testable criterion 2]
- [ ] [Edge case handling]

Priority: [Must Have / Should Have / Nice to Have]
Story Points: [1/2/3/5/8/13]
Dependencies: [List if any]
Design: [Link to mockups]
Notes: [Additional context]
```

### Epic vs Story vs Task

**Epic:** Large body of work (multiple sprints)
- Example: "User Authentication System"

**Story:** Deliverable value (one sprint)
- Example: "As a user, I want to reset my password..."

**Task:** Implementation step (hours/days)
- Example: "Create password reset API endpoint"

---

## Conclusion

Effective user stories:
- Start with the user's perspective
- Clearly articulate value
- Include testable acceptance criteria
- Are sized appropriately
- Enable team collaboration

Use these examples as templates, but adapt them to your product and users' specific needs!
