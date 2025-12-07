# KQL Query of the Week #1

### **Visualize and Price Your Billable Ingest for the Last 90 Days**

If you’re running a SIEM or XDR platform and *not* looking at your ingest patterns regularly… you’re basically swiping your corporate credit card with the lights off.

This week’s KQL is all about shining a flashlight on your **billable data ingestion** in Microsoft Sentinel / Log Analytics over the last 90 days—first visually, then in cold hard cash.

We’re going to look at two versions of the same query:

1. **Query 1** – “Show me billable GB per day, by solution, as a chart.”
2. **Query 2** – “Roll it up per day, in GB and dollars.”

<br/><br/>

## Query 1 – Billable GB per Day, by Solution (Column Chart)

```kql
// Query 1
Usage                                                                               // <--Query the Usage table
| where TimeGenerated > ago(90d)                                                    // <--Query the last 90 days
| where IsBillable == true                                                          // <--Only include 'billable' data
| summarize TotalVolumeGB = sum(Quantity) / 1000 by bin(StartTime, 1d), Solution    // <--Chop it up into GB / Day
| render columnchart                                                                // <--Graph the results
```

### Line-by-line breakdown

**`Usage`**
This is the built-in **Usage** table in Log Analytics.
It tracks what you’re ingesting, how much, and which solution is responsible (Sentinel, Defender plans, etc.). Think of it as your **Ingest Ledger**.

<br/><br/>

**`| where TimeGenerated > ago(90d)`**
We’re scoping to the **last 90 days** of data. Great window for:

* QBRs (Quarterly Business Reviews)
* Trend analysis (did that new connector you added spike costs?)
* Before/after reviews (e.g., “we tuned noisy logs here — did it work?”)

You can tweak `90d` to anything you want: `30d`, `7d`, `365d`, etc.

<br/><br/>

**`| where IsBillable == true`**
This is where the magic (and savings) happen.

We only care about records that **count toward your bill**. Some logs might be free or included (e.g., certain platform logs). `IsBillable == true` filters out the noise, leaving only data that actually costs you money.

<br/><br/>

**`| summarize TotalVolumeGB = sum(Quantity) / 1000 by bin(StartTime, 1d), Solution`**

This line does a lot of work:

* `sum(Quantity)` – Each record has a `Quantity` field representing the size of data ingested (in MB).
* `/ 1000` – Convert MB to **approximate** GB (1000 MB ≈ 1 GB). This is a “marketing GB” vs “binary GB” thing; we’ll tighten this up in Query 2.
* `TotalVolumeGB = ...` – We give that result a friendly column name.
* `by bin(StartTime, 1d), Solution` – We group our data:

  * `bin(StartTime, 1d)` – Buckets by **day** (based on `StartTime`).
  * `Solution` – Breaks the totals down per **solution** (e.g., `Security`, `SecurityInsights`, `Microsoft Sentinel`, etc.).

So you end up with:

| StartTime (day) | Solution         | TotalVolumeGB |
| --------------- | ---------------- | ------------- |
| 2025-09-01      | SecurityInsights | 120.5         |
| 2025-09-01      | AzureDiagnostics | 15.3          |
| 2025-09-02      | SecurityInsights | 98.7          |
| ...             | ...              | ...           |

<br/><br/>

**`| render columnchart`**

Finally, instead of returning a table, we **render a visual**:

* X-axis: Date (per day)
* Y-axis: GB ingested
* Legend: Solution

This is the “Executive Slide” line. It gives you an instant sense of:

* Which solutions are the main cost drivers.
* Whether your ingest is stable, trending up, or spiking all over the place.
* Where to focus tuning and data hygiene efforts.

This version is **perfect for eyeballing trends** and for screenshots in decks, QBRs, and “hey, what happened here?” emails.

<br/><br/>

## Query 2 – Same Data, But Now With Actual Cost 💸

Once you find a spike, the next question is always:

> “Okay, but how much is that **in dollars**?”

Let’s look at the upgraded version:

```kql
// Query 2
// The below query will return the total billable GB and incurred cost per day. 
Usage                                                                               // <--Query the Usage table
| where TimeGenerated > ago(90d)                                                    // <--Query the last 90 days
| where IsBillable == true                                                          // <--Only include 'billable' data
| summarize TotalVolumeGB = round(sum(Quantity) / 1024, 2) by bin(StartTime, 1d)    // <--Chop it up into GB / Day
| extend cost = strcat('$', round(TotalVolumeGB * 4.30, 2))                         // <--Round to 2 decimal places, calculate the cost, and prepend '$'
```

### What’s new vs Query 1?

1. We dropped `Solution` from the `summarize`

   * Now we’re aggregating **total daily ingest** across all solutions.
   * This gives us a nice, simple **“cost per day”** rollup.

2. We switched from `/ 1000` to `/ 1024` and added `round(...)`

3. We added a `cost` column that multiplies GB by a price per GB and formats it nicely.

Let’s break it down.

<br/><br/>

### `summarize TotalVolumeGB = round(sum(Quantity) / 1024, 2) by bin(StartTime, 1d)`

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

### `| extend cost = strcat('$', round(TotalVolumeGB * 4.30, 2))`

This is where we turn GB into dollars:

* `TotalVolumeGB * 4.30` – We assume a price of **$4.30 per GB**.

  * You should replace `4.30` with your actual Sentinel / workspace ingestion rate.
* `round(..., 2)` – Round the result to 2 decimal places (normal currency formatting).
* `strcat('$', ...)` – Prepend a `$` so it reads like `"$512.78"` instead of just `512.78`.

End result:

| StartTime  | TotalVolumeGB | cost    |
| ---------- | ------------- | ------- |
| 2025-09-01 | 135.42        | $582.31 |
| 2025-09-02 | 118.03        | $507.53 |
| ...        | ...           | ...     |

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

* **Query 2 – Daily Total + Cost**

  * Budgeting / forecasting
  * “What did we spend this month?” conversations
  * Feeding into reports, dashboards, or cost management workflows

In a typical DevSecOps flow, I’d run **Query 2 first** to see the total cost curve, then pivot to **Query 1** (or variants of it) to figure out **who** the biggest offenders are.


