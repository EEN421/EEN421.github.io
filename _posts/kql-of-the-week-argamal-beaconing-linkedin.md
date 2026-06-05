# 🛡️ KQL of the Week: Catching Beacons by *Time*, Not Volume

Most beaconing detections ask "how many connections?" The best ones ask "how *persistently* across time?"

This week's Detection Engineering Briefs produced ~23 KQL candidates across npm supply-chain attacks, a PAN-OS GlobalProtect auth bypass (CVE-2026-0257), NetSupport RAT, and a macOS FlutterShell dropper chain. But the query I keep coming back to is the one built for **Argamal RAT** — a remote access trojan recently found hiding inside trojanized game installers (h/t Securelist).

Here's why it's my KQL of the Week. 👇

---

## The problem with "count the connections"

A naive C2 detection thresholds on total connection count. Real malware authors know this, so they go **low-and-slow**: a handful of check-ins per hour, spread out, sitting comfortably under any volume alarm.

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

---

## The three moves that make it work

**1. `dcount(bin(Timestamp, 1h))` is the whole game.**
Binning timestamps into hourly buckets and counting the *distinct* buckets means a beacon that phones home in 4+ separate hours gets surfaced — even if the raw volume stays tiny. Persistence over time is the signal, not noise. `TotalConnections >= 8` is just a floor to drop one-off blips.

**2. Scope to where malware actually lives.**
Filtering `InitiatingProcessFolderPath` to Downloads, Temp, and AppData focuses the hunt on user-writable paths instead of `Program Files`. Argamal runs its payload from exactly these directories — so this isn't an arbitrary filter, it's threat-informed.

**3. Allowlist the legit beacons before they bury you.**
Browsers, OneDrive, Teams, Slack, Discord, Spotify, and Squirrel/`Update.exe` all beacon constantly and live in user space. Excluding them up front is the difference between a usable hunt and 10,000 rows of Slack telemetry. This is the part junior queries always forget.

The final `join` enriches each beacon candidate with the most recent command line via `arg_max`, so the analyst gets context — not just an IP and a process name.

---

## Keeping it honest 🧭

This one ships as **hunting-only**, not a scheduled rule — and rightly so. The thresholds (`>= 4` windows, `>= 8` connections) want baselining against your own environment first. One deployment gate worth flagging: if `InitiatingProcessFolderPath` isn't populated in your `DeviceNetworkEvents`, the `isnotempty()` guard nulls out the entire candidate set. Validate that field is flowing before you trust an empty result.

That's the detection engineering discipline: a clever technique still earns its way into production through tuning, not vibes.

---

**The takeaway:** when you're hunting C2, count the *rhythm*, not the *racket*. Temporal distribution beats raw volume every time.

📬 This query — plus full ATT&CK mappings, triage runbooks, and deployment readiness for every detection — comes from the daily Detection Engineering Brief at **DevSecOpsDadAttack.com**. Threat intel, translated straight into detection engineering action.

What's your go-to KQL pattern for low-and-slow beaconing? Drop it in the comments. 👇

\#DetectionEngineering #KQL #MicrosoftSentinel #DefenderXDR #ThreatHunting #ThreatIntelligence #BlueTeam #DFIR #InfoSec #MITREATTACK
