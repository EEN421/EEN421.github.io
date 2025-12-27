# KQL Toolbox #7 — 🎯 MITRE Coverage → ⏱️ MTTR Reality

In KQL Toolbox #6 we tracked human-risk outcomes (junk clicks) and identity/privilege control signals (who changed what, who escalated). This week we zoom out and ask: _Are our detections aligned to real adversary behavior?_

And once something fires… _are we actually getting faster at resolving it?_

This is the bridge from “we have alerts” to “we have measurable operational performance.”

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

## Why this is useful to a SOC
- **Quick “threat posture snapshot”:** Are you mostly dealing with Initial Access + Execution, or is Lateral Movement + Persistence dominating?
- **Detection engineering priority:** If a tactic is constantly showing up, it’s either (a) reality, (b) a detection bias, or (c) noise you need to tune.
- **Executive translation:** MITRE tactics are one of the fastest ways to communicate “what’s happening” without drowning in product-specific alerts.

<br/>

## Line-by-line breakdown

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


## Tuning upgrades (high-impact)

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

## Operationalization playbook
- Weekly SOC review: “Top tactics” becomes a recurring agenda item.
- Detection backlog: If Defense Evasion is high, prioritize telemetry gaps + hardening detections there.
- Hunt pivot: Pick the #1 tactic and run a themed hunting sprint (one week = one tactic).

<br/><br/>

# Query 2 — Most common MITRE techniques observed (Top 10)

## Why this is useful to a SOC
- Tactics tell you the phase of the attack. Techniques tell you the exact behavior (and often the exact telemetry you should be collecting).
- This query helps you:
- Measure real-world technique frequency (what’s actually firing)
- Spot coverage gaps (if tactics show up but technique mapping is sparse)
- Prioritize enrichment (technique-heavy detections should have playbooks + automation)

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

## Line-by-line breakdown

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

## Tuning upgrades (especially important here)

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

## Operationalization playbook
Technique “Top 10” becomes your playbook roadmap: ensure top techniques have:
- enrichment (entity mapping),
- triage checklist,
- automation/containment actions,
- and detection tuning ownership.

Purple-team alignment: pick one technique and run an emulation test; validate alerts and measure time-to-close.

<br/><br/>

# Query 3 — Median Time to Resolve (MTTR) by severity (Closed incidents)

## Why this is useful to a SOC

- This is the pivot from visibility to operational outcomes; Median time-to-resolve is more honest than average (a few “forever incidents” won’t skew it as hard).
  - By severity shows whether your process matches your priorities.

It’s the beginning of true SOC performance measurement (and a great way to justify headcount, automation, tuning, and MSSP expectations).

```kql
SecurityIncident
| where TimeGenerated > ago(90d)
| where Status == "Closed"
| summarize MedianTTR = percentile(datetime_diff('minute', ClosedTime, CreatedTime), 50) by Severity
| project Severity, ["Median Time to Resolve (minutes)"] = MedianTTR
| order by Severity asc
```

<br/>
<br/>


## Line-by-line breakdown

### `SecurityIncident`
Uses incidents (the “case management” object). Good — this reflects actual SOC workflow, not raw alert spam.

<br/>

### `Status == "Closed"`
Ensures you’re measuring completed work.

<br/>

### `datetime_diff('minute', ClosedTime, CreatedTime)`
Duration from creation to closure (your “time to resolve” definition).

<br/>

### `percentile(..., 50)`
Median. Solid choice for ops metrics.

<br/>

### `order by Severity asc`
Careful: ordering here depends on how severity values sort in your workspace (string vs numeric). You may want an explicit sort order.

<br/>

## Tuning upgrades (make MTTR actionable)
### 1.) Use an explicit severity sort
```kql
| extend SevRank = case(Severity =~ "High", 1, Severity =~ "Medium", 2, Severity =~ "Low", 3, 99)
| order by SevRank asc
| project-away SevRank
```

<br/>

### 2.) Exclude auto-closed / benign closure reasons (if you have them)
If your environment auto-closes incidents, MTTR can look “amazing” but meaningless. Filter those out if fields exist in your tenant.

<br/>

### 3.) Add volume context
**Median** alone hides “we closed 2 incidents fast.” Add counts:
`| summarize Incidents=count(), MedianTTR=percentile(datetime_diff('minute', ClosedTime, CreatedTime), 50) by Severity`

<br/>

### 4.) Add trend over time (weekly median)
This is where MTTR turns into a KPI:
```kql
| summarize MedianTTR=percentile(datetime_diff('minute', ClosedTime, CreatedTime), 50) by bin(TimeGenerated, 7d), Severity
| order by TimeGenerated asc
```

<br/>

## Operationalization playbook
- Set targets (example): High < 240 min, Medium < 1440 min, Low < 4320 min — pick what matches your staffing reality.
- Force multiplier: tie MTTR improvements directly to:
  - automation (Logic Apps / SOAR),
  - enrichment (entity mapping, device/user context),
  - alert quality tuning (reduce false positives),
  - and playbook maturity (tiered triage runbooks).

Use it in retros: every month, review top technique + slowest MTTR severity and decide what to fix.

<br/>
<br/>


# Putting it together: “MITRE → MTTR” SOC storyline
- Tactics tell you the phase of enemy behavior you’re seeing most
- Techniques tell you the specific behaviors to harden detections/playbooks for
- Median TTR (MTTR) tells you whether the SOC can consistently close the loop fast enough

That’s a clean maturity arc: coverage → precision → performance.

<br/>
<br/>

# Framework mapping (high-level but practical)

## NIST CSF 2.0
- DE.CM (Detect: Continuous Monitoring): tactics/techniques observed are direct signals of what detection content is producing and what behaviors are present.
- RS.AN / RS.MI (Respond: Analysis / Mitigation): MTTR measures the speed of analysis + containment/mitigation workflows.
- GV.ME (Govern: Measurement & Oversight): MTTR by severity is a real operational metric for governance/reporting.

<br/>

CIS Controls v8
- Control 8 (Audit Log Management) & Control 13 (Network Monitoring and Defense): MITRE mapping is only as good as your logging + detection coverage.
- Control 17 (Incident Response Management): MTTR is a direct measure of IR operational effectiveness.

<br/>

CMMC / NIST 800-171 (conceptual alignment)
- Incident handling and response performance expectations map naturally to measuring and improving time-to-resolve, especially when you can show severity-based prioritization.

You can now say more than “we have detections;” You can say what adversary behavior is showing up most, what techniques deserve the next wave of tuning, and whether your SOC is actually getting faster at closing the loop. **That’s the difference between a dashboard and a defense program.**

<br/><br/>

# 📚 Want to Go Deeper?

⚡ If you like this kind of **practical KQL + cost-tuning** content, keep an eye on the **DevSecOpsDad KQL Toolbox** series—and if you want the bigger picture across Defender, Sentinel, and Entra, my book *Ultimate Microsoft XDR for Full Spectrum Cyber Defense* goes even deeper with real-world examples, detections, and automation patterns.
&#128591; Huge thanks to everyone who’s already picked up a copy — and if you’ve read it, a quick review on Amazon goes a long way!

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/4vveVCI" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg"
      alt="Ultimate Microsoft XDR for Full Spectrum Cyber Defense"
      style="max-width: 340px; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    📘 <strong>Ultimate Microsoft XDR for Full Spectrum Cyber Defense</strong><br/>
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
- [🧰 Powershell Toolbox Part 1 Of 4: Azure Network Audit](https://www.hanley.cloud/2025-11-16-PowerShell-Toolbox-Part-1-of-4-Azure-Network-Audit/)
- [🧰 Powershell Toolbox Part 2 Of 4: Azure Rbac Privileged Roles Audit](https://www.hanley.cloud/2025-11-19-PowerShell-Toolbox-Part-2-of-4-Azure-RBAC-Privileged-Roles-Audit/)
- [🧰 Powershell Toolbox Part 3 Of 4: Gpo Html Export Script — Snapshot Every Group Policy Object In One Pass](https://www.hanley.cloud/2025-11-20-PowerShell-Toolbox-Part-3-of-4-GPO-HTML-Export-Script-Snapshot-Every-Group-Policy-Object-in-One-Pass/)
- [🧰 Powershell Toolbox Part 4 Of 4: Audit Your Scripts With Invoke Scriptanalyzer](https://www.hanley.cloud/2025-11-24-PowerShell-Toolbox-Part-4-of-4-Audit-Your-Scripts-with-Invoke-ScriptAnalyzer/)

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)
