![DevSecOpsDadAttack!](/assets/img/Meeting2050/meeting_in_2050.png)
This week's seven briefs produced **28 KQL candidates** across a second SharePoint RCE wave (CVE-2026-58644), the WordPress core RCE (CVE-2026-63030) and its web-shell aftermath, ACR Stealer riding ClickFix lures into browser credential stores, BitLocker turned into an extortion tool against office print infrastructure, WebDAV remote paths used to launch execution, a Check Point SmartConsole authentication bypass (CVE-2026-16232) that ran Friday through Sunday, Teams external-guest social engineering, Microsoft's Q2 2026 email threat landscape and its machine-speed M365 attack chains, and — the one this week is about — **Project CAV3RN storing its command-and-control traffic inside Outlook calendar events**.

Last week's theme was *absence*: the sign-in that never happened, the author who was never there. The detections won by demanding a corroborating record the attacker couldn't forge.

This week the attacker solved that problem in the most annoying way possible. **They stopped bringing infrastructure.**

There is no C2 domain to block, because the C2 is `graph.microsoft.com`. There is no beacon on the wire to fingerprint, because the beacon is an OAuth token request to `login.microsoftonline.com`. There is no encryptor to signature, because the encryptor is `manage-bde.exe` and Microsoft signed it. There is no rogue admin console, because the console is your firewall's. Every artifact this week belongs to *you*.

And the best of them — the one that made me put down the coffee — hid its dead drop in the single most-ignored data store in the enterprise: a calendar, in a one-hour window, **on 13 May 2050**. Twenty-four years out. Nobody scrolls there. Nobody has ever scrolled there. It is the most-synced, least-read database in your tenant.

So this week's KQL of the Week is the CAV3RN calendar channel, told in three queries and one correction the briefs got wrong. Act I hunts the **dead drop** from inside the mailbox tenant. Act II hunts the **infected host**, which — and this is the part that matters — is almost never the same organization. The honorable mention hunts the fallback channel, where the attacker encodes their config into things that look exactly like IPv6 addresses and are not addresses at all.

<br/>

---

<br/>

## 🥇 Act I: The Standing Meeting Nobody Will Ever Attend

![Act I](/assets/img/Meeting2050/dead_drop.png)

Here's the problem the winning query solves.

On July 21, [Kaspersky's GReAT team published an analysis of a new Project CAV3RN communication module](https://securelist.com/project-cav3rn-cyberespionage-framework-using-outlook-and-dns/120757/) — a .NET Native AOT DLL named `AzureCommunication.dll` that replaces the framework's older HTTP/WebSocket C2 component. The framework is tied, with low confidence, to OilRig (APT34), and the targeting is Israeli organizations. The briefs picked it up Tuesday, Wednesday, and Thursday and produced four separate detection candidates from it.

The mechanic is beautiful and infuriating in equal measure. The module authenticates to Microsoft Graph as an *application* — `client_credentials` grant, `.default` scope, no user in the loop — against a **compromised third-party Microsoft 365 mailbox**, and then uses that mailbox's default calendar as a dead drop. Operator-to-agent commands arrive as encrypted attachments on a calendar event. Agent-to-operator results go back the same way. There's even a heartbeat event, deleted and recreated on each cycle.

Every single one of those events lives in the same fixed one-hour window: **2050-05-13, 22:00–23:00 UTC**. Not a rolling window. Not "next year." A specific hour, a quarter-century from now, hardcoded, because a meeting in 2050 will never render in anyone's Outlook view, ever.

The subjects are equally deliberate:

| Subject shape | Purpose |
|---|---|
| `Event ID: <agent-id>` | Operator → agent command; deleted after the agent consumes it |
| `Boss update ID: <agent-id>1500` | Agent heartbeat; previous one deleted and replaced each cycle |
| `Boss Report ID: <agent-id>1500` | Agent → operator command output |
| `d` | Temporary subject used at creation, before the real subject is patched on |

That last row is the one to stare at. The module doesn't create an event with its final subject. It creates the event with a placeholder, uploads the encrypted attachments, and *then* PATCHes the subject into place. Which means the mailbox audit log records a **create, then a subject rewrite, seconds apart, on the same item** — a shape that legitimate calendaring almost never produces, because Outlook sends you the whole event in one operation.

So the detection has three independent handles: the marker strings, the single-character placeholder subject, and the create-then-rename latency. It does not need to know anything about 2050 — the calendar year is what makes triage take thirty seconds instead of thirty minutes.

<br/>

### The KQL

```kql
let lookback = 7d;
let RenameWindowSec = 300;
let DeadDropMarkers = dynamic(["Event ID:", "Boss update ID:", "Boss Report ID:"]);
let CalendarOps = OfficeActivity
| where TimeGenerated > ago(lookback)
| where OfficeWorkload =~ "Exchange"
| where Operation in~ ("Create", "Update", "SoftDelete", "HardDelete", "MoveToDeletedItems")
| extend
    ItemId      = tostring(Item.Id),
    ItemSubject = tostring(Item.Subject),
    FolderPath  = tostring(Item.ParentFolder.Path)
| where FolderPath has "Calendar"
| where isnotempty(ItemId)
| project
    TimeGenerated, ItemId, ItemSubject, Operation, FolderPath,
    UserId, UserType, ClientIP, ClientInfoString, AppId, MailboxOwnerUPN;
let MarkerHits = CalendarOps
| where ItemSubject has_any (DeadDropMarkers)
| extend Signal = "SubjectMarker", RenameLatencySec = int(null);
let PlaceholderRenames = CalendarOps
| sort by ItemId asc, TimeGenerated asc
| extend
    PrevItemId  = prev(ItemId),
    PrevOp      = prev(Operation),
    PrevSubject = prev(ItemSubject),
    PrevTime    = prev(TimeGenerated)
| where ItemId == PrevItemId
| where PrevOp =~ "Create" and Operation =~ "Update"
| where strlen(trim(@"\s", PrevSubject)) <= 2
| where PrevSubject != ItemSubject
| extend RenameLatencySec = datetime_diff('second', TimeGenerated, PrevTime)
| where RenameLatencySec between (0 .. RenameWindowSec)
| extend Signal = "PlaceholderRename"
| project-away Prev*;
union MarkerHits, PlaceholderRenames
| summarize
    Events       = count(),
    Signals      = make_set(Signal),
    Subjects     = make_set(ItemSubject, 10),
    Operations   = make_set(Operation, 10),
    ClientIPs    = make_set(ClientIP, 5),
    AppIds       = make_set(AppId, 5),
    MinRenameSec = min(RenameLatencySec),
    FirstSeen    = min(TimeGenerated),
    LastSeen     = max(TimeGenerated)
    by MailboxOwnerUPN, UserId, UserType
| extend BothSignals = array_length(Signals) > 1
| order by BothSignals desc, Events desc
```

<br/>

### The line that does the work

Not the marker list. Markers are strings, strings are free, and the operator can change `Boss Report ID:` to `Q3 Planning Sync` in the time it takes to recompile. It's this:

```kql
| where strlen(trim(@"\s", PrevSubject)) <= 2
```

That is the detection with a shelf life. The placeholder subject isn't a naming choice the operator made for fun — it's **forced by the protocol**. The module cannot create the event with its final subject, because it needs an event ID to attach the encrypted payload to, and it doesn't want a half-built dead drop sitting in the calendar advertising itself while the upload is in flight. Create blank, attach, then rename. That sequence is load-bearing. Rename the markers all you like; the create-then-patch shape stays, because the alternative is a race condition in your own C2.

The supporting choice is the **entity-keyed union**. `MarkerHits` and `PlaceholderRenames` are two genuinely different questions, and I've unioned them anyway — but only because both sides are projected to the same columns and both resolve to the *same entity*, `MailboxOwnerUPN`. The `summarize` at the bottom then earns its keep: `BothSignals` promotes any mailbox where a marker string *and* a placeholder rename both landed, which is the CAV3RN shape and essentially nothing else's.

This is worth stating precisely, because the briefs got it wrong on Tuesday and it's an easy mistake to make. **A union is legitimate when the branches share an entity key and illegitimate when they don't.** Tuesday's Detection 4 unioned calendar Graph activity (keyed on `AccountId`) with a DNS AAAA volume spike (keyed on `DeviceName`), then padded the second branch with `AccountId = ""`, `CalendarOps = 0`, `ActionTypes = dynamic([])` so the schemas would line up. The result is two unrelated hunts sharing an output grid, with half the columns structurally empty on every row. Nothing correlates, because there's nothing to correlate *on* — the brief's own caveat notes that `IPAddress` from `CloudAppEvents` and `DeviceName` from `DeviceNetworkEvents` can't be equated without a device inventory. If you're padding columns to make a union compile, you don't have one detection. You have two, in a trench coat.

<br/>

### A KQL note...

`prev()` requires a **serialized** row set, and `sort by` provides that serialization. Two things about that line will bite you, and they're covered properly in the bonus section below — but the short version, because it changes whether this query works at all:

- `| sort by ItemId asc, TimeGenerated asc` — the `asc` is not decorative. **KQL's `sort by` defaults to descending.** Omit it and `prev()` hands you the *later* row, inverting the entire sequence test into a silent no-op.
- `| where ItemId == PrevItemId` — `prev()` walks the whole serialized table and does not respect groups. Without that guard, the first row of every calendar item borrows the last row of the previous item, and you manufacture "sequences" that never occurred.

<br/>

### Keeping it honest

The briefs filed the CAV3RN calendar work as **hunting-only** every time it appeared, and that's correct. Here's what has to be true before this means anything:

- **`Item` is a dynamic column and its shape is not guaranteed.** `Item.Subject` and `Item.ParentFolder.Path` are populated for Exchange mailbox audit records in most tenants, but coverage depends on your mailbox audit configuration and the operation type. If those extractions come back empty, `tostring()` returns an empty string silently and the query returns a clean, meaningless nothing. Validate first: `OfficeActivity | where OfficeWorkload =~ "Exchange" | where isnotempty(Item) | take 20 | project Operation, Item`. Wednesday's brief made the same class of assumption in the other direction, filtering on `Operation in ("UpdateCalendarItem", "CreateCalendarItem", ...)` — operation names that aren't in the Exchange audit schema at all. Its own caveats section flags this. Survey the real values before you trust any of it.
- **Subject content is a licensing and configuration question.** Mailbox audit logging must be enabled and the Office 365 connector configured, and some tenants restrict subject capture on privacy grounds. A hunt that depends on reading meeting subjects is a hunt that needs sign-off from someone other than you.
- **Wednesday's version keyed on `UserAgent`, and that field belongs to the attacker.** The query filtered to calendar operations where the user agent didn't contain `Mozilla`, `Outlook`, `Microsoft Office`, or `MacOutlook`. Consider what that asks of the adversary: set one HTTP header to a string starting with `Mozilla` and the detection is gone. This is an allowlist built entirely from a value the client controls, which is the same failure family as authenticating on a claim you didn't verify. Worse, the preceding `isnotempty(UserAgent)` drops every record where the field isn't populated — and the brief's own caveats note that `UserAgent` is unreliable for Graph API calls in `OfficeActivity`. The filter over-trusts what it sees and discards what it doesn't. Neither half is recoverable by tuning.
- **Volume thresholds are the wrong axis for this threat.** Tuesday gated on `CalendarOps > 20` over seven days; Thursday on `CallCount > 20`. A room-booking integration clears twenty calendar operations before lunch. A CAV3RN agent polling every six hours clears twenty-eight in a week — barely over the line, and one config change from being under it. You cannot separate a beacon from a business integration by counting, because busy is not the same as regular. If you want to go at this from the cadence side, measure the *variance* of the inter-arrival gaps, not the total.
- **Thursday's Detection 3 queried the wrong table entirely.** It hunted `AuditLogs` for Graph calendar operations. `AuditLogs` is Entra ID's **directory control plane** — app registrations, consent grants, role assignments, group membership. Reading or writing a calendar event is **data plane**, and it does not write an `AuditLogs` record no matter how many times it happens. The query is syntactically fine, will run without error, and will return nothing forever. For app-only Graph activity, the tables that actually see it are `OfficeActivity` / `MailboxAudit` (the operation), `CloudAppEvents` (if you're licensed for Defender for Cloud Apps), and `AADServicePrincipalSignInLogs` (the token acquisition). That last one is genuinely useful here and no brief this week reached for it:

```kql
AADServicePrincipalSignInLogs
| where TimeGenerated > ago(30d)
| where ResultType == 0
| where ResourceDisplayName =~ "Microsoft Graph"
| summarize
    SignIns   = count(),
    IPs       = make_set(IPAddress, 10),
    Countries = make_set(Location, 10),
    FirstSeen = min(TimeGenerated),
    LastSeen  = max(TimeGenerated)
    by AppId, ServicePrincipalName, ServicePrincipalId
| extend AgeDays = datetime_diff('day', LastSeen, FirstSeen)
| order by FirstSeen desc
```

Every CAV3RN `get` and `send` cycle starts with a `client_credentials` token request. A service principal that first appears this month, authenticates to Graph from one or two addresses, and never stops, is a much shorter list than "applications that touch calendars."

- **And the finding is a *lead*, not a verdict.** Confirm in the mailbox, not in the SIEM. Pull the item and look at its start time. If it's a real meeting, it's on a real date. If it's a dead drop, it's in 2050. That's the whole triage step.

Act I hunts the mailbox. Which raises the question the briefs never asked — and it's the one that changes your coverage.

<br/>

---

<br/>

## 🥈 Act II: You Are Probably Not the Mailbox

![Act II](/assets/img/Meeting2050/two_victims.png)

Every CAV3RN detection filed this week hunts tenant-side telemetry: `CloudAppEvents`, `OfficeActivity`, `AuditLogs`. Calendar operations, service principals, Graph calls. All of it assumes the suspicious calendar activity will show up in **your** logs.

Read the GReAT analysis again, though. The dead-drop mailbox belongs to a **compromised Israeli law firm** — a third party. The infected endpoints are somewhere else entirely. Those are two different organizations, two different tenants, two different SOCs.

Which means there are two victims in this campaign and they have almost nothing in common:

- **If you are the mailbox tenant**, you have full visibility. The calendar operations, the app-only sign-ins, the placeholder renames — all of it lands in your audit log. Act I is your query. You may also have no infected endpoints at all; your role in this intrusion is *hosting the drop box*.
- **If you are the endpoint victim**, you have none of that. The calendar operations happen in someone else's tenant. Your `OfficeActivity` is clean. Your `CloudAppEvents` is clean. Your service principal sign-in logs are clean. From your side, an unremarkable process makes ordinary HTTPS connections to `login.microsoftonline.com` and `graph.microsoft.com` — two hosts that are allowlisted on every proxy on earth, including yours.

Run Act I against an infected fleet and it returns nothing, forever, and the nothing looks exactly like health. That's not a tuning problem. It's a **telemetry-domain mismatch**, and it's the most expensive kind of blind spot because the query appears to be working.

So Act II changes sides. And the best detection for the endpoint victim turns out to be five lines long.

The module looks for a relative file named `logAzure.txt` before it does anything. If the file isn't there, it builds the configuration from hardcoded values and **writes the whole thing to disk** — tenant ID, client ID, client secret, target mailbox, DNS bootstrap host, and both RSA keys, in JSON. Because the code supplies only a filename with no path, Windows resolves it against the working directory of whatever process loaded the DLL.

That's not a C2 artifact. That's a plaintext credential file dropped into an arbitrary directory by the malware itself, and it is the highest-fidelity, lowest-cost signal in this entire campaign.

<br/>

### The KQL

```kql
let lookback = 30d;
let ConfigArtifacts = dynamic(["logAzure.txt"]);
let GraphEndpoints  = dynamic(["graph.microsoft.com", "login.microsoftonline.com"]);
let ExpectedGraphClients = dynamic([
    "outlook.exe", "olk.exe", "teams.exe", "ms-teams.exe", "msteams.exe",
    "onedrive.exe", "msedge.exe", "chrome.exe", "firefox.exe",
    "excel.exe", "winword.exe", "powerpnt.exe", "onenote.exe",
    "officeclicktorun.exe", "msoia.exe",
    "powershell.exe", "pwsh.exe", "azurecli.exe", "msedgewebview2.exe",
    "mssense.exe", "senseir.exe", "msmpeng.exe"
]);
let ConfigWrites = DeviceFileEvents
| where Timestamp > ago(lookback)
| where ActionType in ("FileCreated", "FileModified", "FileRenamed")
| where FileName in~ (ConfigArtifacts)
| project
    Timestamp, DeviceId, DeviceName,
    Process     = InitiatingProcessFileName,
    ProcessPath = InitiatingProcessFolderPath,
    Account     = InitiatingProcessAccountName,
    Detail      = strcat(FolderPath, " <- ", InitiatingProcessCommandLine)
| extend Signal = "ConfigArtifactWrite";
let UnexpectedGraphClients = DeviceNetworkEvents
| where Timestamp > ago(lookback)
| where ActionType == "ConnectionSuccess"
| where RemoteUrl in~ (GraphEndpoints)
| where isnotempty(InitiatingProcessFileName)
| where not(InitiatingProcessFileName in~ (ExpectedGraphClients))
| summarize
    Timestamp   = min(Timestamp),
    Connections = count(),
    Endpoints   = make_set(RemoteUrl, 5)
    by DeviceId, DeviceName,
       Process     = InitiatingProcessFileName,
       ProcessPath = InitiatingProcessFolderPath,
       Account     = InitiatingProcessAccountName
| extend
    Detail = strcat(tostring(Connections), " connections to ", strcat_array(Endpoints, ", ")),
    Signal = "UnexpectedGraphClient"
| project-away Connections, Endpoints;
union ConfigWrites, UnexpectedGraphClients
| summarize
    Signals   = make_set(Signal),
    Processes = make_set(Process, 10),
    Paths     = make_set(ProcessPath, 10),
    Accounts  = make_set(Account, 5),
    Details   = make_set(Detail, 10),
    FirstSeen = min(Timestamp),
    LastSeen  = max(Timestamp)
    by DeviceId, DeviceName
| extend
    HasConfigArtifact = set_has_element(Signals, "ConfigArtifactWrite"),
    SignalCount       = array_length(Signals)
| order by SignalCount desc, HasConfigArtifact desc, LastSeen desc
```

<br/>

### The line that does the work

```kql
| where FileName in~ (ConfigArtifacts)
```

That's it. Two words of logic against `DeviceFileEvents`, and it beats every clever thing in this article on cost-per-unit-confidence. `logAzure.txt` is not a filename that appears in legitimate software. There is no tuning phase, no baseline, no threshold, no exclusion list. It runs in seconds across thirty days of fleet telemetry and it either returns zero rows or it returns an incident.

It is also, obviously, the most fragile detection here — it dies the moment the developers change one string in the next build. So it's paired, not standalone, and the pairing is the point: `UnexpectedGraphClients` asks a question the filename change doesn't answer. **Which processes on this endpoint are talking to Microsoft Graph, and are they processes that have any business doing so?** Graph is a browser-and-Office-suite destination. A binary that isn't in that family, authenticating to `login.microsoftonline.com` and then calling `graph.microsoft.com`, is doing something a normal endpoint does not do — no matter what it calls its config file.

Note the join key: `DeviceId`. Both branches are host-scoped, both resolve to a device, and the `summarize` collapses them onto one row per endpoint with `SignalCount` doing the ranking. *That's* what a legitimate union looks like — same entity, two questions, one verdict. Contrast Thursday's version, which correlated `graph_callers` back to the full network stream with `join kind=inner ... on DeviceName` and then filtered `InitiatingProcessFileName =~ SuspectProcess` after the fact. It gets the right answer, but it fans out first — a device with four suspect processes multiplies every candidate row by four before the filter throws three away. The fix is to join on the compound key up front:

```kql
| extend SuspectProcess = InitiatingProcessFileName
| join kind=inner graph_callers on DeviceName, SuspectProcess
```

Same answer. A quarter of the shuffle.

<br/>

### Keeping it honest

I'd take `ConfigWrites` to a scheduled rule tomorrow. `UnexpectedGraphClients` is a hunt, and the gap between those two is where the work is:

- **Thursday's allowlist has last week's bug in it.** The query excluded destinations with `not(RemoteUrl has_any ("graph.microsoft.com", "login.microsoftonline.com", "microsoft.com", "windows.com", "windowsupdate.com"))`. `has_any` is substring matching, so `microsoft.com` matches `login.microsoftonline.com.c2.example.net` and `windowsupdate.com.attacker.io` — an attacker registers one subdomain and walks out through your allowlist. This is precisely the `RemoteIP startswith "172."` mistake from the AsyncAPI honorable mention wearing different clothes: string operations standing in for structured matching, in a filter whose job is to *suppress*. Every over-broad match in a negative filter is an invisible hole. Act II uses `in~` for exact host equality, which cannot over-suppress. If you need suffix matching, `endswith` on a normalized hostname is the floor, not `has_any`.
- **The expected-client list is the whole detection, and mine is not yours.** Every enterprise runs Graph SDK background services nobody documented: RMM agents, backup tools, CASB shims, HR integrations, a PowerShell scheduled task somebody wrote in 2023. Run `DeviceNetworkEvents | where RemoteUrl in~ ("graph.microsoft.com") | summarize count() by InitiatingProcessFileName, InitiatingProcessFolderPath | order by count_ desc` and build the list from your own fleet before this goes anywhere near a schedule.
- **Name-only exclusions are spoofable, and `teams.exe` from `%TEMP%` is not `teams.exe`.** Harden to `(FileName, FolderPath)` pairs or signer checks before promotion — the same correction the CI/CD detection needed last week, for the same reason.
- **`RemoteUrl` is not reliably populated in `DeviceNetworkEvents`.** A connection recorded with only `RemoteIP` will never match `in~ (GraphEndpoints)` and drops out silently. That's a false-negative direction, which is the safer failure, but know it's there: your Graph-client inventory is a floor, not a census.
- **Working directory means the path is unpredictable.** Because the module supplies a bare filename, `logAzure.txt` lands wherever the host process happened to be running — `System32`, a user profile, a service directory, anywhere. Don't scope the file query by `FolderPath`. Let it fire from anywhere and read the path as evidence: *where* it landed tells you which process loaded the DLL.
- **Coverage is the silent gate, again.** No MDE agent, no `DeviceFileEvents`, no finding. A quiet result across a fleet you haven't fully onboarded is a coverage report wearing a clean bill of health.

Act I hunts the drop box. Act II hunts the agent. The last act hunts what the agent does when the drop box stops answering.

<br/>

---

<br/>

## 🎖 Honorable Mention: The Address That Was Never an Address

![Honorable Mention](/assets/img/Meeting2050/not_an_address.png)

If Acts I and II win on where they point, the third query wins on the sheer nerve of what it's looking for.

CAV3RN has a fallback. When the OAuth token request fails, or the `GET /v1.0/organization` validation call comes back wrong — the tenant got cleaned up, the app registration got revoked, the secret rotated — the module doesn't die and it doesn't phone a backup C2. It **re-reads its own configuration out of DNS**.

The mechanism is the good part. The module queries AAAA records against an actor-controlled domain (`cloudlanecdn[.]com`, delegated to four in-bailiwick nameservers that all resolve to the same two addresses — logical redundancy, not real redundancy). The IPv6 addresses that come back are not addresses. They're **16-byte containers**. The module throws away the first two bytes and treats the remaining fourteen as payload, reassembling a new tenant ID, client ID, client secret, and mailbox address fragment by fragment, then writing the whole recovered config back to `logAzure.txt` and reconnecting.

The query structure is where it becomes detectable, because the protocol has to encode a lot into a hostname:

- `d.<hex-agent-id>.<field-index>.p.<host>` asks for a field's length
- `d.<hex-agent-id>.<field-index>.<offset>.q.<host>` asks for 14 bytes at an offset

The agent ID is seven characters, hex-encoded to fourteen, and embedded in every single query. So the detectable shape is: a leftmost label `d`, a second label of even-length hexadecimal, and a bare single-character `p` or `q` marker label sitting between the parameters and the domain. That's a *lot* of structure for something pretending to be a hostname.

```kql
let lookback = 7d;
let BootstrapDomains = dynamic(["cloudlanecdn.com"]);
let FailureSentinel  = "2001:4998:44:3507::8000";
DnsEvents
| where TimeGenerated > ago(lookback)
| where SubType =~ "LookupQuery"
| where QueryType =~ "AAAA"
| extend QueryName = tolower(trim_end(@"\.", Name))
| extend Labels = split(QueryName, ".")
| extend LabelCount = array_length(Labels)
| where LabelCount >= 5
| extend
    FirstLabel  = tostring(Labels[0]),
    SecondLabel = tostring(Labels[1])
| extend
    ShapeMatch = FirstLabel == "d"
        and SecondLabel matches regex @"^[0-9a-f]+$"
        and strlen(SecondLabel) % 2 == 0
        and strlen(SecondLabel) >= 8
        and (set_has_element(Labels, "p") or set_has_element(Labels, "q")),
    DomainMatch   = QueryName has_any (BootstrapDomains),
    SentinelMatch = tostring(IPAddresses) has FailureSentinel
| where ShapeMatch or DomainMatch or SentinelMatch
| summarize
    Queries        = count(),
    DistinctNames  = dcount(QueryName),
    SampleNames    = make_set(QueryName, 10),
    MarkerLabels   = make_set(iff(set_has_element(Labels, "p"), "p", "q"), 2),
    SentinelSeen   = max(SentinelMatch),
    ShapeSeen      = max(ShapeMatch),
    DomainSeen     = max(DomainMatch),
    FirstSeen      = min(TimeGenerated),
    LastSeen       = max(TimeGenerated)
    by ClientIP, Computer
| extend EntropyProxy = DistinctNames * 1.0 / Queries
| order by DistinctNames desc
```

The line that does the work is the shape test, and specifically this half of it:

```kql
set_has_element(Labels, "p") or set_has_element(Labels, "q")
```

Note what that *isn't*. It isn't `QueryName has ".p."`, which would match `example.pizza.com` and half the internet, and it isn't a positional index like `Labels[LabelCount - 3]`, which quietly assumes the registrable domain is exactly two labels and breaks the moment the operator moves to something under `.co.uk`. `set_has_element()` does exact element matching against the parsed label array — it asks "is there a label that is *precisely* the single character `p`," which is a question ordinary DNS almost never answers yes to. Splitting the hostname into labels first and reasoning about labels as structured data, rather than pattern-matching against the string, is what makes the test both specific and portable.

`DomainMatch` and `SentinelMatch` are the cheap IOC lanes riding alongside — `cloudlanecdn[.]com` and the hardcoded failure address `2001:4998:44:3507::8000` (which lives inside a Yahoo allocation, for reasons GReAT couldn't determine either). Those two will be dead within the month. `ShapeMatch` outlives them.

**One correction, and it's the important one.** Thursday's Detection 4 was titled "DNS AAAA Queries from Non-Browser Processes," and it does not query DNS record types, because it can't — the brief says so plainly in its own caveats: `DeviceNetworkEvents` doesn't expose query type, and `DnsQueryResponse` isn't a valid `ActionType` for that table. So the query substitutes a behavioral proxy: find non-browser processes that hit `graph.microsoft.com`, then find other external connections from those same processes. That's honest engineering under a constraint, and I respect that the brief documented it rather than shipping a query that returns zero rows and calling it clean.

But the constraint isn't real. It's a *table* constraint, not a *telemetry* constraint. `DnsEvents` — the Windows DNS Server connector, or Sysmon Event ID 22, or your resolver's own logs — carries `QueryType` as a first-class field. If you want AAAA, you need a DNS source, and MDE endpoint telemetry is not one. The general lesson is worth more than this campaign: **when a query's title describes something the table cannot express, the answer is usually a different table, not a cleverer proxy.** Check your DNS ingestion before you build around its absence:

```kql
DnsEvents
| where TimeGenerated > ago(1d)
| summarize Events = count() by QueryType
| order by Events desc
```

If that returns nothing, you have a data-source project, not a detection project — and that's a far more useful finding than a proxy query that half-works.

Keep this one **hunting-only**. Legitimate AAAA volume is enormous on IPv6-enabled networks, `ClientIP` in `DnsEvents` is your resolver's view and may be a forwarder rather than the real originator, and the shape test will occasionally catch a CDN or telemetry vendor doing genuinely weird things with hostnames. Confirm the shape by eye — the label structure is distinctive enough that thirty seconds of reading `SampleNames` will tell you whether you're looking at a protocol or a coincidence.

<br/>

---

<br/>

## ✨ Bonus: `serialize`, `prev()`, and detecting a *sequence* instead of an *event*

![Sequence](/assets/img/Meeting2050/in_order.png)

Act I's placeholder-rename test needed something most KQL doesn't: it needed to know what happened *immediately before* a given row, within that row's own history. Last week's bonus covered `leftanti`, which reasons about sets — is this key present in that population? This week's is the other axis: reasoning about **order**.

<br/>

### Rows in KQL don't have neighbors — until you say so

By default a KQL result set is unordered. There's no "previous row," because there's no row order to be previous in. `prev()` and `next()` therefore require a **serialized** row set, and there are exactly three ways to get one:

| How | What it does |
|---|---|
| `sort by` / `order by` | Sorts *and* serializes. The usual entry point. |
| `serialize` | Freezes the current arbitrary order into a row order. Fast, and almost never what you want alone. |
| `range`, `row_number()`, `top` | Naturally ordered producers. |

And serialization is **not sticky**. `where`, `extend`, `project`, and `take` preserve it. `summarize`, `join`, `union`, and `mv-expand` destroy it — after any of those, `prev()` will fail or, worse, silently operate on a re-shuffled order. If you need sequence logic after an aggregation, re-`sort` before you reach for `prev()`.

<br/>

### The three ways `prev()` lies to you

`prev()` is a sharp tool with no guard rails, and every failure mode is silent:

- **`sort by` defaults to descending.** This is the one that gets people. `| sort by TimeGenerated` gives you newest-first, so `prev()` returns the *later* event and `next()` returns the earlier one. Every sequence test you wrote is now backwards. It won't error. It'll just return a different, plausible-looking, wrong answer — often zero rows, which reads as "clean." Write `asc` explicitly, every time, even when you think you know the default.
- **`prev()` does not respect partitions.** It walks the entire serialized table top to bottom. Sort by `ItemId, TimeGenerated` and the first row of item B sees the last row of item A as its "previous" — different entity, different timeline, fabricated sequence. The `| where ItemId == PrevItemId` guard in Act I isn't defensive coding, it's **required for correctness**. Every `prev()` needs a partition guard or a `partition` operator around it. The parallel to last week is exact: with `leftanti`, a bad key *creates* findings; with an unguarded `prev()`, a partition boundary *creates* sequences. Both failure modes generate exactly the artifact you were hunting for, which is the worst possible direction for a bug to fail in.
- **`prev()` returns null at the boundary and nulls don't compare the way you hope.** The first row of the whole table has no predecessor. Comparisons against null quietly evaluate false, so boundary rows vanish — usually fine, occasionally the difference between catching the first beacon and catching the second.

<br/>

### The three ways to write a sequence detection

`prev()` is one of three, and they trade off differently:

```kql
// 1. prev() with a partition guard — cheapest, best for adjacent-pair tests
| sort by ItemId asc, TimeGenerated asc
| extend PrevOp = prev(Operation), PrevId = prev(ItemId)
| where ItemId == PrevId and PrevOp =~ "Create" and Operation =~ "Update"

// 2. partition — same logic, guard enforced by the operator instead of by you
| partition hint.strategy=native by ItemId (
    sort by TimeGenerated asc
    | extend PrevOp = prev(Operation)
    | where PrevOp =~ "Create" and Operation =~ "Update"
)

// 3. summarize + make_list — best when you want the whole ordered history
| sort by ItemId asc, TimeGenerated asc
| summarize OpSequence = make_list(Operation), Subjects = make_list(ItemSubject) by ItemId
| where array_length(OpSequence) >= 2
| where tostring(OpSequence) has 'Create","Update'
```

Option 2 is the one to reach for when the partition guard starts feeling like something you might forget. Option 3 is what you want when the question is "show me the whole story of this item" rather than "did these two things happen back to back" — but note that `make_list` only preserves order if the input was serialized first, so the `sort` is doing real work, not decoration.

For genuine multi-stage state machines — sign-in, then rule creation, then bulk download, in that order, within a window — none of these three is right. That's the `scan` operator, which walks a serialized table maintaining explicit state and is the correct tool for the M365 chain detection in Sunday's brief. `scan` is heavier and considerably less readable, but it's the only one of the four that can express "these five things, in this order, with backtracking."

<br/>

### The self-check that makes sequence detections trustworthy

Same habit as last week, different shape. Before you trust a `prev()` result, prove the partition guard is doing something:

```kql
let Base = OfficeActivity
| where TimeGenerated > ago(1d)
| where OfficeWorkload =~ "Exchange"
| extend ItemId = tostring(Item.Id)
| where isnotempty(ItemId)
| sort by ItemId asc, TimeGenerated asc
| extend PrevItemId = prev(ItemId);
union
    (Base | summarize Rows = count() | extend Population = "All rows"),
    (Base | where ItemId == PrevItemId | summarize Rows = count() | extend Population = "Same item as previous"),
    (Base | where ItemId != PrevItemId or isnull(PrevItemId) | summarize Rows = count() | extend Population = "Partition boundary (discarded)")
```

Two things to read off it. First, the three counts must reconcile — if they don't, your sort key isn't what you think it is. Second, and more useful: **if the discarded boundary count is nearly the whole table, your sequence detection has almost nothing to work with.** Most calendar items are touched exactly once, so most rows *are* boundaries. That's expected here. But if you run the same check against process events and find 95% boundaries, your partition key is too granular and the sequence you're hunting can't exist in the data as keyed.

The one-line takeaway: **`leftanti` reasons about membership, `prev()` reasons about order, and order is the more fragile of the two — because a sort direction and a partition boundary are both invisible when they're wrong.** Say `asc` out loud. Guard the partition. Then the sequence means something.

<br/>

---

<br/>

## The Bigger Lesson

![](/assets/img/Meeting2050/borrowed_trust.png)

Seven briefs, twenty-eight candidates, and one thread running through nearly all of them: **this week's attackers didn't bring anything.**

- **The C2 was a calendar.** Not a domain you can block, not a beacon you can fingerprint — an app-only token, a Graph API call, and an appointment in 2050 that no human will ever open (Act I). When the channel is trusted infrastructure, the detection has to move to the *shape of the usage*: a placeholder subject, a rename seconds later, a protocol constraint the operator can't rename away.
- **The malware's best tell was its own housekeeping.** Not the encryption, not the tradecraft, not the dead drop — a config file written to disk because the developers wanted persistence across restarts (Act II). The five-line query beat everything clever in this article. Look for the artifact the adversary created for their own convenience, not the one they built to hide.
- **The fallback channel was a record type.** Sixteen bytes at a time, formatted as IPv6 addresses that were never meant to be routed anywhere (honorable mention). And the reason to check your DNS ingestion this week rather than next: if `QueryType` isn't in your workspace, this detection is unbuildable and you don't currently know that.
- **The encryptor was `manage-bde.exe`.** Wednesday and Thursday both covered BitLocker turned against its owners for extortion — Microsoft-signed, already installed, already trusted, already excluded from half the EDR policies in the industry. Worth a QA note before you deploy either version: both briefs mapped that detection to **T1505.003 Web Shell**, inherited from the initial-access step in the source reporting. The encryption behavior is **T1486 Data Encrypted for Impact**, with **T1490 Inhibit System Recovery** and **T1021.001 Remote Desktop Protocol** alongside it. Thursday's tags carried T1486; the MITRE line didn't. Fix it before it lands in your coverage map, because a mismapped detection reports coverage you don't have. Also worth checking: Thursday's version bounds both the RDP logon and the `manage-bde` execution by the same `ago(1h)` lookback, which means the `TimeDeltaMinutes <= 60` correlation window can never actually be exercised at its stated width — and the `not(ipv4_is_private(RemoteIP))` filter scopes it to internet-facing RDP only, missing the far more common pivot from an already-compromised internal host.
- **And the admin console was your firewall's.** CVE-2026-16232 ran Friday through Sunday across six candidates, all of them variations on the same problem: distinguishing an authenticated administrative session from an authenticated administrative session. All six were filed as *requires environment mapping*, which is exactly right and exactly the point — you cannot detect abuse of a trusted tool without first knowing who is supposed to be using it, from where.

Last week's grammar was corroboration: *what should have come with this, and where is it?* This week's is provenance of a different kind: *this action is normal — but is this actor, from this place, at this cadence, normal too?* When the adversary stops importing infrastructure and starts renting yours, the artifact stops being evidence. The only things left to reason about are **identity, cadence, and context** — and every one of those has to be baselined before it can be alerted on.

Which is the unglamorous conclusion: the detections in this article are downstream of an inventory. Which service principals touch Graph. Which processes are allowed to. What your DNS telemetry actually contains. Who administers the firewall. None of that is a query. All of it is prerequisite.

Every one of these came straight out of this week's daily briefs — each detection shipped with ATT&CK mappings, telemetry requirements, deployment gates, triage runbooks, false-positive notes, and an honest readiness call. Twenty-eight of them this week, and the ones I disagreed with were the ones worth writing about.

This kind of detection content is published _daily_ — fresh threat intel translated straight into deployable detections, so you spend your time tuning and shipping instead of reading and re-deriving — that's the whole point of the **[Daily Detection Engineering Brief at DevSecOpsDadAttack.com](https://devsecopsdadattack.com/detectionengineering/)**.

<br/>

---

<br/>

## Helpful Links and References:

This Week's Detection Engineering Briefs:
- [Monday, 20th July](https://devsecopsdadattack.com/2026-07-20-detection-engineering-brief-monday-july-20-2026/)
- [Tuesday, 21st July](https://devsecopsdadattack.com/2026-07-21-detection-engineering-brief-tuesday-july-21-2026/)
- [Wednesday, 22nd July](https://devsecopsdadattack.com/2026-07-22-detection-engineering-brief-wednesday-july-22-2026/)
- [Thursday, 23rd July](https://devsecopsdadattack.com/2026-07-23-detection-engineering-brief-thursday-july-23-2026/)
- [Friday, 24th July](https://devsecopsdadattack.com/2026-07-24-detection-engineering-brief-friday-july-24-2026/)
- [Saturday, 25th July](https://devsecopsdadattack.com/2026-07-25-detection-engineering-brief-saturday-july-25-2026/)
- [Sunday, 26th July](https://devsecopsdadattack.com/2026-07-26-detection-engineering-brief-sunday-july-26-2026/)

DevSecOpsDadAttack Tags:
- [detection-engineering](https://devsecopsdadattack.com/tags/#detection-engineering)
- [kql](https://devsecopsdadattack.com/tags/#kql)
- [Project CAV3RN](https://devsecopsdadattack.com/tags/#Project-CAV3RN)
- [OilRig](https://devsecopsdadattack.com/tags/#OilRig)
- [APT34](https://devsecopsdadattack.com/tags/#APT34)
- [Microsoft Graph](https://devsecopsdadattack.com/tags/#Microsoft-Graph)
- [Outlook](https://devsecopsdadattack.com/tags/#Outlook)
- [Dead Drop](https://devsecopsdadattack.com/tags/#Dead-Drop)
- [DNS](https://devsecopsdadattack.com/tags/#DNS)
- [AAAA](https://devsecopsdadattack.com/tags/#AAAA)
- [serialize](https://devsecopsdadattack.com/tags/#serialize)
- [prev](https://devsecopsdadattack.com/tags/#prev)
- [Sequence Detection](https://devsecopsdadattack.com/tags/#Sequence-Detection)
- [Service Principal](https://devsecopsdadattack.com/tags/#Service-Principal)
- [OAuth](https://devsecopsdadattack.com/tags/#OAuth)
- [BitLocker](https://devsecopsdadattack.com/tags/#BitLocker)
- [CVE-2026-16232](https://devsecopsdadattack.com/tags/#CVE-2026-16232)
- [T1102](https://devsecopsdadattack.com/tags/#T1102)
- [T1102.002](https://devsecopsdadattack.com/tags/#T1102-002)
- [T1071.004](https://devsecopsdadattack.com/tags/#T1071-004)
- [T1550.001](https://devsecopsdadattack.com/tags/#T1550-001)
- [T1132.001](https://devsecopsdadattack.com/tags/#T1132-001)
- [T1486](https://devsecopsdadattack.com/tags/#T1486)
- [Microsoft Sentinel](https://devsecopsdadattack.com/tags/#Microsoft-Sentinel)
- [Defender XDR](https://devsecopsdadattack.com/tags/#Defender-XDR)
- [Entra ID](https://devsecopsdadattack.com/tags/#Entra-ID)

ATT&CK Coverage in This Article:
- **T1102.002** — Web Service: Bidirectional Communication (calendar dead drop, Act I)
- **T1550.001** — Use Alternate Authentication Material: Application Access Token (app-only Graph auth)
- **T1071.004** — Application Layer Protocol: DNS (configuration recovery, honorable mention)
- **T1132.001** — Data Encoding: Standard Encoding (hex agent ID, 16-byte AAAA containers)
- **T1573.002** — Encrypted Channel: Asymmetric Cryptography (RSA-OAEP + AES-256-GCM payloads)
- **T1486 / T1490 / T1021.001** — BitLocker extortion chain (corrected mapping, see The Bigger Lesson)

External Sources:
- Kaspersky GReAT / Securelist. *New Project CAV3RN module abuses Outlook calendar events for C2 and DNS AAAA records for configuration recovery.* 21 July 2026. <https://securelist.com/project-cav3rn-cyberespionage-framework-using-outlook-and-dns/120757/>
- Kaspersky GReAT / Securelist. *A new extortion cocktail: office printers, small ransoms, and BitLocker.* <https://securelist.com/new-extortion-scheme-printers-bitlocker/120718/>
- Check Point Research. *Cavern Manticore: Exposing an Iran-Linked Modular C2 Framework.* <https://research.checkpoint.com/2026/cavern-manticore-exposing-iran-linked-modular-c2-framework/>
- Microsoft Security Blog. *Email threat landscape: Q2 2026 trends and insights.* <https://www.microsoft.com/en-us/security/blog/2026/07/23/email-threat-landscape-q2-2026-trends-and-insights/>


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
