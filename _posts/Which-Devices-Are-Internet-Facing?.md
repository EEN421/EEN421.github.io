# Introduction & Use Case:
If you’ve spent any amount of time in Microsoft Defender, you’ve definitely seen the `IsInternetFacing` field in `DeviceInfo` and thought:
> “Cool… Microsoft already tells me what’s Internet-facing. Easy win!”

# 🌐 How to *Actually* Identify Internet-Facing Devices with KQL
### (*Because sometimes “IsInternetFacing = true” just lies to you.*)

And then—after about seven seconds of experience in the real world—you learned the truth:
* Some devices **are Internet-exposed but not flagged**
* Some devices **were briefly exposed**, but the flag didn’t update
* Some devices **make outbound connections that *look* inbound**
* Cloud networks, hybrid appliances, VPN concentrators, and IoT junk…
  …**absolutely do not care** about that boolean flag

So today, we’re leveling up.
We’re diving into a **multi-signal, evidence-driven** KQL detection that actually answers the question:

## **“Which of my machines is exposed to the public Internet?”**

And we’re answering it using telemetry—not hope.

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

# 🧩 Breakdown of the Query (Explained Like DevSecOpsDad)

Below are the major components—explained in normal human language, not “Kusto-ese.”

<br/><br/><br/><br/>

# 🏷️ Step 0: Define What Counts as a Private IP

```kql
let PrivateIPRegex = @'^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|169\.254\.|224\.|240\.)';
```

This regex defines **non-routable** address spaces:

* RFC1918 ranges
* Loopback
* Link-local
* Multicast/special blocks

Anything **not matching** this regex is, for practical purposes, considered *public-ish*.

<br/><br/><br/><br/>

# 🕰️ Step 1: Define the Lookback Window

```kql
let LookbackDays = 30d;
```

Most exposure patterns are visible within 30 days. Adjust as needed (14d for strict, 90d for historical).

<br/><br/><br/><br/>

# 🌍 Step 2: Devices Reporting Public IPs via Connected Networks

```kql
let PublicIPDevices = DeviceNetworkInfo
...
```

This is gold. When Defender collects `ConnectedNetworks`, it may include a **PublicIP** property.

If a device ever reports a public IP through this channel:

✔ It touched the Internet
✔ Or it *was* the public edge of something
✔ Or it’s behind a 1:N NAT but still exposes public hops

Good detection method #1.

<br/><br/><br/><br/>

# 🏠 Step 3: Devices with Public *Local* IPs

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

If you see a device with a public LocalIP…

🔥 It *is* exposed
🔥 It *is* reachable
🔥 It *is* Internet-facing

This is one of the most trustworthy signals in the entire diagram.

<br/><br/><br/><br/>

# 🚪 Step 4: Devices Accepting Inbound Public Connections

```kql
let InboundConnections = DeviceNetworkEvents
...
```

This looks for `InboundConnectionAccepted` events **from public IPs only**.
Meaning: a real-world outsider connected to the device.

This is the part where the device is basically shouting:

> “Yes, stranger! Come on in!”

We gather:

* Count of inbound connections
* Unique external IPs
* Ports targeted
* Samples of RemoteIP

Then we threshold (e.g., only devices with >5 accepted inbound connections).

This is detection method #3—and it's extremely practical.

<br/><br/><br/><br/>

# 🔐 Step 5: Devices Listening on Remote-Access Ports

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
| 21/23     | FTP / Telnet 😬 |
| 5900      | VNC             |
| 5985/5986 | WinRM           |

If a public IP hits you on RDP or SSH, you’re exposed—**period**.

This detection reveals:

* Compromised servers
* Shadow IT
* Misconfigured firewalls
* Random cloud-hosted VMs someone forgot about

It’s a personal favorite.

<br/><br/><br/><br/>

# 🏷️ Step 6: Devices Flagged as Internet-Facing in DeviceInfo

```kql
let IsInternetFacingDevices = DeviceInfo
...
```

We include Microsoft’s opinion—but we don’t rely on it.

Think of this as the friend who shows up late to the party, but still gets included in the group photo.

<br/><br/><br/><br/>

# 🔄 Step 7: Union All Signals Into a Final Answer

The full-outer joins bring all devices from all signals together.
We use:

* `coalesce()` to merge various DeviceId columns
* `strcat_array()` to merge detection method tags
* `make_set()` for public IPs, service ports, etc.
* `arg_max()` to dedupe intelligently

The final result:

```kql
DeviceId
DeviceName
PublicIPList
DetectionMethods
InboundCount
UniqueRemoteIPs
RemotePortsStr
ServicePortsStr
```

Each row is a **multi-signal threat picture** of how and why the device appears exposed.

<br/><br/><br/><br/>

# 🛡️ Practical Security Use Cases

This query gives you a **field manual** of exposure scenarios.

<br/><br/>

### ✔ External Attack Surface Mapping

Immediately know which machines are reachable from the Internet.

<br/><br/>

### ✔ Shadow IT Discovery

Find those random Azure VMs someone spun up with public NICs and an RDP port “just for testing.”

<br/><br/>

### ✔ Firewall Misconfiguration Detection

If inbound connections are hitting servers that shouldn’t be public…
…fix your perimeter.

<br/><br/>

### ✔ Compromise Triaging

Inbound traffic spikes from unusual countries?
You’ll see it here.

<br/><br/>

### ✔ Compliance Evidence (CIS, NIST, ISO)

Provides documented proof of systems exposed to the public Internet.

<br/><br/>

### ✔ Identify Stealth Exposures

If a device’s NIC is private, but inbound connections are still happening → NAT or unusual routing.

<br/><br/>

### ✔ Validate Zero Trust Assumptions

Trust but verify.
Zero Trust cannot rely on a single boolean flag.

<br/><br/><br/><br/>

# 🥊 Why This Beats Relying on `IsInternetFacing`

| Metric                                   | `IsInternetFacing` | This Query |
| ---------------------------------------- | ------------------ | ---------- |
| Uses multiple telemetry sources          | ❌                  | ✅          |
| Detects RDP/SSH/Web exposure             | ❌                  | ✅          |
| Finds NAT-exposed devices                | ❌                  | ✅          |
| Captures temporary / historical exposure | ❌                  | ✅          |
| Sees public LocalIPs                     | ⚠️ Sometimes       | ✅ Always   |
| Evidence-driven                          | ❌                  | ✅          |
| Ideal for compliance & audits            | Meh                | Excellent  |

<br/><br/>

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

> If your device accepts inbound connections from the Internet…
> **it’s Internet-facing—whether Defender agrees or not.**

