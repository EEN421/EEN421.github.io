# 🔪 Cutting Through the Noise: Reducing Fortinet Teardown Traffic in Microsoft Sentinel

When you connect a Fortinet firewall to Microsoft Sentinel for full-spectrum visibility, the first thing you notice is… the noise.
Specifically: **connection teardown events** — hundreds of thousands of them.

At first glance, they look harmless — just logs marking the end of a session. But once you start scaling Sentinel ingestion, those teardown logs quietly turn into the digital equivalent of background static: expensive, repetitive, and rarely helpful from a security perspective.

This post breaks down what I've learned and how to tune Fortinet firewall logs to keep the signal — without paying for the noise.

---

## 🔍 The Problem: Too Much Teardown, Too Little Value

In Fortinet network traffic logs, every connection generates *two* major events:

1. **Connection standup** — when a new session is created (`traffic:forward start`)
2. **Connection teardown** — when the session closes (`traffic:forward close`, `client-fin`, `server-fin`, etc.)

Multiply that by thousands of clients and microservices, and teardown events quickly dominate your ingestion stream.

Detection versus Investigation Value:

I like to break down logs into 2 categories that either provide Detection Value or Investigation value. 
- Detection value helps us detect and mitigate malicious behavious in it's tracks.
- Investigation value may not help us detect and stop a malicious act, but it's the first thing the DFIR team asks for during a post-breach investigation.

- Network Teardown Traffic typically:
* Provides **no new security context** (same source/destination/action as the standup event)
* And they **burn Sentinel GBs** — driving up cost with zero detection benefit

That’s when I stepped back and asked: *do teardown logs really help us detect or respond to threats faster?*

---

## 🧠 Why Teardown Logs Don’t Help You Stop a Threat

From a **DFIR (Digital Forensics and Incident Response)** standpoint, teardown events occur **after** the activity is over.
They mark closure, not intent.

* When malware calls home, the **standup log** shows the destination C2 domain — *that’s actionable*.
* When a lateral movement connection is opened, the **standup log** shows source → target — *that’s valuable for threat hunting*.
* But when the connection closes? The teardown event just repeats the tuple and says “we’re done here.”

By the time teardown traffic is written, the attacker’s action already happened.
In short/TLDR: teardown = bookkeeping, not detection.

---

## 🔧 The Fix: Filter the Noise, Keep the Signal

I refine my Sentinel ingestion rules using **KQL-based filters** that exclude teardown-only messages while retaining high-value network telemetry.

Here’s the core Fortinet logic we built:

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

After validating these filters, ingestion dropped by **over 60%** with **no loss in security signal**.
We even confirmed it by comparing Sentinel hunting queries and analytics rules before/after the change — same detection output, far less cost.

---

## 🧾 The Before-and-After Snapshot

| Metric                   | Before Filters | After Filters    |
| ------------------------ | -------------- | ---------------- |
| Daily Fortinet Ingestion | ~18.4 GB       | **6.2 GB**       |
| Detection Count          | 100%           | 100%             |
| DFIR Context             | No change      | No change        |
| Cost Reduction           | —              | **≈65% savings** |

---

## 🧭 Key Takeaways for Other Security Teams

* **Don’t ingest everything.** More logs ≠ more visibility. Focus on what helps you detect and respond.
* **Teardown ≠ telemetry.** Those events tell you a connection *ended*, not that it was *malicious*.
* **Validate before excluding.** Always test filters with a quick `summarize count()` to ensure no legitimate security logs disappear.
* **Reinvest the savings.** Use your reduced ingestion costs to onboard richer data sources — endpoint, identity, or cloud app telemetry.

---

## ⚡ Closing Thoughts

Noise reduction isn’t just about saving money — it’s about sharpening focus.
By filtering teardown traffic, we transformed our firewalls from noisy log generators into **high-value security signal providers**.

That’s the difference between drowning in data and acting on intelligence.


