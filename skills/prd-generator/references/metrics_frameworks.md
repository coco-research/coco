# Product Metrics Frameworks

A comprehensive guide to choosing and implementing product metrics frameworks for measuring success.

---

## Table of Contents

1. [Overview](#overview)
2. [AARRR (Pirate Metrics)](#aarrr-pirate-metrics)
3. [HEART Framework](#heart-framework)
4. [North Star Metric](#north-star-metric)
5. [OKRs (Objectives & Key Results)](#okrs-objectives--key-results)
6. [Product-Market Fit Metrics](#product-market-fit-metrics)
7. [Engagement Metrics](#engagement-metrics)
8. [Choosing the Right Framework](#choosing-the-right-framework)

---

## Overview

### Why Metrics Matter

**Metrics help you:**
- Measure feature success objectively
- Make data-driven decisions
- Align teams around shared goals
- Identify what's working and what's not
- Communicate impact to stakeholders

### Types of Metrics

**Leading Indicators:** Predict future outcomes
- Example: Free trial sign-ups → Future revenue

**Lagging Indicators:** Measure past results
- Example: Monthly revenue, churn rate

**Actionable vs. Vanity Metrics**
- **Actionable:** Can influence through product changes (e.g., conversion rate)
- **Vanity:** Looks good but doesn't drive decisions (e.g., total registered users)

---

## AARRR (Pirate Metrics)

Created by Dave McClure, this framework focuses on the customer lifecycle.

### The Five Stages

```
Acquisition → Activation → Retention → Revenue → Referral
```

### 1. Acquisition

**What:** How do users find you?

**Key Metrics:**
- Website traffic
- App store impressions
- Click-through rate (CTR) from ads
- Cost per acquisition (CPA)
- Traffic sources (organic, paid, referral)

**Example Targets:**
- 10,000 monthly website visitors
- CAC < $50
- 5% CTR on paid ads

**Questions to Answer:**
- Which channels drive the most users?
- What's our cost per channel?
- Which campaigns convert best?

---

### 2. Activation

**What:** Do users have a great first experience?

**Key Metrics:**
- Sign-up completion rate
- Time to "aha moment"
- Percentage reaching key milestone
- Onboarding completion rate
- Feature adoption in first session

**Example Targets:**
- 60% sign-up completion
- 40% reach "aha moment" in first session
- 80% complete onboarding

**Questions to Answer:**
- What does a great first experience look like?
- Where do users drop off in onboarding?
- How quickly do users find value?

**Example "Aha Moments":**
- **Slack:** Send your first message
- **Dropbox:** Upload your first file
- **Airbnb:** Complete your first booking

---

### 3. Retention

**What:** Do users come back?

**Key Metrics:**
- Daily/Weekly/Monthly Active Users (DAU/WAU/MAU)
- Retention curves (Day 1, Day 7, Day 30)
- Churn rate
- Session frequency
- Feature usage over time

**Example Targets:**
- 40% Day 7 retention
- 25% Day 30 retention
- < 5% monthly churn

**Cohort Analysis:**
```
| Cohort    | Week 1 | Week 2 | Week 3 | Week 4 |
|-----------|--------|--------|--------|--------|
| Jan 2024  | 100%   | 45%    | 30%    | 25%    |
| Feb 2024  | 100%   | 50%    | 35%    | 28%    |
```

**Questions to Answer:**
- What makes users come back?
- When do users churn?
- How can we re-engage inactive users?

---

### 4. Revenue

**What:** How do you monetize?

**Key Metrics:**
- Monthly Recurring Revenue (MRR)
- Average Revenue Per User (ARPU)
- Customer Lifetime Value (LTV)
- Conversion to paid rate
- Upsell/cross-sell rate

**Example Targets:**
- 5% free-to-paid conversion
- $50 ARPU
- LTV:CAC ratio > 3:1

**Formulas:**
```
LTV = ARPU × Average Customer Lifespan
LTV:CAC = Lifetime Value ÷ Customer Acquisition Cost
Churn Rate = Customers Lost ÷ Total Customers × 100
```

**Questions to Answer:**
- Which features drive conversions?
- What's our payback period?
- How can we increase ARPU?

---

### 5. Referral

**What:** Do users tell others?

**Key Metrics:**
- Viral coefficient (K-factor)
- Net Promoter Score (NPS)
- Referral rate
- Social shares
- Word-of-mouth attribution

**Example Targets:**
- 15% of users refer others
- NPS > 50
- K-factor > 1 (viral growth)

**Formulas:**
```
K-factor = (Number of Invites per User) × (Conversion Rate of Invites)
NPS = % Promoters - % Detractors
```

**Questions to Answer:**
- Why do users refer others?
- How can we incentivize referrals?
- What makes us shareable?

---

### AARRR Example: SaaS Product

| Stage | Metric | Current | Target | Actions |
|-------|--------|---------|--------|---------|
| Acquisition | Monthly visitors | 50,000 | 75,000 | SEO, content marketing |
| Activation | Trial sign-ups | 5% | 8% | Improve landing page |
| Retention | Day 30 retention | 20% | 30% | Onboarding improvements |
| Revenue | Free-to-paid conversion | 3% | 5% | Pricing page redesign |
| Referral | Users who refer | 8% | 15% | Referral program launch |

---

## HEART Framework

Created by Google, focuses on user experience quality.

### The Five Dimensions

**HEART = Happiness + Engagement + Adoption + Retention + Task Success**

---

### 1. Happiness

**What:** User satisfaction and perception

**Metrics:**
- Net Promoter Score (NPS)
- Customer Satisfaction (CSAT)
- User ratings/reviews
- Support ticket sentiment
- User feedback scores

**Measurement Methods:**
- Surveys (post-interaction, periodic)
- App store ratings
- In-app feedback forms
- Social media sentiment

**Example:**
```
Feature: New checkout flow
Happiness Metric: CSAT score
Target: > 4.5/5 average rating
Measurement: Post-purchase survey
```

---

### 2. Engagement

**What:** Level of user involvement

**Metrics:**
- Session duration
- Pages/screens per session
- Feature usage frequency
- Time spent in app
- Actions per session

**Example:**
```
Feature: News feed
Engagement Metric: Daily sessions per user
Current: 1.2 sessions/day
Target: 2.0 sessions/day
```

---

### 3. Adoption

**What:** New users or feature uptake

**Metrics:**
- New user sign-ups
- Feature adoption rate
- Time to first use
- Percentage of users trying new feature

**Example:**
```
Feature: Dark mode
Adoption Metric: % of users enabling dark mode
Target: 40% within 30 days of launch
```

---

### 4. Retention

**What:** Users returning over time

**Metrics:**
- DAU/WAU/MAU
- Retention curves
- Churn rate
- Repeat usage rate

**Example:**
```
Feature: Collaboration tools
Retention Metric: Week-over-week active teams
Target: 70% of teams active weekly
```

---

### 5. Task Success

**What:** Can users accomplish their goals?

**Metrics:**
- Task completion rate
- Error rate
- Time to complete task
- Search success rate

**Example:**
```
Feature: File upload
Task Success Metric: Upload completion rate
Current: 85%
Target: 95%
Error analysis: Large file timeouts
```

---

### HEART Framework Template

| Dimension | Goals | Signals | Metrics |
|-----------|-------|---------|---------|
| **Happiness** | Users love the feature | Positive feedback | NPS > 40 |
| **Engagement** | Users interact frequently | Daily active usage | 60% DAU/MAU |
| **Adoption** | Most users try it | Feature activation | 70% adoption |
| **Retention** | Users keep coming back | Weekly return rate | 50% W1 retention |
| **Task Success** | Users complete goals | Low error rate | 95% success rate |

---

## North Star Metric

A single metric that best captures the core value you deliver to customers.

### Characteristics of a Good North Star Metric

1. **Reflects value delivery** to customers
2. **Measures progress** toward your vision
3. **Actionable** by the team
4. **Leading indicator** of revenue
5. **Understandable** by everyone

---

### Examples by Company

| Company | North Star Metric | Why |
|---------|------------------|-----|
| **Airbnb** | Nights booked | Core value: successful stays |
| **Spotify** | Time spent listening | Core value: music enjoyment |
| **Slack** | Messages sent by teams | Core value: communication |
| **Facebook** | Daily Active Users | Core value: social connection |
| **Netflix** | Hours watched | Core value: entertainment |
| **Uber** | Rides completed | Core value: transportation |
| **Medium** | Total time reading | Core value: quality content |

---

### Finding Your North Star Metric

**Step 1: Define your value proposition**
- What core value do you deliver?
- What's the "aha moment" for users?

**Step 2: Identify the metric**
- What measurement best captures that value?
- Is it a leading indicator of business success?

**Step 3: Validate the metric**
- Does it correlate with revenue?
- Can teams influence it?
- Is it understandable?

**Step 4: Set targets and track**
- What's the current baseline?
- What's the target growth rate?
- How will you measure progress?

---

### North Star Metric Tree

Break down your North Star into contributing metrics:

```
North Star: Weekly Active Users
    ├── New User Acquisition
    │   ├── Sign-ups
    │   └── Onboarding completion
    ├── Activation
    │   └── Users reaching "aha moment"
    └── Retention
        ├── Week 1 retention
        └── Week 4 retention
```

---

## OKRs (Objectives & Key Results)

Goal-setting framework popularized by Google.

### Structure

**Objective:** Qualitative, inspirational goal
**Key Results:** Quantitative, measurable outcomes (3-5 per objective)

---

### Writing Good OKRs

**Objective Characteristics:**
- Inspirational and motivating
- Qualitative
- Time-bound (quarterly or annual)
- Aligned with company strategy

**Key Result Characteristics:**
- Quantitative and measurable
- Specific with clear targets
- Ambitious but achievable
- 3-5 per objective

---

### Examples

#### Example 1: Growth OKR

**Objective:** Become the go-to platform for small business invoicing

**Key Results:**
1. Increase monthly active businesses from 10,000 to 25,000
2. Achieve 40% month-over-month retention
3. Reach NPS of 50+
4. Generate $500K MRR

---

#### Example 2: Product Quality OKR

**Objective:** Deliver a world-class mobile experience

**Key Results:**
1. Reduce app crash rate from 2.5% to <0.5%
2. Achieve 4.5+ star rating on both app stores
3. Improve app load time to <2 seconds (p95)
4. Increase mobile DAU/MAU ratio from 30% to 45%

---

#### Example 3: Feature Launch OKR

**Objective:** Successfully launch team collaboration features

**Key Results:**
1. 60% of active users try collaboration features within 30 days
2. 25% of users become weekly active collaborators
3. Collaboration features drive 15% increase in paid conversions
4. Achieve CSAT score of 4.2/5 for collaboration features

---

### OKR Template for PRDs

```markdown
## OKRs

### Objective: [Inspirational goal]

**Key Results:**
1. [Metric 1]: Increase/decrease [current] to [target] by [date]
2. [Metric 2]: Achieve [target value] for [metric]
3. [Metric 3]: [Specific measurable outcome]

**Tracking:**
- Current status: [Progress report]
- Dashboard: [Link to metrics dashboard]
- Review cadence: [Weekly/bi-weekly]
```

---

## Product-Market Fit Metrics

Measuring whether you've achieved product-market fit.

### Sean Ellis Test

Survey question: **"How would you feel if you could no longer use [product]?"**

- Very disappointed
- Somewhat disappointed
- Not disappointed

**PMF Threshold:** 40%+ answer "Very disappointed"

---

### Other PMF Indicators

**Qualitative Signals:**
- Users voluntarily refer others
- Organic growth without marketing
- High engagement and retention
- Users find creative use cases
- Positive unsolicited feedback

**Quantitative Metrics:**
- **Retention:** 40%+ month 1 retention
- **NPS:** Score > 50
- **Growth:** 10%+ month-over-month organic growth
- **Engagement:** High DAU/MAU ratio (>40%)
- **LTV:CAC:** Ratio > 3:1

---

## Engagement Metrics

Deep dive into measuring user engagement.

### DAU/WAU/MAU

**Definitions:**
- **DAU:** Daily Active Users (unique users in a day)
- **WAU:** Weekly Active Users (unique users in a week)
- **MAU:** Monthly Active Users (unique users in a month)

**Ratios:**
- **DAU/MAU:** Stickiness (how many monthly users come daily)
- **DAU/WAU:** Daily engagement intensity

**Benchmarks:**
- **Excellent:** DAU/MAU > 50% (e.g., messaging apps)
- **Good:** DAU/MAU = 20-50% (e.g., social media)
- **Average:** DAU/MAU = 10-20% (e.g., utilities)

---

### Session Metrics

**Key Measurements:**
- **Session duration:** Time spent per session
- **Session frequency:** Sessions per user per day/week
- **Session depth:** Actions/pages per session

**Example Targets:**
- Session duration: > 5 minutes
- Session frequency: 2+ sessions/day
- Session depth: > 8 page views

---

### Feature Engagement

**Metrics:**
- **Adoption rate:** % of users who try the feature
- **Active usage:** % of users actively using regularly
- **Depth of use:** Actions per user within feature

**Example:**
```
Feature: Document collaboration
- Adoption: 50% of users have collaborated at least once
- Active usage: 30% collaborate weekly
- Depth: Average 12 collaborative edits per week
```

---

## Choosing the Right Framework

### Decision Matrix

| Framework | Best For | Time Horizon | Complexity |
|-----------|----------|--------------|------------|
| **AARRR** | Growth-focused products, startups | Ongoing | Medium |
| **HEART** | UX quality, feature launches | Per feature | Low-Medium |
| **North Star** | Company alignment, focus | Ongoing | Low |
| **OKRs** | Goal setting, team alignment | Quarterly | Medium-High |

---

### By Product Stage

**Early Stage (Pre-PMF):**
- Focus: Product-Market Fit metrics
- Framework: AARRR (Activation & Retention focus)
- North Star: Early engagement metric

**Growth Stage (Post-PMF):**
- Focus: Scaling user acquisition
- Framework: Full AARRR funnel
- North Star: Growth-oriented metric

**Mature Stage:**
- Focus: Optimization and expansion
- Framework: HEART for features, OKRs for goals
- North Star: Revenue or engagement metric

---

### By Product Type

**Consumer Apps:**
- AARRR for growth funnel
- DAU/MAU for engagement
- Viral coefficient for referral

**B2B SaaS:**
- ARR/MRR for revenue
- Churn rate for retention
- Expansion revenue for growth

**Marketplace:**
- GMV (Gross Merchandise Value)
- Take rate (% of transaction)
- Liquidity (supply/demand balance)

**Content Platforms:**
- Time spent on platform
- Content creation rate
- Content consumption rate

---

## Metrics Anti-Patterns

### Common Mistakes

**1. Too Many Metrics**
- **Problem:** Tracking everything = focusing on nothing
- **Solution:** Choose 3-5 key metrics per initiative

**2. Vanity Metrics**
- **Problem:** Total users looks good but doesn't inform decisions
- **Solution:** Focus on active users, engagement, retention

**3. Lagging Only**
- **Problem:** Only tracking revenue = rear-view mirror
- **Solution:** Balance with leading indicators (activation, engagement)

**4. No Targets**
- **Problem:** Tracking without goals
- **Solution:** Set specific, time-bound targets

**5. Not Segmenting**
- **Problem:** Average metrics hide important patterns
- **Solution:** Segment by user type, cohort, feature usage

---

## Metrics Template for PRDs

```markdown
## Success Metrics

### North Star Metric
**Metric:** [Your single most important metric]
**Current:** [Baseline value]
**Target:** [Goal value by launch + X months]
**Why:** [Why this metric matters]

### Supporting Metrics

#### Acquisition
- **Metric 1:** [Name] - Current: [X], Target: [Y]
- **Metric 2:** [Name] - Current: [X], Target: [Y]

#### Activation
- **Metric 1:** [Name] - Current: [X], Target: [Y]
- **Metric 2:** [Name] - Current: [X], Target: [Y]

#### Retention
- **Metric 1:** [Name] - Current: [X], Target: [Y]
- **Metric 2:** [Name] - Current: [X], Target: [Y]

#### Revenue (if applicable)
- **Metric 1:** [Name] - Current: [X], Target: [Y]

### Counter-Metrics
[Metrics to ensure you're not sacrificing other areas]
- Example: Ensure support tickets don't increase > 10%

### Measurement Plan
- **Dashboard:** [Link]
- **Review Cadence:** [Weekly/bi-weekly]
- **Owner:** [Name]
```

---

## Resources & Tools

### Analytics Platforms
- **Amplitude:** Product analytics, retention analysis
- **Mixpanel:** Event tracking, funnel analysis
- **Google Analytics:** Web analytics
- **Heap:** Auto-capture analytics

### Survey Tools
- **Delighted:** NPS surveys
- **SurveyMonkey:** Custom surveys
- **Typeform:** Engaging survey forms

### Dashboard Tools
- **Tableau:** Data visualization
- **Looker:** Business intelligence
- **Datadog:** Infrastructure metrics
- **Metabase:** Open-source BI

---

## Summary

**Key Takeaways:**

1. **Choose frameworks** that match your product stage and goals
2. **Balance leading and lagging** indicators
3. **Set specific targets** with timelines
4. **Track counter-metrics** to avoid unintended consequences
5. **Review regularly** and iterate on what you measure
6. **Keep it simple** - 3-5 key metrics per initiative
7. **Align metrics** with business objectives
8. **Make metrics actionable** - can the team influence them?

**Remember:** The best metric is one that drives the right behavior and aligns your team around what matters most to users and the business.
