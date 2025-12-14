# 💡 KQL Toolbox #3 — Which Event ID Noises Up Your Logs (and Who’s Causing It)?
**Welcome back to the DevSecOpsDad KQL Toolbox series!** In the last entry (KQL Toolbox #2), we zoomed in on log source cost drivers—using `_IsBillable` and `_BilledSize` to identify which tables, severities, and Event IDs were burning the most money in Microsoft Sentinel. If you missed that one, you can read it here: 👉 [KQL Tip of the Week #2 — Identify Your Top Talkers by Cost](INSERT HERE)

### This week, we’re building directly on that foundation...
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

💾 Full queries are in the public repo:
- [🔗 Which EventID fires the most in a month?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20EventID%20fires%20the%20most%20in%20a%20month%3F.kql)
- [🔗 Which Accounts are throwing this EventID?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Accounts%20are%20Throwing%20this%20EventID%3F.kql)

<br/> 

### 🔍 Why This Matters

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

👉 [**KQL Toolbox #3 — Which EventID fires the most in a month?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20EventID%20fires%20the%20most%20in%20a%20month%3F.kql)

<br/><br/>

### 🔧 Line-by-Line Breakdown

- `where EventID == 4663` --> Focuses the analysis on one known noisy event.

- `summarize count() by Account` --> Shows which identities are responsible for generating the most events.

- `sort by count_ desc` --> Surfaces the heaviest contributors immediately.

- `take 10` --> Keeps the output actionable and readable.

- `render columnchart` --> Highlights disproportionate contributors visually.

<br/><br/>

### 🔎 What You’re Looking For

When you run this query:
- You’ll get a chart of Event IDs ranked by how often they happened in the last 30 days.
- The biggest bars are your “noisiest” events.
- Typical suspects often include event-log-heavy IDs like 4624, 4625, 5156, etc., depending on your environment.

This gives you a quick look at what’s dominating your security log volume.

>💡 Tip: If you’ve already been tracking ingest costs with last week’s queries, overlay this with Table + Cost ranking and you can start connecting “noise” with “dollars.”

# 📊 What the Results Tell You

This output answers one critical question: “What Event IDs dominate my SecurityEvent volume?”

Common examples you’ll often see:
- 4624 – Successful logons
- 4625 – Failed logons
- 4663 – Object access attempts
- 5156 – Windows Filtering Platform traffic

_**High frequency** alone doesn’t mean **“bad”** — but it **does** tell you where to **look next**._

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

👉 [**KQL Toolbox #3 — Which Accounts are Throwing this EventID?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Accounts%20are%20Throwing%20this%20EventID%3F.kql)

<br/><br/>

### 🔧 Line-by-Line Breakdown

- `where EventID == 4663` --> Focuses the analysis on one known noisy event.

- `summarize count() by Account` --> Shows which identities are responsible for generating the most events.

- `sort by count_ desc` --> Surfaces the heaviest contributors immediately.

- `take 10` --> Keeps the output actionable and readable.

- `render columnchart` --> Highlights disproportionate contributors visually.

<br/><br/>

# 🛠️ How to Use It

Replace `4662` with the noisy Event ID you found in **Query #1**, then run the query (in our example we'll use  `4663`). You’ll get a visualization of which accounts are responsible for the most of that event.

This query helps answer:
- Is this noise caused by a service account?
- Is a single user or system behaving abnormally?
- Is an application hammering file or registry access?
- Does this align with expected business behavior?

From here, you can:
- Tune auditing policies
- Exclude unnecessary events
- Refine detections
- Investigate suspicious behavior

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

<br/><br/>

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

👉 [**KQL Toolbox #3 — Which Devices are Spamming this EventID?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Devices%20are%20Throwing%20this%20EventID%3F.kql)

<br/><br/> 

### 🔧 Line-by-Line Breakdown

- `SecurityEvent` --> This is the Windows Security Event Log table (from Windows event forwarding, AMA, MMA, etc.). If you’re ingesting classic Windows Security logs into Sentinel, this is usually where they land.

- `| where EventID == "4663"` --> Filters the dataset down to only Event ID 4663 events.

	- >⚠️ Note: In many workspaces, EventID is stored as a number (int), not a string: _so **EventID == 4663** is often safer than **"4663"**._

- `| summarize count() by Computer` --> Counts how many matching events each device generated, then groups by the Computer field. This instantly exposes your “loudest” devices for that specific event.

- `sort by count_ desc` --> Orders the results from highest to lowest based on the event count calculated in the summarize step (the `count_` column is automatically generated by KQL when you use `summarize count()`). Sorting in descending (desc) order ensures the noisiest devices rise to the top, making problem systems immediately obvious without scanning the entire result set.

- `| render columnchart` --> Turns the results into a quick visual bar chart so the outliers jump out immediately.

![](/assets/img/KQL%20Toolbox/3/3Query3_chart.png)

<br/><br/>

This is especially useful for:
- Legacy servers
- Misconfigured endpoints
- File servers or domain controllers
- Systems with runaway logging


<br/><br/>

# ✅ What these queries are good for

- Noise hunting: Find the one (or few) endpoints generating the bulk of a specific Windows audit event.
- Cost triage: If you already know a certain Event ID is expensive/noisy, this shows where to focus first (often a handful of servers).
- Misconfiguration detection: A workstation or server spamming 4663 can point to:
- overly-broad auditing on a hot file share
- an application account touching tons of objects
- a GPO audit policy applied too broadly

>💡Investigation pivot: Once you find the loudest device, you can drill into which accounts, which files, and what access types are generating the volume.

<br/><br/>

# 🧩 Putting It Together: A Simple Weekly Workflow
Here’s how this query fits into a repeatable SOC hygiene loop:

- 1.) Identify expensive tables --> (Toolbox #1)

- 2.) Identify noisiest log sources --> (Toolbox #2)

- 3.) Identify top Event IDs --> (This article)

- 4.) Attribute noise to users and systems

- 5.) Decide action
	- Tune logging
	- Suppress detections
	- Investigate behavior
	- Reduce ingest cost

- 6.) Re-run monthly to validate improvements

<br/>

>_⚡This is a lightweight but powerful way to go from **macro-noise patterns** to **micro-actionables** in minutes._

<br/>

![](/assets/img/KQL%20Toolbox/3/NinjaCatAnalyst3.png)

<br/><br/>

# 💡 Bonus Tips
🔦 Filter by Logon Type <br/>
If you’re focusing on authentication noise, you can enhance Query #1 with filters on logon type or status (success vs failure).

<br/>

⚡ Combine With Cost Analytics <br/>
Remember the queries from **KQL Toolbox #1 and #2**? Overlaying Event ID noise with ingest cost helps you:
- Spot expensive noise that you can reduce
- Prioritize tuning where it saves real $$

<br/>

🚨 Alerting <br/>
If a specific Event ID spikes above its baseline frequency, you can attach a metric alert in Sentinel and get notified.


<br/><br/>

# ⚠️ Best Practices & Gotchas

- **High frequency ≠ malicious** --> _Always validate against expected behavior._

- **Avoid over-filtering** --> _Don’t blindly suppress Event IDs without understanding downstream detections._

- **Filter early for performance** --> _Time filters should always appear early in your query._

- **Baseline before alerting** --> _Establish “normal” before creating thresholds._

<br/>

![](/assets/img/KQL%20Toolbox/3/Query3.png)

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

This is where the magic happens.

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

👉 [**KQL Toolbox #3 — Which EventID's are Suddently Acting Weird?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Event%20IDs%20Are%20Suddenly%20Acting%20Weird%3F.kql)

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

<br/><br/>

### ⚠️Stuff to watch out for!
- ❌ Alerting on raw counts
- ❌ No baseline window
- ❌ Ignoring expected maintenance windows
- ❌ Treating all Event IDs equally

_**This approach avoids all four.**_

Static thresholds create noise. Baselines create signal. Once you alert on change, not volume, your SOC matures instantly.

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
