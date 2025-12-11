Here we go—KQL of the Week #2 🎉
I’ll write this so you can mostly copy-paste into your post and tweak paths/wording as needed.

---

# 💡 KQL Query of the Week #2 — Find Your Noisiest Log Sources (With Cost)

Last week in **KQL Query of the Week #1**, we zoomed out and looked at **billable ingest trends over time**—how many GiB per day you’re ingesting, and roughly how much that’s costing you in Microsoft Sentinel.

This week, we’re zooming **in**.

Because once you can say *“We’re ingesting 150 GiB/day and spending ~$645/day”*, the very next question from your boss, your CFO, or your own anxiety is:

> **“Okay… *which* log sources are burning that money?”**

That’s what this week’s query set is all about:
**Top 10 log sources by cost**, and then **drilling into two usual suspects**:

* `CommonSecurityLog` (firewalls, proxies, etc.)
* `SecurityEvent` (Windows security logs)

We’ll walk through **three variations of the same pattern**:

1. **Top 10 Log Sources by Cost (All Tables)**
2. **Top 10 `CommonSecurityLog` Severity Levels by Cost**
3. **Top 10 `SecurityEvent` Event IDs by Cost**

All three use the same idea:

> **Sum the billable bytes → convert to GiB → multiply by your per-GB price → rank by cost.**

I’ve published the full queries here:

* **Top 10 Log Sources with Cost (Enhanced)**
* **Top 10 CommonSecurityLogs by Severity Level with Cost (Enhanced)**
* **Top 10 Security Events with Cost (Enhanced)**

👉 You can find them all in my public KQL repo:
`https://github.com/EEN421/KQL-Queries` (look for the **“Top 10 … with Cost (Enhanced)”** files).

---

## Quick Primer: `_IsBillable` and `_BilledSize`

Every Log Analytics table (including `Usage`, `CommonSecurityLog`, `SecurityEvent`, etc.) comes with two core columns for cost analysis: ([Microsoft Learn][1])

* **`_IsBillable`** – `true` if this record actually counts toward your bill.
* **`_BilledSize`** – size of the record in **bytes** that you’re billed for.

These are your **per-row cost knobs**. Instead of just counting events, you can say:

> “Which **events** and **patterns** are responsible for the largest share of my ingestion bill?”

That’s the heart of this week’s queries.

---

## Query 1 – Top 10 Log Sources by Cost (All Tables)

First, let’s answer the high-level question:

> “Which **tables** (log sources) are costing us the most over the last 30 days?”

```kql
// KQL of the Week #2 - Query 1
// Top 10 log sources (tables) by total cost

let PricePerGB = 4.30;   // <-- Replace with your region's actual Sentinel price per GB

Usage
| where TimeGenerated > ago(30d)
| where IsBillable == true
| summarize TotalGiB = round(sum(Quantity) / 1024.0, 2) by DataType
| extend CostUSD = round(TotalGiB * PricePerGB, 2)
| top 10 by CostUSD desc
| order by CostUSD desc
```

### What this does, line-by-line

* **`let PricePerGB = 4.30;`**

  * Workspace-specific knob for your **per-GB Sentinel ingest cost**.
  * Replace `4.30` with your region’s actual value from the official Microsoft Sentinel pricing page. ([Microsoft Learn][2])

* **`Usage`**

  * The **ingest ledger** table—one row per meter usage entry.
  * This is what we used heavily in Week #1 for trend analysis.

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

This immediately tells you:

* Are **firewall logs** the main culprit? (`CommonSecurityLog`)
* Are **Windows Security logs** (`SecurityEvent`) eating the bulk of your budget?
* Are there any surprises—like `Syslog`, `AuditLogs`, or some obscure connector suddenly popping at the top?

Once you know which **table** is noisy, the next step is to dig **inside** that table.

---

## Query 2 – Top 10 `CommonSecurityLog` Severity Levels by Cost

In many environments, **CEF-based logs** (firewalls, proxies, VPNs) are some of the **biggest cost drivers**. Those land in `CommonSecurityLog`. ([Microsoft Learn][4])

But not all firewall events are equal:

* Some are high-value (blocks, VPN auths, IDS/IPS alerts).
* Some are **boring noise** (session teardown, heartbeats, low-value allow events).

This query uses `_IsBillable` and `_BilledSize` **directly on the table** to show which **severity levels** (and products) within `CommonSecurityLog` are costing you the most.

```kql
// KQL of the Week #2 - Query 2
// Top 10 CommonSecurityLog severity levels by cost

let PricePerGB = 4.30;   // <-- Match this to the same rate you used in Query 1

CommonSecurityLog
| where TimeGenerated > ago(30d)
| where _IsBillable == true
| summarize TotalGiB = round(sum(_BilledSize) / 1024.0 / 1024.0 / 1024.0, 2)
          by DeviceVendor, DeviceProduct, LogSeverity
| extend CostUSD = round(TotalGiB * PricePerGB, 2)
| top 10 by CostUSD desc
| order by CostUSD desc
```

### How this works

* **`CommonSecurityLog`**

  * The “CEF catch-all” table for supported security appliances—firewalls, proxies, etc.

* **`| where _IsBillable == true`**

  * Same idea as before, but now the **billing flag is on the table itself**. ([Azure Docs][3])

* **`sum(_BilledSize)`**

  * `_BilledSize` is **per-row billed bytes**. Summed, it gives you the **exact ingest volume** for this group. ([Microsoft Learn][1])

* **`/ 1024 / 1024 / 1024`**

  * Convert bytes → GiB:

    * `/ 1024` = KiB
    * `/ 1024` = MiB
    * `/ 1024` = GiB

* **Group by `DeviceVendor`, `DeviceProduct`, `LogSeverity`**

  * `DeviceVendor` – e.g., *Palo Alto Networks*, *Fortinet*, *Check Point*
  * `DeviceProduct` – specific product line
  * `LogSeverity` – CEF severity (e.g., *Informational*, *Low*, *Medium*, *High*, *Critical*)

This gives you a neat table like:

| DeviceVendor | DeviceProduct | LogSeverity   | TotalGiB | CostUSD |
| ------------ | ------------- | ------------- | -------- | ------- |
| Palo Alto    | PAN-OS        | Informational | 220.48   | 948.06  |
| Palo Alto    | PAN-OS        | Low           | 145.12   | 623.02  |
| Fortinet     | FortiGate     | Informational | 89.33    | 383.12  |
| …            | …             | …             | …        | …       |

From there you can ask:

* “Why are **Informational** events costing us more than all our **High** / **Critical** combined?”
* “Are we **over-logging** low-value categories on the firewalls?”
* “Can we use **DCRs or transformation rules** to drop/trim noisy patterns before ingest?”

This is where **real savings** happen:
You’re not randomly turning off logs—you’re specifically **targeting the lowest-value, highest-cost severities**.

---

## Query 3 – Top 10 `SecurityEvent` Event IDs by Cost

Now let’s turn that same idea on another noisy classic:

> **Windows Security logs** (`SecurityEvent`).

We’ll use `_IsBillable` and `_BilledSize` again to find which **Event IDs** are contributing the most to cost.

```kql
// KQL of the Week #2 - Query 3
// Top 10 SecurityEvent Event IDs by cost

let PricePerGB = 4.30;   // <-- Same price knob as before

SecurityEvent
| where TimeGenerated > ago(30d)
| where _IsBillable == true
| summarize TotalGiB = round(sum(_BilledSize) / 1024.0 / 1024.0 / 1024.0, 2)
          by EventID, Activity
| extend CostUSD = round(TotalGiB * PricePerGB, 2)
| top 10 by CostUSD desc
| order by CostUSD desc
```

### Why this is powerful

* **Cost by Event ID**

  * Instead of “Windows logs are expensive,” you can now say:

    * “EventID **5156** (Windows Filtering Platform) is costing us **$X/month**.”
    * “EventID **4624** (successful logon) vs. **4625** (failed logon) cost comparison.”

* **`Activity`**

  * Including `Activity` in the grouping gives a **human-readable description** next to the ID (`"An account was successfully logged on"`, etc.). ([Microsoft Learn][5])

This helps you decide:

* Which Event IDs are **high-noise, low-value** for your use cases.
* Where you can potentially **filter or redirect** to a cheaper tier (Basic, Auxiliary, or external storage) instead of the full Analytics tier. ([Microsoft Learn][6])

When you combine this with **detections you actually care about**, you can be ruthless:

> “These 3 Event IDs matter for our threat models.
> The other 12 are tax.”

---

## Putting It All Together: A Simple Cost-Hunting Workflow

Here’s how I use these three queries in the real world:

1. **Start with Week #1 query:**

   * Spot **trends** and **spikes** in overall billable ingest.

2. **Run Query 1 (Top 10 log sources by cost):**

   * Identify which **tables** are the heaviest hitters.

3. **For `CommonSecurityLog`:**

   * Run Query 2 to see **which vendor/product + severity combos** are burning the most.
   * Tune firewalls / proxies / DCRs accordingly.

4. **For `SecurityEvent`:**

   * Run Query 3 to see **which Event IDs** are the biggest cost drivers.
   * Review which ones actually matter to your detections and compliance requirements.

5. **Turn insights into actions:**

   * Data Collection Rules (DCRs) to **filter** or **transform**
   * Move low-value logs to **Basic/Auxiliary tiers** or an **external data lake**
   * Adjust retention on particularly noisy tables

Run this loop once a month (or per QBR), and you’ll steadily chip away at:

* **Unnecessary ingest**
* **Unnecessary spend**
* While keeping the **signal** you actually need for detection and forensics.

---

## Caveats and Nuances to Keep in Mind

A few important notes before you start deploying chainsaws to your logs:

* **Cost math is workspace- and region-specific.**

  * Always plug in your **actual Sentinel price per GB** from the pricing page, not the 4.30 example I’m using here. ([Microsoft Learn][2])

* **_BilledSize and _IsBillable are the source of truth.**

  * They account for compression and internal sizing—so they’ll differ from raw event sizes. ([Microsoft Learn][1])

* **Don’t cut before checking detections.**

  * Before trimming a noisy Event ID or severity, check:

    * Do any existing **analytics rules** rely on it?
    * Could future **threat hunts** need it?
    * Are there any **regulatory** or **forensic** reasons to keep it?

* **Trend first, then optimize.**

  * That’s why Week #1 was all about **trends** and Week #2 is about **top talkers**.
  * Use both to tell a complete story:

    * “Here’s how our ingest/cost is trending.”
    * “Here are the specific log sources and patterns we adjusted to control it.”

---

## Next Steps / Call to Action

Here’s your homework for this week:

1. **Run Query 1** in your Sentinel workspace and export the results.
2. Circle the top 3 cost drivers and ask:

   * “Are these logs **worth** what we’re paying for them?”
3. For at least one of those tables:

   * If it’s `CommonSecurityLog`, run Query 2.
   * If it’s `SecurityEvent`, run Query 3.
   * Identify **one concrete optimization** (filter, transformation, tier change, or reduced retention).
4. Document the change + impact:

   * “We trimmed X logs, saving ~Y GiB/day (~$Z/month).”

Run this exercise across a few months and you’ll not only **cut costs**, you’ll also build a defensible narrative for leadership:

> “We didn’t just reduce logging—we removed low-value noise while preserving (and sometimes improving) security signal.”

---

If you like this kind of **practical KQL + cost-tuning** content, keep an eye on the **KQL Query of the Week** series—and if you want the bigger picture across Defender, Sentinel, and Entra, my book *Ultimate Microsoft XDR for Full Spectrum Cyber Defense* goes even deeper with real-world examples, detections, and automation patterns.

Now go make those noisy logs **pay rent**. 😼🗡️📊

[1]: https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-standard-columns?utm_source=chatgpt.com "Standard columns in Azure Monitor log records"
[2]: https://learn.microsoft.com/en-us/azure/sentinel/billing?utm_source=chatgpt.com "Plan costs and understand pricing and billing"
[3]: https://docs.azure.cn/en-us/azure-monitor/logs/analyze-usage?utm_source=chatgpt.com "Analyze usage in Log Analytics workspace"
[4]: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/commonsecuritylog?utm_source=chatgpt.com "Azure Monitor Logs reference - CommonSecurityLog"
[5]: https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/securityevent?utm_source=chatgpt.com "Azure Monitor Logs reference - SecurityEvent"
[6]: https://learn.microsoft.com/en-us/azure/sentinel/billing-reduce-costs?utm_source=chatgpt.com "Reduce costs for Microsoft Sentinel"
