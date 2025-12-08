# **Visualize and Price Your Billable Ingest Trends**
If you’re running a SIEM or XDR platform and *not* looking at your ingest patterns regularly… you’re essentially flying blind on one of the biggest drivers of your security bill. This week’s KQL is all about shining a flashlight on your **billable data ingestion** in Microsoft Sentinel / Log Analytics over the last 90 days—first visually, then in cold hard cash.

We’re going to look at two versions of the same query:

1. **Query 1** – “Show me billable GB per day, by solution, as a chart.”
2. **Query 2** – “Roll it up per day, in GB and dollars.”

<br/><br/>

# Query 1 – Billable GB per Day, by Solution (Column Chart)

```kql
// Query 1 - This is great for checking out your billable ingest patterns over the past quarter for QBRs etc. 

Usage                                                                               // <--Query the Usage table
| where TimeGenerated > ago(90d)                                                    // <--Query the last 90 days
| where IsBillable == true                                                          // <--Only include 'billable' data
| summarize TotalVolumeGB = sum(Quantity) / 1000 by bin(StartTime, 1d), Solution    // <--Chop it up into GB / Day
| render columnchart                                                                // <--Graph the results
```

<br/>

## Line-by-line breakdown:

### 1.) **`Usage`**
This is the built-in **Usage** table in Log Analytics.
It tracks what you’re ingesting, how much, and which solution is responsible (Sentinel, Defender plans, etc.). Think of it as your **Ingest Ledger**.

<br/>

### 2.) **`| where TimeGenerated > ago(90d)`**
We’re scoping to the **last 90 days** of data. Great window for:

* QBRs (Quarterly Business Reviews)
* Trend analysis (did that new connector you added spike costs?)
* Before/after reviews (e.g., “we tuned noisy logs here — did it work?”)

You can tweak `90d` to anything you want: `30d`, `7d`, `365d`, etc.

> **Pro-Tip:** _use 30d for Monthy reports; switch to 90 days at the end of the quarter to pivot to a quarterly report 😎_

<br/>

### 3.) **`| where IsBillable == true`**
This is where the magic (and savings) happen. We only care about records that **count toward your bill**. Some logs might be free or included (e.g., certain platform logs). `IsBillable == true` filters out the noise, leaving only data that actually costs you money.

<br/>

### 4.) **`| summarize TotalVolumeGB = sum(Quantity) / 1000 by bin(StartTime, 1d), Solution`**

This line does a lot of work:

* `sum(Quantity)` – Each record has a `Quantity` field representing the size of data ingested (in MB).
* `/ 1000` – Convert MB to **approximate** GB (1000 MB ≈ 1 GB). This is a “marketing GB” vs “binary GB” thing; we’ll tighten this up in Query 2 and discuss how we got here later on.
* `TotalVolumeGB = ...` – We give that result a friendly column name.
* `by bin(StartTime, 1d), Solution` – We group our data:
  * `bin(StartTime, 1d)` – Buckets by **day** (based on `StartTime`).
  * `Solution` – Breaks the totals down per **solution** (e.g., `Security`, `SecurityInsights`, `Microsoft Sentinel`, etc.).

<br/>

So you end up with:

| StartTime (day) | Solution         | TotalVolumeGB |
| --------------- | ---------------- | ------------- |
| 2025-09-01      | SecurityInsights | 120.5         |
| 2025-09-01      | AzureDiagnostics | 15.3          |
| 2025-09-02      | SecurityInsights | 98.7          |
| ...             | ...              | ...           |

<br/><br/>

### 5.) **`| render columnchart`**

Finally, instead of returning a table, we **render a visual**:

* X-axis: Date (per day)
* Y-axis: GB ingested
* Legend: Solution

<br/>

This is the “Executive Slide” line. It gives you an instant sense of:

* Which solutions are the main cost drivers.
* Whether your ingest is stable, trending up, or spiking all over the place.
* Where to focus tuning and data hygiene efforts.

<br/>

This version is **perfect for eyeballing trends** and for screenshots in decks, QBRs, and “hey, what happened here?” emails.

<br/><br/>

# Query 2 – Same Data, But Now With Actual Cost 🤑

Once you find a spike, the next question is always:

> “Okay, but how much is that **in dollars**?” 💸

Let’s look at the upgraded version:

```kql
// Query 2 - The below query will return the total billable GB and incurred cost per day. 

Usage                                                                                // <--Query the Usage table
| where TimeGenerated > ago(90d)                                                     // <--Query the last 90 days
| where IsBillable == true                                                           // <--Only include 'billable' data
| summarize TotalVolumeGB = round(sum(Quantity) / 1024, 2) by bin(StartTime, 1d)     // <--Chop it up into GB / Day
| extend cost = strcat('$', round(TotalVolumeGB * 4.30, 2))                          // <--Round to 2 decimal places, calculate the cost, and prepend '$'
```

## What’s new vs Query 1?

* We dropped `Solution` from the `summarize`
   * Now we’re aggregating **total daily ingest** across all solutions.
   * This gives us a nice, simple **“cost per day”** rollup.

* We switched from `/ 1000` to `/ 1024` and added `round(...)`

* We added a `cost` column that multiplies GB by a price per GB and formats it nicely.

<br/>

Let’s break it down...

<br/><br/>

### 1.) `summarize TotalVolumeGB = round(sum(Quantity) / 1024, 2) by bin(StartTime, 1d)`

We’re still using `Usage`, 90 days, and `IsBillable == true` — same idea as Query 1.

But now:

* `sum(Quantity)` – Still summing MB.
* `/ 1024` – This time we’re using **binary GB** (1024 MB = 1 GiB), which is more technically precise.
* `round(..., 2)` – We round to **2 decimal places** so you don’t end up with insane precision like `123.4567890123`.

And we group only by `bin(StartTime, 1d)` (no more `Solution`), so we get one row per day:

| StartTime  | TotalVolumeGB |
| ---------- | ------------- |
| 2025-09-01 | 135.42        |
| 2025-09-02 | 118.03        |
| ...        | ...           |

This is your **daily billable volume** in GB.

<br/><br/>

### 2.) `| extend cost = strcat('$', round(TotalVolumeGB * 4.30, 2))`

This is where we turn GB into dollars:

* `TotalVolumeGB * 4.30` – We assume a price of **$4.30 per GB** (this is the cost per GB on the pay-as-you-go commitment tier for the Eastern US region, you can find your cost per GB on [Microsoft's offical pricing page for Sentinel](https://www.microsoft.com/en-us/security/pricing/microsoft-sentinel/?msockid=2ae8ebcef0f5615a2c3bfed2f1326064)).

  * You should replace `4.30` with your actual Sentinel / workspace ingestion rate.
* `round(..., 2)` – Round the result to 2 decimal places (normal currency formatting).
* `strcat('$', ...)` – Prepend a `$` so it reads like `"$512.78"` instead of just `512.78`.

<br/><br/>

End result:

| StartTime  | TotalVolumeGB | cost    |
| ---------- | ------------- | ------- |
| 2025-09-01 | 135.42        | $582.31 |
| 2025-09-02 | 118.03        | $507.53 |
| ...        | ...           | ...     |

<br/><br/>

You now have a **simple, daily cost breakdown** that you can:

* Export to CSV / Excel for finance 📊
* Drop into a QBR deck 📈
* Use to justify:

  * Turning off noisy logs
  * Changing retention
  * Moving certain sources to cheaper storage

If you want, you can still add back `render columnchart` at the end:

```kql
| render columnchart
```

This will give you a nice **“Cost per day”** chart.

<br/><br/>

## When to Use Each Version

* **Query 1 – Visual, by Solution**

  * Quick QBR visuals
  * “Which solution is killing me?” analysis
  * Great starting point for hunting noisy connectors or tables

<br/>

* **Query 2 – Daily Total + Cost**

  * Budgeting / forecasting
  * “What did we spend this month?” conversations
  * Feeding into reports, dashboards, or cost management workflows


<br/><br/>

# 🧠 Quick Note: Gibibytes vs Gigabytes

You’ll sometimes see data measured in gigabytes (GB) and other times in gibibytes (GiB) — and while they sound similar, they’re not the same.

- `Gigabytes (GB)` use **base-10 math**, the same system your hard drive or cloud provider marketing uses:
`1 GB = 1,000,000,000 bytes`

- `Gibibytes (GiB)` use **base-2 math**, which matches how computers actually store and address memory:
`1 GiB = 1,073,741,824 bytes (1024³)`

In other words, **1 GiB is about 7% larger than 1 GB.** So depending on whether a platform reports usage in GB or GiB, the numbers may look slightly different even though the underlying data is identical. This matters in KQL because some tables report usage in binary units (GiB) while pricing calculators often use decimal units (GB). The important part isn’t which one you choose — _it’s that you apply it consistently when analyzing ingest trends or estimating cost._

<br/>

## 💽 How We Ended Up With Gigabytes Instead of Gibibytes
For decades, the tech industry used the word gigabyte (GB) to describe both decimal and binary measurements — even though they’re not the same. This wasn’t intentional deception; it was simply convenient shorthand during the early personal computing era.

<br/>

Hard drive manufacturers used decimal gigabytes (powers of 10) because it made capacity numbers round, clean, and easier to market.
- `1 GB = 1,000,000,000 bytes`

<br/>

Operating systems used binary measurements (powers of 2) because that’s how memory addressing actually works.
- `1 GiB = 1,073,741,824 bytes`

<br/>

For years, both groups called their units GB — which caused confusion as storage capacities grew. To fix the ambiguity, the International Electrotechnical Commission (IEC) introduced new binary-prefixed terms in 1998:

- Kibibyte (KiB)
- Mebibyte (MiB)
- Gibibyte (GiB)

…and so on

The idea was simple: **Use GB for decimal, GiB for binary.** But adoption was slow: Developers and OS vendors (Linux, BSD, macOS) gradually embraced the binary IEC terms. Windows kept using “GB” for binary values for many years. Cloud platforms went mixed — pricing calculators tended to use GB (decimal), but logs and metrics often used binary math. By the time cloud computing exploded, GB had already become the de facto public-facing unit, while GiB remained the technically correct measurement under the hood.

Today, both exist because both are useful:

- GB → pricing, marketing, cloud billing
- GiB → memory, file systems, compute workloads, low-level metrics

And because the names sound similar, the confusion never totally went away — which is why it’s worth calling out in a KQL series where cost math actually matters.

<br/><br/>

## When to Use Each Version

* **Query 1 – Visual, by Solution**

  * Quick QBR visuals
  * “Which solution is killing me?” analysis
  * Great starting point for hunting noisy connectors or tables

* **Query 2 – Daily Total + Cost**

  * Budgeting / forecasting
  * “What did we spend this month?” conversations
  * Feeding into reports, dashboards, or cost management workflows

<br/>
<br/>
<br/>
<br/>

# 📚 Want to Go Deeper?

If this kind of automation gets your gears turning, check out my book:
🎯 Ultimate Microsoft XDR for Full Spectrum Cyber Defense
 — published by Orange Education, available on Kindle and print. 👉 Get your copy here: [📘Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ)

⚡ It dives into Defender XDR, Sentinel, Entra ID, and Microsoft Graph automations just like this one — with real-world MSSP use cases and ready-to-run KQL + PowerShell examples.

&#128591; Huge thanks to everyone who’s already picked up a copy — and if you’ve read it, a quick review on Amazon goes a long way!

![Ultimate Microsoft XDR for Full Spectrum Cyber Defense](/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg)

<br/>
<br/>

# 🔗 References (good to keep handy)

- [🔎Billable Ingest Volume Trend.kql](https://github.com/EEN421/KQL-Queries/blob/Main/90%20Day%20Billable%20Ingest%20Volume.kql)
- [💰Microsoft's Official Sentinel Pricing](https://www.microsoft.com/en-us/security/pricing/microsoft-sentinel/?msockid=2ae8ebcef0f5615a2c3bfed2f1326064)
- [😼Origin of Defender NinjaCat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025) 
- [📘Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ)

<br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)


