# 🧱 Cutting Through the Noise: Reducing Fortinet Teardown Traffic in Microsoft Sentinel

When you connect a Fortinet firewall to Microsoft Sentinel for full-spectrum visibility, the first thing you notice is… the noise.
Specifically: **connection teardown events** — hundreds of thousands of them.

At first glance, they look harmless — just logs marking the end of a session. But once you start scaling Sentinel ingestion, those teardown logs quietly turn into the digital equivalent of background static: expensive, repetitive, and rarely helpful from a security perspective.

This post breaks down what we ran into, what we learned, and how we tuned Fortinet (and later Cisco Meraki) firewall logs to keep the signal — without paying for the noise.

---

## 🔍 The Problem: Too Much Teardown, Too Little Value

In Fortinet syslog output, every connection generates *two* major events:

1. **Connection standup** — when a new session is created (`traffic:forward start`)
2. **Connection teardown** — when the session closes (`traffic:forward close`, `client-fin`, `server-fin`, etc.)

Multiply that by thousands of clients and microservices, and teardown events quickly dominate your ingestion stream.

We initially noticed that:

* Teardown logs made up **60–70% of total Fortinet traffic volume**
* They provided **no new security context** (same source/destination/action as the standup event)
* And they were **burning Sentinel GBs** — driving up cost with zero detection benefit

That’s when we stepped back and asked: *do teardown logs really help us detect or respond to threats faster?*

---

## 🧠 Why Teardown Logs Don’t Help You Stop a Threat

From a **DFIR (Digital Forensics and Incident Response)** standpoint, teardown events occur **after** the activity is over.
They mark closure, not intent.

* When malware calls home, the **standup log** shows the destination C2 domain — *that’s actionable*.
* When a lateral movement connection is opened, the **standup log** shows source → target — *that’s valuable for threat hunting*.
* But when the connection closes? The teardown event just repeats the tuple and says “we’re done here.”

By the time teardown traffic is written, the attacker’s action already happened.
In short: teardown = bookkeeping, not detection.

---

## 🔧 The Fix: Filter the Noise, Keep the Signal

We refined our Sentinel ingestion rules using **KQL-based filters** that exclude teardown-only messages while retaining high-value network telemetry.

Here’s the core Fortinet logic we built:

```kql
// CURRENT FILTERS - Only connection teardown/close events:
| where _msg !~ @"traffic:forward close"       // Connection close events
| where _msg !~ @"traffic:forward client-rst"  // Client reset packets  
| where _msg !~ @"traffic:forward server-rst"  // Server reset packets
| where _msg !~ @"traffic:forward timeout"     // Connection timeouts
| where _msg !~ @"traffic:forward cancel"      // Cancelled connections
| where _msg !~ @"traffic:forward client-fin"  // Client FIN packets
| where _msg !~ @"traffic:forward server-fin"  // Server FIN packets
| where _msg !~ @"traffic:local close"         // Local (intra-device) connection close events
| where _msg !~ @"traffic:local client-rst"    // Local (intra-device) client reset packets
| where _msg !~ @"traffic:local timeout"       // Local (intra-device) connection timeouts
| where _msg !~ @"traffic:local server-rst"    // Local (intra-device) server reset packets
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


