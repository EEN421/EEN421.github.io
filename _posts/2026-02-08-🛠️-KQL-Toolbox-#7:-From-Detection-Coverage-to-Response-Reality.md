![](/assets/img/KQL%20Toolbox/7/KQL7.png)
## Welcome back to KQL Toolbox 👋
So now comes the unavoidable next question: _**Are our detections actually aligned to how attackers operate — and are we getting faster at shutting them down?**_ This is where many SOCs stall out... They collect alerts, map techniques, and celebrate coverage — but never stop to ask whether all that visibility is translating into **better response outcomes.**

<br/>

In this installment of KQL Toolbox, we zoom out just enough to connect the dots:
- MITRE ATT&CK tells us what adversary behaviors are showing up most often
- Mean Time to Resolution (MTTR) tells us whether the SOC can consistently respond fast enough when they do

Together, they form the bridge from detection coverage to operational effectiveness.

Because at the end of the day, the goal isn’t to say “we detect a lot of techniques.” The goal is to say _“when these behaviors occur, we resolve them faster — with confidence and consistency.”_

That’s the shift this post is about:
- from dashboards to discipline,
- from coverage maps to closed incidents,
- and from theoretical security to measurable defense.

Let’s get into it. 😼🥷🛡️

![](/assets/img/KQL%20Toolbox/7/kql7-opening.png)

<br/>

# Query 1 — Most common MITRE tactics observed (Top 10 + pie chart)

```kql
SecurityAlert
| where TimeGenerated > ago(90d)
| where isnotempty(Tactics)
| mv-expand tactic = split(Tactics, ", ")
| summarize Count = count() by tostring(tactic)
| sort by Count desc
| top 10 by Count
| render piechart
```

<br/>

![](/assets/img/KQL%20Toolbox/7/kql7-piechart2.png)

<br/>

## 🤔 Why this is useful to a SOC
- **Quick “threat posture snapshot”:** Are you mostly dealing with Initial Access + Execution, or is Lateral Movement + Persistence dominating?
- **Detection engineering priority:** If a tactic is constantly showing up, it’s either (a) reality, (b) a detection bias, or (c) noise you need to tune.
- **Executive translation:** MITRE tactics are one of the fastest ways to communicate “what’s happening” without drowning in product-specific alerts.

<br/>

## 🕵️ Line-by-line breakdown

### `SecurityAlert`
Pulls alert records (Sentinel incidents/alerts depending on connector + normalization) where many products populate MITRE fields.

<br/>

### `where TimeGenerated > ago(90d)`
A 90-day window is usually long enough to smooth weekly weirdness and short enough to stay relevant.

<br/>

### `where isnotempty(Tactics)`
Ensures you only count alerts that actually have MITRE mapping (also acts like a “coverage check”).

<br/>

### `mv-expand tactic = split(Tactics, ", ")`
If the field is stored as a comma-separated list, this expands each tactic into its own row so you can count cleanly.

<br/>

### `summarize Count = count() by tostring(tactic)`
Counts occurrences per tactic.

<br/>

### `top 10… + render piechart`
Great for dashboards and “what are we fighting?” visuals.

<br/>
<br/>


## 🎚️ Tuning upgrades (high-impact)

### 1.) Normalize whitespace + casing (prevents “Persistence” vs “ Persistence” splitting counts)
```kql
| extend tactic = trim(" ", tostring(tactic))
| extend tactic = tostring(tolower(tactic))
```

<br/>

### 2.) Slice by severity or product (answer “what’s driving this?”)
`| summarize Count=count() by tostring(tactic), AlertSeverity, ProductName`

<br/>

### 3.) Filter out known noisy analytics rules (if one rule dominates your chart)
`| where AlertName !in ("Rule A", "Rule B")`

<br/>

## ⚡ Operationalization playbook
- Weekly SOC review: “Top tactics” becomes a recurring agenda item.
- Detection backlog: If Defense Evasion is high, prioritize telemetry gaps + hardening detections there.
- Hunt pivot: Pick the #1 tactic and run a themed hunting sprint (one week = one tactic).

<br/>

![](/assets/img/KQL%20Toolbox/7/kql7-piechart.png)

<br/><br/>

# Query 2 — Most common MITRE techniques observed (Top 10)

```kql
SecurityAlert
| where TimeGenerated > ago(90d)
| where isnotempty(Techniques)
| mv-expand technique = split(Techniques, ", ")
| summarize Count = count() by tostring(technique)
| sort by Count desc
| top 10 by Count
| project ["MITRE Technique"] = technique, Count
```

<br/>

![](/assets/img/KQL%20Toolbox/7/kql7-techniques.png)

<br/>

## 🤔 Why this is useful to a SOC
- Tactics tell you the phase of the attack. Techniques tell you the exact behavior (and often the exact telemetry you should be collecting).
- This query helps you:
- Measure real-world technique frequency (what’s actually firing)
- Spot coverage gaps (if tactics show up but technique mapping is sparse)
- Prioritize enrichment (technique-heavy detections should have playbooks + automation)

<br/>

## 🕵️ Line-by-line breakdown

Same pattern as tactics, but at the technique level: `where isnotempty(Techniques)`
Useful as a coverage signal: if this returns very few results, you’re either missing mappings or your alert sources aren’t enriching.

<br/>

### `mv-expand … split(Techniques, ", ")`
Splits and expands technique list into rows

<br/>

### `summarize Count`
Counts each technique occurrence

<br/>

### `project`
Renames the column for clean dashboards/exports.

<br/>

## 🎚️ Tuning upgrades (especially important here)

### 1.) Trim and standardize technique strings
`| extend technique = trim(" ", tostring(technique))`

<br/>

### 2.) Break out Technique IDs vs Names
If your environment stores T1059 style IDs mixed with names, standardize them (or extract IDs if present) so counts don’t fragment.

<br/>

### 3) Add a **“who/where”** pivot
Techniques are most valuable when you can immediately ask: which hosts, which users, which rule?

```kql
| summarize Count=count() by tostring(technique), AlertName, CompromisedEntity
| sort by Count desc
```

<br/>

## ⚡ Operationalization playbook
Technique “Top 10” becomes your playbook roadmap: ensure top techniques have:
- enrichment (entity mapping),
- triage checklist,
- automation/containment actions,
- and detection tuning ownership.

Purple-team alignment: pick one technique and run an emulation test; validate alerts and measure time-to-close.

<br/>

![](/assets/img/KQL%20Toolbox/7/kql7-top10MITRE.png)

<br/><br/>

# Query 3 — Median Time to Resolve (MTTR) by severity (Closed incidents)

```kql
// Get total MTTR
let TotalMTTRTable = 
    SecurityIncident
    | where TimeGenerated > ago(90d)
    | where Status == "Closed"
    | summarize TotalMTTR = round(avg(datetime_diff('minute', ClosedTime, CreatedTime)), 2)
    | extend Key = 1;  // Adding a key for joining
// Calculate MTTR per severity
let SeverityMTTR = 
    SecurityIncident
    | where TimeGenerated > ago(90d)
    | where Status == "Closed"
    | summarize MedianTTR = percentile(datetime_diff('minute', ClosedTime, CreatedTime), 50) by Severity
    | extend Key = 1;  // Adding a key for joining
// Join both results to calculate percentage
SeverityMTTR
| join kind=inner (TotalMTTRTable) on Key
| extend PercentageOfTotal = strcat(iff(TotalMTTR > 0, round((MedianTTR * 100.0) / TotalMTTR, 2), 0.0), '%')  // Ensure consistent data type
| extend MTTR_Severity = case(
                             MedianTTR <= 60,
                             '✅ Fast', 
                             MedianTTR <= 180,
                             '⚠️ Medium', 
                             '❌ Slow'
                         )
| project
    Severity, 
    ["Median Time to Resolve (minutes)"] = MedianTTR, 
    ["% of Total MTTR"] = PercentageOfTotal, 
    ["MTTR Classification"] = MTTR_Severity
| order by Severity asc

```

<br/>

![](/assets/img/KQL%20Toolbox/7/MTTR.png)

<br/>

## 🤔 Why this is useful to a SOC

- This is the pivot from visibility to operational outcomes; Median time-to-resolve is more honest than average (a few “forever incidents” won’t skew it as hard).
  - By severity shows whether your process matches your priorities.

It’s the beginning of true SOC performance measurement (and a great way to justify headcount, automation, tuning, and MSSP expectations).

<br/>

## 🕵️ Line-by-line breakdown

### ✅ Block 1: Calculate your overall MTTR benchmark

```kql
// Get total MTTR
let TotalMTTRTable = 
```

What it means: You’re creating a reusable “mini table” (a variable) named TotalMTTRTable that will hold your overall MTTR baseline.

    SecurityIncident

<br/>

What it means: Pulls from the SecurityIncident table (Microsoft Sentinel incidents).

    | where TimeGenerated > ago(90d)

<br/>

What it means: Limits analysis to the last 90 days so you’re measuring recent operational behavior, not ancient history.

    | where Status == "Closed"


<br/>

What it means: Only closed incidents count for MTTR (because we need a “start + finish”). Open incidents don’t have a real resolve time yet.

    | summarize TotalMTTR = round(avg(datetime_diff('minute', ClosedTime, CreatedTime)), 2)


<br/>

What it means:
- `datetime_diff('minute', ClosedTime, CreatedTime)` = “minutes between created and closed”
- `avg(...)` = overall average resolution time
- `round(..., 2)` = keep it neat for reporting

⚠️ Note: This is actually an average TTR baseline (not median). That’s fine—just know averages are more sensitive to outliers (one nasty incident can skew it).

<br/>

    | extend Key = 1;  // Adding a key for joining

- What it means: Adds a constant Key column so you can join this 1-row table to another table later.
- Why it exists: KQL joins need a shared column—this is the “duct tape key.”

<br/><br/>

### ✅ Block 2: MTTR by severity (your “where it hurts” view)

```kql
// Calculate MTTR per severity
let SeverityMTTR = 
```

What it means: Another variable table—this one will store resolve time by severity.

<br/>

    SecurityIncident
    | where TimeGenerated > ago(90d)
    | where Status == "Closed"


What it means: Same scope rules as your baseline so comparisons are apples-to-apples.

<br/>

    | summarize MedianTTR = percentile(datetime_diff('minute', ClosedTime, CreatedTime), 50) by Severity

What it means:
- Computes resolve minutes per incident
- Uses `percentile(..., 50)` = median (the “typical” experience, less impacted by outliers)
- Groups by Severity so you get one row per severity level

✅ Why median matters: Median tells you what most cases feel like. Average tells you what your worst days feel like.

<br/>

    | extend Key = 1;  // Adding a key for joining

What it means: Same join trick—every severity row gets Key=1.

<br/><br/>

## ✅ Block 3: Join + compute “% of total MTTR” + classify speed

```kql
// Join both results to calculate percentage
SeverityMTTR
| join kind=inner (TotalMTTRTable) on Key
```

What it means: Adds the TotalMTTR baseline column onto every Severity row.
Result: Each severity row now knows the “overall MTTR number” too.

<br/>

    | extend PercentageOfTotal = strcat(iff(TotalMTTR > 0, round((MedianTTR * 100.0) / TotalMTTR, 2), 0.0), '%')  // Ensure consistent data type

What it means: Creates a percent value showing how big each severity’s median is relative to total average MTTR.
- `MedianTTR * 100.0 / TotalMTTR` = percent
- `iff(TotalMTTR > 0, ..., 0.0)` prevents divide-by-zero
- `strcat(..., '%')` turns it into a display-friendly string like 82.14%

⚠️ Reality check: This “% of total MTTR” is a relative indicator, not a true “contribution” metric (because you’re comparing median severity time to average overall time). Still useful as a quick “severity vs baseline” lens.

<br/>

```kql
| extend MTTR_Severity = case(
                             MedianTTR <= 60,
                             '✅ Fast', 
                             MedianTTR <= 180,
                             '⚠️ Medium', 
                             '❌ Slow'
                         )
```

What it means: Operational classification:
- ≤ 60 min: ✅ Fast
- ≤ 180 min: ⚠️ Medium
- 180 min: ❌ Slow

Why it matters: This turns a metric into a decision signal—something you can throw into a dashboard and immediately spot where process / staffing / automation needs help.

<br/>

```kql
| project
    Severity, 
    ["Median Time to Resolve (minutes)"] = MedianTTR, 
    ["% of Total MTTR"] = PercentageOfTotal, 
    ["MTTR Classification"] = MTTR_Severity
```

What it means: Clean, report-ready output with friendly column names for workbooks / exec screenshots.

<br/>

    | order by Severity asc

What it means: Sorts results by severity label ascending.

✅ Tip: If your severities aren’t naturally ordered (e.g., “High/Medium/Low/Informational”), you might later add a custom sort key.

<br/>

![](/assets/img/KQL%20Toolbox/7/kql7-MTTR.png)

<br/><br/>

## ⚡ Operationalization playbook: Turning MTTR from a Metric into Muscle

This query is where metrics stop being vanity charts and start driving real operational change. Here’s how to wire it into your SOC so ❌ Slow doesn’t just sit there judging you.

### 📊 1. Workbook Placement (Make MTTR Impossible to Ignore)

Where this belongs:
- Microsoft Sentinel → Workbooks
- Create or extend a workbook called:
    - “SOC Performance & Detection Reality”
    - Or “MITRE Coverage → MTTR Reality” (chef’s kiss for execs)

Recommended layout:
- Top row — KPI tiles
- Overall MTTR (minutes)
- % of incidents classified ❌ Slow
- % change vs previous 30 / 90 days
- Middle — Severity MTTR table (this query)
- Severity
- Median Time to Resolve
- MTTR Classification (✅ / ⚠️ / ❌)
- Bottom — Trend chart
- Median MTTR by severity over time (weekly bins)

> 💡 DevSecOpsDad tip: Color-code the MTTR Classification column. Humans respond faster to color than numbers—just like alerts.

<br/>

## 🚨 2. Alerting Thresholds (When “Slow” Becomes a Signal)

This query is not an alert by itself—but it feeds alerts beautifully.

Suggested alert conditions (starting point):

| Condition	                         | Trigger                                  |
|------------------------------------|------------------------------------------|
| ❌ Slow incidents (High/Critical)  | MedianTTR > 180 min                      |
| ⚠️ Medium trending worse	         | +20% MTTR increase week-over-week        |
| SOC regression	                 | Overall MTTR increases 2 periods in a row |
| Burnout indicator                  | Low severity MTTR creeping > 120 min

How to implement:
- Wrap this query into a Scheduled Analytics Rule
- Evaluate daily or weekly (weekly is usually saner)
- Fire alerts to:
    - SOC Manager channel
    - Incident response lead
    - ServiceNow / Jira (if you’re fancy)

#### 🧠 Key mindset shift:
You’re not alerting on attacks—you’re alerting on operational failure.

<br/>

### 🛠️ 3. Turning ❌ Slow into an Action List (The Part That Actually Matters)

A ❌ Slow classification is not a failure—it’s a diagnostic flag.

When a severity shows ❌ Slow, immediately pivot with these follow-ups:

#### 🔍 A. Is it a detection problem?

Run:
- MITRE coverage queries
- Time-to-first-alert analysis
- Duplicate / noisy incident checks

Common finding:
- “We detected it… but 90 minutes too late.”

➡️ Action:
- Improve analytics rules, correlation logic, or data source coverage.

<br/>

#### 🧑‍🤝‍🧑 B. Is it an ownership problem?

Ask:
- Who was assigned?
- How long did assignment take?
- Was escalation manual?

➡️ Action:
- Auto-assign by severity
- Enforce SLA timers
- Add Logic Apps / automation rules

#### 🔁 C. Is it a workflow problem?

Look for:
- Reopened incidents
- Excessive comments
- Long “waiting” gaps

➡️ Action:
- Create playbooks for top 5 slow scenarios
- Add decision trees to runbooks
- Remove approval bottlenecks

<br/>

#### 👥 D. Is it a people problem?

Yes, sometimes it is—and that’s okay.

➡️ Action:
- Targeted training (not generic)
- Shadow reviews on slow incidents
- Rotate analysts off burnout lanes

### 🎯 4. The Real Win: MTTR as a Feedback Loop

When operationalized correctly, this query becomes:
- A weekly SOC standup slide
- A monthly maturity metric
- A before/after proof point for leadership
- A budget justification engine (tools + headcount)

You’re no longer saying:
- “We have alerts.”

You’re saying:
- “We detect what matters, respond faster each quarter, and can prove it.”

That’s the jump from SOC activity to SOC performance.

<br/>


<br/>

![](/assets/img/KQL%20Toolbox/7/kql7-playbook.png)


<br/>
<br/>

# 👉 Are we actually keeping up?
If “Opened” stays above “Closed,” you don’t have a SOC… you have a security debt factory.

What to look for:
- Healthy: Closed line meets or exceeds Opened most days (or catches up quickly after spikes).
- Unhealthy: Opened consistently above Closed → backlog growth.
- False confidence trap: MTTR improves but Opened outpaces Closed (you’re closing easy stuff fast while hard stuff piles up).

## Turn “❌ Slow” into an action list

When the chart shows backlog growth:
- Pivot by Severity (is the backlog all Medium? Or are Highs stacking?)
- Pivot by MITRE tactic/technique (which behaviors are generating most incident volume?)
- Pivot by Product / Source (Defender for Endpoint vs Cloud Apps vs Identity — what’s feeding the beast?)

Fix the cause:
- Too many duplicates → tune analytics / suppression
- Too many benigns → tighten entity mapping + thresholds
- Too many “real” incidents → detection coverage is fine, response automation/playbooks aren’t

```kql
SecurityIncident
| summarize OpenedIncidents = countif(Status == "New"), ClosedIncidents = countif(Status == "Closed") by bin(TimeGenerated, 1d)
| render timechart
```

<br/>

![](/assets/img/KQL%20Toolbox/7/kql7-mttrCHART.png)

<br/>

## Line-by-Line Breakdown — Daily Incident Open vs Close Velocity

This query answers a deceptively simple but operationally critical question: _Are we opening incidents faster than we’re closing them?_

Let’s break it down line by line 👇

        SecurityIncident

This is your source table in Microsoft Sentinel.

It contains one row per incident, including:
- Creation time
- Current status (New, Active, Closed)
- Severity
- Owner
- MITRE context (when mapped)

Everything that follows is scoped to incident lifecycle telemetry, not raw alerts.

<br/>

        | summarize

This summarize is where the math happens. Instead of inspecting individual incidents, we’re aggregating them to answer a trend question:
- How many incidents are opening vs closing over time?

<br/>

        OpenedIncidents = countif(Status == "New"),

This creates a calculated column called OpenedIncidents. `countif()` counts rows only when the condition is true. Here, we’re counting incidents whose Status is "New."

💡 Why this matters:
This represents incoming SOC workload — alerts that escalated into incidents and just landed on your team’s desk.

If this number spikes and stays high… your SOC is under pressure.

<br/>

        ClosedIncidents = countif(Status == "Closed")

This creates a second calculated column: ClosedIncidents; Same idea, different condition... Counts incidents that have reached a terminal state

💡 Why this matters:
This is your throughput — proof that analysts are resolving, not just triaging.

A healthy SOC closes incidents at or above the rate they open.

<br/>

        by bin(TimeGenerated, 1d)

This is the time-bucketing logic.

`bin(TimeGenerated, 1d)` groups incidents into daily buckets and each row in the result represents one day.

💡 Why this matters:
SOC performance is about trendlines, not point-in-time snapshots.

Daily granularity is perfect for:
- Shift analysis
- Week-over-week improvement
- Executive dashboards

<br/>

        | render timechart

This turns raw numbers into instant visual truth 📈
- X-axis: Time (by day)
- Y-axis: Count of incidents

Two lines:
- Opened incidents
- Closed incidents

💡 Why this matters:
Executives don’t read tables — they read shapes.

This chart immediately shows:
- Backlog growth
- Burn-down efficiency
- Whether MTTR improvements are actually working

<br/>

### 🎯 What This Query Really Tells You

At a glance, this chart answers:
- Are we keeping up with incident volume?
- Are process changes reducing backlog?
- Did a new detection rule overwhelm the SOC?
- Is MTTR improvement translating into closure velocity?
- This is where MITRE coverage meets operational reality.

<br/>

### 🔧 Why This Belongs in KQL Toolbox

This query is a bridge metric:
- From detections → incidents
- From alerts → outcomes
- From “we have signals” → “we have control”

It pairs perfectly with:
- MTTR by severity
- MITRE tactic frequency
- Analyst workload distribution

<br/><br/>

# 🧩 Putting it together: “MITRE → MTTR” SOC storyline
- Tactics tell you the phase of enemy behavior you’re seeing most
- Techniques tell you the specific behaviors to harden detections/playbooks for
- Median TTR (MTTR) tells you whether the SOC can consistently close the loop fast enough

That’s a clean maturity arc: coverage → precision → performance.

<br/>
<br/>

# 🛡️ Framework mapping

## NIST CSF 2.0
- DE.CM (Detect: Continuous Monitoring): tactics/techniques observed are direct signals of what detection content is producing and what behaviors are present.
- RS.AN / RS.MI (Respond: Analysis / Mitigation): MTTR measures the speed of analysis + containment/mitigation workflows.
- GV.ME (Govern: Measurement & Oversight): MTTR by severity is a real operational metric for governance/reporting.

<br/>

## CIS Controls v8
- Control 8 (Audit Log Management) & Control 13 (Network Monitoring and Defense): MITRE mapping is only as good as your logging + detection coverage.
- Control 17 (Incident Response Management): MTTR is a direct measure of IR operational effectiveness.

<br/>

## CMMC / NIST 800-171 (conceptual alignment)
- Incident handling and response performance expectations map naturally to measuring and improving time-to-resolve, especially when you can show severity-based prioritization.


<br/><br/>

# 🧠 Final Thoughts — The Bigger Picture

Over the course of this KQL Toolbox series, we didn’t just write queries — we built a repeatable SOC operating model.
- We started by making telemetry understandable and accountable: _what you ingest, what it costs, what’s noisy, and what changed._
- Then we shifted from volume to risk, from threats delivered to human behavior, identity impact, and privilege control.
- And now, we’ve closed the loop by asking the only question that truly matters at scale: _Is all of this making us faster and better at defending the environment?_

By connecting adversary behavior (MITRE) to response outcomes (MTTR), you move beyond dashboards and coverage claims into something far more powerful — measurable operational maturity. You can explain not just what you see, but why it matters, what you prioritize, and how your SOC is improving over time.

> _That’s the difference between running KQL queries and running a defense program._

If there’s one takeaway from the entire KQL Toolbox series, it’s this: _Logs are only potential energy. Discipline, workflows, and measurement are what turn them into results._

Now take these patterns, adapt them to your environment, and keep pushing your SOC up the maturity ladder — one intentional query at a time. 😼🥷🔎

<br/>

![](/assets/img/KQL%20Toolbox/7/kql7-closing.png)

<br/><br/>

# 📚 Want to go deeper?

From logs and scripts to judgment and evidence — the DevSecOpsDad Toolbox shows how to operate Microsoft security platforms defensibly, not just effectively.


<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/hZ1TVpO" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/KQL Toolbox Cover.jpg"
      alt="KQL Toolbox: Turning Logs into Decisions in Microsoft Sentinel"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🛠️ <strong>KQL Toolbox:</strong> Turning Logs into Decisions in Microsoft Sentinel
  </p>
</div>

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/ifIo6eT" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/PowerShell-Cover.jpg"
      alt="PowerShell Toolbox: Hands-On Automation for Auditing and Defense"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🧰 <strong>PowerShell Toolbox:</strong> Hands-On Automation for Auditing and Defense
  </p>
</div>

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/4vveVCI" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg"
      alt="Ultimate Microsoft XDR for Full Spectrum Cyber Defense"
      style="max-width: 340px; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    📖 <strong>Ultimate Microsoft XDR for Full Spectrum Cyber Defense</strong><br/>
    Real-world detections, Sentinel, Defender XDR, and Entra ID — end to end.
  </p>
</div>

<br/><br/>

# 🔗 Helpful Links & Resources

- [🔗 Who's Clicking on Junk Mail?](https://github.com/EEN421/KQL-Queries/blob/Main/Who's%20Clicking%20on%20Junk%20Mail%3F.kql)
- [🔗 Who Deleted an AD User?](https://github.com/EEN421/KQL-Queries/blob/Main/Who_Deleted_an_AD_User%3F.kql)
- [🔗 Who's Activating PIM Roles?](https://github.com/EEN421/KQL-Queries/blob/Main/Who's%20Activating%20Roles%20via%20PIM%3F.kql)
- [🔗 Who's Logging In and When? RDP Queries A & B](https://github.com/EEN421/KQL-Queries/blob/Main/Who's%20Logging%20In%20and%20When%3F.kql)

<br/>

# ⚡Other Fun Stuff...
- [🛠️ Kql Toolbox #1: Track & Price Your Microsoft Sentinel Ingest Costs](https://www.hanley.cloud/2025-12-14-KQL-Toolbox-1-Track-&-Price-Your-Microsoft-Sentinel-Ingest-Costs/)
- [🛠️ Kql Toolbox #2: Find Your Noisiest Log Sources (with Cost 🤑)](https://www.hanley.cloud/2026-01-05-KQL-Toolbox-2-Find-Your-Noisiest-Log-Sources-(with-Cost-)/)
- [🛠️ Kql Toolbox #3: Which Event Id Noises Up Your Logs (and Who’s Causing It)?](https://www.hanley.cloud/2026-01-10-KQL-Toolbox-3-Which-Event-ID-Noises-Up-Your-Logs-(and-Who-s-Causing-It)/)
- [🛠️ Kql Toolbox #4: What Changed? Finding Log Sources With The Biggest Delta In Volume & Cost](https://www.hanley.cloud/2026-01-18-KQL-Toolbox-4-What-Changed-Finding-Log-Sources-with-the-Biggest-Delta-in-Volume-&-Cost/)
- [🛠️ Kql Toolbox #5: Phishing & Malware Hunting](https://www.hanley.cloud/2026-01-25-KQL-Toolbox-5-Phishing-&-Malware-Hunting/)
- [🧰 Powershell Toolbox Part 1 Of 4: Azure Network Audit](https://www.hanley.cloud/2025-11-16-PowerShell-Toolbox-Part-1-of-4-Azure-Network-Audit/)
- [🧰 Powershell Toolbox Part 2 Of 4: Azure Rbac Privileged Roles Audit](https://www.hanley.cloud/2025-11-19-PowerShell-Toolbox-Part-2-of-4-Azure-RBAC-Privileged-Roles-Audit/)
- [🧰 Powershell Toolbox Part 3 Of 4: Gpo Html Export Script — Snapshot Every Group Policy Object In One Pass](https://www.hanley.cloud/2025-11-20-PowerShell-Toolbox-Part-3-of-4-GPO-HTML-Export-Script-Snapshot-Every-Group-Policy-Object-in-One-Pass/)
- [🧰 Powershell Toolbox Part 4 Of 4: Audit Your Scripts With Invoke Scriptanalyzer](https://www.hanley.cloud/2025-11-24-PowerShell-Toolbox-Part-4-of-4-Audit-Your-Scripts-with-Invoke-ScriptAnalyzer/)
- [😼 Legend of Defender Ninja Cat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025)

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)
