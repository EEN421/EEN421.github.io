![DevSecOpsDadAttack!](/assets/img/Attack1.png)
Every week our [Detection Engineering Brief](https://DevSecOpsDadAttack.com) turns fresh threat intel into deployable detection content — KQL for Microsoft Sentinel and Defender XDR, ATT&CK mappings, triage runbooks, and deployment-readiness calls. This week's five briefs produced **23 KQL candidates** across npm supply-chain attacks, NetSupport RAT, a macOS FlutterShell dropper chain, a Key Vault secret-access anomaly, an API-recon sweep, and more.

Out of all 23, two queries stuck with me — not because of the malware they target, but because of the *primitives* they're built on. One counts **rhythm**. The other detects **absence**. Both generalize far beyond the threat that produced them, and both are worth adding to your mental toolkit.

Let's pull them apart.

---

## 🥇 The main event: count the rhythm, not the racket

The featured query this week comes from the **Argamal RAT** hunt (Thursday's brief). Argamal is a remote access trojan recently caught hiding inside trojanized game installers — it drops its payload into user-writable directories and then quietly phones home (h/t Securelist). It's the C2 stage that's interesting here, because the detection isn't really about Argamal at all. It's about how you find any implant that beacons low-and-slow.

### The problem with "count the connections"

The naive way to hunt C2 is a volume threshold: tally outbound connections per process, alert when the number is high. The trouble is that a high number is exactly what your *noisiest legitimate software* produces. A browser or a sync client racks up hundreds of connections an hour and buries the real implant making one quiet check-in every fifteen minutes. Malware authors know this, so they go low-and-slow and sit comfortably under any volume alarm.

The fix is to stop counting *connections* and start counting *the windows you were connected in*.

```kql
let lookback = 24h;
let beaconCandidates = DeviceNetworkEvents
| where Timestamp > ago(lookback)
| where (RemoteIPType == "Public") or (isempty(RemoteIPType) and not(ipv4_is_private(RemoteIP)))
| where isnotempty(InitiatingProcessFolderPath)
| where InitiatingProcessFolderPath has_any ("\\Downloads\\", "\\Temp\\", "\\AppData\\Local\\Temp\\", "\\AppData\\Roaming\\")
| where not (InitiatingProcessFileName in~ (
    "chrome.exe", "msedge.exe", "firefox.exe", "iexplore.exe",
    "MicrosoftEdge.exe", "OneDrive.exe", "Teams.exe",
    "Slack.exe", "Code.exe", "Discord.exe", "Spotify.exe",
    "Update.exe", "squirrel.exe"
))
| summarize
    ConnectionWindows = dcount(bin(Timestamp, 1h)),
    TotalConnections = count(),
    RemoteIPs = make_set(RemoteIP, 10),
    RemotePorts = make_set(RemotePort, 10)
    by DeviceId, DeviceName, AccountName, InitiatingProcessFileName, InitiatingProcessFolderPath
| where ConnectionWindows >= 4 and TotalConnections >= 8;
let procContext = DeviceProcessEvents
| where Timestamp > ago(lookback)
| where FolderPath has_any ("\\Downloads\\", "\\Temp\\", "\\AppData\\Local\\Temp\\", "\\AppData\\Roaming\\")
| summarize ProcessCommandLine = arg_max(Timestamp, ProcessCommandLine) by DeviceId, FileName, FolderPath
| project DeviceId, FileName, FolderPath, ProcessCommandLine;
beaconCandidates
| join kind=leftouter procContext on DeviceId
| where FileName =~ InitiatingProcessFileName
| project
    DeviceId, DeviceName, AccountName,
    InitiatingProcessFileName, InitiatingProcessFolderPath, ProcessCommandLine,
    ConnectionWindows, TotalConnections, RemoteIPs, RemotePorts
| order by ConnectionWindows desc
```

### The line that does the work

```kql
ConnectionWindows = dcount(bin(Timestamp, 1h))
```

That's the whole idea. `bin(Timestamp, 1h)` rounds every connection's timestamp down to the start of its hour, so all the events in the 14:00–15:00 window collapse to one value. `dcount(...)` then counts how many *distinct* hour-buckets a process appeared in.

Now the two thresholds tell a story together:

- `ConnectionWindows >= 4` — the process was active in **at least four separate hours**. That's the *spread-over-time* requirement.
- `TotalConnections >= 8` — there was enough traffic to be a real channel, not a coincidence. That's the *substance* requirement.

A burst of 200 connections in five minutes fails the first test — it lives in one bucket. A single connection in each of three hours fails the second. Only sustained, recurring activity satisfies both, and that's exactly the signature of a heartbeat. **Eight connections in a two-minute window look like one chatty event. Eight connections spread one-per-hour across eight hours look like a beacon.** A raw `count()` can't tell those apart. `dcount(bin())` can.

### The three supporting moves

**1. A defensive public-IP gate.**

```kql
| where (RemoteIPType == "Public") or (isempty(RemoteIPType) and not(ipv4_is_private(RemoteIP)))
```

It trusts Defender's own `RemoteIPType` label first and only falls back to `ipv4_is_private()` when the field is empty. That matters because `ipv4_is_private()` silently ignores IPv6 — leaning on the platform's classification first closes a blind spot in dual-stack environments.

**2. Scope to where malware actually lives.** Filtering `InitiatingProcessFolderPath` to Downloads, Temp, and AppData focuses the hunt on user-writable paths instead of `Program Files`. Argamal runs from exactly these directories, so this isn't an arbitrary filter — it's threat-informed.

**3. Allowlist the legit beacons before they bury you.** Slack, VS Code, Discord, Spotify, OneDrive, Teams, and the Squirrel/`Update.exe` updater framework all live in AppData and beacon persistently by design. They'd pass every behavioral test in this query, so they're named and excluded up front. This is the part junior queries always forget — and the part you'll keep growing. Treat the list as a baseline, not a finished artifact.

Finally, the `join` back to `DeviceProcessEvents` uses `arg_max(Timestamp, ProcessCommandLine)` to grab the most recent command line per process and stitch it onto each result. The statistics tell you *that* something beaconed; the command line tells the analyst *what it is*.

### Keeping it honest

This ships as a **hunting query, not a scheduled rule** — and rightly so. Before you promote it: baseline the allowlist against your own tenant for a week, scale the `ConnectionWindows` floor if you shorten the lookback (four windows out of one hour means nothing), and consider a tighter `bin(Timestamp, 15m)` for faster heartbeats if you can tolerate the jitter sensitivity.

And one deployment gate worth flagging loudly: this query leans on `InitiatingProcessFolderPath` in `DeviceNetworkEvents` and gates on it with `isnotempty()`. That field is **not guaranteed across all Defender for Endpoint sensor versions.** If it's blank in your tenant, the guard silently zeroes out the entire candidate set and the rule returns nothing — the worst kind of failure, because it looks like "all clear." Validate coverage first:

```kql
DeviceNetworkEvents
| where Timestamp > ago(1d)
| summarize Total = count(), WithPath = countif(isnotempty(InitiatingProcessFolderPath))
| extend PercentPopulated = round(100.0 * WithPath / Total, 1)
```

If `PercentPopulated` is low, pivot the path logic to a join against `DeviceProcessEvents` on the process ID instead.

---

## 🥈 The honorable mention, in depth: detect the login that never happened

If the beaconing query wins on reusability, Monday's **GlobalProtect VPN Session Without Prior Authentication** detection wins on ambition — and it's the more instructive of the two, because it's a powerful idea wrapped around a subtle, ship-breaking bug.

### Why absence is a great primitive

Most detections look for a *thing that happened*: a bad process, a known-bad hash, a suspicious command line. But some of the strongest intrusion signals are about a thing that **should have happened and didn't.** A VPN tunnel established with no preceding authentication. A privileged action with no preceding privilege grant. A file decrypted with no preceding key request.

"Absence" detections are valuable precisely because attackers exploiting a logic flaw don't generate a malicious artifact — they generate a *legitimate-looking* event that's missing its usual prerequisite. That's the shape of **CVE-2026-0257**, a PAN-OS GlobalProtect authentication-bypass vulnerability that Rapid7 observed being exploited in the wild, where remote unauthenticated attackers stood up VPN sessions without ever completing a normal auth flow. There's no malware to hash and no payload to fingerprint. The only tell is the missing login.

### The query

```kql
let AuthEvents = CommonSecurityLog
| where TimeGenerated > ago(1d)
| where DeviceVendor =~ "Palo Alto Networks"
| where DeviceProduct has_any ("GlobalProtect", "PAN-OS")
| where Activity has_any ("login", "authenticate", "auth-success", "prelogin")
    or Message has_any ("login", "authenticate", "prelogin")
| project AuthTime = TimeGenerated, SourceIP;
CommonSecurityLog
| where TimeGenerated > ago(1d)
| where DeviceVendor =~ "Palo Alto Networks"
| where DeviceProduct has_any ("GlobalProtect", "PAN-OS")
| where Activity has_any ("connected", "tunnel-established", "gateway-connected")
    or Message has_any ("connected", "tunnel established")
| where not(ipv4_is_private(SourceIP))
| project SessionTime = TimeGenerated, SourceIP, DeviceProduct, Activity, DeviceAction, Message, LogSeverity, DestinationIP
| join kind=leftanti (
    AuthEvents
) on SourceIP
    , $left.SessionTime - 5m <= $right.AuthTime
    , $right.AuthTime <= $left.SessionTime
| sort by SessionTime desc
```

### How it's supposed to work

The structure is clean. Build one set of **authentication events** and one set of **session-established events**, both from the PAN-OS CEF feed. Then `join kind=leftanti` the sessions against the auths: `leftanti` keeps only the left-side rows that have **no match** on the right. In plain English, "show me every VPN session that has no corresponding authentication." The author then tries to bound that match to a five-minute pre-session window with the inequality predicates `$left.SessionTime - 5m <= $right.AuthTime` and `$right.AuthTime <= $left.SessionTime`.

That's the dream version of the query. Now the problem.

### The trap: time-bounding inside an equality join

KQL's `join ... on` clause is built for **equality** matching. It's happiest with `$left.x == $right.y`. Trying to express a *range* condition — "auth within five minutes before the session" — inside that same `on` clause does not reliably do what you intend. The brief documents the practical consequence precisely:

> The leftanti join as written suppresses any session alert if a matching SourceIP auth event exists *anywhere* in the 1-day lookback window, not within a bounded window relative to the session event — a morning auth event will suppress an afternoon bypass session from the same IP, producing false negatives.

Read that again, because it's the worst possible failure for this particular detection. The whole point is to catch a session with no auth. But if that same source IP authenticated *legitimately* at 9 a.m., a genuine bypass session at 3 p.m. from that IP gets **silently suppressed**. The query designed to catch the attack quietly hides it. A NAT gateway or a shared egress IP — where one real user authenticates and an attacker rides the same address — is the exact scenario where you'd want this rule, and the exact scenario where the broken time-bound betrays you.

This is the cardinal rule of absence detection: **an anti-join lives or dies by the time-bounding of its match.** Get it wrong and you don't get noise — you get silence.

### The corrected, production-ready rewrite

The robust pattern is to do the equality join on the key (`SourceIP`), evaluate the time window with an explicit `between` *after* the join, and then keep only the sessions where **zero** auths landed inside their personal pre-session window:

```kql
let lookback = 1d;
let window = 5m;
let AuthEvents = CommonSecurityLog
| where TimeGenerated > ago(lookback)
| where DeviceVendor =~ "Palo Alto Networks"
| where DeviceProduct has_any ("GlobalProtect", "PAN-OS")
| where Activity has_any ("login", "authenticate", "auth-success", "prelogin")
    or Message has_any ("login", "authenticate", "prelogin")
| project AuthTime = TimeGenerated, SourceIP;
CommonSecurityLog
| where TimeGenerated > ago(lookback)
| where DeviceVendor =~ "Palo Alto Networks"
| where DeviceProduct has_any ("GlobalProtect", "PAN-OS")
| where Activity has_any ("connected", "tunnel-established", "gateway-connected")
    or Message has_any ("connected", "tunnel established")
| where not(ipv4_is_private(SourceIP))
| project SessionTime = TimeGenerated, SourceIP, DeviceProduct, Activity, DeviceAction, Message, LogSeverity, DestinationIP
| join kind=leftouter (AuthEvents) on SourceIP
| extend AuthInWindow = AuthTime between ((SessionTime - window) .. SessionTime)
| summarize PriorAuthCount = countif(AuthInWindow == true)
    by SessionTime, SourceIP, DeviceProduct, Activity, DeviceAction, Message, LogSeverity, DestinationIP
| where PriorAuthCount == 0
| sort by SessionTime desc
```

Walk the fix:

- `join kind=leftouter` keeps every session and attaches each candidate auth from the same `SourceIP` as its own row.
- `AuthInWindow` flags, per row, whether that auth actually fell in the five minutes before *this specific session*.
- `summarize ... countif(AuthInWindow == true)` collapses back to one row per session and counts how many auths genuinely landed in-window. Sessions with no matching IP at all produce a null `AuthTime`, which counts as zero — correctly kept as a true no-auth bypass.
- `where PriorAuthCount == 0` keeps only the sessions with no in-window authentication.

Now the 9 a.m. login no longer masks the 3 p.m. bypass, because the window is evaluated relative to each session instead of "anywhere in the day." Same idea the author intended — just bounded where KQL can actually enforce it.

### The operational caveats that still apply

Fixing the join doesn't make this a fire-and-forget rule. Three things gate it in the real world:

- **Validate the keyword lists against your own logs.** The `Activity` and `Message` strings for GlobalProtect session and auth events vary by PAN-OS firmware and log verbosity. Run a `distinct Activity, Message` against your PAN-OS CEF data and confirm the exact strings before trusting either side. Incomplete *auth* keyword coverage is especially dangerous here — a missed auth string turns legitimate sessions into false positives.
- **Mind cert and SAML flows.** Certificate-based or SAML authentication may not emit an event that matches the auth keywords at all, which can make a perfectly legitimate session look like a bypass. Baseline your auth paths before going to a scheduled rule.
- **Confirm the connector.** This depends entirely on `CommonSecurityLog` being populated by a PAN-OS CEF/Syslog connector with `DeviceVendor` set to `Palo Alto Networks`. If your PAN logs land in a custom table or via a different connector, the query returns a confident, empty, meaningless result.

---

## Two patterns worth stealing

Strip away the malware names and you're left with two reusable primitives:

- **Rhythm** — when you hunt C2, count *distinct time windows* (`dcount(bin(Timestamp, 1h))`), not raw volume. Persistence across time is the signal a beacon can't hide. Count the rhythm, not the racket.
- **Absence** — when the attack is a logic bypass, hunt for the prerequisite that's missing (`leftanti`, or a windowed `leftouter` + `countif`). Just remember that absence detections are only as trustworthy as their time-bound — get the window wrong and the query goes quiet exactly when it matters.

Both of these came straight out of this week's daily briefs, fully written up with ATT&CK mappings, triage runbooks, false-positive notes, and deployment-readiness calls for every single detection — 23 of them this week alone.

If you want this kind of detection content landing in your inbox every day, that's the whole point of the **[Detection Engineering Brief at DevSecOpsDadAttack.com](https://DevSecOpsDadAttack.com)** — fresh threat intel translated straight into deployable detections, so you spend your time tuning and shipping instead of reading and re-deriving.

---

<br/>

# Stay Ahead of Emerging Threats

_Looking for actionable threat intelligence and detection engineering insights?_

DevSecOpsDadAttack publishes daily:

📈 Threat Intelligence Briefs focused on active campaigns, exploitation trends, and operational risk
🛠️ Detection Engineering Briefs with ATT&CK mappings, telemetry requirements, KQL detections, tuning guidance, and triage workflows
🔍 Practical analysis designed for SOC teams, threat hunters, detection engineers, and security leaders

Visit [DevSecOpsDadAttack.com](https://devsecopsdadattack.com) for the latest intelligence and detection content.

<br/>

![DevSecOpsDadAttack!](/assets/img/Attack1.png)

<br/><br/>

# 📚 Want to go deeper?

Anyone can aggregate threat intel.
Very few teams can prove why they acted—or why they didn’t.

The below books are about closing that gap; turning curated signal into defensible decisions across KQL, PowerShell, and the Microsoft security stack.

<br/><br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/hZ1TVpO" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/KQL Toolbox Cover.jpg"
      alt="KQL Toolbox: Turning Logs into Decisions in Microsoft Sentinel"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🛠️ <strong>KQL Toolbox:</strong> Turning Logs into Decisions in Microsoft Sentinel
  </p>
</div>

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/ifIo6eT" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/PowerShell-Cover.jpg"
      alt="PowerShell Toolbox: Hands-On Automation for Auditing and Defense"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🧰 <strong>PowerShell Toolbox:</strong> Hands-On Automation for Auditing and Defense
  </p>
</div>

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/4vveVCI" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg"
      alt="Ultimate Microsoft XDR for Full Spectrum Cyber Defense"
      style="max-width: 340px; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    📖 <strong>Ultimate Microsoft XDR for Full Spectrum Cyber Defense</strong><br/>
    Real-world detections, Sentinel, Defender XDR, and Entra ID — end to end.
  </p>
</div>

<br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)
