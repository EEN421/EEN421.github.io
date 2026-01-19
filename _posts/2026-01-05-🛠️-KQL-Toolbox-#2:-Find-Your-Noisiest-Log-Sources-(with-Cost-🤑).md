## Welcome back to KQL Toolbox 👋
In the last **KQL Toolbox**, we zoomed out and looked at **billable ingest trends over time**—how many GiB per day you’re ingesting, and roughly how much that’s costing you in Microsoft Sentinel. This time, we’re zooming **in**.

Because once you can say *“We’re ingesting 150 GiB/day and spending ~$645/day”*, the very next question from your boss, your CFO, or your own anxiety is:

> **“Okay… *which* log sources are burning that money?”**

![](/assets/img/KQL%20Toolbox/2/Toolbox2.png)

That’s what today’s query set is all about:
**Top 10 log sources by cost**, and then **drilling into two usual suspects**:

* `CommonSecurityLog` (firewalls, proxies, etc.)
* `SecurityEvent` (Windows security logs)

<br/>

We’ll walk through **three variations of the same pattern**:

1. **Top 10 Log Sources by Cost (All Tables)**
2. **Top 10 `CommonSecurityLog` Severity Levels by Cost**
3. **Top 10 `SecurityEvent` Event IDs by Cost**

<br/>

All three use the same idea: **_Sum the billable bytes → convert to GiB → multiply by your per-GB price → rank by cost._**

<br/>

![Edible Bytes: Alert-Fatigue Formula](/assets/img/KQL%20Toolbox/2/NinjaCatAnalyst.png)

<br/><br>

Get the full, copy-pasta ready KQL queries here on GitHub:

* [**🔗 Top 10 Log Sources with Cost (Enhanced)**](https://github.com/EEN421/KQL-Queries/blob/Main/Top%2010%20Log%20Sources%20with%20Cost%20(Enhanced).kql)
* [**🔗 Top 10 CommonSecurityLogs by Severity Level with Cost (Enhanced)**](https://github.com/EEN421/KQL-Queries/blob/Main/Top%2010%20CommonSecurityLogs%20by%20Severity%20Level%20with%20Cost%20(Enhanced).kql)
* [**🔗 Top 10 Security Events with Cost (Enhanced)**](https://github.com/EEN421/KQL-Queries/blob/Main/Top%2010%20Security%20Events%20with%20Cost%20(Enhanced).kql)


<br/><br/>

## Quick Primer: `_IsBillable` and `_BilledSize`

Every Log Analytics table (including `Usage`, `CommonSecurityLog`, `SecurityEvent`, etc.) comes with two core columns for cost analysis: 

* **`_IsBillable`** – `true` if this record actually counts toward your bill.
* **`_BilledSize`** – size of the record in **bytes** that you’re billed for.

These are your **per-row cost knobs**. Instead of just counting events, you can say: _“Which **events** and **patterns** are responsible for the largest share of my ingestion bill❓”_


<br/><br/>

# Query 1 – Top 10 Log Sources by Cost (All Tables)

First, let’s answer the high-level question: _“Which **tables** (log sources) are costing us the most over the last 30 days❔”_

```kql
// KQL Toolbox #2 - Query 1
// Top 10 log sources (tables) by total cost

let PricePerGB = 5.16;   // <-- Replace with your region's actual Sentinel price per GB

Usage
| where TimeGenerated > ago(30d)
| where IsBillable == true
| summarize TotalGiB = round(sum(Quantity) / 1024.0, 2) by DataType
| extend CostUSD = round(TotalGiB * PricePerGB, 2)
| top 10 by CostUSD desc
| order by CostUSD desc
```

![](/assets/img/KQL%20Toolbox/2/kql1-1.png)

<br/><br/>

## What this does, line-by-line...

* **`let PricePerGB = 4.30;`**

  * Workspace-specific knob for your **per-GB Sentinel ingest cost**.
  * Replace `4.30` with your region’s actual value from the [official Microsoft Sentinel pricing page](https://www.microsoft.com/en-us/security/pricing/microsoft-sentinel/?msockid=2ae8ebcef0f5615a2c3bfed2f1326064). 

* **`Usage`**

  * The **ingest ledger** table—one row per meter usage entry.
  * This is what we used heavily in [KQL Toolbox #1](https://www.hanley.cloud/2025-12-14-KQL-Toolbox-1-Track-&-Price-Your-Microsoft-Sentinel-Ingest-Costs/) for trend analysis.

* **`| where TimeGenerated > ago(30d)`**

  * Scope to the **last 30 days** for a nice “recent” view.
  * Swap `30d` for `7d`, `90d`, or whatever cadence fits your QBRs.

* **`| where IsBillable == true`**

  * We only care about log sources that **actually cost money**. (Some tables can be free/benefit-covered.)

* **`| summarize TotalGiB = round(sum(Quantity) / 1024.0, 2) by DataType`**

  * `Quantity` is in MB; divide by `1024` to get **GiB**. ([Azure Docs][3])
  * `round(..., 2)` keeps results human-friendly (e.g., `152.37` GiB).
  * Group by `DataType` = **table name** (`SecurityEvent`, `CommonSecurityLog`, `SigninLogs`, etc.).

* **`| extend CostUSD = round(TotalGiB * PricePerGB, 2)`**

  * Convert GiB → **dollars** with a single inline expression.
  * This is your “ingest bill by table.”

* **`| top 10 by CostUSD desc`**

  * Surface just your **top 10 most expensive log sources**.

<br/>

This immediately tells you:

* Are **firewall logs** the main culprit? (`CommonSecurityLog`)
* Are **Windows Security logs** (`SecurityEvent`) eating the bulk of your budget?
* Are there any surprises—like `Syslog`, `AuditLogs`, or some obscure connector suddenly popping at the top?

Once you know which **table** is noisy, the next step is to dig **inside** that table.

<br/>

## ⚔️ Steps to Operationalize:
- Schedule this query to run weekly via a Sentinel scheduled analytics rule or runbook.
- Visualize on a dashboard showing cost contribution by log source.
- Monthly review in SOC/QBR meetings to identify cost outliers.

<br/>

## 🚨 Example Alerting:
- Threshold alert when any log source exceeds a configured GiB/day or cost/day threshold, triggering an investigation into noisy sources.

<br/>

## 🛡️ Framework Mapping:
- **NIST CSF DE.CM-7** – Monitors and analyzes continuous events for potential malicious activity or misconfigurations; here it adds a cost lens to visibility.

- **NIST CSF ID.RA-1** – Helps classify the sources of logs (assets/systems) and determine their impact.

- **CIS Control 6 (Maintenance, Monitoring, and Analysis of Audit Logs)** – Ensures audit logs are collected and analyzed for usability and cost effectiveness.

<br/>

![](/assets/img/KQL%20Toolbox/2/ByteRiver.png)

<br/><br/>

# Query 2 – Top 10 `CommonSecurityLog` Severity Levels by Cost

In many environments, **CEF-based logs** (firewalls, proxies, VPNs) are some of the **biggest cost drivers**. Those land in `CommonSecurityLog`.

But not all firewall events are equal:

* Some are high-value (blocks, VPN auths, IDS/IPS alerts).
* Some are **boring noise** (session teardown, heartbeats, low-value allow events).

This query uses `_IsBillable` and `_BilledSize` **directly on the table** to show which **severity levels** (and products) within `CommonSecurityLog` are costing you the most.

```kql
// KQL Toolbox #2 - Query 2
// Top 10 CommonSecurityLog severity levels by cost

let PricePerGB = 5.16;   // <-- Match this to the same rate you used in Query 1

CommonSecurityLog
| where TimeGenerated > ago(30d)
| where _IsBillable == true
| summarize TotalGiB = round(sum(_BilledSize) / 1024.0 / 1024.0 / 1024.0, 2)
          by DeviceVendor, DeviceProduct, LogSeverity
| extend CostUSD = round(TotalGiB * PricePerGB, 2)
| top 10 by CostUSD desc
| order by CostUSD desc
```

![](/assets/img/KQL%20Toolbox/2/kql2-1.png)

<br/><br/>

## How this works:

* **`CommonSecurityLog`**

  * The “CEF catch-all” table for supported security appliances—firewalls, proxies, etc. 

* **`| where _IsBillable == true`**

  * Same idea as before, but now the **billing flag is on the table itself**. ([Azure Docs][3])

* **`sum(_BilledSize)`**

  * `_BilledSize` is **per-row billed bytes**. Summed, it gives you the **exact ingest volume** for this group. 

* **`/ 1024 / 1024 / 1024`**

  * Convert bytes → GiB:

    * `/ 1024` = KiB
    * `/ 1024` = MiB
    * `/ 1024` = GiB

* **Group by `DeviceVendor`, `DeviceProduct`, `LogSeverity`**

  * `DeviceVendor` – e.g., *Palo Alto Networks*, *Fortinet*, *Check Point*
  * `DeviceProduct` – specific product line
  * `LogSeverity` – CEF severity (e.g., *Informational*, *Low*, *Medium*, *High*, *Critical*)

<br/>

This gives you a neat table like:

| DeviceVendor | DeviceProduct | LogSeverity   | TotalGiB | CostUSD |
| ------------ | ------------- | ------------- | -------- | ------- |
| Palo Alto    | PAN-OS        | Informational | 220.48   | 948.06  |
| Palo Alto    | PAN-OS        | Low           | 145.12   | 623.02  |
| Fortinet     | FortiGate     | Informational | 89.33    | 383.12  |
| …            | …             | …             | …        | …       |

<br/>

From there you can ask:

* “Why are **Informational** events costing us more than all our **High** / **Critical** combined?”
* “Are we **over-logging** low-value categories on the firewalls?”
* “Can we use **DCRs or transformation rules** to drop/trim noisy patterns before ingest?”

This is where **real savings** happen:
You’re not randomly turning off logs—you’re specifically **targeting the lowest-value, highest-cost severities**.

<br/>

## ⚔️ Steps to Operationalize:
- Embed in a workbook segmented by vendor/product and severity.
- Pair with DCR/Log Filters: Identify low-value severity buckets (e.g., informational or low) that can be filtered or redirected to Basic tier or external storage.
- Integrate with Change Controls: When tuning log sources, include cost impact in the change request narrative.

<br/>

### 🚨 Example Alerting:
- Alert when a new vendor or severity group suddenly rises above expected cost baselines.

<br/>

## 🛡️ Framework Mapping:
- **NIST CSF DE.CM-8** – Use automated tools to support detection processes; here it adds depth to severity interpretation.

- **NIST CSF PR.IP-1** – Baselines for configuration and cost awareness.

- **CIS Control 6.1 & 6.2** – Ensure audit logs and network device logs are collected and analyzed (including cost efficiency).

<br/>

![](/assets/img/KQL%20Toolbox/2/CatDad.png)

<br/><br/>

# Query 3 – Top 10 `SecurityEvent` Event IDs by Cost

Now let’s turn that same idea on another noisy classic:

> **Windows Security logs** (`SecurityEvent`).

We’ll use `_IsBillable` and `_BilledSize` again to find which **Event IDs** are contributing the most to cost.

```kql
// KQL Toolbox #2 - Query 3
// Top 10 SecurityEvent Event IDs by cost

let PricePerGB = 5.16;   // <-- Same price knob as before

SecurityEvent
| where TimeGenerated > ago(30d)
| where _IsBillable == true
| summarize TotalGiB = round(sum(_BilledSize) / 1024.0 / 1024.0 / 1024.0, 2)
          by EventID, Activity
| extend CostUSD = round(TotalGiB * PricePerGB, 2)
| top 10 by CostUSD desc
| order by CostUSD desc
```

![](/assets/img/KQL%20Toolbox/2/kql3-1.png)

<br/><br/>

## Why this is powerful

* **Cost by Event ID**

  * Instead of “Windows logs are expensive,” you can now say:

    * “EventID **5156** (Windows Filtering Platform) is costing us **$X/month**.”
    * “EventID **4624** (successful logon) vs. **4625** (failed logon) cost comparison.”

* **`Activity`**

  * Including `Activity` in the grouping gives a **human-readable description** next to the ID (`"An account was successfully logged on"`, etc.).

This helps you decide:

* Which Event IDs are **high-noise, low-value** for your use cases.
* Where you can potentially **filter or redirect** to a cheaper tier (Basic, Auxiliary, or external storage) instead of the full Analytics tier. 

When you combine this with **detections you actually care about**, you can be ruthless:

> “These 3 Event IDs matter for our threat models. The other 12 are tax.”

<br/>

## ⚔️ Steps to Operationalize:
- Include in monthly cost review alongside threat detection priorities.
- Map high-cost Event IDs to detection rules to ensure you aren’t dropping signals needed for security detections if tuning filters.
- Run histograms/heatmaps to visualize shifts over time in noisy WindowsIDs.

<br/>

## 🚨 Example Alerting:
- Alert when a specific Event ID’s cost contribution increases above established percent of total.

<br/>

## 🛡️ Framework Mapping:
- **NIST CSF DE.DP-4 (Event detection)** – Identifies anomalous activities via event patterns; here with cost relevance.
- **NIST CSF PR.IP-3** – Secure configurations informed by usage and impact.
- **CIS Control 8 (Audit Log Management)** – Ensures audit event logs are used effectively for both security and cost governance.

<br/><br/>

# 👀 Visual Upgrade! 
_Did you know you can use **Emojies** in your **KQL!?**_

Let's add some severity colour-coding to make our query results **pop!**

### Query 1 - Revamped! 
```
Usage
| where TimeGenerated > ago(30d)
| where IsBillable == true
| summarize GiB= round(sum(Quantity) / 1024, 2) by DataType
| extend Cost=round(GiB * 5.16, 2)
| sort by Cost desc
| extend CostLevel = case(
                         Cost >= 1000,
                         '🤑🤑🤑🤑🤑',  // Most Expensive
                         Cost >= 750,
                         '💰💰💰💰',
                         Cost >= 500,
                         '💰💰💰',
                         Cost >= 250,
                         '💰💰',
                         Cost >= 100,
                         '💰',          // Least Expensive
                         '💸'                         // Fallback
                     )
| extend Cost=strcat('$', Cost, ' ', CostLevel)
| project DataType, GiB, Cost
| take 10
```

![](/assets/img/KQL%20Toolbox/2/kql1-2.png)

This is purely presentation/triage. It buckets spend into ranges for quick scanning, but it looks cool!

> 💡 Pro Tip: The order of **case()** matters: <br/>
> 👉 _it checks top-to-bottom and stops at the first match (so the >= 1000 check must come before >= 100, etc.)._

<br/><br/>

### Query 2 - Revamped! 
```
CommonSecurityLog
| where TimeGenerated > ago(90d)
| where isnotempty(Reason) and Reason != "N/A"
| summarize TotalEvents = count(), 
            TotalBytes = sum(_BilledSize) 
            by Reason, LogSeverity
| extend TotalGB = round(TotalBytes / (1024.0 * 1024.0 * 1024.0), 4)
| extend RawCost = round(TotalGB * 5.16, 2)
| extend CostLevel = case(
                         RawCost >= 1000, '🤑🤑🤑🤑🤑',
                         RawCost >= 750, '💰💰💰💰',
                         RawCost >= 500, '💰💰💰',
                         RawCost >= 250, '💰💰',
                         RawCost >= 100, '💰',
                         '💸')
| extend IngestCost = strcat('$', tostring(RawCost), ' ', CostLevel)
| project Reason, LogSeverity, TotalEvents, TotalGB, IngestCost
| top 10 by TotalEvents desc
```

![](/assets/img/KQL%20Toolbox/2/kql2-2.png)

<br/><br/>

### Query 3 - Revamped! 
```
SecurityEvent
| where TimeGenerated > ago(30d)
| where _IsBillable == True
| summarize EventCount=count(), GiB=round(sum(_BilledSize / 1024 / 1024 / 1024), 2) by EventID
| extend TotalCost = round(GiB * 5.16, 2)
| sort by GiB desc
| extend CostLevel = case(
                         TotalCost >= 1000,
                         '🤑🤑🤑🤑🤑',  // Most Expensive
                         TotalCost >= 750,
                         '💰💰💰💰',
                         TotalCost >= 500,
                         '💰💰💰',
                         TotalCost >= 250,
                         '💰💰',
                         TotalCost >= 100,
                         '💰',          // Least Expensive
                         '💸'                             // Fallback
                     )
| extend TotalCost=strcat('$', TotalCost, ' ', CostLevel)
| project EventID, GiB, TotalCost
| limit 10
```

![](/assets/img/KQL%20Toolbox/2/kql3-2.png)

<br/><br/>

# Putting It All Together: A Simple Cost-Hunting Workflow

Here’s how I use these three queries in the real world:

1. **Start with [KQL Toolbox #1](https://www.hanley.cloud/2025-12-14-KQL-Toolbox-1-Track-&-Price-Your-Microsoft-Sentinel-Ingest-Costs/), [query #1](https://github.com/EEN421/KQL-Queries/blob/Main/90%20Day%20Billable%20Ingest%20Volume.kql):**

   * Spot **trends** and **spikes** in overall billable ingest.

   <br/>

2. **Run Query 1 (Top 10 log sources by cost):**

   * Identify which **tables** are the heaviest hitters.

   <br/>

3. **For `CommonSecurityLog`:**

   * Run **Query 2** to see **which vendor/product + severity combos** are burning the most.
   * Tune firewalls / proxies / DCRs accordingly.

   <br/>

4. **For `SecurityEvent`:**

   * Run **Query 3** to see **which Event IDs** are your _biggest cost drivers._
   * Review which ones actually matter to your detections and compliance requirements.

   <br/>

5. **Turn insights into actions:**

   * Data Collection Rules (DCRs) to **filter** or **transform**
   * Move low-value logs to **Basic/Auxiliary tiers** or an **external data lake**
   * Adjust retention on particularly noisy tables

   <br/>

Run this loop once a month (or per QBR), and you’ll steadily chip away at:

* **Unnecessary ingest**
* **Unnecessary spend**
* While keeping the **signal** you actually need for detection and forensics.

<br/><br/>

# Operationalizing these & Mapping to NIST/CIS Outcomes

The three core queries in this post help you pinpoint which log sources (tables, severities, or event IDs) are driving the majority of your Microsoft Sentinel ingestion costs. To make these queries truly operational — that is, actionable, repeatable, and tied to security outcomes — you should embed them into recurring monitoring workflows, alerts, dashboards, and governance processes. Below is a breakdown of how to do that in context of NIST CSF and CIS Controls.

### Operational Playbook Patterns

Here’s a pattern you can embed into your daily/weekly SOC processes:

#### 1) Scheduled Monitoring & Alerts
  - Run the Top 10 Tables by Cost query every Monday.
  - Generate alerts if any log source cost increases by x% vs prior week.
  - Outcome: Continuous detection of ingest anomalies and cost spikes.

<br/>

#### 2) Dashboards with Context
  - Build a Cost + Value Dashboard that shows:
    - Total cost by log source
    - Percentage of total
    - Severity breakdown (for CEF logs)
    - EventID relevance
  - Outcome: Centralized monitoring that supports both security and governance decisions.

<br/>

#### 3) Governance Review Loop
- Monthly review of top cost drivers.
- Pair with detection and compliance policies to decide:
  - If the log source is essential
  - If filtering / transformations are required
  - If retention tiers need adjustment
- Outcome: Improve log signal-to-noise ratio and align with organizational risk appetite.

<br/>

### Mapping to Compliance and Security Outcomes

| Query / Activity                    | NIST CSF Outcome                	| CIS Control Outcome                |
| ----------------------------------- | --------------------------------- | ---------------------------------- |
| Top 10 log source cost (Query 1)    |	DE.CM-7 (Continuous monitoring)        |	6.1-6.2 Audit log analysis   |
| Severity cost breakdown (Query 2)   |	DE.CM-8 (Automated detection tools)    |	6.2, 8 Log management        |
| EventID cost ranking (Query 3)      |	DE.DP-4 (Event detection and analysis) |	8 Focused audit log analysis |
| Alert thresholds                    |	DE.AE-5 (Response to events)           |	6.6 Alert triage             |

<br/>

> 💡 These mappings justify why cost governance is part of detection engineering, not a finance-only exercise.

<br/>

### Quick Implementation Checklist

☑ Automate these queries as Sentinel scheduled analytics rules <br/>
☑ Dashboards visualizing cost drivers and trends <br/>
☑ Threshold Alerts for anomalous cost spikes <br/>
☑ DCR/Retention Plans tied to cost & value analysis <br/>
☑ Monthly Review Process with documented tuning decisions <br/>

<br/>

![](/assets/img/KQL%20Toolbox/2/NinjaBar.png)


<br/><br/>

# ⚠️ Caveats and Nuances to Keep in Mind

A few important notes before you start deploying chainsaws to your logs:

* **Cost math is workspace- and region-specific.**

  * Always plug in your **actual Sentinel price per GB** from the [official Microsoft pricing page](https://www.microsoft.com/en-us/security/pricing/microsoft-sentinel/?msockid=2ae8ebcef0f5615a2c3bfed2f1326064), and not the example I’m using here.

     <br/>

* **_BilledSize and _IsBillable are the source of truth.**

  * They account for compression and internal sizing—so they’ll differ from raw event sizes; [Log standard columns – Microsoft Learn](https://learn.microsoft.com/azure/azure-monitor/logs/log-standard-columns).

     <br/>

* **Don’t cut before checking detections.**

  * Before trimming a noisy Event ID or severity, check:

    * Do any existing **analytics rules** rely on it?
    * Could future **threat hunts** need it?
    * Are there any **regulatory** or **forensic** reasons to keep it?

   <br/>

* **Trend first, then optimize.**

  * That’s why [KQL Toolbox #1](https://www.hanley.cloud/2025-12-14-KQL-Toolbox-1-Track-&-Price-Your-Microsoft-Sentinel-Ingest-Costs/) was all about **trends;** so KQL Toolbox 2 can transition into **top talkers**.
  * Use both to tell a complete story:

    * “Here’s how our ingest/cost is trending.”
    * “Here are the specific log sources and patterns we adjusted to control it.”

<br/><br/>

# ⏩ Next Steps

Here’s your homework for this week:

1. **Run Query 1** in your Sentinel workspace and export the results.
2. Circle the top 3 cost drivers and ask:

   * “Are these logs **worth** what we’re paying for them?”
3. For at least one of those tables:

   * If it’s `CommonSecurityLog`, **run Query 2.**
   * If it’s `SecurityEvent`, **run Query 3.**
   * Identify **one concrete optimization** (filter, transformation, tier change, or reduced retention).
4. Document the change + impact:

   * “We trimmed X logs, saving ~Y GiB/day (~$Z/month).”

Run this exercise across a few months and you’ll not only **cut costs**, you’ll also build a defensible narrative for leadership:

> 👉 “We didn’t just reduce logging—we removed low-value noise while preserving (and sometimes improving) security signal.” 😎

<br/><br/>

# 🧠 Closing Thoughts
At this point, you’re no longer guessing where your Sentinel budget disappears — you’ve got hard evidence. You can see which tables are screaming, which severities are over-collecting, and which data sources are quietly siphoning dollars day after day. That visibility alone puts you ahead of most SOCs still flying blind.

But here’s the reality check: tables don’t create noise — specific events do.
And events don’t log themselves.

In the next installment of KQL Toolbox, we zoom all the way in — down to the exact Event IDs, accounts, and systems responsible for the bloat. You’ll move from “this table is expensive” to “this event, on this host, by this user, is the problem.” 🔍🔥

That’s where cost optimization turns into control, and logging hygiene becomes an engineering discipline — not a guessing game.

Stay sharp. The receipts are about to get very specific. 😼⚔️

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

<br/>

### 👉 Now go make those noisy logs **pay rent**. 😼🗡️💰

<br/><br/>

# 🔗 Helpful Links & Resources
- [🛠️ Kql Toolbox #1: Track & Price Your Microsoft Sentinel Ingest Costs](https://www.hanley.cloud/2025-12-14-KQL-Toolbox-1-Track-&-Price-Your-Microsoft-Sentinel-Ingest-Costs/)
- [⚡ Top 10 Log Sources with Cost (Enhanced)](https://github.com/EEN421/KQL-Queries/blob/Main/Top%2010%20Log%20Sources%20with%20Cost%20(Enhanced).kql)
- [⚡ Top 10 CommonSecurityLogs by Severity Level with Cost (Enhanced)](https://github.com/EEN421/KQL-Queries/blob/Main/Top%2010%20CommonSecurityLogs%20by%20Severity%20Level%20with%20Cost%20(Enhanced).kql)
- [⚡ Top 10 Security Events with Cost (Enhanced)](https://github.com/EEN421/KQL-Queries/blob/Main/Top%2010%20Security%20Events%20with%20Cost%20(Enhanced).kql)
- [💲 Official Microsoft Sentinel pricing page](https://www.microsoft.com/en-us/security/pricing/microsoft-sentinel/?msockid=2ae8ebcef0f5615a2c3bfed2f1326064)
- [📚 Standard columns in Azure Monitor log records](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-standard-columns)
- [📚 Plan costs and understand pricing and billing](https://learn.microsoft.com/en-us/azure/sentinel/billing)
- [📚 Analyze usage in Log Analytics workspace](https://docs.azure.cn/en-us/azure-monitor/logs/analyze-usage)
- [📚 Azure Monitor Logs reference - CommonSecurityLog](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/commonsecuritylog)
- [📚 Azure Monitor Logs reference - SecurityEvent](https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityevent)
- [📚 Reduce costs for Microsoft Sentinel](https://learn.microsoft.com/en-us/azure/sentinel/billing-reduce-costs)
- [📚 Log standard columns – Microsoft Learn](https://learn.microsoft.com/azure/azure-monitor/logs/log-standard-columns)
- [📚 Analyze usage in Azure Monitor Logs – Microsoft Learn](https://learn.microsoft.com/azure/azure-monitor/logs/analyze-usage)
- [📚 StorageBlobLogs table reference – Microsoft Learn](https://learn.microsoft.com/azure/azure-monitor/reference/tables/storagebloblogs)
- [📚 DeviceInfo table reference – Microsoft Learn](https://learn.microsoft.com/azure/azure-monitor/reference/tables/deviceinfo)
- [😼 Legend of Defender Ninja Cat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025)

<br/>

# Other Fun Stuff...
- [🧰 Powershell Toolbox Part 1 Of 4: Azure Network Audit](https://www.hanley.cloud/2025-11-16-PowerShell-Toolbox-Part-1-of-4-Azure-Network-Audit/)
- [🧰 Powershell Toolbox Part 2 Of 4: Azure Rbac Privileged Roles Audit](https://www.hanley.cloud/2025-11-19-PowerShell-Toolbox-Part-2-of-4-Azure-RBAC-Privileged-Roles-Audit/)
- [🧰 Powershell Toolbox Part 3 Of 4: Gpo Html Export Script — Snapshot Every Group Policy Object In One Pass](https://www.hanley.cloud/2025-11-20-PowerShell-Toolbox-Part-3-of-4-GPO-HTML-Export-Script-Snapshot-Every-Group-Policy-Object-in-One-Pass/)
- [🧰 Powershell Toolbox Part 4 Of 4: Audit Your Scripts With Invoke Scriptanalyzer](https://www.hanley.cloud/2025-11-24-PowerShell-Toolbox-Part-4-of-4-Audit-Your-Scripts-with-Invoke-ScriptAnalyzer/)

<br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)
