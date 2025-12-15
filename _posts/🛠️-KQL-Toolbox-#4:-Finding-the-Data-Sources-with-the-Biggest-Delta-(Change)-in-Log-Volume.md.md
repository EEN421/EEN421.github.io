# 🛠️ KQL Toolbox #4: Finding the Data Sources with the Biggest Delta in Log Volume
In KQL Toolbox #1, we learned how to measure Microsoft Sentinel ingest and translate it into real dollars.

In #2, we identified which data sources were driving that cost.

And in #3, we drilled all the way down to specific Event IDs, accounts, and devices generating noise.

At this point, you can answer what’s expensive, what’s noisy, and who’s responsible.

But there’s one critical question every SOC analyst, engineer, and cost owner eventually asks:

“What changed?”

Because in the real world, cost spikes, alert storms, and performance issues rarely come from what’s always been there — they come from sudden shifts:

A misconfigured data connector

A new audit policy rolled out too broadly

A broken agent stuck in a logging loop

Or a “temporary” change that quietly became permanent

That’s where this week’s KQL comes in.

Instead of ranking data sources by total volume or cost, KQL Toolbox #4 focuses on delta — identifying which log sources have experienced the largest change in volume compared to their historical baseline.

This lets you stop guessing, stop scrolling through charts, and immediately zero in on what deserves investigation first.
If you’re working with Azure Monitor Logs / Log Analytics or Microsoft Sentinel, one of the biggest operational headaches is tracking down why your log volume / billable data is changing. Whether it’s a cloud migration, a new app rollout, a misconfigured agent … or just normal growth — understanding what’s driving increases or drops in ingested logs is critical for budgeting, troubleshooting, and SOC hygiene.

Today we’re going to unpack one of my favorite preventive analytics KQL queries: “Data Sources with Biggest Delta in Log Volume.” I’ll walk through what it’s doing, how it works, and the use cases it helps you solve.

# 🧠 What This Query Is Solving

The core problem here is simple:

### 👉 What data sources (log tables) have changed the most in terms of billable ingestion volume between two periods?

You care about this because:

### 📈 Log ingestion = direct cost in Azure Monitor / Sentinel (billable ingestion volume affects your bill). 
Microsoft Learn
+1

### 🚨 Sudden increases can indicate misconfigurations, runaway telemetry, or silent internal change.

### 🔎 Drops in volume usually point to missing telemetry (broken agents, misconfigured pipelines, stopped services) — which can blind your SOC. 
Microsoft Sentinel 101

This KQL query is a drill-down that compares two time windows — the prior 30 days vs. the most recent 30 days — and shows you which data sources saw the biggest changes in billable GB.

# 🧩 Anatomy of the Query
```kql
let PriorPeriod = toscalar(
    Usage
    | where TimeGenerated > ago(60d) and TimeGenerated <= ago(30d)
    | where IsBillable == true
    | summarize min(TimeGenerated)
);
let CurrentPeriod = toscalar(
    Usage
    | where TimeGenerated > ago(30d)
    | where IsBillable == true
    | summarize max(TimeGenerated)
);
let PriorData = Usage
    | where TimeGenerated between (PriorPeriod .. ago(30d))
    | where IsBillable == true
    | summarize PriorGB = round(todouble(sum(Quantity))/1024, 2) by DataType;
let CurrentData = Usage
    | where TimeGenerated > ago(30d)
    | where IsBillable == true
    | summarize CurrentGB = round(todouble(sum(Quantity))/1024, 2) by DataType;
PriorData
| join kind=fullouter CurrentData on DataType
| extend 
    DataType = coalesce(DataType, DataType1),
    PriorGB = coalesce(PriorGB, 0.0),
    CurrentGB = coalesce(CurrentGB, 0.0),
    ChangeGB = coalesce(CurrentGB - PriorGB, 0.0)
| project 
    ['Data Source'] = DataType,
    ['Previous 30 Days (GB)'] = PriorGB,
    ['Current 30 Days (GB)'] = CurrentGB,
    ['Change (GB)'] = round(CurrentGB - PriorGB, 2),
    ['Change %'] = iif(PriorGB > 0, round(((CurrentGB - PriorGB) / PriorGB) * 100, 1), 100.0),
    ['Change $'] = strcat('$', round(ChangeGB * {CostPerGB}, 2))
| where ['Current 30 Days (GB)'] > 0 or ['Previous 30 Days (GB)'] > 0
| top 10 by abs(['Change (GB)']) desc
```

Let’s decode that step by step.

### 🧱 Step 1 — Define Time Windows
```kql
let PriorPeriod = ...
let CurrentPeriod = ...
```

This part sets up two windows:
- Prior period: The 30–60 days ago span
- Current period: The most recent 30 days

It pulls the earliest and latest timestamps for billable entries in each window so that the subsequent data slices are clean and consistent.

This is important in Azure Monitor usage because the Usage table reflects hourly or periodic summaries, not raw events. 
Microsoft Learn

### 🪄 Step 2 — Summarize Billable Volume
```kql
let PriorData = ...
let CurrentData = ...
```

Here we split the consumption data:

Filter to billable records (IsBillable == true) — this ensures we only count the ingestion that affects billing. 

- Aggregate (summarize) to total GB per log type (DataType)

- Convert from MBytes to GB (sum(Quantity) / 1024)

Now we have two tables:

- `DataType`	`PriorGB`

and

- `DataType`	`CurrentGB`

### 🔗 Step 3 — Compare the Two
```kql
PriorData
| join kind=fullouter CurrentData on DataType
```

This is the heart of the delta — we join both tables to ensure all data sources show up, even if they only exist in one period.

Then we calculate:
- Absolute GB change (ChangeGB)
- Percentage change (Change %)
- Estimated cost impact (Change $) based on a {CostPerGB} placeholder (you’d supply this)

### 📊 Step 4 — Filter and Rank
```kql
| where ...
| top 10 by abs(['Change (GB)']) desc
```

Finally we keep only sources with usage, and take the top 10 by absolute GB change — giving you the biggest movers regardless of direction.

# 🔍 Why This Matters

This query solves real-world operational questions:

### 🧪 1. Detect Sudden Spikes

If one data source starts spiking (e.g., DNS logs, Syslog, SecurityEvents), this will bring it to the top. A sudden spike can:
- Blow your budget
- Signal misconfiguration
- Trigger alerts early

Teams often set up alerts based on these deltas to catch anomalies before the invoice arrives. 

### ❗ 2. Detect Unexpected Drops

A drop isn’t always good. Missing logs often means:

Agents stopped sending

Retention changes

Obsolete connectors

Data source misconfiguration

You lose visibility before you lose money — and that’s worse. 
Microsoft Sentinel 101

### 💰 3. Understand Cost Drivers

When you’re budgeting for Azure Monitor or Sentinel, most of your bill comes from log ingestion. This query lets you:
- Attribute ingestion per source
- Show projected costs due to volume changes
- Justify retention or filtering decisions

Because billing is based on ingested volume, understanding what is driving volume is essential for FinOps. 

### 📅 4. Trend Reporting

Companies often run this weekly or monthly:
- Trend dashboards
- QBR reviews
- Drill-downs for executive reporting

This fits perfectly into quantitative operational reviews.

# 🛠️ How to Operationalize It

### 💡 Enhancements you can add:

- Dashboard: plot each DataType over time
- Alerts: fire if any source grows > X% vs prior period
- Automation: trigger tickets when unexpected drops occur

# 🧠 Final Thoughts

This query is a simple yet powerful FinOps + SOC diagnostic tool. It gives you:

✔ A clear comparison of before vs after
✔ Cost context
✔ Anomaly detection opportunities
✔ A basis for automation and alerting

If you’re managing a growing Azure footprint, you’ll want this in your reporting toolkit.
