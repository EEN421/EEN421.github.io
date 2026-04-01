# Hunting for Actions Performed by Blank/Null/Empty Accounts

There’s a class of problems most environments quietly ignore:

> **“Who did this?” → “We don’t know.”**

Blank usernames. Missing UPNs. “Unknown.” “N/A.”
And yet… actions still happened.

That’s not just messy telemetry—that’s **broken accountability**.

This query is built to hunt one thing:

> **Actions performed without a clear identity — and reconstruct who (or what) actually did them.**

Not just in one place, either. This pulls across:

* Entra ID sign-ins
* Entra ID audit logs
* Azure control plane
* Defender for Endpoint (process + logon activity)

And then does the most important thing:

> **Normalizes the chaos into a decision-grade dataset.**

Let’s break it down. 👇

```kql
// Hunt for actions performed by blank/empty/null accounts
// Includes originator/application context to identify the true actor
// ── 1. Entra ID Sign-In Logs ──────────────────────────────────────────────────
let EntraSignIns = SigninLogs
| where TimeGenerated > ago(7d)
| where isnull(UserPrincipalName) or isempty(UserPrincipalName) or UserPrincipalName in ("", "N/A", "unknown", "-")
       or isnull(UserDisplayName) or isempty(UserDisplayName) or UserDisplayName in ("", "N/A", "unknown", "-")
| extend Originator = case(
    isnotempty(ServicePrincipalName),                           strcat("SPN: ", ServicePrincipalName),
    isnotempty(ServicePrincipalId),                             strcat("SPN ID: ", ServicePrincipalId),
    isnotempty(AppDisplayName),                                 strcat("App: ", AppDisplayName),
    isnotempty(AppId),                                          strcat("AppID: ", AppId),
    isnotempty(ClientAppUsed),                                  strcat("Client: ", ClientAppUsed),
    isnotempty(tostring(DeviceDetail.displayName)),             strcat("Device: ", tostring(DeviceDetail.displayName)),
                                                                "Unknown Originator"
  )
| extend OriginatorDetail = strcat(
    "Resource: ", ResourceDisplayName,
    " | ClientApp: ", ClientAppUsed,
    " | UserAgent: ", UserAgent
  )
| project
    TimeGenerated,
    Source                  = "EntraID - SigninLogs",
    AccountUPN              = UserPrincipalName,
    AccountDisplay          = UserDisplayName,
    Action                  = "Sign-In",
    Result                  = tostring(ResultType),
    ResultDesc              = ResultDescription,
    Originator,
    OriginatorDetail,
    AppDisplayName,
    AppId,
    ServicePrincipalName,
    ServicePrincipalId,
    ClientAppUsed,
    IPAddress,
    Location                = tostring(LocationDetails),
    DeviceDetail            = tostring(DeviceDetail),
    ConditionalAccessStatus,
    CorrelationId;
// ── 2. Entra ID Audit Logs ───────────────────────────────────────────────────
let EntraAudit = AuditLogs
| where TimeGenerated > ago(7d)
| extend InitiatedUPN    = tostring(InitiatedBy.user.userPrincipalName)
| extend InitiatedApp    = tostring(InitiatedBy.app.displayName)
| extend InitiatedAppId  = tostring(InitiatedBy.app.appId)
| extend InitiatedSPNId  = tostring(InitiatedBy.app.servicePrincipalId)
| extend InitiatedSPN    = tostring(InitiatedBy.app.servicePrincipalName)
| extend InitiatedUserId = tostring(InitiatedBy.user.id)
| where (isnull(InitiatedUPN) or isempty(InitiatedUPN) or InitiatedUPN in ("", "N/A", "unknown", "-"))
      and (isnull(InitiatedApp) or isempty(InitiatedApp) or InitiatedApp in ("", "N/A", "unknown", "-"))
| extend Originator = case(
    isnotempty(InitiatedSPN),     strcat("SPN: ", InitiatedSPN),
    isnotempty(InitiatedSPNId),   strcat("SPN ID: ", InitiatedSPNId),
    isnotempty(InitiatedAppId),   strcat("AppID: ", InitiatedAppId),
    isnotempty(InitiatedUserId),  strcat("UserID: ", InitiatedUserId),
                                  "Unknown Originator"
  )
| extend OriginatorDetail = strcat(
    "AppId: ", InitiatedAppId,
    " | SPNId: ", InitiatedSPNId,
    " | UserId: ", InitiatedUserId
  )
| project
    TimeGenerated,
    Source                  = "EntraID - AuditLogs",
    AccountUPN              = InitiatedUPN,
    AccountDisplay          = InitiatedApp,
    Action                  = OperationName,
    Result                  = Result,
    ResultDesc              = ResultDescription,
    Originator,
    OriginatorDetail,
    AppDisplayName          = InitiatedApp,
    AppId                   = InitiatedAppId,
    ServicePrincipalName    = InitiatedSPN,
    ServicePrincipalId      = InitiatedSPNId,
    ClientAppUsed           = "",
    IPAddress               = tostring(InitiatedBy.user.ipAddress),
    Location                = "",
    DeviceDetail            = "",
    ConditionalAccessStatus = "",
    CorrelationId;
// ── 3. Azure Activity Logs (Control Plane) ───────────────────────────────────
let AzureActivity_ = AzureActivity
| where TimeGenerated > ago(7d)
| where isnull(Caller) or isempty(Caller) or Caller in ("", "N/A", "unknown", "-")
| extend ClaimsJson        = todynamic(Claims)
| extend ClaimAppId        = tostring(ClaimsJson.appid)
| extend ClaimAppIdAcr     = tostring(ClaimsJson.appidacr)
| extend ClaimOid          = tostring(ClaimsJson.oid)
| extend ClaimTid          = tostring(ClaimsJson.tid)
| extend Originator = case(
    isnotempty(ClaimAppId),         strcat("AppID: ", ClaimAppId),
    isnotempty(ClaimOid),           strcat("ObjectID: ", ClaimOid),
    isnotempty(ResourceProviderValue), strcat("ResourceProvider: ", ResourceProviderValue),
                                    "Unknown Originator"
  )
| extend OriginatorDetail = strcat(
    "AppId: ", ClaimAppId,
    " | AppIdAcr: ", ClaimAppIdAcr,
    " | ObjectId: ", ClaimOid,
    " | TenantId: ", ClaimTid,
    " | ResourceProvider: ", ResourceProviderValue,
    " | ResourceGroup: ", ResourceGroup
  )
| project
    TimeGenerated,
    Source                  = "AzureActivity",
    AccountUPN              = Caller,
    AccountDisplay          = Caller,
    Action                  = OperationNameValue,
    Result                  = ActivityStatusValue,
    ResultDesc              = tostring(Properties),
    Originator,
    OriginatorDetail,
    AppDisplayName          = ClaimAppId,
    AppId                   = ClaimAppId,
    ServicePrincipalName    = "",
    ServicePrincipalId      = ClaimOid,
    ClientAppUsed           = "",
    IPAddress               = CallerIpAddress,
    Location                = "",
    DeviceDetail            = "",
    ConditionalAccessStatus = "",
    CorrelationId;
// ── 4. Microsoft Defender for Endpoint – Device Events ───────────────────────
let DefenderEvents = DeviceEvents
| where TimeGenerated > ago(7d)
| where (isnull(AccountName) or isempty(AccountName) or AccountName in ("", "N/A", "unknown", "-"))
       or (isnull(AccountDomain) or isempty(AccountDomain) or AccountDomain in ("", "N/A", "unknown", "-"))
| where isnotempty(ActionType)
| extend Originator = case(
    isnotempty(InitiatingProcessAccountName),   strcat("Process Account: ", InitiatingProcessAccountDomain, "\\", InitiatingProcessAccountName),
    isnotempty(InitiatingProcessFileName),      strcat("Process: ", InitiatingProcessFileName),
    isnotempty(InitiatingProcessParentFileName),strcat("Parent Process: ", InitiatingProcessParentFileName),
                                                "Unknown Originator"
  )
| extend OriginatorDetail = strcat(
    "Process: ", InitiatingProcessFileName,
    " | PID: ", tostring(InitiatingProcessId),
    " | ParentProcess: ", InitiatingProcessParentFileName,
    " | ProcessAccount: ", InitiatingProcessAccountDomain, "\\", InitiatingProcessAccountName,
    " | CmdLine: ", InitiatingProcessCommandLine
  )
| project
    TimeGenerated,
    Source                  = "MDE - DeviceEvents",
    AccountUPN              = strcat(AccountDomain, "\\", AccountName),
    AccountDisplay          = AccountName,
    Action                  = ActionType,
    Result                  = "",
    ResultDesc              = tostring(AdditionalFields),
    Originator,
    OriginatorDetail,
    AppDisplayName          = InitiatingProcessFileName,
    AppId                   = "",
    ServicePrincipalName    = "",
    ServicePrincipalId      = "",
    ClientAppUsed           = "",
    IPAddress               = RemoteIP,
    Location                = "",
    DeviceDetail            = DeviceName,
    ConditionalAccessStatus = "",
    CorrelationId           = "";
// ── 5. Microsoft Defender for Endpoint – Logon Events ────────────────────────
let DefenderLogons = DeviceLogonEvents
| where TimeGenerated > ago(7d)
| where (isnull(AccountName) or isempty(AccountName) or AccountName in ("", "N/A", "unknown", "-"))
       or (isnull(AccountSid) or isempty(AccountSid) or AccountSid in ("", "N/A", "unknown", "-"))
| extend Originator = case(
    isnotempty(InitiatingProcessAccountName),    strcat("Process Account: ", InitiatingProcessAccountDomain, "\\", InitiatingProcessAccountName),
    isnotempty(InitiatingProcessFileName),       strcat("Process: ", InitiatingProcessFileName),
    isnotempty(InitiatingProcessParentFileName), strcat("Parent Process: ", InitiatingProcessParentFileName),
                                                 "Unknown Originator"
  )
| extend OriginatorDetail = strcat(
    "Process: ", InitiatingProcessFileName,
    " | PID: ", tostring(InitiatingProcessId),
    " | ParentProcess: ", InitiatingProcessParentFileName,
    " | ProcessAccount: ", InitiatingProcessAccountDomain, "\\", InitiatingProcessAccountName,
    " | CmdLine: ", InitiatingProcessCommandLine
  )
| project
    TimeGenerated,
    Source                  = "MDE - DeviceLogonEvents",
    AccountUPN              = strcat(AccountDomain, "\\", AccountName),
    AccountDisplay          = AccountName,
    Action                  = strcat("Logon (", LogonType, ")"),
    Result                  = ActionType,
    ResultDesc              = tostring(AdditionalFields),
    Originator,
    OriginatorDetail,
    AppDisplayName          = InitiatingProcessFileName,
    AppId                   = "",
    ServicePrincipalName    = "",
    ServicePrincipalId      = "",
    ClientAppUsed           = "",
    IPAddress               = RemoteIP,
    Location                = "",
    DeviceDetail            = DeviceName,
    ConditionalAccessStatus = "",
    CorrelationId           = "";
// ── Union + Summarize ─────────────────────────────────────────────────────────
EntraSignIns
| union isfuzzy=true EntraAudit, AzureActivity_, DefenderEvents, DefenderLogons
| summarize
    EventCount          = count(),
    FirstSeen           = min(TimeGenerated),
    LastSeen            = max(TimeGenerated),
    Actions             = make_set(Action, 25),
    Results             = make_set(Result, 10),
    IPAddresses         = make_set(IPAddress, 10),
    Devices             = make_set(DeviceDetail, 10),
    OriginatorDetails   = make_set(OriginatorDetail, 10)
  by Source, AccountUPN, AccountDisplay, Originator, AppDisplayName, AppId, ServicePrincipalName, ServicePrincipalId, ClientAppUsed
| extend BlankReason = case(
    isnull(AccountUPN) or AccountUPN == "",   "Null/Empty UPN",
    AccountUPN == "N/A",                       "Explicit N/A",
    AccountUPN == "unknown",                   "Unknown string",
    AccountUPN startswith "\\",                "Domain only - no username",
                                               "Other blank pattern"
  )
| extend OriginatorDetail = tostring(OriginatorDetails)
| project-reorder
    Source, BlankReason, AccountUPN, AccountDisplay,
    Originator, OriginatorDetail,
    AppDisplayName, AppId, ServicePrincipalName, ServicePrincipalId, ClientAppUsed,
    EventCount, FirstSeen, LastSeen,
    Actions, Results, IPAddresses, Devices
| sort by EventCount desc
```

---

# 🧠 Step 1 — Define the Problem Space (Blank Identity Hunting)

Every section starts with the same core pattern:

```kql
isnull(...) or isempty(...) or in ("", "N/A", "unknown", "-")
```

This is deliberate.

You’re not just looking for:

* `null`

You’re looking for:

* **Telemetry lies** (“unknown”)
* **Bad parsing** (“-”)
* **Broken integrations** (“N/A”)
* **Empty strings masquerading as valid data**

👉 DevSecOpsDad takeaway:

> **If you only hunt nulls, you miss half the problem.**

---

# 🔐 Step 2 — Entra ID Sign-Ins (Authentication Without Identity)

```kql
let EntraSignIns = SigninLogs
```

### What it's doing:

* Filters last 7 days
* Finds sign-ins with missing identity fields
* Builds **Originator context**

### The key move:

```kql
extend Originator = case(...)
```

This is where the query starts thinking like an architect.

Instead of saying:

> “User is blank → shrug”

It says:

> “Fine. Who else can I attribute this to?”

Hierarchy:

1. Service Principal Name (SPN)
2. Service Principal ID
3. App name / App ID
4. Client app
5. Device name
6. Fallback: Unknown

👉 This is **identity reconstruction**.

### Why this matters:

In modern environments:

* Apps act
* Tokens act
* Devices act

> **The “user” is often the least reliable identity field.**

---

# 🧾 Step 3 — Entra Audit Logs (Control Plane Actions Without Attribution)

```kql
let EntraAudit = AuditLogs
```

Here we’re hunting:

* Changes to identity, permissions, config
* Where BOTH user AND app context are missing

That’s critical:

```kql
where (InitiatedUPN is blank)
  and (InitiatedApp is blank)
```

👉 That’s a **true attribution gap**

Then again:

```kql
extend Originator = case(...)
```

We fall back to:

* SPN
* App ID
* User ID (GUID-level attribution)

👉 DevSecOpsDad takeaway:

> **When names fail, IDs still tell the truth.**

---

# ☁️ Step 4 — Azure Activity Logs (Control Plane Without Caller)

```kql
let AzureActivity_ = AzureActivity
```

Here’s the problem:

* `Caller` is blank

So we pivot to:

```kql
ClaimsJson = todynamic(Claims)
```

Now we extract:

* `appid`
* `oid` (object ID)
* `tid` (tenant)

This is **token-level attribution**.

👉 This is advanced hunting.

Most engineers stop at `Caller`.

You’re digging into:

> **JWT claim-level identity reconstruction**

---

# 🖥️ Step 5 — Defender Device Events (Execution Without User Context)

```kql
let DefenderEvents = DeviceEvents
```

Looking for:

* Process activity
* Where account name/domain is missing

Then:

```kql
Originator = InitiatingProcess*
```

Now we pivot from identity → execution context:

* Process name
* Parent process
* Process account
* Command line

👉 DevSecOpsDad truth:

> **On endpoints, processes are often more trustworthy than users.**

---

# 🔑 Step 6 — Defender Logon Events (Authentication Without Identity)

Same pattern as above, but focused on:

* Logon activity
* Missing SID / username

Again:

* Attribute via process chain

---

# 🔗 Step 7 — Union Everything (This Is Where It Gets Powerful)

```kql
union isfuzzy=true EntraAudit, AzureActivity_, DefenderEvents, DefenderLogons
```

Now we:

* Break silos
* Combine identity + control plane + endpoint

👉 `isfuzzy=true` ensures schema mismatches don’t break the union

---

# 📊 Step 8 — Normalize into Decision-Grade Data

This is the **money section**:

```kql
summarize
```

We collapse noise into:

* EventCount
* FirstSeen / LastSeen
* Actions
* Results
* IPs
* Devices
* OriginatorDetails

👉 This transforms:

> Raw telemetry → **Operational signal**

---

# 🧾 Step 9 — Classify the “Why is it Blank?”

```kql
extend BlankReason = case(...)
```

Now we categorize:

* Null/Empty
* Explicit “N/A”
* “unknown”
* Domain-only (no username)

👉 This is subtle but powerful:

> You’re not just finding bad data—you’re **understanding failure modes**

---

# 📦 Step 10 — Output Designed for Humans

```kql
project-reorder ...
sort by EventCount desc
```

This ensures:

* High-signal entities bubble to the top
* Output is analyst-friendly
* Context is preserved

---

# 🔥 DevSecOpsDad Closing: What This Query Actually Gives You

This isn’t just a query.

This is an **operating model for broken identity telemetry**.

Most teams:

* Trust identity fields blindly
* Ignore blanks
* Lose attribution

This query does the opposite:

> **It assumes identity is unreliable—and rebuilds truth from surrounding signals.**

---

## The Real Maturity Shift

This is the difference between:

| Level        | Behavior                                          |
| ------------ | ------------------------------------------------- |
| Basic        | “User is null → ignore”                           |
| Intermediate | “User is null → alert”                            |
| Advanced     | “User is null → reconstruct identity”             |
| Elite        | “User is null → understand *why* identity failed” |

---

## Final Thought

If actions are happening in your environment without identity:

> **You don’t have a logging problem.
> You have an accountability problem.**

And accountability is the foundation of detection, response, and trust.

---

If you want, next step I can help you turn this into:

* A polished blog post (ready for DevSecOpsDad site)
* A LinkedIn teaser post (high-conversion style)
* Or a “Decision Surface” section to match your book format
