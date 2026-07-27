![DevSecOpsDadAttack!](/assets/img/Meeting2050/NinjaCat.png)
There is a meeting on your calendar for **13 May 2050**. Nobody will ever attend it. Nobody has ever scrolled there — a quarter-century out, in a fixed one-hour window between 22:00 and 23:00 UTC, parked in the most-synced, least-read database in your tenant.

That meeting is a command-and-control channel.

This week the attacker solved the detection problem in the most annoying way possible. **They stopped bringing infrastructure.** There is no C2 domain to block, because the C2 is `graph.microsoft.com`. There is no beacon on the wire to fingerprint, because the beacon is an OAuth token request to `login.microsoftonline.com`. There is no encryptor to signature, because the encryptor is `manage-bde.exe` and Microsoft signed it. There is no rogue admin console, because the console is your firewall's. Every artifact this week belongs to *you*.

That thread ran through all seven of this week's briefs and their **28 KQL candidates** — a second SharePoint RCE wave (CVE-2026-58644), the WordPress core RCE (CVE-2026-63030) and its web-shell aftermath, ACR Stealer riding ClickFix lures into browser credential stores, BitLocker turned into an extortion tool against office print infrastructure, WebDAV remote paths used to launch execution, a Check Point SmartConsole authentication bypass (CVE-2026-16232) that ran Friday through Sunday, Teams external-guest social engineering, and Microsoft's Q2 2026 email threat landscape with its machine-speed M365 attack chains. But the one that made me put down the coffee was **Project CAV3RN storing its command-and-control traffic inside Outlook calendar events**.

Last week's theme was *absence*: the sign-in that never happened, the author who was never there. The detections won by demanding a corroborating record the attacker couldn't forge. This week there is no absence to point at. Every record is present, legitimate, and signed.

So this week's KQL of the Week is the CAV3RN calendar channel, told in three queries and one correction the briefs got wrong. Act I hunts the **dead drop** from inside the mailbox tenant. Act II hunts the **infected host**, which — and this is the part that matters — is almost never the same organization. The honorable mention hunts the fallback channel, where the attacker encodes their config into things that look exactly like IPv6 addresses and are not addresses at all.

<br/>

---

<br/>

## 🥇 Act I: The Standing Meeting Nobody Will Ever Attend

![Act I](/assets/img/Meeting2050/ACT_I.png)

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
let CalendarFolderNames = dynamic(["Calendar","Kalender","Calendrier","Calendario","Agenda","カレンダー","日历","Календарь","לוח שנה"]);
let CalendarOps = OfficeActivity
| where TimeGenerated > ago(lookback)
| where OfficeWorkload =~ "Exchange"
| where Operation in~ ("Create", "Update", "SoftDelete", "HardDelete", "MoveToDeletedItems")
// Item is a STRING column in OfficeActivity, not dynamic. parse_json() is required.
| extend ItemJson = parse_json(Item)
| extend
    ItemId      = tostring(ItemJson.Id),
    ItemSubject = coalesce(tostring(ItemJson.Subject), ItemName),
    FolderPath  = coalesce(tostring(ItemJson.ParentFolder.Path), Folder)
| where FolderPath has_any (CalendarFolderNames)
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
// between (1 .. 2), NOT <= 2 — an empty PrevSubject would otherwise match every create/update pair
| where strlen(trim(@"\s", PrevSubject)) between (1 .. 2)
| where isnotempty(ItemSubject) and PrevSubject != ItemSubject
| extend RenameLatencySec = datetime_diff('second', TimeGenerated, PrevTime)
| where RenameLatencySec between (0 .. RenameWindowSec)
| extend Signal = "PlaceholderRename"
| project-away Prev*;
union MarkerHits, PlaceholderRenames
// The entity is the mailbox. Everything else is an attribute of the finding,
// not a dimension of it — including who Exchange thinks did it.
| extend Mailbox = coalesce(MailboxOwnerUPN, UserId)
| where isnotempty(Mailbox)
| summarize
    Events       = count(),
    Signals      = make_set(Signal),
    Subjects     = make_set(ItemSubject, 10),
    Operations   = make_set(Operation, 10),
    Actors       = make_set(UserId, 5),
    ActorTypes   = make_set(UserType, 5),
    Clients      = make_set(ClientInfoString, 5),
    ClientIPs    = make_set(ClientIP, 5),
    AppIds       = make_set(AppId, 5),
    MinRenameSec = min(RenameLatencySec),
    FirstSeen    = min(TimeGenerated),
    LastSeen     = max(TimeGenerated)
    by Mailbox
| extend
    BothSignals = array_length(Signals) > 1,
    MixedActors = array_length(ActorTypes) > 1
| order by BothSignals desc, MixedActors desc, Events desc
```

<br/>

### The line that does the work

Not the marker list. Markers are strings, strings are free, and the operator can change `Boss Report ID:` to `Q3 Planning Sync` in the time it takes to recompile. It's this:

```kql
| where strlen(trim(@"\s", PrevSubject)) between (1 .. 2)
```

Note `between (1 .. 2)` and not `<= 2`, because that difference is the whole detection. `Item.Subject` is not guaranteed to be populated on `Create` records the way it is on `Update` records — and if it comes back empty, `strlen()` returns zero, zero satisfies `<= 2`, and the filter matches **every create-then-update pair in the tenant**. The marker branch of this query fails toward silence when extraction breaks. This branch fails toward noise. Same missing field, opposite direction, and only one of them is obvious from reading the results. Excluding the empty case costs nothing — the placeholder the module actually writes is a single character — and it's the difference between a hunt and a pager.

Beyond that, this is the detection with a shelf life. The placeholder subject isn't a naming choice the operator made for fun — it's **forced by the protocol**. The module cannot create the event with its final subject, because it needs an event ID to attach the encrypted payload to, and it doesn't want a half-built dead drop sitting in the calendar advertising itself while the upload is in flight. Create blank, attach, then rename. That sequence is load-bearing. Rename the markers all you like; the create-then-patch shape stays, because the alternative is a race condition in your own C2.

The supporting choice is the **entity-keyed union**. `MarkerHits` and `PlaceholderRenames` are two genuinely different questions, and I've unioned them anyway — but only because both sides are projected to the same columns and both resolve to the *same entity*, the mailbox. The `summarize` at the bottom then earns its keep: `BothSignals` promotes any mailbox where a marker string *and* a placeholder rename both landed, which is the CAV3RN shape and essentially nothing else's.

Which is a claim you have to actually honor in the `summarize`, and my first version didn't. I grouped by `MailboxOwnerUPN, UserId, UserType` — the entity, plus two attributes of the record. Every extra key in a `by` clause is a finer partition, and a finer partition is a *smaller* chance that two signals about the same thing land on the same row. If Exchange attributes the marker write to the service principal and the rename to the mailbox owner, those become two rows, `array_length(Signals)` is 1 on both, and `BothSignals` — the entire point of the union — can never fire. The correlation was defeated by the grouping, in a query whose whole argument is that correlations live and die by their key.

The rule that falls out: **anything that isn't the entity belongs in the aggregation, not the `by` clause.** `Actors = make_set(UserId, 5)` tells you the same thing without fragmenting the row. And it tells you something extra — `MixedActors` flags a mailbox whose calendar writes are attributed to *both* a service principal and an interactive owner. Legitimate integrations and humans share calendars all the time; sharing them in a create-then-rename pattern is a different matter.

This is worth stating precisely, because the briefs got it wrong on Tuesday and it's an easy mistake to make. **A union is legitimate when the branches share an entity key and illegitimate when they don't.** Tuesday's Detection 4 unioned calendar Graph activity (keyed on `AccountId`) with a DNS AAAA volume spike (keyed on `DeviceName`), then padded the second branch with `AccountId = ""`, `CalendarOps = 0`, `ActionTypes = dynamic([])` so the schemas would line up. The result is two unrelated hunts sharing an output grid, with half the columns structurally empty on every row. Nothing correlates, because there's nothing to correlate *on* — the brief's own caveat notes that `IPAddress` from `CloudAppEvents` and `DeviceName` from `DeviceNetworkEvents` can't be equated without a device inventory. If you're padding columns to make a union compile, you don't have one detection. You have two, in a trench coat.

<br/>

### A KQL note...

`prev()` requires a **serialized** row set, and `sort by` provides that serialization. Two things about that line will bite you, and they're covered properly in the bonus section below — but the short version, because it changes whether this query works at all:

- `| sort by ItemId asc, TimeGenerated asc` — the `asc` is not decorative. **KQL's `sort by` defaults to descending.** Omit it and `prev()` hands you the *later* row, inverting the entire sequence test into a silent no-op.
- `| where ItemId == PrevItemId` — `prev()` walks the whole serialized table and does not respect groups. Without that guard, the first row of every calendar item borrows the last row of the previous item, and you manufacture "sequences" that never occurred.

<br/>

### Keeping it honest

The briefs filed the CAV3RN calendar work as **hunting-only** every time it appeared, and that's correct. Here's what has to be true before this means anything:

- **`Item` is a `string` column, not a dynamic one, and dot access on it will not run.** This is the trap I nearly shipped. `OfficeActivity` types `Item` as **String** — "represents the item upon which the operation was performed" — and the same is true of `AffectedItems` and `Folders`. The schema does have genuine dynamic columns (`OperationProperties`, `Members`, `ExtraProperties`), so the distinction is deliberate, not an artifact of the docs. Write `Item.Subject` and you don't get an empty result, you get a semantic error. `parse_json(Item)` first, every time. There is also no `ParentFolder` column at all — there's `Folder` and `Folders` — which is why the query above coalesces the parsed path against `Folder` rather than trusting either alone. `ItemName` is likewise a first-class column documented as carrying the subject, and if it's populated for calendar records in your tenant it's cheaper and steadier than digging into the blob. Validate all of it before you build: `OfficeActivity | where OfficeWorkload =~ "Exchange" | where isnotempty(Item) | take 20 | project Operation, Item, ItemName, Folder`. Wednesday's brief made the same class of assumption in the other direction, filtering on `Operation in ("UpdateCalendarItem", "CreateCalendarItem", ...)` — operation names that aren't in the Exchange audit schema at all. Its own caveats section flags this. Survey the real values before you trust any of it.
- **`Calendar` is an English string.** The folder-path test above matches a name list for exactly that reason. A tenant running localized Outlook stores the same folder as `Kalender`, `Calendrier`, `カレンダー`, or `לוח שנה` — and given this campaign's targeting, the Hebrew case is not hypothetical. A hardcoded `has "Calendar"` is a silent false negative in precisely the environments most likely to be affected. Confirm what your own tenant writes: `OfficeActivity | where OfficeWorkload =~ "Exchange" | summarize count() by Folder | order by count_ desc`.
- **Subject content is a licensing and configuration question.** Mailbox audit logging must be enabled and the Office 365 connector configured, and some tenants restrict subject capture on privacy grounds. A hunt that depends on reading meeting subjects is a hunt that needs sign-off from someone other than you.
- **Wednesday's version keyed on `UserAgent`, and that field belongs to the attacker.** The query filtered to calendar operations where the user agent didn't contain `Mozilla`, `Outlook`, `Microsoft Office`, or `MacOutlook`. Consider what that asks of the adversary: set one HTTP header to a string starting with `Mozilla` and the detection is gone. This is an allowlist built entirely from a value the client controls, which is the same failure family as authenticating on a claim you didn't verify. Worse, the preceding `isnotempty(UserAgent)` drops every record where the field isn't populated — and the brief's own caveats note that `UserAgent` is unreliable for Graph API calls in `OfficeActivity`. The filter over-trusts what it sees and discards what it doesn't. Neither half is recoverable by tuning.
- **Volume thresholds are the wrong axis for this threat.** Tuesday gated on `CalendarOps > 20` over seven days; Thursday on `CallCount > 20`. A room-booking integration clears twenty calendar operations before lunch. A CAV3RN agent polling every six hours clears twenty-eight in a week — barely over the line, and one config change from being under it. You cannot separate a beacon from a business integration by counting, because busy is not the same as regular. If you want to go at this from the cadence side, measure the *variance* of the inter-arrival gaps, not the total.
- **Thursday's Detection 3 queried the wrong table entirely.** It hunted `AuditLogs` for Graph calendar operations. `AuditLogs` is Entra ID's **directory control plane** — app registrations, consent grants, role assignments, group membership. Reading or writing a calendar event is **data plane**, and it does not write an `AuditLogs` record no matter how many times it happens. The query is syntactically fine, will run without error, and will return nothing forever. For app-only Graph activity, the tables that actually see it are `OfficeActivity` / `MailboxAudit` (the operation), `CloudAppEvents` (if you're licensed for Defender for Cloud Apps), and `AADServicePrincipalSignInLogs` (the token acquisition). That last one is genuinely useful here and no brief this week reached for it:

```kql
let Baseline = AADServicePrincipalSignInLogs
| where TimeGenerated between (ago(180d) .. ago(30d))
| where ResultType == 0
| distinct AppId;
AADServicePrincipalSignInLogs
| where TimeGenerated > ago(30d)
| where ResultType == 0
| where ResourceDisplayName =~ "Microsoft Graph"
| summarize
    SignIns     = count(),
    IPs         = make_set(IPAddress, 10),
    Countries   = make_set(Location, 10),
    FirstSeen   = min(TimeGenerated),
    LastSeen    = max(TimeGenerated),
    ActiveDays  = dcount(bin(TimeGenerated, 1d))
    by AppId, ServicePrincipalName, ServicePrincipalId
| join kind=leftanti Baseline on AppId
| extend ObservedSpanDays = datetime_diff('day', LastSeen, FirstSeen)
| order by FirstSeen desc
```

The `leftanti` is doing the load-bearing work, and it's worth saying why, because the obvious version of this query silently can't answer the question. `FirstSeen = min(TimeGenerated)` is bounded by the lookback. Inside a 30-day window, a service principal that has been running since 2023 reports the same `FirstSeen` as one registered last Tuesday — the aggregate cannot see past its own filter, and "new" is not a property you can compute from a single window. It's a **membership** question, which means it needs a population to be absent from. Hence the 180-day baseline and the anti-join: *authenticating now, and not in the six months before now.* Last week's operator, doing this week's job.

Every CAV3RN `get` and `send` cycle starts with a `client_credentials` token request. A service principal that first appears this month, authenticates to Graph from one or two addresses, and never stops, is a much shorter list than "applications that touch calendars."

- **`MailboxOwnerUPN` is not guaranteed to be populated**, and app-only access is precisely where it goes missing. Group on an empty key and every such record collapses into a single row that appears to represent one mailbox and actually represents all of them — a `BothSignals` hit on a group with no entity in it. The `coalesce(MailboxOwnerUPN, UserId)` and the `isnotempty()` guard exist for that. Same failure family as the `strlen` case above: a missing field turning a filter into a firehose.
- **And the finding is a *lead*, not a verdict.** Confirm in the mailbox, not in the SIEM. Pull the item and look at its start time. If it's a real meeting, it's on a real date. If it's a dead drop, it's in 2050. That's the whole triage step.

Act I hunts the mailbox. Which raises the question the briefs never asked — and it's the one that changes your coverage.

<br/>

---

<br/>

## 🥈 Act II: You Are Probably Not the Mailbox

![Act II](/assets/img/Meeting2050/ACT_II.png)

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
    "mssense.exe", "senseir.exe", "msmpeng.exe",
    // Windows itself. svchost (Web Account Manager / TokenBroker) alone will dominate
    // login.microsoftonline.com volume on every managed fleet.
    "svchost.exe", "searchhost.exe", "searchapp.exe", "runtimebroker.exe",
    "backgroundtaskhost.exe", "phoneexperiencehost.exe", "microsoft.sharepoint.exe"
]);
let ConfigWrites = DeviceFileEvents
| where Timestamp > ago(lookback)
| where ActionType in ("FileCreated", "FileModified", "FileRenamed")
| where FileName in~ (ConfigArtifacts)
// Row-level branch: first and last are the same instant. Name them anyway, so the
// union carries one vocabulary and the outer summarize has nothing to guess about.
| extend FirstSeen = Timestamp, LastSeen = Timestamp
| project
    FirstSeen, LastSeen, DeviceId, DeviceName,
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
    FirstSeen   = min(Timestamp),
    LastSeen    = max(Timestamp),
    Connections = count(),
    ActiveDays  = dcount(bin(Timestamp, 1d)),
    Endpoints   = make_set(RemoteUrl, 5)
    by DeviceId, DeviceName,
       Process     = InitiatingProcessFileName,
       ProcessPath = InitiatingProcessFolderPath,
       Account     = InitiatingProcessAccountName
| extend
    Detail = strcat(tostring(Connections), " connections over ", tostring(ActiveDays),
                    " active days to ", strcat_array(Endpoints, ", ")),
    Signal = "UnexpectedGraphClient"
| project-away Connections, ActiveDays, Endpoints;
union ConfigWrites, UnexpectedGraphClients
| summarize
    Signals   = make_set(Signal),
    Processes = make_set(Process, 10),
    Paths     = make_set(ProcessPath, 10),
    Accounts  = make_set(Account, 5),
    Details   = make_set(Detail, 10),
    FirstSeen = min(FirstSeen),
    LastSeen  = max(LastSeen)
    by DeviceId, DeviceName
| extend
    HasConfigArtifact = set_has_element(Signals, "ConfigArtifactWrite"),
    SignalCount       = array_length(Signals),
    ActiveSpanDays    = datetime_diff('day', LastSeen, FirstSeen)
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
| join kind=inner graph_callers on DeviceId, SuspectProcess
```

Same answer, a fraction of the shuffle — and note that it's `DeviceId`, not `DeviceName`. If the argument three paragraphs up is that the entity key is what makes a correlation legitimate, then the key has to be the one that actually identifies the entity. `DeviceName` is a label. It collides across a fleet, it changes on rename, and it's the reason half the "correlated" detections in circulation quietly fan out across two unrelated hosts that a naming convention happened to give the same string.

<br/>

### Keeping it honest

I'd take `ConfigWrites` to a scheduled rule tomorrow. `UnexpectedGraphClients` is a hunt, and the gap between those two is where the work is:

- **Thursday's allowlist has last week's bug in it.** The query excluded destinations with `not(RemoteUrl has_any ("graph.microsoft.com", "login.microsoftonline.com", "microsoft.com", "windows.com", "windowsupdate.com"))`. The hole is real, but it isn't the one I first wrote, and the mechanism is worth getting right because it changes which hostnames get through. `has_any` is **term-based**, not substring-based — KQL tokenizes both sides into maximal alphanumeric runs, and a multi-token needle matches when its tokens appear as an *adjacent sequence* in the haystack. So `microsoft.com` does **not** match `login.microsoftonline.com.c2.example.net`: the tokens there are `login`, `microsoftonline`, `com`, and there is no `microsoft` immediately followed by `com`. That's what `contains` would have done. What `has_any` does instead is match without regard to *position*, which is the actual problem: `windowsupdate.com.attacker.io` tokenizes to `windowsupdate`, `com`, `attacker`, `io` — the needle's two tokens sit adjacent at the front, so the allowlist suppresses it. Register `microsoft.com.c2.example.net` and you walk out the same door. A term test answers "do these tokens appear next to each other somewhere," and a suffix test answers "does this name end here." Those are different questions, and only the second one is the one an allowlist means to ask. This is the `RemoteIP startswith "172."` mistake from the AsyncAPI honorable mention wearing different clothes: an operator whose semantics almost fit, used in a filter whose job is to *suppress*, where every over-broad match is an invisible hole. Act II uses `in~` for exact host equality, which cannot over-suppress. If you need to cover subdomains, `endswith` on a normalized hostname is the floor, not `has_any`.
- **The expected-client list is the whole detection, and mine is not yours.** Every enterprise runs Graph SDK background services nobody documented: RMM agents, backup tools, CASB shims, HR integrations, a PowerShell scheduled task somebody wrote in 2023. Run `DeviceNetworkEvents | where RemoteUrl in~ ("graph.microsoft.com") | summarize count() by InitiatingProcessFileName, InitiatingProcessFolderPath | order by count_ desc` and build the list from your own fleet before this goes anywhere near a schedule.
- **Name-only exclusions are spoofable, and `teams.exe` from `%TEMP%` is not `teams.exe`.** Harden to `(FileName, FolderPath)` pairs or signer checks before promotion — the same correction the CI/CD detection needed last week, for the same reason.
- **`RemoteUrl` is not reliably populated in `DeviceNetworkEvents`.** A connection recorded with only `RemoteIP` will never match `in~ (GraphEndpoints)` and drops out silently. That's a false-negative direction, which is the safer failure, but know it's there: your Graph-client inventory is a floor, not a census.
- **Working directory means the path is unpredictable.** Because the module supplies a bare filename, `logAzure.txt` lands wherever the host process happened to be running — `System32`, a user profile, a service directory, anywhere. Don't scope the file query by `FolderPath`. Let it fire from anywhere and read the path as evidence: *where* it landed tells you which process loaded the DLL.
- **An aggregate collapses a time range into whatever fields you name — and a field you didn't name is a field the analyst will infer wrongly.** My first version summarized the network branch to `Timestamp = min(Timestamp)` before the union, so the outer `max(Timestamp)` faithfully reported the maximum of a set of minimums, which is a number that describes nothing. `LastSeen: 29 days ago` on a host that has been beaconing every day since is how a live finding gets triaged to the bottom of the queue. Carry `min` *and* `max` through any branch that aggregates, and reconcile them at the top. `ActiveDays` is the field that actually answers the question anyway: a config write is a point event, but a Graph client is a behavior, and "180 connections across 28 of 30 days" is a different finding from "180 connections in one afternoon."
- **Coverage is the silent gate, again.** No MDE agent, no `DeviceFileEvents`, no finding. A quiet result across a fleet you haven't fully onboarded is a coverage report wearing a clean bill of health.

Act I hunts the drop box. Act II hunts the agent. The last act hunts what the agent does when the drop box stops answering.

<br/>

---

<br/>

## 🎖 Honorable Mention: The Address That Was Never an Address

![Honorable Mention](/assets/img/Meeting2050/Honorable_Mention.png)

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
// Shared, cheap base. Nothing expensive happens here.
let AaaaLookups = DnsEvents
| where TimeGenerated > ago(lookback)
| where SubType =~ "LookupQuery"
| where QueryType =~ "AAAA"
| extend QueryName = tolower(trim_end(@"\.", Name));
// Lane 1 — protocol shape. The label-count floor belongs to THIS lane only.
let ShapeLane = AaaaLookups
| where QueryName startswith "d."          // leading-label test, cheap, drops nearly everything
| extend Labels = split(QueryName, ".")
| where array_length(Labels) >= 5
| extend SecondLabel = tostring(Labels[1])
| where strlen(SecondLabel) >= 8 and strlen(SecondLabel) % 2 == 0
| where SecondLabel matches regex @"^[0-9a-f]+$"   // regex last, on the smallest surviving set
| where set_has_element(Labels, "p") or set_has_element(Labels, "q")
| extend
    Lane        = "ProtocolShape",
    MarkerLabel = iff(set_has_element(Labels, "p"), "p", "q")
| project TimeGenerated, ClientIP, Computer, QueryName, Lane, MarkerLabel;
// Lane 2 — bootstrap domain IOC. No label-count floor: the bare domain is two labels.
// has_any is term-sequence matching, so this also catches sub.cloudlanecdn.com and
// cloudlanecdn.com.evil.net. In a positive lane that breadth is free; in the suppression
// filter discussed in Act II, the same behavior is a hole.
let DomainLane = AaaaLookups
| where QueryName has_any (BootstrapDomains)
| extend Lane = "BootstrapDomain", MarkerLabel = ""
| project TimeGenerated, ClientIP, Computer, QueryName, Lane, MarkerLabel;
// Lane 3 — failure sentinel in the ANSWER. Cheap lossy prefilter, then authoritative compare.
// IPv6 has no single textual form. 2001:4998:44:3507::8000 and its expanded
// equivalent are the same address and different strings — so narrow on a term,
// decide with ipv6_compare().
let SentinelLane = AaaaLookups
| where IPAddresses has "8000"
| mv-apply AnswerIP = split(tostring(IPAddresses), ",") to typeof(string) on (
    summarize SentinelHits = countif(ipv6_compare(trim(@"\s", AnswerIP), FailureSentinel) == 0)
  )
| where SentinelHits > 0
| extend Lane = "FailureSentinel", MarkerLabel = ""
| project TimeGenerated, ClientIP, Computer, QueryName, Lane, MarkerLabel;
union ShapeLane, DomainLane, SentinelLane
| summarize
    Queries       = count(),
    DistinctNames = dcount(QueryName),
    SampleNames   = make_set(QueryName, 10),
    MarkerLabels  = make_set_if(MarkerLabel, isnotempty(MarkerLabel)),
    ShapeCount    = countif(Lane == "ProtocolShape"),
    DomainCount   = countif(Lane == "BootstrapDomain"),
    SentinelCount = countif(Lane == "FailureSentinel"),
    Lanes         = make_set(Lane),
    FirstSeen     = min(TimeGenerated),
    LastSeen      = max(TimeGenerated)
    by ClientIP, Computer
| extend
    ShapeSeen    = ShapeCount > 0,
    SentinelSeen = SentinelCount > 0,
    DomainSeen   = DomainCount > 0,
    LaneCount    = array_length(Lanes)
// Rank by fidelity, not volume — a noisy IOC-only hit must not outrank a single shape hit
| order by ShapeSeen desc, SentinelSeen desc, LaneCount desc, DistinctNames desc
```

The line that does the work is the shape test, and specifically this half of it:

```kql
set_has_element(Labels, "p") or set_has_element(Labels, "q")
```

Note what that *isn't*. It isn't `QueryName has ".p."` — and the reason is more interesting than "that would over-match," because it wouldn't over-match the way you'd guess. `has` is term-based, so the dots in that needle are **silently discarded**: it tokenizes to the single term `p`, and the query you actually shipped is `has "p"`. It won't match `example.pizza.com`, because `pizza` is one term and there's no standalone `p` in it. It *will* match `cdn-p-edge.example.com`, because hyphens are term delimiters too, and anything else where a lone `p` survives tokenization in a context that has nothing to do with DNS labels. The punctuation you wrote to mean "a label, delimited by dots" was never evaluated. That's the failure worth naming — not a filter that matches too much, but a filter that quietly answers a different question than the one on the page. It also isn't a positional index like `Labels[array_length(Labels) - 3]`, which quietly assumes the registrable domain is exactly two labels and breaks the moment the operator moves to something under `.co.uk`. `set_has_element()` does exact element matching against the parsed label array — it asks "is there a label that is *precisely* the single character `p`," which is a question ordinary DNS almost never answers yes to. Splitting the hostname into labels first and reasoning about labels as structured data, rather than pattern-matching against the string, is what makes the test both specific and portable.

One line up in the shared base is doing quiet, load-bearing work, and it deserves naming because lifting the regex without it produces a clean zero-row result:

```kql
| extend QueryName = tolower(trim_end(@"\.", Name))
```

The agent ID is hex-encoded **uppercase**. `^[0-9a-f]+$` does not match `A1B2C3`. Whether your resolver preserves query case varies by source — the Windows DNS connector generally lowercases, Sysmon generally doesn't — so the normalization is the difference between a working detection and a detection that works only on your test box. Normalize before you pattern-match, always, and never let case survive into a regex you're relying on.

The domain and sentinel lanes are the cheap IOC lanes riding alongside — `cloudlanecdn[.]com` and the hardcoded failure address `2001:4998:44:3507::8000` (which lives inside a Yahoo allocation, for reasons GReAT couldn't determine either). Those two will be dead within the month. The shape lane outlives them.

Four things about how those lanes are handled, three of which I got wrong on the first pass:

- **Don't string-match an IPv6 address.** `IPAddresses has "2001:4998:44:3507::8000"` only fires if your resolver logged that exact compression. The same address written `2001:4998:44:3507:0:0:0:8000` is a different string and an identical destination, and the miss is silent. `ipv6_compare()` normalizes both sides and answers the question you actually asked. It would be a strange article that spends a paragraph arguing structured label matching beats string matching, and then string-matches an address three lines later.
- **But put something cheap in front of it.** My first version ran the `mv-apply` and the address comparison against *every* AAAA lookup in the window, and filtered afterwards. That is the expensive operation sitting upstream of the filter that would have contained it — on an IPv6-enabled network it's a query that returns the right answer and never finishes. The fix is `| where IPAddresses has "8000"` ahead of the `mv-apply`. KQL's tokenizer treats the colon as a separator, so the trailing hextet is a distinct term in every textual form of that address, and the final group is always four hex digits — there's no zero-padded variant that hides it. Narrowing with a string operation and *deciding* with a structured one is not a contradiction; it's the whole pattern. The mistake is letting the string operation make the call.
- **Separate lanes, not shared booleans.** Computing `ShapeMatch`, `DomainMatch`, and `SentinelMatch` as columns on one row set forces every row through every test, and it couples their preconditions. That coupling had already broken something: `| where LabelCount >= 5` is a *shape* precondition, but sitting at the top of a single pipeline it also discarded every domain-IOC hit on the bare `cloudlanecdn.com` — two labels — and every sentinel hit returned to a short hostname. Three `let`-bound branches let each lane carry its own floor. The union at the bottom is legitimate for the usual reason: same entity, `ClientIP` and `Computer`, three questions.
- **`max()` doesn't aggregate booleans**, so the `ShapeSeen`/`DomainSeen`/`SentinelSeen` flags are built with `countif()` and compared after the `summarize`. And the ordering runs on `ShapeSeen` first, not on volume. A chatty host that tripped the domain IOC once should not outrank a single host exhibiting the protocol shape — that's the same `BothSignals` discipline from Act I, applied to three lanes of very unequal fidelity instead of two of equal fidelity.

**One correction, and it's the important one.** Thursday's Detection 4 was titled "DNS AAAA Queries from Non-Browser Processes," and it does not query DNS record types, because it can't — the brief says so plainly in its own caveats: `DeviceNetworkEvents` doesn't expose query type, and `DnsQueryResponse` isn't a valid `ActionType` for that table. So the query substitutes a behavioral proxy: find non-browser processes that hit `graph.microsoft.com`, then find other external connections from those same processes. That's honest engineering under a constraint, and I respect that the brief documented it rather than shipping a query that returns zero rows and calling it clean.

But the constraint isn't real. It's a *table* constraint, not a *telemetry* constraint. `DnsEvents` — the Windows DNS Server connector, or Sysmon Event ID 22, or your resolver's own logs — carries `QueryType` as a first-class field. If you want AAAA, you need a DNS source, and MDE endpoint telemetry is not one. The general lesson is worth more than this campaign: **when a query's title describes something the table cannot express, the answer is usually a different table, not a cleverer proxy.** Check your DNS ingestion before you build around its absence:

```kql
DnsEvents
| where TimeGenerated > ago(1d)
| summarize Events = count() by QueryType
| order by Events desc
```

If that returns nothing, you have a data-source project, not a detection project — and that's a far more useful finding than a proxy query that half-works.

One thing to confirm in your own workspace before you run the sentinel lane, because it's the assumption the `split()` rests on:

```kql
DnsEvents
| where TimeGenerated > ago(1d) and QueryType =~ "AAAA" and isnotempty(IPAddresses)
| take 20
| project IPAddresses
```

The Windows DNS connector writes multiple answers comma-delimited, which is what the query assumes. If yours uses spaces, change the separator — `trim(@"\s", ...)` covers `", "` but not a bare space.

Keep this one **hunting-only**. Legitimate AAAA volume is enormous on IPv6-enabled networks, `ClientIP` in `DnsEvents` is your resolver's view and may be a forwarder rather than the real originator, and the shape test will occasionally catch a CDN or telemetry vendor doing genuinely weird things with hostnames. Confirm the shape by eye — the label structure is distinctive enough that thirty seconds of reading `SampleNames` will tell you whether you're looking at a protocol or a coincidence.

<br/>

---

<br/>

## ✨ Bonus: `serialize`, `prev()`, and detecting a *sequence* instead of an *event*

![Sequence](/assets/img/Meeting2050/Bonus.png)

Act I's placeholder-rename test needed something most KQL doesn't: it needed to know what happened *immediately before* a given row, within that row's own history. Last week's bonus covered `leftanti`, which reasons about sets — is this key present in that population? This week's is the other axis: reasoning about **order**.

<br/>

### Rows in KQL don't have neighbors — until you say so

By default a KQL result set is unordered. There's no "previous row," because there's no row order to be previous in. `prev()` and `next()` therefore require a **serialized** row set, and there are exactly three ways to get one:

| How | What it does |
|---|---|
| `sort by` / `order by` | Sorts *and* serializes. The usual entry point. |
| `serialize` | Freezes the current arbitrary order into a row order. Fast, and almost never what you want alone. |
| `range`, `top`, `top-hitters`, `getschema` | Operators that emit an already-serialized set. |

Note what is *not* on that list: `row_number()`. It's easy to assume a function that assigns sequence numbers must be creating the sequence, but it's the other way round — `row_number()` is one of the functions that *requires* a serialized input, exactly like `prev()` and `next()`. It reads an order someone else established. If you reach for it to fix a serialization error, you'll get the same error back.

And serialization is **not sticky**. `where`, `extend`, `project`, and `take` preserve it. `summarize`, `join`, `union`, and `mv-expand` destroy it — after any of those, `prev()` will fail or, worse, silently operate on a re-shuffled order. If you need sequence logic after an aggregation, re-`sort` before you reach for `prev()`.

<br/>

### The three ways `prev()` lies to you

`prev()` is a sharp tool with no guard rails, and every failure mode is silent:

- **`sort by` defaults to descending.** This is the one that gets people. `| sort by TimeGenerated` gives you newest-first, so `prev()` returns the *later* event and `next()` returns the earlier one. Every sequence test you wrote is now backwards. It won't error. It'll just return a different, plausible-looking, wrong answer — often zero rows, which reads as "clean." Write `asc` explicitly, every time, even when you think you know the default.
- **`prev()` does not respect partitions.** It walks the entire serialized table top to bottom. Sort by `ItemId, TimeGenerated` and the first row of item B sees the last row of item A as its "previous" — different entity, different timeline, fabricated sequence. The `| where ItemId == PrevItemId` guard in Act I isn't defensive coding, it's **required for correctness**. Every `prev()` needs a partition guard or a `partition` operator around it. The parallel to last week is exact: with `leftanti`, a bad key *creates* findings; with an unguarded `prev()`, a partition boundary *creates* sequences. Both failure modes generate exactly the artifact you were hunting for, which is the worst possible direction for a bug to fail in.
- **`prev()` returns null at the boundary, and "null" means different things by type.** The first row of the whole table has no predecessor. For numeric and datetime columns that's a real null, and comparisons against it quietly evaluate false, so boundary rows vanish — usually fine, occasionally the difference between catching the first beacon and catching the second. For **string** columns there is no distinct null in KQL: the null value *is* the empty string, and `isnull()` on a string always returns false. Test string boundaries with `isempty()`. Writing `isnull(PrevItemId)` against a string column isn't a bug that errors — it's a clause that never fires, sitting in your query looking like a guard.

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
| extend ItemId = tostring(parse_json(Item).Id)
| where isnotempty(ItemId)
| sort by ItemId asc, TimeGenerated asc
| extend PrevItemId = prev(ItemId);
union
    (Base | summarize Rows = count() | extend Population = "All rows"),
    (Base | where ItemId == PrevItemId | summarize Rows = count() | extend Population = "Same item as previous"),
    (Base | where ItemId != PrevItemId or isempty(PrevItemId) | summarize Rows = count() | extend Population = "Partition boundary (discarded)")
```

Two things to read off it. First, the three counts must reconcile — if they don't, your sort key isn't what you think it is. Second, and more useful: **if the discarded boundary count is nearly the whole table, your sequence detection has almost nothing to work with.** Most calendar items are touched exactly once, so most rows *are* boundaries. That's expected here. But if you run the same check against process events and find 95% boundaries, your partition key is too granular and the sequence you're hunting can't exist in the data as keyed.

The one-line takeaway: **`leftanti` reasons about membership, `prev()` reasons about order, and order is the more fragile of the two — because a sort direction and a partition boundary are both invisible when they're wrong.** Say `asc` out loud. Guard the partition. Then the sequence means something.

<br/>

---

<br/>

## The Bigger Lesson

![](/assets/img/Meeting2050/Borrowed_Trust.png)

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
