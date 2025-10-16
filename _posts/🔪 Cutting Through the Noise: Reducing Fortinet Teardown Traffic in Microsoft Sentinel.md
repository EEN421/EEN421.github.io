In the modern SOC, more data isn’t always better data. When you connect a Fortinet firewall to Microsoft Sentinel for full-spectrum visibility, the first thing you notice is… the noise. Specifically: **connection teardown events** — hundreds of thousands of them.

At first glance, they look harmless — just logs marking the end of a session. But once you start scaling Sentinel ingestion, those teardown logs quietly turn into the digital equivalent of background static: expensive, repetitive, and rarely helpful from a security perspective. _**Every log you ingest should earn its place** by delivering detection value or investigation value — and Fortinet teardown traffic fails that test._

This post breaks down what I've learned about Data Collection Rules (DCRs), Fortinet logs, and how to tune them to keep the signal — without paying for the noise.

---

In this Post We Will:
- &#x1F50E; Identify low-value teardown events using KQL.
- 🔧 Convert that query into a Data Collection Rule (DCR) transformation that stops them before ingestion.
- 🧠 Understand the “Detection vs. Investigation Value” framework — and why teardown logs don’t make the cut.
- &#x02620; Avoid the gotchas that cause DCRs to silently fail.

---

## 🔍 The Problem: Too Much Teardown, Too Little Value

In Fortinet network traffic logs, every connection generates *two* major events:

1. **Connection standup** — when a new session is created (`traffic:forward start`)
2. **Connection teardown** — when the session closes (`traffic:forward close`, `client-fin`, `server-fin`, etc.)

Multiply that by thousands of clients and microservices, and teardown events quickly dominate your ingestion stream.

## 🧠 Detection versus Investigation Value Breakdown

Before diving into KQL and JSON, it’s worth defining what “value” means in a logging context; I like to break down logs into 2 categories that either provide Detection Value or Investigation value:

- **Detection Value** helps us detect and mitigate malicious behaviour in it's tracks. Example: A DeviceFileEvents record showing an unsigned executable dropped into a startup folder. _That’s actionable — it can trigger a rule, block an action, or enrich an alert._ Another example: * When malware calls home, the **standup log** shows the destination C2 domain — *that’s actionable*.
  
- **Investigation Value** may not help us detect and stop a malicious act, but it's the first thing the DFIR team asks for during a post-breach investigation and helps reconstruct what happened after a compromise. Example: VPN session duration or DNS lookup history. _It doesn’t detect the attack, but it helps the DFIR team trace lateral movement and data exfiltration._ Additional examples: When a lateral movement connection is opened, the **standup log** shows source → target — _that’s valuable for threat hunting._ But when the connection closes? _The teardown event just repeats the tuple and says “we’re done here.”_

- By the time teardown traffic is written, the attacker’s action already happened.
In short/TLDR: teardown = bookkeeping, not detection.

With that framing, Fortinet teardown traffic sits firmly in the “no value” zone:

- It offers no detection value — by the time a connection teardown happens, the event is already over.

- It offers minimal investigation value, because a teardown only confirms what a “session start” already implied: that a connection eventually closed.

- The network standup (session start) logs already include source, destination, port, protocol, duration, and bytes — all you need for forensic reconstruction.

What it does add:

- **Noise and cost** — these logs inflate ingestion with no added visibility.

Unless you’re in a niche scenario like analyzing abnormal session terminations (e.g., repeated client-RSTs indicating a DDoS condition or proxy instability), teardown logs add noise, not insight.

That’s when I stepped back and asked: *do teardown logs really help us detect or respond to threats faster?* The answer was a resounding "No" the more I thought about it. 

---

## 🔧 The Fix: Filter the Noise, Keep the Signal

I refine my Sentinel ingestion rules using **KQL-based filters** that exclude teardown-only messages while retaining high-value network telemetry.

Here’s the core Fortinet logic in KQL for the DCR rule. DCRs are pushed via JSON format so you can't just copy and paste the below KQL (even though it works in the Log blade) into the Transformation Editor; only simplified KQL works here because as a DCR it gets applied prior to ingestion, so many of the advanced functions such as Coalesce() will not work. You can copy this KQL into the **Log** blade in Sentinel to test:

```kql
source 
| where DeviceVendor == "Fortinet" or DeviceProduct startswith "Fortigate"  // Keep only Fortinet events; match explicit vendor name or products that start with “Fortigate”.
| extend tmpMsg = tostring(columnifexists("Message",""))    // Create a temp column from Message if it exists; otherwise default to empty string. columnifexists() prevents runtime errors when a column is missing.
| extend tmpAct = tostring(columnifexists("Activity",""))  // Same idea for the Activity field (some connectors use Activity instead of Message).
| extend tmpCombined = iff(isnotempty(tmpMsg), tmpMsg, tmpAct)  // Combine the two: prefer Message when it’s non-empty; otherwise fall back to Activity. iff() is KQL’s inline if; isnotempty() checks for null/blank.
// ------- Network teardown / close signals to EXCLUDE at ingest -------
| where tmpCombined !has "traffic:forward close"        // Exclude “forward” path closes (generic close). `has` is token-based, case-insensitive; good for structured text with clear word boundaries.
| where tmpCombined !has "traffic:forward client-rst"   // Exclude client-initiated resets on forward traffic.
| where tmpCombined !has "traffic:forward server-rst"   // Exclude server-initiated resets on forward traffic.
| where tmpCombined !has "traffic:forward timeout"      // Exclude idle/timeout closes on forward traffic.
| where tmpCombined !has "traffic:forward cancel"       // Exclude user/admin or system cancellations on forward traffic.
| where tmpCombined !has "traffic:forward client-fin"   // Exclude FIN-based client closes on forward traffic.
| where tmpCombined !has "traffic:forward server-fin"   // Exclude FIN-based server closes on forward traffic.
| where tmpCombined !has "traffic:local close"          // Exclude “local” (device-originated) generic close events.
| where tmpCombined !has "traffic:local client-rst"     // Exclude client resets on local traffic.
| where tmpCombined !has "traffic:local timeout"        // Exclude timeouts on local traffic.
| where tmpCombined !has "traffic:local server-rst"     // Exclude server resets on local traffic.
| project-away tmpMsg, tmpAct, tmpCombined              // Drop the temp helper columns so they don’t flow downstream or get stored.
```

Each line intentionally excludes teardown variants across both *forward* and *local* traffic types — while preserving **start**, **allow**, and **deny** events that matter for detection and compliance.

## ⚠️ Not every KQL function that works in Logs is allowed in DCR transformations.
**Transform queries run per record and only support a documented subset of operators and functions.** Microsoft’s “[Supported KQL features in Azure Monitor transformations](https://learn.microsoft.com/en-us/azure/azure-monitor/data-collection/data-collection-transformations-kql)” explicitly says that only the listed operators/functions are supported—and coalesce() isn’t on that list. In practice, that means queries relying on coalesce() (and a few other conveniences) will error or silently fail when placed in transformKql. 


Two key takeaways from the doc that matter here:

Per-record constraint: Transformations process one event at a time; anything that aggregates or isn’t in the “supported” set won’t run. 
Microsoft Learn

Allowed functions are explicit: If it’s not in the list, assume it’s unsupported in DCRs—even if it works fine in Log Analytics queries. (You will see iif, case, isnull, isnotnull, isnotempty, etc., but not coalesce.) 
Microsoft Learn

Another common snag when porting queries is using dynamic literals like ```kql dynamic({})```. In DCR transforms, prefer ```kql parse_json("{}")``` instead.

---

## 🧭 Key Takeaways for Other Security Teams

* **Don’t ingest everything.** More logs ≠ more visibility. Focus on what helps you detect and respond.
* **Teardown ≠ telemetry.** Those events tell you a connection *ended*, not that it was *malicious*.
* **Validate before excluding.** Always test filters with a quick `summarize count()` to ensure no legitimate security logs disappear.
* **Reinvest the savings.** Use your reduced ingestion costs to onboard richer data sources — endpoint, identity, or cloud app telemetry.

---

## ⚡ Ian's Insights

Noise reduction isn’t just about saving money — it’s about sharpening focus.
By filtering teardown traffic, we transformed our firewalls from noisy log generators into **high-value security signal providers**.

That’s the difference between drowning in data and acting on intelligence.

## 🔗 Helpful Links & Refences

- [Supported KQL features in Azure Monitor transformations — the canonical list (note coalesce() is absent; use iif/case/isnotempty instead).](https://learn.microsoft.com/en-us/azure/azure-monitor/data-collection/data-collection-transformations-kql)

- [Create a transformation in Azure Monitor — reiterates that only certain KQL is supported.](https://learn.microsoft.com/en-us/azure/azure-monitor/data-collection/data-collection-transformations-create?utm_source=chatgpt.com&tabs=portal)

- [coalesce() function (Kusto) — valid in general KQL, but not in DCR transforms per the supported list; this is why your Log query worked but the transform didn’t.](https://learn.microsoft.com/en-us/kusto/query/coalesce-function?view=microsoft-fabric)
