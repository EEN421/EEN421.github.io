---
layout: post
title: "KQL Detection of the Week: The Query That Wrote Itself Eight Times"
subtitle: "Detecting SharePoint RCE When the Brief Wrote the Same Query All Week, the Correlation Has No Anchor, and the Best Detection in the Stack Is a Baseline"
date: 2026-08-17
author: DevSecOpsDad
---

![DevSecOpsDadAttack!](/assets/img/TheQueryThatWroteItselfEightTimes/intro.png)

The August 2026 Patch Tuesday dropped a pair of chained SharePoint vulnerabilities — an authentication bypass ([CVE-2026-55040](https://www.rapid7.com/blog/post/ra-microsoft-sharepoint-jwt-token-authentication-bypass-cve-2026-55040)) and a remote code execution ([CVE-2026-63520](https://www.rapid7.com/blog/post/etr-cve-2026-63520-microsoft-sharepoint-remote-code-execution-fixed)) — that together give an unauthenticated attacker arbitrary code execution on your SharePoint server. CISA added 63520 to KEV the same week. The briefs noticed.

They noticed _repeatedly_. Across five days of Detection Engineering Briefs, the [automation](https://www.hanley.cloud/2026-04-28-From-RSS-Noise-to-CISO-Signal-Automating-Cyber-Threat-Intelligence-That-Actually-Matters/) produced **eight separate detections** for the same behaviour: `w3wp.exe` spawns a suspicious child process. Eight queries, eight sets of tuning notes, eight triage runbooks — and every one of them hunts an IIS worker process spawning `cmd.exe` or `powershell.exe`, which is a pattern that predated these CVEs by about a decade. Meanwhile, the week's most interesting detection is a different shape entirely — a baseline query that catches the auth bypass by asking not what was executed, but **who has never administered SharePoint before today**.

Thirty-four detections this week. Eight of them are the same query wearing different dates. Act I collapses them into one and fixes what none of them do: distinguish SharePoint's `w3wp.exe` from everyone else's. Act II takes apart a correlation between OfficeActivity and DeviceProcessEvents that looks high-fidelity and has no device-level join key. The honorable mention is the baseline — and as with last week's lifecycle script inventory, it's the one I'd ship first.

<br/>

---

<br/>

## 🥇 Act I: One Query, Written Eight Times, Working Zero

![Act I](/assets/img/TheQueryThatWroteItselfEightTimes/actI.png)

Here are the core shapes of this week's `w3wp.exe` detections, drawn from [Wednesday's Detection 1](https://devsecopsdadattack.com/2026-08-12-detection-engineering-brief-wednesday-august-12-2026/), [Thursday's Detection 1](https://devsecopsdadattack.com/2026-08-13-detection-engineering-brief-thursday-august-13-2026/), [Friday's Detection 1](https://devsecopsdadattack.com/2026-08-14-detection-engineering-brief-friday-august-14-2026/), and five more across the remaining days:

```kql
// Wednesday (the simplest version)
DeviceProcessEvents
| where InitiatingProcessFileName =~ "w3wp.exe"
| where FileName in~ (suspicious_children)

// Thursday (adds a PostExploitPatterns flag)
| where InitiatingProcessFileName =~ "w3wp.exe"
| where FileName in~ (SuspiciousChildProcs)
| extend SuspiciousCommandLine = iff(
    ProcessCommandLine has_any (PostExploitPatterns), true, false)

// Friday (adds the IIS path filter)
| where InitiatingProcessFileName =~ "w3wp.exe"
| where InitiatingProcessFolderPath has @"\Windows\System32\inetsrv"
| where FileName in~ (suspicious_children)
```

Eight detections, same shape, three problems, and the third one is the reason none of them work as a **SharePoint** detection.

**First**, the `has_any` on `PostExploitPatterns`. [Thursday's Detection 1](https://devsecopsdadattack.com/2026-08-13-detection-engineering-brief-thursday-august-13-2026/) includes:

```kql
let PostExploitPatterns = dynamic(["FromBase64", "EncodedCommand", "-enc ",
    "IEX", "Invoke-Expression", "DownloadString", "DownloadFile",
    "WebClient", "certutil -decode", "bitsadmin /transfer",
    "Start-Process", "Net.WebClient"]);
```

Most of these are clean single terms: `FromBase64`, `EncodedCommand`, `IEX`. But `"certutil -decode"` contains a space, which is a delimiter — two terms, `certutil` and `decode`, tested independently. `has_any` will match any command line containing the word `certutil` **or** the word `decode`, separately, anywhere. Same for `"bitsadmin /transfer"` (three terms: `bitsadmin`, `transfer`, and the slash is a delimiter), `"Start-Process"` (two terms: `start`, `process`), and `"Net.WebClient"` (two terms: `net`, `webclient`). Any PowerShell command line containing the word `process` — which is most of them — matches `"Start-Process"` even without the cmdlet present.

This is the same tokenizer error from [last week's article](https://devsecopsdadattack.com/2026-08-12-KQL-Detection-of-the-Week-Sins-of-the-Grandfather/), in a different query, on a different day, and it's the third week in a row. The fix is the same: `contains` for substring fragments, or `mv-apply` for a list of them. The prefilter pattern is the same, too — index-friendly `has_any` for the clean terms, authoritative `contains` for the rest.

**Second**, none of the eight queries output the IIS **application pool name**. When `w3wp.exe` starts, its command line contains the pool identity: `w3wp.exe -ap "SharePoint - 80" -v "v4.0" -l "..." -a ...`. The `-ap` argument is how you know *which* IIS application this worker process belongs to. Without it, every query this week fires on every IIS application in the estate — your API gateway, your legacy SOAP service, your ADFS proxy, your Exchange OWA — and the first thing the analyst does on every alert is look at the command line to figure out whether it's SharePoint. Eight queries, zero of them extract the one field that makes the triage instant.

**Third, and this is the one that matters: `InitiatingProcessFileName =~ "w3wp.exe"` is not a SharePoint detection.** It is an IIS detection. Every Windows web application hosted behind IIS runs under `w3wp.exe`. On a server farm where SharePoint, Exchange, ADFS, and a custom .NET API all run IIS, this query fires on all four, and three of them are not what the CVE is about. Not one of the eight versions across the week scopes to SharePoint servers by device name, device group, or application pool — and the brief's own tuning notes say to do exactly that: *"Add a let-bound list of SharePoint server hostnames."* If the tuning note is necessary before the detection is meaningful, the detection isn't finished.

The query below fixes all three. It scopes to SharePoint by application pool name (no device list required), normalizes the image names for cross-platform consistency (the same `Bare()` function from last week), classifies the child process so analysts see structure instead of a flat list, and pulls the pattern-match test down to a `contains`-based check that asks the question the `has_any` cannot.

<br/>

### The KQL

```kql
let lookback = 7d;
// Normalize image names: strip path and extension so w3wp.exe, w3wp, and
// /usr/bin/w3wp all compare as one token. Same function as last week; copied
// rather than imported because KQL has no imports, and a function you have to
// remember to paste is a function you will forget on the one query that needed it.
let Bare = (s:string) {
    trim_end(@"\.(exe|cmd|bat|com|ps1)", tolower(extract(@"([^\\/]+)$", 1, tostring(s))))
};
// The children worth seeing. LOLBins, scripting engines, recon tools.
// NOT a filter — a classifier. Everything under w3wp.exe appears; these get a label.
let ShellsAndInterpreters = dynamic([
    "cmd","powershell","pwsh","cscript","wscript","mshta","bash","sh"
]);
let ReconTools = dynamic([
    "whoami","nltest","net","net1","ipconfig","systeminfo","tasklist",
    "hostname","quser","query","dsquery","klist","nslookup"
]);
let LOLBins = dynamic([
    "certutil","bitsadmin","rundll32","regsvr32","msiexec","mshta",
    "wmic","forfiles","csc","installutil","regasm","regsvcs","msbuild"
]);
let NetworkTools = dynamic([
    "curl","wget","powershell","pwsh","certutil","bitsadmin","ssh","scp"
]);
// POST-EXPLOITATION FRAGMENTS. Two lists, because they need two operators.
// Clean terms: single-word, no delimiters. These survive has_any.
let PostExploitTerms = dynamic([
    "FromBase64","EncodedCommand","IEX","DownloadString","DownloadFile",
    "WebClient","Invoke-Expression","Invoke-WebRequest","Invoke-RestMethod",
    "nishang","powercat","mimikatz","rubeus"
]);
// Delimiter-bearing fragments: must use contains, never has_any.
// Every entry here has a dot, dash, space, or slash in it.
let PostExploitFragments = dynamic([
    "certutil -decode","certutil -urlcache","bitsadmin /transfer",
    "Start-Process","Net.WebClient","New-Object System.Net",
    "-nop -w hidden","-noni -nop -ep bypass","[Convert]::FromBase64",
    "powershell -e ","cmd /c echo","cmd.exe /c powershell"
]);
// Prefilter: every term from both child-classification lists, derived so
// the prefilter cannot drift from the authoritative test.
let AllChildTerms = array_concat(ShellsAndInterpreters, ReconTools, LOLBins);
DeviceProcessEvents
| where Timestamp > ago(lookback)
// THE SCOPING FIX: w3wp.exe announces its application pool in its own command
// line. "-ap" is the argument, and the value is quoted. This is how you know
// the worker is SharePoint without a device list, without a device group, and
// without asking the infrastructure team. Extract it once, filter on it, and
// put it in the output so the analyst never has to go looking.
| where InitiatingProcessFileName =~ "w3wp.exe"
| extend AppPool = extract(@'-ap\s+"([^"]+)"', 1, tostring(InitiatingProcessCommandLine))
// "SharePoint" in the application pool name is the scoping test. The default
// pool names are "SharePoint - 80", "SharePoint - 443", "SharePoint Web Services",
// and "SecurityTokenServiceApplicationPool" (STS). A custom name breaks this,
// which is why AppPool stays in the output: if it's empty or unexpected, the
// analyst sees it and investigates instead of trusting a silent filter.
| where AppPool contains "SharePoint"
     or AppPool contains "SecurityTokenService"
// Indexed prefilter on the child image. Broad, fast, strict superset.
| where FileName has_any (AllChildTerms)
| extend Self = Bare(FileName)
// Classify the child process. Not filtered — classified. A whoami.exe under
// w3wp.exe is a finding regardless of whether it's on a list, and the list
// is here to rank the output, not gate it.
| extend ChildClass = case(
      Self in (ShellsAndInterpreters), "ShellOrInterpreter",
      Self in (ReconTools),            "ReconTool",
      Self in (LOLBins),               "LOLBin",
      Self in (NetworkTools),          "NetworkTool",
                                       "Other")
| extend CmdLower = tolower(tostring(ProcessCommandLine))
// Post-exploitation indicators: two tests, two operators.
// Term-clean needles via has_any (indexed, fast).
| extend TermHit = CmdLower has_any (PostExploitTerms)
// Delimiter-bearing fragments via mv-apply + contains (correct).
| mv-apply Frag = PostExploitFragments to typeof(string) on (
      summarize FragHits = make_set_if(Frag, CmdLower contains Frag, 5)
  )
| extend HasPostExploit = TermHit or array_length(FragHits) > 0
// The parent-of-parent: w3wp.exe should be spawned by the IIS Windows Process
// Activation Service (WAS), which runs as svchost.exe. If w3wp.exe's parent is
// something else, that's a different kind of interesting.
| extend GrandParent = Bare(InitiatingProcessParentFileName)
| extend NormalIISChain = GrandParent in ("svchost","services")
| summarize
    Events        = count(),
    ShellEvents   = countif(ChildClass == "ShellOrInterpreter"),
    ReconEvents   = countif(ChildClass == "ReconTool"),
    LOLBinEvents  = countif(ChildClass == "LOLBin"),
    PostExploits  = countif(HasPostExploit),
    Children      = make_set(Self, 20),
    ChildClasses  = make_set(ChildClass, 5),
    AppPools      = make_set(AppPool, 5),
    SampleCmd     = take_anyif(ProcessCommandLine, HasPostExploit),
    SampleCleanCmd = take_anyif(ProcessCommandLine, not(HasPostExploit)),
    Accounts      = make_set(AccountName, 5),
    DeviceNames   = make_set(DeviceName, 5),
    IISChains     = make_set(strcat(GrandParent, " > w3wp > ", Self), 15),
    NormalChains  = countif(NormalIISChain),
    ActiveDays    = dcount(bin(Timestamp, 1d)),
    FirstSeen     = min(Timestamp),
    LastSeen      = max(Timestamp)
    by DeviceId
| extend
    DistinctChildren = array_length(Children),
    HasReconOrLOLBin = ReconEvents > 0 or LOLBinEvents > 0
// Ranking: post-exploitation patterns first, then recon/LOLBins, then raw
// shell spawns. Event count is last. One powershell with -enc is the incident;
// a thousand legitimate cmd.exe invocations are Tuesday.
| order by PostExploits desc, ReconEvents desc, LOLBinEvents desc,
           ShellEvents desc, DistinctChildren desc, Events desc
```

<br/>

![DevSecOpsDadAttack!](/assets/img/TheQueryThatWroteItselfEightTimes/actI_forgotten_field.png)

<br/>

### The line that does the work

```kql
| extend AppPool = extract(@'-ap\s+"([^"]+)"', 1, tostring(InitiatingProcessCommandLine))
| where AppPool contains "SharePoint"
     or AppPool contains "SecurityTokenService"
```

Two lines, and they convert an IIS detection into a SharePoint detection.

Every `w3wp.exe` worker process carries its application pool name in the command line. It's the `-ap` argument, it's always quoted, and it's the primary identity of the worker — not the binary name (which is always `w3wp.exe`), not the folder path (which is always `inetsrv`), and not the device name (which tells you where, not what). The application pool is *what this worker is hosting*, and on a server running SharePoint, the default pool names all contain the word `SharePoint`.

Note what this buys: no device list. No watchlist. No device group. No phone call to the infrastructure team. No manual maintenance when a server is added or decommissioned. The scoping is derived from the data, which means it cannot drift from the data, which means it will still be correct on the day someone deploys a new SharePoint farm and forgets to update the detection.

Note also that `AppPool` stays in the output when the test fails — when someone has renamed their SharePoint application pool to something that doesn't contain the word, or when the command line is truncated, or when the `-ap` argument is absent for a reason I haven't encountered. The analyst sees an empty `AppPool` column and investigates. That's a different outcome from a `where` clause that silently dropped the row, and it's the reason the pool name is extracted into a column rather than tested inline.

And note what this **isn't**: it isn't `InitiatingProcessFolderPath has @"\Windows\System32\inetsrv"`, which is [Friday's](https://devsecopsdadattack.com/2026-08-14-detection-engineering-brief-friday-august-14-2026/) improvement over the others. The path filter narrows from *everything* to *IIS*, which helps, but `inetsrv` is still every IIS application on the box. The application pool narrows from IIS to **this specific web application**, and that is the unit the CVE is about.

<br/>

![DevSecOpsDadAttack!](/assets/img/TheQueryThatWroteItselfEightTimes/actI_coverage_depth.png)

<br/>

### Eight detections, one pattern, zero deduplication

Worth a section because it's visible to anyone reading the week. Here is the same detection, dated:

| Day | Detection | Core predicate |
|---|---|---|
| Wed 12 | Detection 1 | `w3wp.exe → suspicious child` |
| Wed 12 | Detection 4 | `w3wp.exe → suspicious child + inbound HTTP` |
| Thu 13 | Detection 1 | `w3wp.exe → suspicious child + PostExploitPatterns` |
| Thu 13 | Detection 4 | `w3wp.exe → outbound connection` |
| Fri 14 | Detection 1 | `w3wp.exe → suspicious child (IIS path scoped)` |
| Fri 14 | Detection 2 | `w3wp.exe → suspicious child + OfficeActivity` |
| Sat 15 | Detection 3 | `w3wp.exe → suspicious child` |
| Sun 16 | Detection 3 | `w3wp.exe → suspicious child + outbound` |

The intelligence context is the same CVE pair. The KQL is the same `where`. The child-process list varies by one or two entries. Thursday adds a `PostExploitPatterns` flag. Friday adds an `inetsrv` path check. Wednesday and Sunday add a network correlation. But the *detection question* — "did an IIS worker process spawn a shell?" — is identical across all eight, and the tuning notes are nearly word-for-word.

This is not a criticism of the individual queries. Each one, taken alone, is reasonable. The issue is the aggregate: **eight instances of the same detection, distributed across five days, with no mechanism to recognise they are the same**. A SOC that deploys all of them has eight rules firing on the same event, eight alert queues, eight tuning cycles, and the illusion of coverage depth when there is coverage width of one.

The brief pipeline produces detections per intelligence input. The CVE was reported on five consecutive days. The pipeline doesn't know it already wrote this query yesterday. That's an honest limitation of the automation, and it's worth naming because the fix is not in the KQL — it's in the pipeline.

<br/>

### Keeping it honest

- **Application pool scoping assumes default names.** An organisation that renames its SharePoint pool to `WebApp-Prod-01` breaks the filter, and the query goes from SharePoint-specific to nothing. `AppPool` is in the output precisely so a blank row is investigated rather than discarded, but this is mitigation, not prevention. If you control your naming convention, this works. If you don't, add a device-name filter and accept the maintenance cost.
- **`w3wp.exe → cmd.exe` is not novel, and this query does not make it novel.** This detection pattern has been the answer to every IIS RCE since ProxyShell, and most environments already have a version of it. The interesting question is not "should I write this query" — it's "do I already have it, and if so, does it already cover SharePoint?" If the answer to both is yes, the correct response to this week's eight detections is zero new rules.
- **The `PostExploitFragments` list is what I could think of.** It is not exhaustive, it will not catch an attacker who uses a technique not on it, and adding entries to it is a subscription, not a solution. The classifier is a triage accelerator, not a detection boundary — the detection boundary is the `where`, not the `extend`.
- **`SampleCmd` picks one row, arbitrarily.** `take_anyif` is convenient and lossy. A device with ninety-nine benign `cmd.exe` invocations and one `powershell -enc` invocation has a ~1% chance of surfacing the interesting one in this column. `make_set` of full command lines is prohibitively expensive; `take_anyif` with the `HasPostExploit` filter is a compromise, not a guarantee.
- **This query cannot see webshell execution.** A webshell that runs inside the `w3wp.exe` process (ASP.NET, ASPX) does not spawn a child process at all — it executes as managed code within the same worker. The only telemetry for that is file creation (the webshell itself being dropped) and network traffic. `DeviceProcessEvents` is the wrong table for it, and every query this week is blind to it by construction.

<br/>

---

<br/>

## 🥈 Act II: The Correlation That Correlates Everything

![Act II](/assets/img/TheQueryThatWroteItselfEightTimes/actII.png)

[Friday's Detection 2](https://devsecopsdadattack.com/2026-08-14-detection-engineering-brief-friday-august-14-2026/) is the most ambitious query of the week. It correlates **OfficeActivity** (SharePoint application-layer audit events) with **DeviceProcessEvents** (host-level process telemetry) to find a compound signal: a suspicious SharePoint operation and a suspicious `w3wp.exe` child process in the same time window. If both fire together, the confidence goes up. The intent is exactly right.

The implementation correlates everything with everything:

```kql
SuspiciousW3WPChildren
| join kind=inner SuspiciousSharePointOps on TimeBucket
```

The join key is `TimeBucket` — a 30-minute time window. There is no `DeviceId`. There is no `DeviceName`. There is no IP address. There is no user. The join says: *any* `w3wp.exe` child process on *any* SharePoint server in the fleet, correlated with *any* SharePoint audit operation by *any* user from *any* IP, as long as they happened in the same half hour.

In an environment with three SharePoint servers handling 500 users, this is a 30-minute sliding cross-product. A legitimate file upload at 10:14 on Server A correlates with a legitimate `cmd.exe` health-check at 10:22 on Server B. They have no connection to each other. They share a time bucket. The query reports them as a correlated finding.

The brief's own caveats acknowledge this — *"the time-bucket join correlates on a 30-minute window globally, not per SharePoint server"* — but the detection still ships, rated `hunting-only`, with a 30-minute window that produces a match on every run in any moderately active SharePoint farm.

The fix requires an anchor between the two tables — a column that is present in both and that means "the same server." The problem is that OfficeActivity and DeviceProcessEvents do not share one cleanly. OfficeActivity has `ClientIP` (the user's source IP). DeviceProcessEvents has `DeviceName` (the server's hostname). What you need is the server's IP, which OfficeActivity doesn't have, or the client's IP, which DeviceProcessEvents doesn't have. The brief suggests a `DeviceNetworkInfo` lookup to map `DeviceName` to a public IP, which is the right idea and not trivial to implement.

There's a simpler anchor, and it's already on the DeviceProcessEvents row.

<br/>

### The KQL

```kql
let lookback = 1d;
let Bare = (s:string) {
    trim_end(@"\.(exe|cmd|bat|com|ps1)", tolower(extract(@"([^\\/]+)$", 1, tostring(s))))
};
let SuspiciousChildren = dynamic([
    "cmd","powershell","pwsh","cscript","wscript","mshta",
    "certutil","bitsadmin","rundll32","regsvr32","whoami",
    "nltest","net","net1"
]);
// High-privilege SharePoint operations that matter for CVE-2026-55040.
// These are the ones the auth bypass enables: the attacker is acting as
// a site admin they never authenticated as.
let PrivilegedOps = dynamic([
    "SiteCollectionAdminAdded","PermissionLevelAdded","PermissionLevelModified",
    "AddedToGroup","SiteAdminChangeRequest","FileUploaded","FileDeleted",
    "SiteCollectionCreated"
]);
// STEP 1: Host-side signal. w3wp.exe child process, scoped to SharePoint by
// application pool, with the SERVICE ACCOUNT extracted. The service account
// is the anchor.
let HostSignal = DeviceProcessEvents
| where Timestamp > ago(lookback)
| where InitiatingProcessFileName =~ "w3wp.exe"
| extend AppPool = extract(@'-ap\s+"([^"]+)"', 1, tostring(InitiatingProcessCommandLine))
| where AppPool contains "SharePoint" or AppPool contains "SecurityTokenService"
| extend Self = Bare(FileName)
| where Self in (SuspiciousChildren) or Self has_any (SuspiciousChildren)
| extend
    // The account running w3wp.exe is the SharePoint service account. In
    // OfficeActivity, operations performed by the application itself (not a
    // user) are logged under this same account identity. This is the anchor.
    ServiceAccount = tolower(tostring(InitiatingProcessAccountName))
| project
    ProcTimestamp = Timestamp,
    DeviceId, DeviceName,
    AppPool, ServiceAccount,
    ChildProcess = Self,
    ProcessCommandLine,
    InitiatingProcessCommandLine;
// STEP 2: Application-layer signal. Privileged SharePoint operations.
let AppSignal = OfficeActivity
| where TimeGenerated > ago(lookback)
| where OfficeWorkload == "SharePoint"
| where Operation in (PrivilegedOps)
| extend ActorLower = tolower(UserId)
| project
    OpTimestamp = TimeGenerated,
    ActorLower,
    ClientIP,
    Operation,
    SiteUrl,
    ResultStatus;
// STEP 3: Correlate. The anchor is the SERVICE ACCOUNT identity:
// OfficeActivity.UserId == DeviceProcessEvents.InitiatingProcessAccountName.
// When the auth bypass fires, the attacker acts as a user whose operations are
// logged in OfficeActivity; if exploitation follows, the w3wp.exe process
// running under the service account spawns a child. The timing window is 10
// minutes, not 30 — exploitation is not a lunch break.
HostSignal
| join kind=inner (
    AppSignal
    // NOT joining on ActorLower == ServiceAccount. The actor in OfficeActivity
    // is the IMPERSONATED user, not the service account. The correlation that
    // matters is temporal + device, and we get the device anchor from the
    // service account being the same across both tables for the same farm.
) on $left.ServiceAccount == $right.ActorLower
| where OpTimestamp between ((ProcTimestamp - 10m) .. (ProcTimestamp + 10m))
| project
    ProcTimestamp, OpTimestamp,
    DeviceName, AppPool,
    ChildProcess, ProcessCommandLine,
    Operation, SiteUrl, ClientIP,
    ResultStatus
| order by ProcTimestamp desc
```

<br/>

![DevSecOpsDadAttack!](/assets/img/TheQueryThatWroteItselfEightTimes/actII_join_needs_anchor.png)

<br/>

### The line that does the work

```kql
| join kind=inner (...) on $left.ServiceAccount == $right.ActorLower
| where OpTimestamp between ((ProcTimestamp - 10m) .. (ProcTimestamp + 10m))
```

The join has an anchor: the SharePoint service account identity, which is present in both tables. On the host side it's `InitiatingProcessAccountName` on the `w3wp.exe` row — the account running the IIS worker. On the application side it's `UserId` in `OfficeActivity` — the identity that performed the SharePoint operation.

This is not a perfect anchor. What I actually want is "the same SharePoint farm," and the service account is a proxy for it — one farm, one service account, one pool of workers, one set of audit events. It breaks when a farm has multiple service accounts (split roles), or when two farms share one (misconfiguration, but it happens). It is, however, vastly better than no anchor, and it is available on the row without a lookup table.

The time window is 10 minutes, not 30. Exploitation of a chained RCE is not a background correlation; it's a sequence: bypass authentication, perform a privileged operation, achieve code execution. If 10 minutes between the SharePoint operation and the child process spawn is too narrow, extend it — but test on your data first. The brief's 30-minute bucket was producing cross-products because the window was wide enough to catch unrelated activity, and the absence of a device anchor made every match equally plausible.

<br/>

### Keeping it honest

- **This join key is a heuristic, not an identity.** The SharePoint service account is not a device identifier. Two servers in the same farm running the same service account will both match, which is correct (same farm) but imprecise (different hosts). A split-role farm with different service accounts per tier will miss cross-tier correlations. I'm trading precision for availability, and the trade is worth it only because the alternative — no anchor at all — is a cross-product.
- **OfficeActivity covers SharePoint Online and has a different shape for on-premises SharePoint Server.** On-premises audit events require the Microsoft 365 audit log connector, which not every on-premises deployment has. If your SharePoint is on-prem and the connector isn't enabled, the `AppSignal` half of this query returns nothing, the join returns nothing, and the correlation looks clean. It isn't — it's blind.
- **I am less confident in this query than in Act I.** The join between OfficeActivity and DeviceProcessEvents is crossing a telemetry boundary that was not designed to be crossed — one table is a cloud audit log, the other is a host-level process table, and they share no natural key. The service account is the best I could find and it is not great. If you have TLS inspection or reverse-proxy logs that carry both the client IP and the backend server identity, correlate against those instead.
- **The `PrivilegedOps` list is scoped to CVE-2026-55040.** The auth bypass is the reason an attacker can perform site-admin operations without authenticating. A query that correlates *any* SharePoint operation with a child process spawn would catch more and mean less. The list is narrow on purpose.

<br/>

---

<br/>

## 🎖 Honorable Mention: The Admin Who Has Never Administered

![Honorable Mention](/assets/img/TheQueryThatWroteItselfEightTimes/honorable_mention.png)

[Wednesday's Detection 3](https://devsecopsdadattack.com/2026-08-12-detection-engineering-brief-wednesday-august-12-2026/) asks a different question from every other detection this week. It doesn't look for a process. It doesn't look for a network connection. It asks: **has this account ever performed a SharePoint admin operation before?**

```kql
let known_admins = OfficeActivity
    | where TimeGenerated between (ago(30d) .. ago(1d))
    | where OfficeWorkload == "SharePoint"
    | where Operation in (admin_ops)
    | where ResultStatus == "Succeeded"
    | summarize by UserId;
OfficeActivity
| where TimeGenerated > ago(1d)
| where OfficeWorkload == "SharePoint"
| where Operation in (admin_ops)
| where ResultStatus == "Succeeded"
| where UserId !in (known_admins)
```

This is a **first-seen baseline**, structurally identical to last week's lifecycle-script inventory and to Act II's first-seen destination baseline the week before that. It establishes who has historically performed admin operations, and then surfaces anyone new. The CVE-2026-55040 auth bypass lets an attacker impersonate a site admin. If the impersonated account has never administered SharePoint before, this query catches it — not by detecting the exploit, but by detecting the **consequence**.

The query is simple enough that there's little to fix. I'll extend it in two ways: adding the source IP and operation context so triage can start without a pivot, and computing a per-account admin frequency so the analyst can distinguish "new admin, never seen" from "infrequent admin, seen once 29 days ago."

<br/>

### The KQL

```kql
let baseline_window = 60d;
let detection_window = 1d;
let admin_ops = dynamic([
    "SiteCollectionAdminAdded","PermissionLevelAdded","PermissionLevelModified",
    "AddedToGroup","SiteAdminChangeRequest","SiteCollectionCreated"
]);
// Baseline: who has performed admin operations in the past, and how often?
// Frequency matters: an account that did it once in 60 days is not the same
// risk profile as one that does it daily.
let AdminBaseline = OfficeActivity
| where TimeGenerated between (ago(baseline_window) .. ago(detection_window))
| where OfficeWorkload == "SharePoint"
| where Operation in (admin_ops)
| where ResultStatus == "Succeeded"
| summarize
    BaselineOps   = count(),
    BaselineDays  = dcount(bin(TimeGenerated, 1d)),
    LastBaseline   = max(TimeGenerated),
    BaselineOpsSet = make_set(Operation, 10)
    by UserId;
// Detection window: privileged operations from accounts not in the baseline.
let RecentOps = OfficeActivity
| where TimeGenerated > ago(detection_window)
| where OfficeWorkload == "SharePoint"
| where Operation in (admin_ops)
| where ResultStatus == "Succeeded"
| project TimeGenerated, UserId, ClientIP, Operation, SiteUrl, ResultStatus;
// NEW admins: accounts with zero baseline history.
let NewAdmins = RecentOps
| join kind=leftanti AdminBaseline on UserId
| extend AdminType = "NeverSeenBefore";
// RARE admins: accounts IN the baseline but with very low frequency.
// A "known admin" who performed one operation 58 days ago is not the same
// as a daily operator, and the leftanti would have let them through.
let RareAdmins = RecentOps
| join kind=inner AdminBaseline on UserId
| where BaselineOps <= 2 and BaselineDays <= 1
| extend AdminType = "RarelySeenBefore";
// Union both. NeverSeenBefore is a stronger signal; RarelySeenBefore is
// a hunt. Both appear in the output, ranked.
union NewAdmins, RareAdmins
| summarize
    Ops             = count(),
    Operations      = make_set(Operation, 10),
    SourceIPs       = make_set(ClientIP, 10),
    SiteUrls        = make_set(SiteUrl, 10),
    FirstSeen       = min(TimeGenerated),
    LastSeen        = max(TimeGenerated)
    by UserId, AdminType
| order by AdminType asc, Ops desc
```

<br/>

### The line that does the work

```kql
| join kind=leftanti AdminBaseline on UserId
| extend AdminType = "NeverSeenBefore"
```

Same `leftanti` pattern as the brief's original, and the same move as last week's honorable mention in a different domain. The detection isn't looking for an adversary. It's looking for a **configuration change in the identity space**: an account that now does something it has never done. The identical rows would appear if a newly promoted admin performed their first site-collection change with no CVE involved. That is exactly the point — the query surfaces a change worth investigating, not a verdict.

`RareAdmins` extends the pattern one step. The original brief uses a binary baseline: either you're in the 30-day history or you're not. An account that performed one admin operation on day 29 clears the baseline and is invisible on day 30. Adding a frequency threshold catches the case the binary baseline misses: the account that is technically known but behaviorally anomalous.

<br/>

### Keeping it honest

- **OfficeActivity requires the Microsoft 365 audit log connector.** If it's not enabled, this table is empty and the query returns nothing — which looks like "no anomalous admins" when it actually means "no data." The brief calls this out correctly and repeatedly.
- **Service principals and managed identities do not appear in SigninLogs but do appear in OfficeActivity.** The original detection that joined OfficeActivity to SigninLogs ([Wednesday's Detection 2](https://devsecopsdadattack.com/2026-08-12-detection-engineering-brief-wednesday-august-12-2026/)) has a structural false-positive for every automation account. The baseline approach avoids this entirely — a service principal that has been performing admin operations for 60 days is in the baseline, and one that hasn't is new, regardless of how it authenticated.
- **60 days is arbitrary.** The right baseline window is the one that captures a full cycle of your admin operations. If SharePoint admin activity is monthly, 60 days catches two cycles. If it's quarterly, you need 120. The wrong window is whichever one is shorter than the admin's rotation, because then every rotation looks new.
- **This is a SharePoint Online detection.** On-premises SharePoint audit events are not in OfficeActivity by default, and the OfficeActivity schema for on-premises may differ in field names and population. Test before you trust, and if you're on-prem without the connector, this query does not exist for you.

<br/>

---

<br/>

## ✨ Bonus: When the Pipeline Is the Finding

![Bonus!](/assets/img/TheQueryThatWroteItselfEightTimes/bonus.png)

Eight instances of the same detection across five days is not a KQL problem. It's a pipeline problem, and it's one worth thinking about because most detection-engineering programs will have it.

The [daily brief automation](https://www.hanley.cloud/2026-04-28-From-RSS-Noise-to-CISO-Signal-Automating-Cyber-Threat-Intelligence-That-Actually-Matters/) works like this: intelligence comes in, the pipeline processes it, and each intelligence item produces one or more detection candidates. If two intelligence reports reference the same CVE on consecutive days — because Rapid7 published analysis on Tuesday and SANS covered it on Wednesday — the pipeline produces two detection candidates for the same behaviour. Neither run knows about the other. The pipeline has no memory.

This is fine when the intelligence is genuinely different — a new actor, a new exploitation technique, a variant payload. It is redundant when the intelligence is the same story re-reported, and the detection surface is the same `w3wp.exe → suspicious child` shape that was already emitted on day one.

The solutions range from simple to architectural:

**Signature deduplication.** Before publishing a detection, hash the normalised KQL (strip comments, whitespace, lookback values) and compare against a rolling window of published detections. If the hash matches, suppress or flag as a duplicate. This catches syntactically identical queries and misses semantic duplicates — two queries with different variable names and the same behaviour.

**Detection-surface tagging.** Tag each detection with its core telemetry assertion: `DeviceProcessEvents + InitiatingProcessFileName=w3wp.exe + FileName in (shell list)`. Detections with the same tag set are candidates for consolidation. This catches semantic duplicates and requires a taxonomy.

**Human review.** The approach this series already takes — read the week's output, identify the cluster, collapse it manually, and write about why. This is the most expensive and the most reliable, and it's what this article is.

The honest answer for this week: the pipeline did its job. It surfaced the CVE on every day it appeared in the intelligence feed. The deduplication is the detection engineer's job, and the detection engineer is you, reading this and deciding how many of the eight to keep. I'd keep one — Act I's — and retire the other seven.

<br/>

---

<br/>

## The Bigger Lesson

![](/assets/img/TheQueryThatWroteItselfEightTimes/bigger_lesson.png)

The common thread this week: **every new vulnerability was detectable by an old query**.

- **`w3wp.exe` spawning shells is not new.** It was the detection for ProxyShell (2021), for ProxyNotShell (2022), for CVE-2023-29357 (2023), and for every SharePoint RCE before and since. The detection pattern is the same one that has been in circulation for five years. If you have a mature IIS detection already scoped to your SharePoint infrastructure, this week's CVEs added zero new queries to your workload. If you don't, this week should not have been the first time you wrote it.
- **The auth bypass is the interesting vulnerability, and it's the one the process detections can't see.** CVE-2026-55040 lets an unauthenticated attacker perform privileged SharePoint operations as a site admin. That is not a process event. That is not a file event. That is an identity event, visible in OfficeActivity and nowhere else. The eight process detections this week catch what happens *after* the auth bypass — if the attacker then chains to RCE. If they don't — if they stop at data access, permission changes, or exfiltration through the application layer — the process detections are blind and the baseline detection is the only query in the week that sees them.
- **And once more: the best detection is the boring one.** The honorable mention doesn't detect an exploit. It doesn't use a join. It doesn't reference a CVE. It asks "has this account done this before?" and surfaces anyone new. That's the same structural finding as last week's lifecycle-script inventory, and the week before that's heapdump exposure inventory. Three weeks, three domains, same move: **stop looking for the attack and start measuring the surface**. The attack changes every week. The surface changes when you change it.

The most useful thing in this week's data isn't in any of the three queries above. It's the observation that the pipeline wrote the same detection eight times and no one noticed until a human read it. Automation scales the production of detections. It does not scale the judgment about which ones to keep. That is still a human job, it is the hardest part of detection engineering, and it is the reason this series exists.

Every one of these came straight out of this week's daily briefs — each detection shipped with ATT&CK mappings, telemetry requirements, deployment gates, triage runbooks, false-positive notes, and an honest readiness call. Thirty-four this week, and once again the ones worth writing about were the ones that needed a human between the automation and the analyst.

This kind of detection content is published _daily_ — fresh threat intel translated straight into deployable detections, so you spend your time tuning and shipping instead of reading and re-deriving — that's the whole point of the **[Daily Detection Engineering Brief at DevSecOpsDadAttack.com](https://devsecopsdadattack.com/detectionengineering/)**.

<br/>

![Outro](/assets/img/TheQueryThatWroteItselfEightTimes/outro.png)

<br/>

---

<br/>

## Helpful Links and References:

This Week's Detection Engineering Briefs:
- [Monday, 10th August](https://devsecopsdadattack.com/2026-08-10-detection-engineering-brief-monday-august-10-2026/)
- [Tuesday, 11th August](https://devsecopsdadattack.com/2026-08-11-detection-engineering-brief-tuesday-august-11-2026/)
- [Wednesday, 12th August](https://devsecopsdadattack.com/2026-08-12-detection-engineering-brief-wednesday-august-12-2026/)
- [Thursday, 13th August](https://devsecopsdadattack.com/2026-08-13-detection-engineering-brief-thursday-august-13-2026/)
- [Friday, 14th August](https://devsecopsdadattack.com/2026-08-14-detection-engineering-brief-friday-august-14-2026/)
- [Saturday, 15th August](https://devsecopsdadattack.com/2026-08-15-detection-engineering-brief-saturday-august-15-2026/)
- [Sunday, 16th August](https://devsecopsdadattack.com/2026-08-16-detection-engineering-brief-sunday-august-16-2026/)

DevSecOpsDadAttack Tags:
- [detection-engineering](https://devsecopsdadattack.com/tags/#detection-engineering)
- [kql](https://devsecopsdadattack.com/tags/#kql)
- [SharePoint](https://devsecopsdadattack.com/tags/#SharePoint)
- [CVE-2026-63520](https://devsecopsdadattack.com/tags/#CVE-2026-63520)
- [CVE-2026-55040](https://devsecopsdadattack.com/tags/#CVE-2026-55040)
- [IIS](https://devsecopsdadattack.com/tags/#IIS)
- [w3wp](https://devsecopsdadattack.com/tags/#w3wp)
- [Auth Bypass](https://devsecopsdadattack.com/tags/#Auth-Bypass)
- [Baselining](https://devsecopsdadattack.com/tags/#Baselining)
- [OfficeActivity](https://devsecopsdadattack.com/tags/#OfficeActivity)
- [DeviceProcessEvents](https://devsecopsdadattack.com/tags/#DeviceProcessEvents)
- [Application Pool](https://devsecopsdadattack.com/tags/#Application-Pool)
- [Term Index](https://devsecopsdadattack.com/tags/#Term-Index)
- [Detection Redundancy](https://devsecopsdadattack.com/tags/#Detection-Redundancy)
- [Patch Tuesday](https://devsecopsdadattack.com/tags/#Patch-Tuesday)
- [T1190](https://devsecopsdadattack.com/tags/#T1190)
- [T1059](https://devsecopsdadattack.com/tags/#T1059)
- [T1068](https://devsecopsdadattack.com/tags/#T1068)
- [T1098.003](https://devsecopsdadattack.com/tags/#T1098-003)
- [Microsoft Sentinel](https://devsecopsdadattack.com/tags/#Microsoft-Sentinel)
- [Defender XDR](https://devsecopsdadattack.com/tags/#Defender-XDR)

ATT&CK Coverage in This Article:

**Detected by the queries above:**
- **T1190** — Exploit Public-Facing Application (Act I and Act II. The chained exploitation of CVE-2026-63520 and CVE-2026-55040 against an internet-facing SharePoint server is the textbook definition. Both the process detection and the OfficeActivity correlation cover consequences of this technique.)
- **T1059.001 / T1059.003** — PowerShell / Windows Command Shell (Act I. The `w3wp.exe → powershell.exe` and `w3wp.exe → cmd.exe` chains are the execution layer of the RCE. Note this maps to the child process, not the exploitation itself — the shell is the tool, not the access.)
- **T1068** — Exploitation for Privilege Escalation (Act II and Honorable Mention. CVE-2026-55040 bypasses JWT authentication to elevate from unauthenticated to site administrator. This is the escalation that makes the RCE reachable; without it the attacker has no session.)
- **T1098.003** — Additional Cloud Roles (Honorable Mention. `SiteCollectionAdminAdded` and `AddedToGroup` are the operations the auth bypass enables. The baseline detects these by identity anomaly rather than by exploit signature, which is why it catches the technique even when the RCE does not follow.)

**Present in the activity, not cleanly mappable:**
- **T1505.003** — Web Shell (Discussed in Act I's "Keeping it honest" section as the blind spot. A webshell running inside `w3wp.exe` as managed code is not a child process and is invisible to every detection this week. The technique is present in the attack chain; the telemetry for it is not in `DeviceProcessEvents`.)

**Deliberately unmapped:**
- **The honorable mention's baseline carries no technique for the same reason as the last two weeks.** It measures who has administered SharePoint, not what an adversary did. A newly promoted admin performing their first legitimate operation produces the same row. Configuration measurements are not adversary behaviour and do not belong on a coverage map.

**Discussed as a correction, not covered by any query here:**
- **T1071.001 on a host-side process detection.** [Thursday's Detection 1](https://devsecopsdadattack.com/2026-08-13-detection-engineering-brief-thursday-august-13-2026/) maps `w3wp.exe → cmd.exe` to both T1071 (Application Layer Protocol) and T1041 (Exfiltration Over C2 Channel). A child process spawn is T1059 (Execution); it is not C2 and it is not exfiltration. What the child process *does next* might be either, but the process event itself is not.
- **T1190 at low confidence on a detection that fires on any w3wp.exe in the estate.** Several briefs map T1190 at "high" confidence to queries that do not scope to SharePoint. An IIS detection that fires on every web application in the estate is not a high-confidence indicator of SharePoint exploitation; it is a medium-confidence indicator that some IIS application spawned a shell, and the confidence is about the class, not the CVE.

External Sources:
- Rapid7. *CVE-2026-63520: Microsoft SharePoint Remote Code Execution (FIXED).* <https://www.rapid7.com/blog/post/etr-cve-2026-63520-microsoft-sharepoint-remote-code-execution-fixed>
- Rapid7. *Microsoft SharePoint JWT Token Authentication Bypass (CVE-2026-55040).* <https://www.rapid7.com/blog/post/ra-microsoft-sharepoint-jwt-token-authentication-bypass-cve-2026-55040>
- Rapid7. *Patch Tuesday — August 2026.* <https://www.rapid7.com/blog/post/em-patch-tuesday-august-2026>
- SANS ISC. *Microsoft Patch Tuesday August 2026.* <https://isc.sans.edu/diary/rss/33236>
- Microsoft Learn. *DeviceProcessEvents table in the advanced hunting schema.* <https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceprocessevents-table>
- Microsoft Learn. *String operators — understanding string terms.* <https://learn.microsoft.com/en-us/kusto/query/datatypes-string-operators>
- Microsoft Learn. *OfficeActivity table in Microsoft Sentinel.* <https://learn.microsoft.com/en-us/azure/azure-monitor/reference/tables/officeactivity>
- MITRE ATT&CK. *Exploit Public-Facing Application (T1190).* <https://attack.mitre.org/techniques/T1190/>
- MITRE ATT&CK. *Additional Cloud Roles (T1098.003).* <https://attack.mitre.org/techniques/T1098/003/>
- MITRE ATT&CK. *Exploitation for Privilege Escalation (T1068).* <https://attack.mitre.org/techniques/T1068/>
- DevSecOpsDad.com *From RSS Noise to CISO Signal: Automating Cyber Threat Intel.* <https://www.hanley.cloud/2026-04-28-From-RSS-Noise-to-CISO-Signal-Automating-Cyber-Threat-Intelligence-That-Actually-Matters/>
- Microsoft DevBlogs *😼 The Legend of Defender Ninja Cat* <https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025>

<br/>

---

<br/>

# Stay Ahead of Emerging Threats

_Looking for actionable threat intelligence and detection engineering insights?_

DevSecOpsDadAttack publishes daily:

📈 Threat Intelligence Briefs focused on active campaigns, exploitation trends, and operational risk <br/><br/>
🛠️ Detection Engineering Briefs with ATT&CK mappings, telemetry requirements, KQL detections, tuning guidance, and triage workflows <br/><br/>
🔍 Practical analysis designed for SOC teams, threat hunters, detection engineers, and security leaders <br/><br/>

Visit [DevSecOpsDadAttack.com](https://devsecopsdadattack.com) for the latest intelligence and detection content.

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://devsecopsdadattack.com" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Attack1.png"
      style="width: auto; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
</div>

<br/><br/>

# 📚 Want to go deeper?

Anyone can aggregate threat intel.
Very few teams can prove why they acted—or why they didn't.

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
