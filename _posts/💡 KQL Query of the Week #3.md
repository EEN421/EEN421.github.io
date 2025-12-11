# 💡 KQL Query of the Week #3 — Which Event ID Noises Up Your Logs (and Who’s Causing It)?
Welcome back to the KQL Query of the Week series! In last week’s entry (KQL Tip of the Week #2), we zoomed in on log source cost drivers—using _IsBillable and _BilledSize to identify which tables, severities, and Event IDs were burning the most money in Microsoft Sentinel. If you missed that one, you can read it here: 👉 [KQL Tip of the Week #2 — Identify Your Top Talkers by Cost](INSERT HERE)

### This week, we’re building directly on that foundation
Because once you know which log sources and which Event IDs are the most expensive, the very next question becomes:
> “Okay… but which Event ID fires the most often, and which accounts are responsible for generating it?”

This is where today’s paired queries shine. 🌞

Instead of looking at cost, we shift focus to raw event frequency—a metric that drives both noise and cost. With two short KQL queries, you’ll identify:
- Which Event ID fires most in your environment over the last 30 days, and
- Which accounts are generating that Event ID the most

This gives you a clean, fast workflow for spotting noisy Event IDs, isolating misconfigured or anomalous accounts, and tightening both your detection logic and cost posture. With that, let’s jump into this week’s analysis...



# 👉 This week’s pair of KQL queries helps you spot the loudest Event ID in your environment — and then drill down into which accounts are responsible for firing it most often.

These queries are perfect for your weekly cost-noise correlation checks, operational hygiene reviews, or threat hunting warmups.

💾 Full queries are in the public repo:

Which EventID fires the most in a month?

Which Accounts are throwing this EventID?

🔍 Why This Matters

In most orgs, a handful of Event IDs generate most of the volume in SecurityEvent — and those high-frequency IDs can:

Inflate your ingest costs

Obscure real signals from the noise

Make detection rules less efficient

Hide suspicious behavior behind mountains of normal activity

So step one is simple:

Find the Event ID that fires most often — then look at who’s actually triggering it.

That’s exactly what this week’s queries do.

📈 Query #1 — Which Event ID Fires the Most in the Last Month?

This query counts all SecurityEvent occurrences in the last 30 days and ranks Event IDs by frequency. No filters, no cost calculations — just the raw noise metric.

// Which EventID fires the most in a month?
SecurityEvent
| where TimeGenerated > ago(30d)
| summarize count() by EventID
| render columnchart


Source: GitHub query text 
GitHub

🧠 What You’re Looking For

When you run this query:

You’ll get a chart of Event IDs ranked by how often they happened in the last 30 days.

The biggest bars are your “noisiest” events.

Typical suspects often include event-log-heavy IDs like 4624, 4625, 5156, etc., depending on your environment.

This gives you a quick look at what’s dominating your security log volume.

💡 Tip: If you’ve already been tracking ingest costs with last week’s queries, overlay this with Table + Cost ranking and you can start connecting “noise” with “dollars.”

👤 Query #2 — Which Accounts Are Throwing This Event ID?

So you found the loudest Event ID. Now let’s see who’s generating it.

This second query takes a specific Event ID (in this example 4662) and counts how many times each account triggered it.

// Which Accounts are throwing this EventID?
SecurityEvent
| where EventID == "4662"
| summarize count() by Account
| render columnchart


Source: GitHub query text 
GitHub

🔍 How to Use It

Replace "4662" with the noisy Event ID you found in Query #1.

Run the query.

You’ll get a visualization of which accounts are responsible for the most of that event.

This is incredibly useful to:

Spot compromised or misconfigured accounts

Find noisy service accounts

Detect unusual authentication or access patterns

For example:

Account	Count
svc-backup	12,350
jdoe@contoso.com
	8,710
workstation01$	6,204
...	...

If one account is way above the rest, that could be:

A high-traffic service account you expected

A misconfigured script

A potential security issue worth investigating

🧩 Putting It Together: A Simple Weekly Workflow

Here’s a pattern you can run every week to keep tabs on log noise and potential issues:

Run Query #1 — See which Event ID fired the most in the last month.

Pick the Top Culprit — This is your “Event of Interest.”

Run Query #2 — Feed that Event ID into the accounts query.

Investigate Outliers — Accounts with unusually high counts might need attention.

This is a lightweight but powerful way to go from macro noise patterns to micro actionables in minutes.

🥅 Bonus Tips
📌 Filter by Logon Type

If you’re focusing on authentication noise, you can enhance Query #1 with filters on logon type or status (success vs failure).

📌 Combine With Cost Analytics

Remember the queries from Weeks #1 and #2?
Overlaying Event ID noise with ingest cost helps you:

Spot expensive noise that you can reduce

Prioritize tuning where it saves real $$

📌 Alerting

If a specific Event ID spikes above its baseline frequency, you can attach a metric alert in Sentinel and get notified.

🛠 Wrap-Up

Two simple queries.
One powerful insight loop:

Find the loudest Event ID

See which accounts are driving it

Adjust collection, alerting, or investigation focus accordingly

And as always—if you want to keep digging deeper into real-world Sentinel analytics, let me know and I’ll help you build that next automation or optimization!

Stay curious, stay efficient, and keep those logs both loud and useful. 📊🔍💪
