Alright — here’s a **true line-by-line breakdown** of your query, in “DevSecOpsDad toolbox” style (what it does + why it matters + gotchas).

---

## 🧠 What this query is trying to answer

> **“Which data sources changed the most in billable log volume when comparing the last 30 days vs the 30 days before that?”**

It does this by:

* defining **two time windows**
* summarizing **billable Usage** by `DataType`
* doing a **full outer join** so new/discontinued sources still show up
* calculating **absolute delta (GB)** and **percent delta (%)**
* returning the **top 5 biggest absolute swings**

---

## 🔍 Line-by-line breakdown

### Comment header

```kql
//This query:
//-->Finds the exact time ranges for comparison periods (previous 30 days vs current 30 days)
//-->Calculates total GB for each data source in both periods
//-->Joins the results to show the comparison
//-->Calculates both absolute and percentage changes
//-->Shows top 5 sources with biggest absolute changes
//-->Handles cases where sources might be new or discontinued
```

This is your “intent block.” Love it. It tells the reader what to expect before they see any KQL.

---

## 1) Find the prior period start time

```kql
let PriorPeriod = toscalar(Usage
    | where TimeGenerated > ago(60d) and TimeGenerated <= ago(30d) // Data from 30 to 60 days ago
    | where IsBillable == true
    | summarize min(TimeGenerated)); // Get the earliest record in that period
```

### What this does

* Looks at the **Usage** table (Sentinel billing/usage telemetry).
* Filters to the window: **60d ago → 30d ago** (the *previous* 30-day period).
* Keeps **only billable rows** (`IsBillable == true`).
* Finds the **earliest** `TimeGenerated` in that window.
* Wraps it in `toscalar(...)` so the result becomes a **single datetime value** stored in `PriorPeriod`.

### Why it matters

You’re trying to anchor the “prior 30 days” window using real data boundaries.

### Gotcha

This is *not* “the prior period start time” in a calendar sense — it’s **the earliest event found** in that window. If ingestion was paused or sparse, the “start” could slide forward.

---

## 2) Find the current period end time (but… you don’t actually use it)

```kql
let CurrentPeriod = toscalar(Usage
    | where TimeGenerated > ago(30d) // Data from the last 30 days
    | where IsBillable == true
    | summarize max(TimeGenerated)); // Get the latest record in the current period
```

### What this does

* Filters to **last 30 days**
* Gets the **latest** `TimeGenerated` found
* Stores it in `CurrentPeriod`

### Gotcha (important)

You **never reference `CurrentPeriod` later**, so this line currently:

* adds clarity (intent)
* but **does not affect results**

If you want “exact time ranges,” you’d use `CurrentPeriod` in your filters (we can improve that later).

---

## 3) Summarize prior-period GB by data source

```kql
let PriorData = Usage
    | where TimeGenerated between (PriorPeriod .. ago(30d)) // Filter for data in the prior period
    | where IsBillable == true
    | summarize PriorGB = round(todouble(sum(Quantity))/1024, 2) by DataType; // Calculate GB by data type in the prior period
```

### What this does

* Queries **Usage**
* Filters to `TimeGenerated between (PriorPeriod .. ago(30d))`

That is:

* **start:** `PriorPeriod` (earliest record found in that prior window)
* **end:** `ago(30d)` (exactly 30 days ago from “now”)

Then it:

* keeps only billable
* groups by `DataType` (this is the “data source/table” name in Usage)
* sums `Quantity` for each `DataType`
* converts to GB-ish by dividing by `1024`
* rounds to 2 decimals

### Why the `todouble()`?

KQL sometimes keeps `sum(Quantity)` as a numeric type that can behave oddly in math or formatting. `todouble()` ensures consistent numeric output before division and rounding.

### Gotcha

**What unit is `Quantity`?** In the Usage table, `Quantity` is generally in **MB** for data ingestion usage records, so dividing by `1024` is converting **MB → GB (GiB-ish)**. That’s commonly how folks do it, but it’s worth being explicit in your blog copy.

---

## 4) Summarize current-period GB by data source

```kql
let CurrentData = Usage
    | where TimeGenerated > ago(30d) // Filter for data in the current period
    | where IsBillable == true
    | summarize CurrentGB = round(todouble(sum(Quantity))/1024, 2) by DataType; // Calculate GB by data type in the current period
```

### What this does

Same as `PriorData`, but for the **last 30 days**.

### Gotcha

This uses `TimeGenerated > ago(30d)` which is open-ended to “now” (not to `CurrentPeriod`). In most cases, that’s fine, but it means your “end boundary” is “query execution time,” not “latest record time.”

---

## 5) Join prior + current together (including new/discontinued sources)

```kql
PriorData
| join kind=fullouter CurrentData on DataType // Join data from prior and current periods by data type
```

### What this does

A `fullouter` join includes:

* sources only in **PriorData** (discontinued / went quiet)
* sources only in **CurrentData** (new / newly billable)
* sources in **both** (normal)

This is exactly what you want for “delta hunting.”

### Gotcha

When one side is missing, fields come back null, and you’ll see *two* DataType columns:

* `DataType` (left)
* `DataType1` (right)

That’s why you handle coalesce next.

---

## 6) Normalize nulls and merge the DataType columns

```kql
| extend DataType = coalesce(DataType, DataType1), // Handle null values from join
        PriorGB = coalesce(PriorGB, 0.0),
        CurrentGB = coalesce(CurrentGB, 0.0)
```

### What this does

* `coalesce(DataType, DataType1)` picks the first non-null value.

  * If the source only exists in CurrentData, `DataType` (left) is null → it uses `DataType1`
* `coalesce(PriorGB, 0.0)` turns null into 0 (meaning “no data that period”)
* same for CurrentGB

This is the key step that makes new/discontinued sources behave logically in math.

---

## 7) Shape output columns + calculate deltas

```kql
| project ['Data Source'] = DataType, // Create columns for data source and GB changes
         ['Previous 30 Days (GB)'] = PriorGB, 
         ['Current 30 Days (GB)'] = CurrentGB, 
         ['Change (GB)'] = round(CurrentGB - PriorGB, 2), // Calculate the change in GB
         ['Change %'] = iif(PriorGB > 0, round(((CurrentGB - PriorGB) / PriorGB) * 100, 1), 100.0) // Calculate percentage change
```

### What this does

* Renames columns to human-friendly labels (great for blog screenshots / workbooks)
* Computes:

  * **Change (GB)** = current minus prior
  * **Change %**:

    * if PriorGB > 0 → normal percent change math
    * else (prior was 0) → hardcodes `100.0`

### Gotcha (this is a subtle one)

That `else 100.0` is a *choice*, not “math truth.”

If PriorGB = 0 and CurrentGB > 0:

* percent change is technically “infinite / undefined”
* you’re treating it as **100%**, which reads like “doubled,” but actually means “went from zero to something.”

That’s not wrong for dashboards (it avoids NaN/inf), but you may want to label it in the post as:

> “When a source is brand new, percent change is shown as 100% by convention.”

(We can improve this later with a clearer “NEW” label or null.)

---

## 8) Remove completely empty rows

```kql
| where ['Current 30 Days (GB)'] > 0 or ['Previous 30 Days (GB)'] > 0 // Only include records with non-zero data
```

### What this does

After the join + coalesce, you could theoretically end up with rows that are 0/0 (rare, but possible depending on joins and data quirks). This ensures you only keep meaningful sources.

---

## 9) Show the biggest movers

```kql
| top 5 by abs(['Change (GB)']) desc // Get top 5 data sources by absolute volume change
```

### What this does

* Uses `abs(ChangeGB)` so it catches:

  * big increases **and** big decreases
* Returns the **top 5** most significant swings

### Why that’s good

For “what changed?” hunting, you want both:

* sudden spike (new noise)
* sudden drop (something broke, or tuning worked)

---

## ✅ Summary: what a reader should understand after this breakdown

This query is essentially a “delta radar”:

* **prior 30 days vs current 30 days**
* per data source (`DataType`)
* shows biggest swings first
* includes new/discontinued sources via `fullouter`

---

If you want, next we can tighten just **one thing** before moving to the cost version:

* Make the time windows truly “exact” and symmetric (so we aren’t mixing `PriorPeriod`, `ago(30d)`, and an unused `CurrentPeriod`).
