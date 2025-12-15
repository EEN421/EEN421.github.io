# 💡 KQL Toolbox #3 — Which Event ID Noises Up Your Logs (and Who’s Causing It)?
**Welcome back to the DevSecOpsDad KQL Toolbox series!** In the last entry (KQL Toolbox #2), we zoomed in on log source cost drivers—using `_IsBillable` and `_BilledSize` to identify which tables, severities, and Event IDs were burning the most money in Microsoft Sentinel. If you missed that one, you can read it here: 👉 [KQL Tip of the Week #2 — Identify Your Top Talkers by Cost](INSERT HERE)

## This week, we’re building directly on that foundation...
Because once you know which **log sources** and which **Event IDs** are the _most expensive_, the very next question becomes:
> “Okay… but which Event ID fires the most often, and which accounts are responsible for generating it?”

This is where today’s KQL shines 🌞

Instead of looking at cost, we shift focus to raw event frequency—a metric that drives both noise and cost. With two short KQL queries, you’ll identify:
- Which Event ID fires most in your environment over the last 30 days?
- Which accounts are generating that Event ID the most?
- Which devices are these Event ID's coming from?

This gives you a clean, fast workflow for spotting noisy Event IDs, isolating misconfigured or anomalous accounts, and tightening both your detection logic and cost posture. With that, let’s jump into this week’s analysis...

<br/>

![](/assets/img/KQL%20Toolbox/3/DevSecSignal.png)

<br/><br/>

# 🔊 Today's KQL helps you spot the loudest Event ID in your environment — and then drill down into which accounts are responsible for firing it most often.

These queries are perfect for your weekly cost-noise correlation checks, operational hygiene reviews, or threat hunting warmups.

💾 Full queries are in my public repo:
- [🔗 Which EventID fires the most in a month?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20EventID%20fires%20the%20most%20in%20a%20month%3F.kql)
- [🔗 Which Accounts are throwing this EventID?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Accounts%20are%20Throwing%20this%20EventID%3F.kql)
- [🔗 Which Devices are Throwing this EventID?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Devices%20are%20Throwing%20this%20EventID%3F.kql)
- [🔗 Which Event IDs Are Suddenly Acting Weird?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Event%20IDs%20Are%20Suddenly%20Acting%20Weird%3F.kql)

<br/> 

## 🔍 Why This Matters

Frequent aggregation and ranking of event volumes help you spot noise that obscures real threats. Comprehensive logging and centralized analysis — combined with targeted filtering like this — improves both cost efficiency and detection quality.

In most orgs, a handful of Event IDs generate most of the volume in SecurityEvent — and those high-frequency IDs can:
- Inflate your ingest costs
- Obscure real signals from the noise
- Make detection rules less efficient
- Hide suspicious behavior behind mountains of normal activity

So step one is simple: **Find the Event ID that fires most often — then look at who’s actually triggering it...** And that’s exactly what today’s queries do.

<br/><br/>

# 📈 Query #1 — Which Event ID Fires the Most in the Last Month?

This query counts all SecurityEvent occurrences in the last 30 days and ranks Event IDs by frequency. No filters, no cost calculations — just the raw noise metric.

```kql
SecurityEvent                       // <--Define the table to query
| where TimeGenerated > ago(30d)    // <--Query the last 30 days
| summarize count() by EventID      // <--Return number of hits per EventID
| take 10                           // <--Take the top 10
| render columnchart                // <--Helps visualize which EventIDs are the heavy hitters
```

![](/assets/img/KQL%20Toolbox/3/3kql1.png)

[**🔗 KQL Toolbox #3 — Which EventID fires the most in a month?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20EventID%20fires%20the%20most%20in%20a%20month%3F.kql)

<br/><br/>

## 🔧 Line-by-Line Breakdown

### 1️⃣ `SecurityEvent`

This selects the SecurityEvent table, which contains Windows Security Log events collected from domain controllers, member servers, and workstations. These events include authentication activity, object access, process creation, policy changes, and more — making this table a common source of high-volume ingest in Microsoft Sentinel.

<br/>

### 2️⃣ `| where TimeGenerated > ago(30d)`

This filters the dataset to only events generated in the last 30 days.
- Keeps the query performant
- Focuses analysis on recent and relevant behavior
- Makes results suitable for monthly reporting, tuning reviews, or QBR discussions

>💡 You can easily adjust this window (e.g., `7d`, `14d`, `90d`) depending on how much history you want to analyze.

<br/>

### 3️⃣ `| summarize count() by EventID`

This is the heart of the query.
- Groups all events by EventID
- Counts how many times each EventID appears in the time window
- Produces a frequency table showing which EventIDs are most common

> 👉 At this stage, the query transforms raw logs into actionable signal, revealing which event types dominate your environment.

<br/>

### 4️⃣ `| sort by count_ desc`

This sorts the summarized results from highest to lowest count. Without this step, you’d be looking at an arbitrary order — but with it, the loudest EventIDs float to the top, making it immediately clear where your log volume is coming from.

> ⚠️ This is critical before using `take` in the next step. 👇

<br/>

### 5️⃣ `| take 10`

This limits the output to the **top 10 EventIDs by volume**, focusing on just the top offenders keeps the output:
- Readable
- Actionable
- Ideal for dashboards and quick reviews

>💡 In most environments, these 10 EventIDs account for a disproportionate share of SecurityEvent ingest.

<br/>

### 6️⃣ render columnchart

This renders the result as a column chart, making patterns instantly visible...

- Each column represents an EventID
- Column height reflects how frequently it occurs
- Outliers and “runaway” events stand out immediately

>💡 This visualization is especially useful when presenting findings to stakeholders or deciding where to focus tuning and filtering efforts.


<br/><br/>

## 🔎 What You’re Looking For

When you run this query:
- You’ll get a chart of Event IDs ranked by how often they happened in the last 30 days.
- The biggest bars are your “noisiest” events.
- Typical suspects often include event-log-heavy IDs like 4624, 4625, 5156, etc., depending on your environment.

This gives you a quick look at what’s dominating your security log volume.

>⚡ Pro-Tip: If you’ve already been tracking ingest costs with last week’s queries, overlay this with Table + Cost ranking and you can start connecting “noise” with “dollars.”

<br/>

### 📊 What the Results Will Contain

This output answers one critical question: “What Event IDs dominate my SecurityEvent volume?”

Common examples you’ll often see:
- 4624 – Successful logons
- 4625 – Failed logons
- 4663 – Object access attempts
- 5156 – Windows Filtering Platform traffic

>💡 _**High frequency** alone doesn’t mean **“bad”** — but it does tell you where to **look next**._

<br/><br/>

## 🎯 How to Use the Results

Once you identify your top EventIDs, you can:
- Investigate why they’re so noisy
- Decide whether they’re security-relevant or just operational
- Tune collection policies, analytics rules, or DCRs
- Reduce Sentinel ingest cost without losing meaningful detections

<br/><br/>

# 👤 Query #2 — Which Accounts Are Throwing This Event ID?

So you found the loudest Event ID... The next step is attribution; let’s see who’s generating it. This second query takes a specific Event ID (in this example **4663**) and counts how many times each account triggered it.

```kql
// Which Accounts are throwing this EventID?
SecurityEvent                     // <--Define the table to query
| where EventID == 4663         // <--Declare which EventID you're looking for
| summarize count() by Account    // <--Show how many times that EventID was thrown per account
| render columnchart              // <--Optional, but helps quickly visualize potential outliers
```

![](/assets/img/KQL%20Toolbox/3/3kql2.png)

[**🔗 KQL Toolbox #3 — Which Accounts are Throwing this EventID?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Accounts%20are%20Throwing%20this%20EventID%3F.kql)

<br/><br/>

## 🔧 Line-by-Line Breakdown

### 1️⃣ SecurityEvent

This selects the SecurityEvent table, which contains Windows Security Log data collected from systems such as domain controllers, file servers, and workstations.

`Event ID` `4663` specifically relates to object access attempts (e.g., **files, folders, registry keys**), making it a common source of high-volume noise in environments with broad auditing enabled.

<br/>

### 2️⃣ `| where EventID == 4663`

This filters the dataset to only Event ID 4663. <br/>
By isolating a single EventID:
- You remove unrelated noise
- Narrow the investigation scope
- Make it easier to attribute behavior to specific actors

>⚔️ This line assumes you’ve already identified 4663 as a high-volume or high-interest event worth investigating further.

<br/>

### 3️⃣ summarize count() by Account

This groups all 4663 events by Account and counts how many times each account triggered the event. <br/>
The result highlights:
- Users accessing large numbers of objects
- Service accounts performing bulk operations
- Potential misconfigurations or runaway processes

>🔍 In many cases, you’ll see a small number of accounts responsible for the majority of the volume.

<br/>

### 4️⃣ render columnchart

This renders the summarized results as a column chart, making high-volume accounts immediately visible, like...
- Each column represents an account
- Taller columns indicate heavier activity
- Outliers stand out at a glance

>🔧 This visualization is especially useful when presenting findings or deciding where to focus remediation or tuning efforts.

<br/>

### 🤔 How to Use It

Replace `4662` with the noisy Event ID you found in **Query #1**, then run the query (in our example we'll use  `4663`). You’ll get a visualization of which accounts are responsible for the most of that event.

Once you identify the top accounts generating Event ID 4663, you can:
- Determine whether the activity is expected or excessive
- Identify service accounts that may need narrower permissions
- Tune auditing policies to reduce unnecessary noise
- Exclude known-benign accounts from alerting logic
- Quantify potential Sentinel ingest cost impact

<br/>

For example:
| Account		   			| Count		|
|---------------------------|-----------|
| domain\DevSecOpsDad	    | 12,350 	|
| domain\PhishingPharoah$	| 8,710		|
| domain\SecuritySultan   	| 6,204		|
| ...			   			| ...		|
| ...			   			| ...		|

<br/>

If one account is way above the rest, that could be:
- A high-traffic service account you expected
- A misconfigured script
- A potential security issue worth investigating

<br/>

# 🖥️ Query #3 — Bonus: Which Devices Are Driving the Noise?

Sometimes the problem isn’t who — it’s where. This query answers a simple but powerful question: “Which computers are generating the most of Event ID 4663?” <br/>
> 4663 = An attempt was made to access an object — commonly used for file/folder auditing noise-hunting and investigation.)

```kql
SecurityEvent                     // <--Define the table to query
| where EventID == 4663           // <--Declare which EventID you're looking for
| summarize count() by Computer   // <--Show how many times that EventID was thrown per device
| sort by count_ desc             // <-- Sort by heaviest hitters first
| render columnchart              // <--Optional, but helps quickly visualize potential outliers
```

![](/assets//img/KQL%20Toolbox/3/3Query3_nochart.png)

[**🔗  KQL Toolbox #3 — Which Devices are Spamming this EventID?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Devices%20are%20Throwing%20this%20EventID%3F.kql)

<br/><br/> 

### 🔧 Line-by-Line Breakdown

- `SecurityEvent` --> This is the Windows Security Event Log table (from Windows event forwarding, AMA, MMA, etc.). If you’re ingesting classic Windows Security logs into Sentinel, this is usually where they land.

- `| where EventID == "4663"` --> Filters the dataset down to only Event ID 4663 events.

	- >⚠️ Note: In many workspaces, EventID is stored as a number (int), not a string: _so **EventID == 4663** is often safer than **"4663"**._

- `| summarize count() by Computer` --> Counts how many matching events each device generated, then groups by the Computer field. This instantly exposes your “loudest” devices for that specific event.

- `sort by count_ desc` --> Orders the results from highest to lowest based on the event count calculated in the summarize step (the `count_` column is automatically generated by KQL when you use `summarize count()`). Sorting in descending (desc) order ensures the noisiest devices rise to the top, making problem systems immediately obvious without scanning the entire result set.

- `| render columnchart` --> Turns the results into a quick visual bar chart so the outliers jump out immediately.

![](/assets/img/KQL%20Toolbox/3/3Query3_chart.png)

[**🔗  KQL Toolbox #3 — Which Devices are Spamming this EventID?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Devices%20are%20Throwing%20this%20EventID%3F.kql)

<br/><br/>

# ✅ What these queries are good for

Taken together, the four queries in KQL Toolbox #3 form a progressive noise-hunting workflow — moving from “what’s loud?” to “who and what is causing it?”.

They’re particularly effective for: <br/><br/>
**Noise hunting at scale**
- Quickly identify which Event IDs, endpoints, and accounts are responsible for the majority of Windows Security Event volume — without manually digging through raw logs.

<br/>

**Sentinel cost triage** <br/>
- Once a noisy or expensive Event ID is identified, these queries help you pinpoint exactly where the volume is coming from, which is often just a handful of servers, services, or users driving disproportionate ingest cost.

**Misconfiguration detection**
- Consistent high-volume events (especially Event ID 4663) frequently reveal:
    - Overly broad auditing on hot file shares
    - Service or application accounts touching massive numbers of objects
    - GPO audit policies applied too widely across the environment

**Safe tuning and scoping decisions**
- By breaking noise down by `Event ID` → `device` → `account`, you gain the confidence needed to tune auditing, analytics rules, or data collection — _without blindly suppressing potentially valuable security signal._

>💡Investigation pivot: These queries are intentionally designed to chain together. Once you identify the loudest Event ID, you can pivot to the noisiest device, then to the accounts generating the activity — and finally down to the files, paths, or access types responsible for the volume.

<br/><br/>

# 🧩 Putting It Together: A Simple Weekly Workflow
Here’s how this query fits into a repeatable SOC hygiene loop:

- **1.)** Identify expensive tables --> KQL Toolbox #1

- **2.)** Identify noisiest log sources --> KQL Toolbox #2

- **3.)** Identify top Event IDs --> This article / KQL Toolbox #3

- **4.)** Attribute noise to users and systems

- **5.)** Decide action
	- Tune logging
	- Suppress detections
	- Investigate behavior
	- Reduce ingest cost

- **6.)** Re-run monthly to validate improvements

<br/>

>_⚡This is a lightweight but powerful way to go from **macro-noise patterns** to **micro-actionables** in minutes._

<br/>

![](/assets/img/KQL%20Toolbox/3/NinjaCatAnalyst3.png)

<br/><br/>

# 💡 Bonus Tips & Guardrails (Quick Hits)

A few advanced considerations to keep in mind as you work through the queries above: 
- **Target the right noise** --> Authentication-related Event IDs can often be refined further using logon type or success/failure filters.
- **Pair noise with cost** --> When you correlate noisy Event IDs with ingest cost (from KQL Toolbox #1 and #2), it becomes much easier to prioritize tuning that actually reduces spend.
- **Alert _thoughtfully**_ --> Spikes above a normal baseline can be alert-worthy — but only after you understand what “normal” looks like in your environment.
- **Context matters** --> High event volume alone doesn’t imply malicious activity. Always validate against expected behavior before tuning or suppressing data.

<br/>

>💡 The next section expands on these tips with concrete examples, best practices, and common pitfalls to avoid when tuning or alerting on Event ID noise. 👇


<br/><br/>

# 🚨 Alerting on Event ID Noise Using Baselines

Once you’ve identified your noisiest Event IDs, the real power move is to stop reacting and start detecting change. Instead of alerting on raw volume (which creates noise), we alert on deviation from baseline.

The goal:
“Alert me when an Event ID suddenly gets louder than normal.”

### 🧠 Baseline Strategy (High Level)

We’ll use:

- A historical baseline window (e.g., last 30 days)
- A recent comparison window (e.g., last 24 hours)
- A multiplier threshold (e.g., 2× normal)

This avoids static thresholds and adapts automatically to each environment.

### 🔍 Step 1: Build a Baseline for Event ID Frequency

This query calculates the average daily count for each Event ID over the last 30 days.

```kql
let BaselineWindow = 30d;
SecurityEvent
| where TimeGenerated > ago(BaselineWindow)
| summarize DailyCount = count() by EventID, Day = bin(TimeGenerated, 1d)
| summarize AvgDailyCount = avg(DailyCount) by EventID
```
What this gives you

- A rolling normal activity baseline
- One row per Event ID
- No assumptions about “good” or “bad” events

### 🔎 Step 2: Measure Recent Activity

Now we calculate recent volume (last 24 hours).

```kql
let RecentWindow = 1d;
SecurityEvent
| where TimeGenerated > ago(RecentWindow)
| summarize RecentCount = count() by EventID
```

### 🔗 Step 3: Compare Recent Activity vs Baseline

This is where the magic happens. Let's establish a 90-day “normal” baseline for each Event ID, compare it to the last 30 days, and flag Event IDs whose recent volume is ≥ 2× their typical daily activity.

```kql
let BaselineWindow = 90d;
let RecentWindow = 30d;
let ThresholdMultiplier = 2.0;
let Baseline =
    SecurityEvent
    | where TimeGenerated > ago(BaselineWindow)
    | summarize DailyCount = count() by EventID, Day = bin(TimeGenerated, 1d)
    | summarize AvgDailyCount = round(avg(DailyCount),2) by EventID;
let Recent =
    SecurityEvent
    | where TimeGenerated > ago(RecentWindow)
    | summarize RecentCount = count() by EventID;
Baseline
| join kind=inner Recent on EventID
| extend DeviationRatio = round(RecentCount / AvgDailyCount, 2)
| where DeviationRatio >= ThresholdMultiplier
| project EventID, AvgDailyCount, RecentCount, DeviationRatio
| take 10
| sort by DeviationRatio desc
```

![](/assets/img/KQL%20Toolbox/3/3Weird.png)

[**🔗 KQL Toolbox #3 — Which EventID's are Suddently Acting Weird?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Event%20IDs%20Are%20Suddenly%20Acting%20Weird%3F.kql)

<br/><br/>

### 🔧 Line-by-line breakdown

`let BaselineWindow = 90d;` -->  Defines how far back to look when calculating “normal” behavior. Here, your baseline is the last 90 days.

`let RecentWindow = 30d;` --> Defines the “recent” comparison window. Here, the query compares against the last 30 days of activity.

`let ThresholdMultiplier = 2.0;` --> Sets the “spike” threshold. Any Event ID whose recent activity is 2× or greater than its baseline average gets flagged.

`let Baseline = SecurityEvent` --> Creates a reusable dataset named Baseline starting from the SecurityEvent table (Windows Security logs ingested into Sentinel / Log Analytics).

`| where TimeGenerated > ago(BaselineWindow)` --> Limits baseline data to only the last 90 days (based on BaselineWindow).

`| summarize DailyCount = count() by EventID, Day = bin(TimeGenerated, 1d)` --> Counts how many times each EventID appears per day, by:
- grouping on EventID
- grouping on a daily time bucket (bin(TimeGenerated, 1d))
- storing the result as DailyCount

`| summarize AvgDailyCount = round(avg(DailyCount),2) by EventID;` --> Takes those daily counts and calculates the average events per day for each Event ID across the 90-day baseline. `round(..., 2)` keeps the baseline average readable.

`let Recent = SecurityEvent` --> Creates a second reusable dataset named Recent, again using the SecurityEvent table.

`| where TimeGenerated > ago(RecentWindow)` --> Limits this dataset to only the last 30 days.

`| summarize RecentCount = count() by EventID;` --> Counts total occurrences of each EventID within the recent window and stores it as RecentCount.

`Baseline`
`| join kind=inner Recent on EventID` --> Joins the baseline results to the recent results using EventID as the key:

- `kind=inner` --> means only Event IDs present in both datasets will be returned.

- `| extend DeviationRatio = round(RecentCount / AvgDailyCount, 2)` --> creates a new calculated field showing how far the recent count deviates from baseline average.

A value of:
- 1.0 ≈ normal
- 2.0 = about 2× baseline
- 5.0 = about 5× baseline

> (Note: this is comparing “30-day total” to “average per day,” so the ratio is a practical “loudness score,” not a strict per-day-to-per-day comparison.)

`| where DeviationRatio >= ThresholdMultiplier` --> Filters to only those Event IDs whose deviation ratio meets/exceeds your threshold (default 2×).

`| project EventID, AvgDailyCount, RecentCount, DeviationRatio` --> Selects the exact columns you want in the output (clean, readable results).

`| take 10` --> Limits the output to 10 rows (often used to keep dashboards fast / results short).

`| sort by DeviationRatio desc` --> Sorts the final results so the biggest spikes appear at the top.

<br/><br/>

### 📊 How to Interpret the Results

| Column			| Meaning				  |
| ----------------- | ----------------------- |
|EventID			| The event that changed  |
|AvgDailyCount   	| Normal daily behavior   |
|RecentCount		| What happened recently  |
|DeviationRatio		| How much louder it got  |

<br/>

Example:
- AvgDailyCount = 5,000
- RecentCount = 15,000
- DeviationRatio = 3.0

👉 This Event ID is 3× louder than normal → investigate.

<br/><br/>

# 🚨 Turning This into a Sentinel Alert

### Recommended Alert Configuration

**Analytics Rule Type**
- 📌 Scheduled query rule

**Query Schedule**
- Run every: 1 hour
- Lookup data from: Last 1 hour
	- (Baseline window is already embedded in the query)

**Alert Threshold**
- Trigger if results > 0

**Entity Mapping**
- Map EventID → Custom entity (or string)
- Severity Guidance
- DeviationRatio >= 5 → High
- DeviationRatio >= 3 → Medium
- DeviationRatio >= 2 → Low

### 🛠️ Pro Tips:
- ✅ Exclude Known “Always Noisy” Event IDs: `| where EventID !in ("4624", "4625")`
- ✅ Scope to a Single Event ID (Targeted Alert) — Perfect for things like 4663 or 4688: `| where EventID == "4663"`
- ✅ Attribute Noise Automatically (`Account` / `Device`)
	- Add this at the end of the above query:

```kql
| join (
    SecurityEvent
    | where TimeGenerated > ago(RecentWindow)
    | summarize count() by EventID, Account, Computer
) on EventID
```

👉 Now your alert says: **“Event ID 4663 spiked 3.8× — driven by SERVICE-SQL on FILESRV01”** for example.

![](/assets/img/KQL%20Toolbox/3/3Weird2.png)

 [**🔗 KQL Toolbox #3 — Which EventID's are Suddently Acting Weird?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Event%20IDs%20Are%20Suddenly%20Acting%20Weird%3F.kql)

<br/><br/>

### ⚠️Stuff to watch out for!
- ❌ Alerting on raw counts
- ❌ No baseline window
- ❌ Ignoring expected maintenance windows
- ❌ Treating all Event IDs equally

_**This approach avoids all four.**_

Static thresholds create noise. Baselines create signal. Once you alert on change, not volume, your SOC matures instantly.

<br/>

![](/assets/img/KQL%20Toolbox/3/Query3.png)

<br/><br/>

# 🎁 Wrap-Up & Final Thoughts
Two simple queries. One powerful insight loop:
- Find the loudest Event ID
- See which accounts or devices are driving it
- Adjust collection, alerting, or investigation focus accordingly

> _**Cost visibility** tells you where your **money goes.** Noise analysis tells you where your **attention should go**._

When you combine both, you build a **leaner, clearer, more effective SOC.**

<br/>

### 👉 Stay curious, stay efficient, and keep those logs both loud and useful. 📊🔍💪

<br/><br/>

# 📚 Want to Go Deeper?

⚡ If you like this kind of **practical KQL + cost-tuning** content, keep an eye on the **DevSecOpsDad KQL Toolbox** series—and if you want the bigger picture across Defender, Sentinel, and Entra, my book *Ultimate Microsoft XDR for Full Spectrum Cyber Defense* goes even deeper with real-world examples, detections, and automation patterns.
&#128591; Huge thanks to everyone who’s already picked up a copy — and if you’ve read it, a quick review on Amazon goes a long way!

![Ultimate Microsoft XDR for Full Spectrum Cyber Defense](/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg)



<br/><br/>

# 🔗 Helpful Links & Resources
- [⚡Which EventID fires the most in a month?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20EventID%20fires%20the%20most%20in%20a%20month%3F.kql)
- [⚡Which Accounts are throwing this EventID?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Accounts%20are%20Throwing%20this%20EventID%3F.kql)



<br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)
