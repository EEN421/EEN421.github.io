# 💡 KQL Toolbox #3 — Which Event ID Noises Up Your Logs (and Who’s Causing It)?
**Welcome back to the DevSecOpsDad KQL Toolbox series!** In the last entry (KQL Toolbox #2), we zoomed in on log source cost drivers—using `_IsBillable` and `_BilledSize` to identify which tables, severities, and Event IDs were burning the most money in Microsoft Sentinel. If you missed that one, you can read it here: 👉 [KQL Tip of the Week #2 — Identify Your Top Talkers by Cost](INSERT HERE)

### This week, we’re building directly on that foundation...
Because once you know which **log sources** and which **Event IDs** are the _most expensive_, the very next question becomes:
> “Okay… but which Event ID fires the most often, and which accounts are responsible for generating it?”

This is where today’s KQL shines 🌞

Instead of looking at cost, we shift focus to raw event frequency—a metric that drives both noise and cost. With two short KQL queries, you’ll identify:
- Which Event ID fires most in your environment over the last 30 days, and
- Which accounts are generating that Event ID the most

This gives you a clean, fast workflow for spotting noisy Event IDs, isolating misconfigured or anomalous accounts, and tightening both your detection logic and cost posture. With that, let’s jump into this week’s analysis...

<br/>

![](/assets/img/KQL%20Toolbox/3/DevSecSignal.png)

<br/><br/>

# 🔊 Today's KQL helps you spot the loudest Event ID in your environment — and then drill down into which accounts are responsible for firing it most often.

These queries are perfect for your weekly cost-noise correlation checks, operational hygiene reviews, or threat hunting warmups.

💾 Full queries are in the public repo:
- [🔗 Which EventID fires the most in a month?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20EventID%20fires%20the%20most%20in%20a%20month%3F.kql_)
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
SecurityEvent
| where TimeGenerated > ago(30d)
| summarize count() by EventID
| render columnchart
```

![](/assets/img/KQL%20Toolbox/3/3kql1.png)

👉 [**KQL Toolbox #3 — Which EventID fires the most in a month?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20EventID%20fires%20the%20most%20in%20a%20month%3F.kql)

<br/><br/>

### 🔎 What You’re Looking For

When you run this query:
- You’ll get a chart of Event IDs ranked by how often they happened in the last 30 days.
- The biggest bars are your “noisiest” events.
- Typical suspects often include event-log-heavy IDs like 4624, 4625, 5156, etc., depending on your environment.

This gives you a quick look at what’s dominating your security log volume.

>💡 Tip: If you’ve already been tracking ingest costs with last week’s queries, overlay this with Table + Cost ranking and you can start connecting “noise” with “dollars.”

<br/><br/>

# 👤 Query #2 — Which Accounts Are Throwing This Event ID?

So you found the loudest Event ID. Now let’s see who’s generating it. This second query takes a specific Event ID (in this example **4663**) and counts how many times each account triggered it.

```kql
// Which Accounts are throwing this EventID?
SecurityEvent
| where EventID == "4663"
| summarize count() by Account
| render columnchart
```

![](/assets/img/KQL%20Toolbox/3/3kql2.png)

👉 [**KQL Toolbox #3 — Which Accounts are Throwing this EventID?**](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Accounts%20are%20Throwing%20this%20EventID%3F.kql)

<br/><br/>

# 🛠️ How to Use It

Replace `4662` with the noisy Event ID you found in **Query #1**, then run the query (in our example we'll use  `4663`). You’ll get a visualization of which accounts are responsible for the most of that event.

This is incredibly useful to:
- Spot compromised or misconfigured accounts
- Find noisy service accounts
- Detect unusual authentication or access patterns

<br/>

For example:
| Account		   			| Count		|
|---------------------------|------------|
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

# 🧩 Putting It Together: A Simple Weekly Workflow
Here’s a pattern you can run every week to keep tabs on log noise and potential issues:
- **Run Query #1** — See which Event ID fired the most in the last month.
	- Pick the Top Culprit — This is your “Event of Interest.”

<br/>

- **Run Query #2** — Feed that Event ID into the accounts query.
	- Investigate Outliers — Accounts with unusually high counts might need attention.

<br/>

This is a lightweight but powerful way to go from macro noise patterns to micro actionables in minutes.

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

<br/>

![](/assets/img/KQL%20Toolbox/3/Query3.png)


<br/><br/>

# 🎁 Wrap-Up
Two simple queries. One powerful insight loop:
- Find the loudest Event ID
- See which accounts are driving it
- Adjust collection, alerting, or investigation focus accordingly

<br/>

### 👉 Stay curious, stay efficient, and keep those logs both loud and useful. 📊🔍💪

<br/><br/>

# 📚 Want to Go Deeper?

⚡ If you like this kind of **practical KQL + cost-tuning** content, keep an eye on the **KQL Query of the Week** series—and if you want the bigger picture across Defender, Sentinel, and Entra, my book *Ultimate Microsoft XDR for Full Spectrum Cyber Defense* goes even deeper with real-world examples, detections, and automation patterns.
&#128591; Huge thanks to everyone who’s already picked up a copy — and if you’ve read it, a quick review on Amazon goes a long way!

![Ultimate Microsoft XDR for Full Spectrum Cyber Defense](/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg)



<br/><br/>

# 🔗 Helpful Links & Resources
- [⚡Which EventID fires the most in a month?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20EventID%20fires%20the%20most%20in%20a%20month%3F.kql_)
- [⚡Which Accounts are throwing this EventID?](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Accounts%20are%20Throwing%20this%20EventID%3F.kql)



<br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)