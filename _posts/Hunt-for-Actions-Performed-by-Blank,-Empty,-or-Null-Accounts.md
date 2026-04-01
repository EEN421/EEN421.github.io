# When “Who Did It” Stops Working

Most security programs assume one thing without ever saying it out loud:

Every action in your environment can be tied back to a real identity.

That assumption breaks more often than people realize.

Sometimes it’s sloppy telemetry.
Sometimes it’s parser drift.
Sometimes it’s system-level behavior that never mapped cleanly in the first place.
And sometimes… it’s something you actually need to worry about.

But here’s the problem:

👉 Most teams never go looking for it.

They hunt for malicious activity, not missing identity.
They alert on bad behavior, not broken attribution.

And that’s a gap.

Because the moment you lose the ability to answer “who did this?”, you’re no longer operating a security program — you’re operating a guessing engine.

This Is an Attribution Problem, Not Just a Detection Problem

In mature environments, detection isn’t just about what happened.
It’s about:

Who did it
From where
Under what context
With what level of confidence

If any of those fall apart — especially identity — your detections degrade fast.

You can’t:

enforce accountability
build reliable detections
trust your incident timelines
or defend decisions in front of leadership

And yet, most teams never explicitly measure this.

What This Query Is Actually Doing

This isn’t a “find bad stuff” query.

It’s a “find where identity breaks down” query.

Across:

Entra sign-ins
Entra audit logs
Azure control plane activity
Defender for Endpoint telemetry

…it asks a very simple, very uncomfortable question:

“Where are things happening in my environment without a clean, trustworthy identity attached?”

Not nulls for the sake of nulls.
Not noise for the sake of noise.

Signal about where your security model loses attribution fidelity.

Why This Matters More Than You Think

If you’re running:

an MDR practice
a SOC
or any kind of detection engineering function

…this is where maturity shows up.

Anyone can write a detection.

Fewer teams can answer:

“How confident are we in the identity behind the event?”

And almost nobody builds that into their operating model.

The Real Goal

This isn’t about cleaning up logs.

It’s about moving from:

👉 “We saw something happen”
to
👉 “We know who did it, and we trust that answer”

Because without that…

You don’t have detection.
You don’t have response.
You don’t have accountability.

You have ambiguity.

## What this query is trying to do

At a high level, the query is asking:

**“Where in my environment are things happening under accounts that don’t resolve cleanly to an actual user or service identity?”** 

That matters because blank or weird account values usually mean one of four things:

* bad telemetry
* parser / schema inconsistency
* system-level activity that was not attributed cleanly
* something genuinely suspicious that deserves a second look

This is a **hunting query**, not a clean compliance report. Its purpose is to surface identity gaps and force you to inspect them. 

```kql
// Hunt for actions performed by blank/empty/null accounts
// Covers: Entra ID Sign-ins, Audit Logs, Azure Activity, Defender for Endpoint
// ── 1. Entra ID Sign-In Logs ──────────────────────────────────────────────────
let EntraSignIns = SigninLogs
| where TimeGenerated > ago(7d)
| where isnull(UserPrincipalName) or isempty(UserPrincipalName) or UserPrincipalName in ("", "N/A", "unknown", "-")
       or isnull(UserDisplayName) or isempty(UserDisplayName) or UserDisplayName in ("", "N/A", "unknown", "-")
| project
    TimeGenerated,
    Source          = "EntraID - SigninLogs",
    AccountUPN      = UserPrincipalName,
    AccountDisplay  = UserDisplayName,
    Action          = "Sign-In",
    Result          = tostring(ResultType),
    ResultDesc      = ResultDescription,
    AppDisplayName,
    IPAddress,
    Location        = tostring(LocationDetails),
    DeviceDetail    = tostring(DeviceDetail),
    ConditionalAccessStatus,
    CorrelationId;
// ── 2. Entra ID Audit Logs ───────────────────────────────────────────────────
let EntraAudit = AuditLogs
| where TimeGenerated > ago(7d)
| extend InitiatedUPN = tostring(InitiatedBy.user.userPrincipalName)
| extend InitiatedApp = tostring(InitiatedBy.app.displayName)
| where (isnull(InitiatedUPN) or isempty(InitiatedUPN) or InitiatedUPN in ("", "N/A", "unknown", "-"))
      and (isnull(InitiatedApp) or isempty(InitiatedApp) or InitiatedApp in ("", "N/A", "unknown", "-"))
| project
    TimeGenerated,
    Source          = "EntraID - AuditLogs",
    AccountUPN      = InitiatedUPN,
    AccountDisplay  = InitiatedApp,
    Action          = OperationName,
    Result          = Result,
    ResultDesc      = ResultDescription,
    AppDisplayName  = InitiatedApp,
    IPAddress       = tostring(InitiatedBy.user.ipAddress),
    Location        = "",
    DeviceDetail    = "",
    ConditionalAccessStatus = "",
    CorrelationId;

// ── 3. Azure Activity Logs (Control Plane) ───────────────────────────────────
let AzureActivity_ = AzureActivity
| where TimeGenerated > ago(7d)
| where isnull(Caller) or isempty(Caller) or Caller in ("", "N/A", "unknown", "-")
| project
    TimeGenerated,
    Source          = "AzureActivity",
    AccountUPN      = Caller,
    AccountDisplay  = Caller,
    Action          = OperationNameValue,
    Result          = ActivityStatusValue,
    ResultDesc      = tostring(Properties),
    AppDisplayName  = "",
    IPAddress       = CallerIpAddress,
    Location        = "",
    DeviceDetail    = "",
    ConditionalAccessStatus = "",
    CorrelationId;

// ── 4. Microsoft Defender for Endpoint – Device Events ───────────────────────
let DefenderEvents = DeviceEvents
| where TimeGenerated > ago(7d)
| where (isnull(AccountName) or isempty(AccountName) or AccountName in ("", "N/A", "unknown", "-"))
       or (isnull(AccountDomain) or isempty(AccountDomain) or AccountDomain in ("", "N/A", "unknown", "-"))
| where isnotempty(ActionType)
| project
    TimeGenerated,
    Source          = "MDE - DeviceEvents",
    AccountUPN      = strcat(AccountDomain, "\\", AccountName),
    AccountDisplay  = AccountName,
    Action          = ActionType,
    Result          = "",
    ResultDesc      = tostring(AdditionalFields),
    AppDisplayName  = InitiatingProcessFileName,
    IPAddress       = RemoteIP,
    Location        = "",
    DeviceDetail    = DeviceName,
    ConditionalAccessStatus = "",
    CorrelationId   = "";

// ── 5. Microsoft Defender for Endpoint – Logon Events ────────────────────────
let DefenderLogons = DeviceLogonEvents
| where TimeGenerated > ago(7d)
| where (isnull(AccountName) or isempty(AccountName) or AccountName in ("", "N/A", "unknown", "-"))
       or (isnull(AccountSid) or isempty(AccountSid) or AccountSid in ("", "N/A", "unknown", "-"))
| project
    TimeGenerated,
    Source          = "MDE - DeviceLogonEvents",
    AccountUPN      = strcat(AccountDomain, "\\", AccountName),
    AccountDisplay  = AccountName,
    Action          = strcat("Logon (", LogonType, ")"),
    Result          = ActionType,
    ResultDesc      = tostring(AdditionalFields),
    AppDisplayName  = InitiatingProcessFileName,
    IPAddress       = RemoteIP,
    Location        = "",
    DeviceDetail    = DeviceName,
    ConditionalAccessStatus = "",
    CorrelationId   = "";
// ── Union + Summarize ─────────────────────────────────────────────────────────
EntraSignIns
| union isfuzzy=true EntraAudit, AzureActivity_, DefenderEvents, DefenderLogons
| summarize
    EventCount      = count(),
    FirstSeen       = min(TimeGenerated),
    LastSeen        = max(TimeGenerated),
    Actions         = make_set(Action, 25),
    Results         = make_set(Result, 10),
    IPAddresses     = make_set(IPAddress, 10),
    Devices         = make_set(DeviceDetail, 10)
  by Source, AccountUPN, AccountDisplay
| extend BlankReason = case(
    isnull(AccountUPN) or AccountUPN == "",   "Null/Empty UPN",
    AccountUPN == "N/A",                       "Explicit N/A",
    AccountUPN == "unknown",                   "Unknown string",
    AccountUPN startswith "\\",                "Domain only - no username",
                                               "Other blank pattern"
  )
| project-reorder
    Source, BlankReason, AccountUPN, AccountDisplay,
    EventCount, FirstSeen, LastSeen,
    Actions, Results, IPAddresses, Devices
| sort by EventCount desc
```

---

## The operating model behind it

The query is built like a proper cross-platform hunt:

1. Pull potentially unattributed activity from several tables.
2. Normalize the columns so the results can be unioned together.
3. Summarize by account and source.
4. Add a reason label explaining *why* the account looks blank.
5. Sort by event volume so the biggest issues rise to the top. 

That is good engineering discipline. It is not just “dump everything weird.” It is trying to make different telemetry sources speak a common language.

---

# Section-by-section breakdown

## 1. Entra ID sign-in logs

```kusto
let EntraSignIns = SigninLogs
| where TimeGenerated > ago(7d)
| where isnull(UserPrincipalName) or isempty(UserPrincipalName) or UserPrincipalName in ("", "N/A", "unknown", "-")
       or isnull(UserDisplayName) or isempty(UserDisplayName) or UserDisplayName in ("", "N/A", "unknown", "-")
```

This part looks at **interactive or non-interactive sign-in activity** from Entra ID over the last 7 days and filters for records where the user identity fields are missing or junk values. 

### What it’s doing

It says:

* give me sign-ins from the past week
* keep only rows where either:

  * `UserPrincipalName` is null/empty/fake
  * or `UserDisplayName` is null/empty/fake 

### Why this matters

In a healthy tenant, sign-in events should generally tell you **who** signed in. If that falls apart, you want to know whether:

* the event came from an app or token flow that did not map cleanly
* there is connector normalization drift
* the sign-in is malformed or partially populated
* identity attribution is breaking where you least want it to break: authentication telemetry

### What gets projected

This block standardizes columns like:

* source
* account UPN
* display name
* action = “Sign-In”
* result / result description
* app name
* IP
* location
* device detail
* CA status
* correlation ID 

That projection step is important because later every data source has to fit the same shape.

---

## 2. Entra ID audit logs

```kusto
let EntraAudit = AuditLogs
| where TimeGenerated > ago(7d)
| extend InitiatedUPN = tostring(InitiatedBy.user.userPrincipalName)
| extend InitiatedApp = tostring(InitiatedBy.app.displayName)
| where (isnull(InitiatedUPN) or isempty(InitiatedUPN) or InitiatedUPN in ("", "N/A", "unknown", "-"))
      and (isnull(InitiatedApp) or isempty(InitiatedApp) or InitiatedApp in ("", "N/A", "unknown", "-"))
```

This block checks **directory audit activity** where the actor is unclear. 

### What it’s doing

Audit logs can be initiated by:

* a user
* an application
* automation / service principal behavior

So the query extracts both:

* `InitiatedUPN`
* `InitiatedApp`

Then it keeps only records where **both are blank or junk**. 

### Why that’s smart

This is stricter than the sign-in logic.

For sign-ins, if either the UPN or display name is blank, that is notable.

For audit logs, the query only flags records when **neither a user nor an app identity is meaningfully present**. That reduces false positives. A lot of audit actions are legitimately app-driven, so you do not want to alert just because the user field is empty if the app field clearly identifies the actor.

### What this means operationally

If something changed in Entra — app registration, policy update, group membership, directory config — and the actor is effectively unknown, that is worth attention.

---

## 3. Azure Activity logs

```kusto
let AzureActivity_ = AzureActivity
| where TimeGenerated > ago(7d)
| where isnull(Caller) or isempty(Caller) or Caller in ("", "N/A", "unknown", "-")
```

This block looks for **Azure control plane operations** where `Caller` is blank or junk. 

### Why this matters

`AzureActivity` is where you see subscription/resource-manager actions like:

* resource creation
* role assignments
* policy changes
* networking changes
* VM actions

If `Caller` is empty, your ability to attribute who made the change is degraded.

### DevSecOpsDad translation

This is the cloud-control-plane equivalent of someone changing production and the badge reader not recording who entered the room.

That does not always mean compromise. But it absolutely means **reduced accountability**.

---

## 4. Defender for Endpoint device events

```kusto
let DefenderEvents = DeviceEvents
| where TimeGenerated > ago(7d)
| where (isnull(AccountName) or isempty(AccountName) or AccountName in ("", "N/A", "unknown", "-"))
       or (isnull(AccountDomain) or isempty(AccountDomain) or AccountDomain in ("", "N/A", "unknown", "-"))
| where isnotempty(ActionType)
```

This block hunts through **MDE device events** where account attribution is incomplete. 

### What it means

Device events often contain process, file, registry, network, and other endpoint activity. This block keeps events where:

* `AccountName` is bad
* or `AccountDomain` is bad
* and there is still a valid `ActionType` 

That last line matters. It avoids meaningless blank rows by requiring that an actual event action exists.

### Why it’s useful

On endpoints, unattributed events are common enough to exist but dangerous enough to monitor. Sometimes they reflect:

* SYSTEM / kernel-ish behavior
* telemetry gaps
* edge-case parsing failures
* attacker activity through contexts that do not cleanly map to a normal user

The query builds a synthetic identity field here:

```kusto
AccountUPN = strcat(AccountDomain, "\\", AccountName)
```

That is not a real UPN — it is a convenience string so the endpoint data can align with the same account column concept used elsewhere. 

---

## 5. Defender for Endpoint logon events

```kusto
let DefenderLogons = DeviceLogonEvents
| where TimeGenerated > ago(7d)
| where (isnull(AccountName) or isempty(AccountName) or AccountName in ("", "N/A", "unknown", "-"))
       or (isnull(AccountSid) or isempty(AccountSid) or AccountSid in ("", "N/A", "unknown", "-"))
```

This one is focused specifically on **logon activity on devices** where the account name or SID is missing. 

### Why SID matters

A SID is often more trustworthy than a display label. If the SID is blank too, then the logon event is missing one of the strongest identity anchors available in Windows telemetry.

### Why this is worth checking

A blank account name might be annoying.

A blank account name **and** weak identity backing on a logon event is much more worth investigation.

This section again normalizes the output into the common schema and labels the action as:

```kusto
strcat("Logon (", LogonType, ")")
```

Nice touch. That preserves the logon type context instead of reducing everything to a generic “logon.”

---

# The union step

```kusto
EntraSignIns
| union isfuzzy=true EntraAudit, AzureActivity_, DefenderEvents, DefenderLogons
```

This is the glue. It combines all those shaped datasets into one result set. 

### Why `isfuzzy=true` matters

Different tables do not always have perfectly matching column sets or types. `isfuzzy=true` tells KQL to be more forgiving during union, which is practical when you are normalizing heterogeneous sources.

Translation: **“Don’t make me perfectly align every schema edge case before I can hunt.”**

That is a good move in exploratory cross-table hunting.

---

# The summarize step

```kusto
| summarize
    EventCount      = count(),
    FirstSeen       = min(TimeGenerated),
    LastSeen        = max(TimeGenerated),
    Actions         = make_set(Action, 25),
    Results         = make_set(Result, 10),
    IPAddresses     = make_set(IPAddress, 10),
    Devices         = make_set(DeviceDetail, 10)
  by Source, AccountUPN, AccountDisplay
```

This is where the query stops being raw telemetry and starts becoming investigation-ready. 

### What it does

It groups results by:

* source
* account identifier
* account display value

Then it rolls up:

* total event count
* first seen / last seen
* distinct actions
* distinct results
* IPs
* devices 

### Why this is the right move

Analysts do not want 600 rows of the same bad identity pattern.

They want:

* how often it happened
* where it happened
* over what time window
* what actions were associated
* what infrastructure it touched

This is exactly the difference between **query output** and **decision support**.

---

# The `BlankReason` logic

```kusto
| extend BlankReason = case(
    isnull(AccountUPN) or AccountUPN == "",   "Null/Empty UPN",
    AccountUPN == "N/A",                       "Explicit N/A",
    AccountUPN == "unknown",                   "Unknown string",
    AccountUPN startswith "\\",                "Domain only - no username",
                                               "Other blank pattern"
  )
```

This adds interpretation. 

### Why it matters

Without this, the analyst still has to eyeball why the account is considered blank.

With this, the query starts classifying the defect pattern:

* null/empty
* explicitly marked N/A
* literally “unknown”
* domain present but username missing
* other weirdness 

### DevSecOpsDad take

This is good because it turns an ambiguous “bad identity” result into a **triageable data quality signal**.

It helps you separate:

* expected telemetry ugliness
  from
* strange operational conditions
  from
* suspicious attribution failures

---

# Final output shape

```kusto
| project-reorder
    Source, BlankReason, AccountUPN, AccountDisplay,
    EventCount, FirstSeen, LastSeen,
    Actions, Results, IPAddresses, Devices
| sort by EventCount desc
```

This is just presentation, but it is good presentation. 

### Why sort by event count?

Because the biggest piles of unattributed activity are where your operational risk usually lives first.

Not always the most malicious.
But usually the most impactful to investigate.

---

# What this query is good at

This query is strong for:

* surfacing unattributed actions across identity, cloud, and endpoint logs
* exposing telemetry normalization issues
* identifying service/system activity that lacks clear identity mapping
* finding places where accountability breaks down
* building follow-on investigations from IPs, devices, and actions 

---

# What it is *not* good at

This query is **not** automatically proving malicious behavior.

A blank identity does **not** equal compromise.

It may just mean:

* connector weirdness
* ingestion/parser inconsistency
* platform-generated activity
* fields that are legitimately unset for a given event type

So the right mindset is:

**“This is a hunting pivot, not a verdict.”**

---

# Things I would tell an engineer or SOC analyst about it

## 1. It is intentionally broad

This query is trying to catch **identity ambiguity**, not just attacker behavior.

That means there will be false positives.

## 2. It is schema-normalized well

The author did a good job forcing multiple sources into a common structure so the results can be compared side by side. 

## 3. The MDE sections may surface a lot of benign noise

Especially on endpoints, missing account context can happen around system activity, service activity, or telemetry edge cases.

## 4. The Entra Audit block is more disciplined than the others

Requiring both user and app initiator to be blank is a more mature filter than blindly flagging missing user-only fields.

## 5. The summary output is investigation-friendly

You get counts, time bounds, actions, IPs, and devices rather than drowning in raw rows.

---

# Where I would tighten it up

A few improvements I’d consider:

## Add known benign exclusions

For example, exclude well-known system-generated patterns once you validate them. Otherwise this can become a “look how weird telemetry is” report instead of a detection aid.

## Normalize case before comparison

Values like `"Unknown"` vs `"unknown"` can slip through. Using `tolower()` would make this sturdier.

## Treat `"-"` and `"N/A"` carefully

Those are often parser placeholders, not native product values. Good to catch them, but they may indicate upstream transformation issues more than original log issues.

## Consider preserving raw rows for drilldown

The summarize is great, but in a production hunt workbook you might want a second view with raw events for immediate pivoting.

## Consider splitting “identity missing” from “identity malformed”

Those are related, but not always the same operational problem.

---

# The plain-English summary

This query is a **cross-source hunt for actions that happened without a trustworthy identity attached**. It checks Entra sign-ins, Entra audit logs, Azure control-plane logs, and Defender endpoint telemetry for blank, null, or obviously placeholder account fields, then summarizes the results so you can see where attribution is breaking down at scale. 

Or in DevSecOpsDad language:

**It’s not asking “was this evil?” first.**
It’s asking:
**“Where am I making security decisions without being able to cleanly say who did the thing?”**

That is exactly the kind of question mature defenders should ask.

Paste the next query and I’ll break that one down the same way.
