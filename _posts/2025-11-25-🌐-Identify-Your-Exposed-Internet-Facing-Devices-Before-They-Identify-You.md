# Introduction & Use Case:
**Identifying Internet-Facing Devices Matters to Every Framework You Care About.** Before we even dive into tooling, let’s anchor the importance of this work in the actual security and compliance frameworks that govern nearly every mature organization. Pretty much every major framework assumes you know which assets are exposed to the public internet — because this shapes your entire risk profile.

If you’ve spent any amount of time in Microsoft Defender, you’ve definitely seen the `IsInternetFacing` field in `DeviceInfo` and thought: _“Cool… Microsoft already tells me what’s Internet-facing. Easy win!”_ — But is it _really??_ 🤔

You'll want to know for the following **_really good_** reasons:


### 🔐 NIST Cybersecurity Framework (CSF)

- ID.AM-1 — Physical Devices & Systems Are Inventoried
You cannot inventory devices meaningfully without knowing which ones are externally reachable.

- ID.AM-2 — Software Platforms & Applications Are Inventoried
Public exposure affects patching, configuration, and lifecycle decisions.

- ID.RA-1 — Asset Vulnerabilities Are Identified and Documented
Internet-facing assets have a dramatically higher threat frequency and must be treated differently.

- PR.AC-3 — Remote Access Is Managed
Internet-accessible services are remote access — even when not intended to be.

- DE.CM-8 — Vulnerability Scans Are Performed
External scans start with knowing what is internet-facing in the first place.

<br/>

### 🛡️ ISO/IEC 27001:2022

- A.5.9 — Inventory of Information and Other Associated Assets
Asset inventories must distinguish externally accessible systems.

- A.8.23 — Web Filtering / Internet Exposure Management
Controls require that externally reachable systems be treated as higher-risk.

- A.13.1.1 — Network Security Controls
Segmentation, firewalls, and external exposure fall directly under this clause.

- A.5.24 — Information Security Incident Management Planning
Internet-facing devices represent higher incident probability and require forward planning.

<br/>

### 🧰 CIS Critical Security Controls (v8)

- CSC 1 — Inventory of Enterprise Assets
External exposure is part of classification.

- CSC 4 — Secure Configuration of Enterprise Assets
Internet-facing = hardened baseline required.

- CSC 14 — Security Awareness & Skills Training
Teams must recognize risky external assets.

- CSC 18 — Penetration Testing
Internet-exposed assets are always in-scope by default for pen tests & red teams.

<br/>

### ☁️ CIS Azure / M365 Benchmarks

- Azure 1.1 — Ensure Public Network Access Is Disabled Unless Required
Exactly the scenario we’re evaluating.

- Azure 3.4 — Ensure VM NICs Are Not Assigned Public IPs
Direct mapping to identifying internet-facing VMs.

- M365 5.6 — Monitor External Exposure
External accessibility increases alerting requirements.

<br/>

### 🏥 HIPAA (if PHI is involved)

Even though HIPAA doesn’t explicitly say “internet-facing,” auditors consistently tie this topic to:

- §164.308(a)(1)(ii)(A) — Risk Analysis
Internet-exposed assets are higher likelihood/impact.

- §164.312(e)(1) — Transmission Security
Public endpoints require encryption and strong access control. 

<br/>

### 🏛️ CMMC / NIST 800-171

For DoD contractors or manufacturing:

- 3.1.3 — Control Remote Access

- 3.13.1 — Boundary Protection

- 3.14.1 — Scan for Vulnerabilities

Internet-facing endpoints are the _**first thing**_ your CMMC assessor will ask about.

<br/><br/>

# 🌐 How to *Actually* Identify Internet-Facing Devices with KQL
### (*Because sometimes “IsInternetFacing = true” just lies to you.*)

And then—after about seven seconds of experience in the real world—you learned the truth:
* Some devices **are Internet-exposed but not flagged**
* Some devices **were briefly exposed**, but the flag didn’t update
* Some devices **make outbound connections that *look* inbound**
* Cloud networks, hybrid appliances, VPN concentrators, and IoT junk…
  …**absolutely do not care** about that boolean flag

So today, we’re leveling up.
We’re diving into a **multi-signal, evidence-driven** KQL detection like an **attack surface samurai** and cut straight to the point: **“Which of my machines is exposed to the public Internet?”** And we’re answering it using telemetry—not hope.

<br/> <br/>

![](/assets/img/Internet-Facing/internet-facing-cat.png)

<br/><br/><br/><br/>

# 🧠 Why We Need a Better Method

`IsInternetFacing` relies on Defender’s internal classification. It’s great when it’s correct.
But Internet exposure isn’t a simple binary state—it's a pattern of behavior:

* Does the device ever report a public IP?
* Does it accept inbound connections from public IPs?
* Does it listen on remote-access ports where outsiders connect?
* Does Defender *think* it's internet-facing?

This blog post covers a **KQL query that unifies all of these signals** into one answer.

It’s like running a security investigation with **multiple witnesses instead of one sleepy intern.**

<br/><br/><br/><br/>

# 🛠️ Query Breakdown

Here's the full KQL query breakdown and comparison with comments:

### ❌ Using 'IsInternetFacing == True'
```kql
DeviceInfo
| where IsInternetFacing == True
```
![](/assets/img/Internet-Facing/Fail.png)

<br/><br/>

### ✅ Our New and Improved Query:
```bash
// Define a regex that matches *private* and non-routable IP ranges
// Includes: 10.0.0.0/8, 172.16.0.0–172.31.255.255, 192.168.0.0/16,
// loopback (127.*), link-local (169.254.*), and some special ranges (224.*, 240.*)
let PrivateIPRegex = @'^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|169\.254\.|224\.|240\.)';

// How far back to look in the telemetry
let LookbackDays = 30d;

// -------------------------------------------
// 1) Devices with public IPs seen in ConnectedNetworks
// -------------------------------------------
let PublicIPDevices = DeviceNetworkInfo
    // Limit to the lookback window
    | where Timestamp > ago(LookbackDays)
    // Only keep rows where ConnectedNetworks has data
    | where isnotempty(ConnectedNetworks)
    // Expand the ConnectedNetworks JSON array into one row per network object
    | mv-expand ConnectedNetwork = parse_json(ConnectedNetworks)
    // Extract the PublicIP property from each ConnectedNetwork object
    | extend PublicIP = tostring(ConnectedNetwork.PublicIP)
    // Keep only non-empty, non-private IPs (i.e., likely public IPs)
    | where isnotempty(PublicIP) and not(PublicIP matches regex PrivateIPRegex)
    // Aggregate all public IPs per device into a set (distinct list)
    | summarize PublicIPs = make_set(PublicIP) by DeviceId, DeviceName
    // Tag this dataset with how we detected it
    | extend DetectionMethod = "PublicIP";

// -------------------------------------------
// 2) Devices whose *local* IP is actually public
// (e.g., directly assigned public IP address)
// -------------------------------------------
let PublicLocalIP = DeviceNetworkInfo
    // Same lookback window
    | where Timestamp > ago(LookbackDays)
    // Only rows where IPAddresses has data
    | where isnotempty(IPAddresses)
    // Expand IPAddresses JSON array into one row per IP object
    | mv-expand IPAddress = parse_json(IPAddresses)
    // Extract the IPAddress field from each object
    | extend LocalIP = tostring(IPAddress.IPAddress)
    // Keep only non-empty IPs that are not private ranges
    | where isnotempty(LocalIP) and not(LocalIP matches regex PrivateIPRegex)
    // Aggregate all public "local" IPs per device
    | summarize PublicLocalIPs = make_set(LocalIP) by DeviceId, DeviceName
    // Tag how we detected this
    | extend DetectionMethod = "PublicLocalIP";

// -------------------------------------------
// 3) Devices with a significant number of inbound connections
// -------------------------------------------
let InboundConnections = DeviceNetworkEvents
    // Same lookback window
    | where Timestamp > ago(LookbackDays)
    // Only inbound connection accepted events
    | where ActionType == "InboundConnectionAccepted"
    // Exclude private source IPs; keep only external (public-ish) sources
    | where not(RemoteIP matches regex PrivateIPRegex)
    // Extra safety: explicitly exclude some special/broadcast ranges
    | where RemoteIP !in ("169.254.0.0/16", "224.0.0.0/4", "255.255.255.255")
    // Summarize inbound activity per device
    | summarize 
        InboundCount      = count(),                // total accepted inbound connections
        UniqueRemoteIPs   = dcount(RemoteIP),       // number of distinct remote IPs
        RemotePorts       = make_set(RemotePort),   // list of remote ports seen
        SampleRemoteIPs   = make_set(RemoteIP, 5)   // sample up to 5 remote IPs
      by DeviceId, DeviceName
    // Only keep devices with more than 5 inbound connections (tune this threshold)
    | where InboundCount > 5
    // Tag detection method
    | extend DetectionMethod = "InboundConnections";

// -------------------------------------------
// 4) Devices listening on common remote access / service ports
// -------------------------------------------
let RemoteAccessServices = DeviceNetworkEvents
    // Same lookback window
    | where Timestamp > ago(LookbackDays)
    // Focus on common remote access / admin / web ports
    // (22=SSH, 3389=RDP, 443/80=HTTPS/HTTP, 21=FTP, 23=Telnet, 5900=VNC, 5985/5986=WinRM)
    | where RemotePort in (22, 3389, 443, 80, 21, 23, 5900, 5985, 5986)
    // Only inbound accepted events
    | where ActionType == "InboundConnectionAccepted"
    // From non-private IPs (i.e., likely internet-originated)
    | where not(RemoteIP matches regex PrivateIPRegex)
    // Summarize per device: which service ports and how many connections
    | summarize 
        ServicePorts     = make_set(RemotePort),
        ConnectionCount  = count()
      by DeviceId, DeviceName
    // Tag detection method
    | extend DetectionMethod = "RemoteAccessPorts";

// -------------------------------------------
// 5) Devices already flagged as Internet-facing in DeviceInfo
// -------------------------------------------
let IsInternetFacingDevices = DeviceInfo
    // Same lookback window
    | where Timestamp > ago(LookbackDays)
    // Only devices explicitly flagged as Internet-facing
    | where IsInternetFacing == true
    // Distinct list per DeviceId/DeviceName
    | distinct DeviceId, DeviceName
    // Tag detection method
    | extend DetectionMethod = "IsInternetFacing";

// -------------------------------------------
// 6) Union all detections, merge by DeviceId/DeviceName
// -------------------------------------------

// Start with devices that had public IPs from ConnectedNetworks
PublicIPDevices
// Full outer join with devices that had public LocalIP
| join kind=fullouter (PublicLocalIP) on DeviceId, DeviceName
// Full outer join with devices that had inbound connections
| join kind=fullouter (InboundConnections) on DeviceId, DeviceName
// Full outer join with devices on remote access/service ports
| join kind=fullouter (RemoteAccessServices) on DeviceId, DeviceName
// Full outer join with devices explicitly marked as Internet-facing
| join kind=fullouter (IsInternetFacingDevices) on DeviceId, DeviceName

// After multiple joins, the same logical field may exist as DeviceId, DeviceId1, DeviceId2...
// coalesce() picks the first non-null value across those
| extend DeviceId   = coalesce(DeviceId,   DeviceId1,   DeviceId2,   DeviceId3,   DeviceId4)
| extend DeviceName = coalesce(DeviceName, DeviceName1, DeviceName2, DeviceName3, DeviceName4)

// Combine all public IP lists (from ConnectedNetworks or LocalIP)
| extend AllPublicIPs = coalesce(PublicIPs, PublicLocalIPs)

// Combine all detection method tags into one comma-separated string
| extend DetectionMethods = strcat_array(
                                pack_array(
                                    DetectionMethod, DetectionMethod1, 
                                    DetectionMethod2, DetectionMethod3, DetectionMethod4
                                ), 
                                ", "
                            )

// Ensure these complex fields are converted to string for output
| extend RemotePortsStr  = tostring(RemotePorts)
| extend ServicePortsStr = tostring(ServicePorts)
| extend PublicIPList    = tostring(AllPublicIPs)

// Choose the final set of columns to output
| project 
    DeviceId, 
    DeviceName, 
    PublicIPList, 
    DetectionMethods, 
    InboundCount, 
    UniqueRemoteIPs, 
    RemotePortsStr, 
    ServicePortsStr

// If there are multiple rows per device, pick the row with the "highest" DetectionMethods value
// (arg_max uses the lexicographically max DetectionMethods as the tiebreaker)
| summarize arg_max(DetectionMethods, *) by DeviceId, DeviceName
```
<br/>

![](/assets/img/Internet-Facing/Results.png)

<br/>

### 👉 You can grab your copy [HERE](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Devices%20are%20Internet%20Facing%3F.kql) 👈

<br/><br/><br/><br/> 

# ⚡ Below are the major components for our new and improved method—explained in normal human language, translated from “Kusto-ese.”

### 📃 Step 0: Define What Counts as a Private IP

```kql
let PrivateIPRegex = @'^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|169\.254\.|224\.|240\.)';
```

This regex defines **non-routable** address spaces:

* RFC1918 ranges
* Loopback
* Link-local
* Multicast/special blocks

Anything **not matching** this regex is, for practical purposes, considered *public-ish*.

<br/><br/>

### ⏱️ Step 1: Define the Lookback Window

```kql
let LookbackDays = 30d;
```

Most exposure patterns are visible within 30 days. Adjust as needed (14d for strict, 90d for historical).

<br/><br/>

### 🌍 Step 2: Devices Reporting Public IPs via Connected Networks

```kql
let PublicIPDevices = DeviceNetworkInfo
...
```

When Defender collects `ConnectedNetworks`, it may include a **PublicIP** property.

If a device ever reports a public IP through this channel:

✔ It touched the Internet
✔ Or it *was* the public edge of something
✔ Or it’s behind a 1:N NAT but still exposes public hops

<br/><br/>

### 🏠 Step 3: Devices with Public *Local* IPs

```kql
let PublicLocalIP = DeviceNetworkInfo
...
```

Some devices literally have public IPs **assigned directly** to a network interface:

* Web servers
* Firewalls
* VPN appliances
* Load balancers
* Cloud VMs with public NICs

> If you see a device with a public LocalIP… <br/>
>🔥 It *is* exposed <br/>
>🔥 It *is* reachable <br/>
>🔥 It *is* Internet-facing <br/>

<br/><br/>

### 🚪 Step 4: Devices Accepting Inbound Public Connections

```kql
let InboundConnections = DeviceNetworkEvents
...
```

This looks for `InboundConnectionAccepted` events **from public IPs only**.
Meaning: _a real-world outsider connected to the device._

We gather:

* Count of inbound connections
* Unique external IPs
* Ports targeted
* Samples of RemoteIP

Then we threshold (e.g., only devices with >5 accepted inbound connections. This is great for tackling the biggest offenders first, then you can adjust the threshold as you see fit).


<br/><br/>

### 🔐 Step 5: Devices Listening on Remote-Access Ports

```kql
let RemoteAccessServices = DeviceNetworkEvents
...
```

We examine inbound connections on common high-risk ports:

| Port      | Use Case        |
| --------- | --------------- |
| 22        | SSH             |
| 3389      | RDP             |
| 80/443    | Web Servers     |
| 21/23     | FTP / Telnet    |
| 5900      | VNC             |
| 5985/5986 | WinRM           |

<br/>

> ⚠️ If a public IP hits you on RDP or SSH, you’re exposed—**period** 👀

This detection (a personal favourite) reveals:

* Compromised servers
* Shadow IT
* Misconfigured firewalls
* Random cloud-hosted VMs someone forgot about


<br/><br/>

### 🚩 Step 6: Devices Flagged as Internet-Facing in DeviceInfo

```kql
let IsInternetFacingDevices = DeviceInfo
...
```

While we do include Microsoft’s opinion via ```IsInternetFacing```  —we don’t rely on it. This is the last source to take into consideration in our logic. Taken together with whether it has a public IP and if any ports are listening, we can make a more informed decision than relying on ```IsInternetFacing``` alone. 

<br/><br/>

### 🔄 Step 7: Union All Signals Into a Final Answer

The full-outer joins bring all devices from all signals together.
We use:

* `coalesce()` to merge various DeviceId columns
* `strcat_array()` to merge detection method tags
* `make_set()` for public IPs, service ports, etc.
* `arg_max()` to dedupe intelligently

<br/>

The final result:

- DeviceId
- DeviceName
- PublicIPList
- DetectionMethods
- InboundCount
- UniqueRemoteIPs
- RemotePortsStr
- ServicePortsStr

<br/>

Each row is a **multi-signal threat picture** of _how and why_ the device appears exposed.

<br/><br/><br/><br/>

# 🛡️ Practical Security Use Cases

This query gives you a **field manual** of exposure scenarios on top of previously mentioned audit use cases.

<br/>

### 📍 External Attack Surface Mapping

✔️ Immediately know which machines are reachable from the Internet.

<br/>

### 👤 Shadow IT Discovery

✔️ Find those random Azure VMs someone spun up with public NICs and an RDP port “just for testing.”

<br/>

### 🧱 Firewall Misconfiguration Detection

✔️ If inbound connections are hitting servers that shouldn’t be public…
…fix your perimeter.

<br/>

### ⚔️ Compromise Triaging

✔️ Inbound traffic spikes from unusual countries? You’ll see it here.

<br/>

### 📋 Compliance Evidence (CIS, NIST, ISO)

✔️ Provides documented proof of systems exposed to the public Internet.

<br/>

### 📡 Identify Stealth Exposures

✔️ If a device’s NIC is private, but inbound connections are still happening → NAT or unusual routing.

<br/>

### 🗝️ Validate Zero Trust Assumptions

✔️ **Trust but verify.** Zero Trust cannot rely on a single boolean flag.

<br/><br/><br/><br/>

# 🤺 Why This Beats Relying on `IsInternetFacing`

| Metric                                   | `IsInternetFacing` | This Query |
| ---------------------------------------- | ------------------ | ---------- |
| Uses multiple telemetry sources          | ❌                  | ✅          |
| Detects RDP/SSH/Web exposure             | ❌                  | ✅          |
| Finds NAT-exposed devices                | ❌                  | ✅          |
| Captures temporary / historical exposure | ❌                  | ✅          |
| Sees public LocalIPs                     | ⚠️ Sometimes        | ✅ Always   |
| Evidence-driven                          | ❌                  | ✅          |
| Ideal for compliance & audits            | Meh                 | Excellent  |

<br/>

### The bottom line:

`IsInternetFacing` is a **hint**.
This query is **proof**.

<br/><br/><br/><br/>

# 🚀 Final Thoughts

In security, reality always beats assumptions.

This multi-signal KQL approach gives you a **complete, accurate assessment** of Internet exposure across Defender data—no guesswork, no reliance on backend classifiers, and no blind spots created by NAT, hybrid infrastructures, or quietly misconfigured firewall rules.

Use it to:

* Hunt exposures
* Power dashboards
* Enrich attack surface reports
* Alert on real-world inbound traffic
* Catch mistakes before attackers do

And most importantly:

> 👉 If your device accepts inbound connections from the Internet…
> **it’s Internet-facing—whether Defender agrees or not.**

If you’ve followed the steps above, you now have a clearer view of which devices in your environment are Internet-facing — and which are silently gobbling up risk and cost.
Don’t stop here. Grab your network inventory, fire up your scanner, and map every inbound point from the public Internet. Then ask yourself:

- What unnecessary services are exposed?

- Which endpoints haven’t been patched or reviewed in months?

- Where can I tighten firewall rules, disable unused ports, or shift systems behind a VPN/DMZ?

Locking down these devices isn’t just about reducing noise in your logs — it’s about reclaiming control over your attack surface, cutting ingestion costs, and reducing audit risk.

⚙️ So go ahead — run the scan, clean house, and harden your perimeter. Then come back and tell me what you found. If you hit surprises or want to share weird edge cases (I bet you will), drop a comment below, or ping me on LinkedIn. I want to see your results, learn what you ran into, and help you tighten up your baseline before your next compliance push.

### Stay sharp out there — and may the only open ports in your environment be the ones you absolutely need. 🔐


<br/>

![](/assets/img/Internet-Facing/Exposed.jpg)

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
<br/>
<br/>

# 🔗 References (good to keep handy)

- [🔎Which Devices are Internet Facing?.kql](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Devices%20are%20Internet%20Facing%3F.kql)
- [😼Origin of Defender NinjaCat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025) 
- [📘Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ)

<br/>
<br/>
<br/>
<br/>



<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
