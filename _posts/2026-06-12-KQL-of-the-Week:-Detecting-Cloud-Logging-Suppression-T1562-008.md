![DevSecOpsDadAttack!](/assets/img/Attack1.png)
Every day our [Detection Engineering Brief](https://DevSecOpsDadAttack.com) turns fresh threat intel into deployable detection content — KQL for Microsoft Sentinel and Defender XDR, ATT&CK mappings, triage runbooks, and deployment-readiness calls. This week's five briefs produced **21 KQL candidates** across Apache ActiveMQ and Gogs RCE, a Check Point VPN zero-day (CVE-2026-50751), PAN-OS exploitation (CVE-2026-0257), the Ivanti Sentry auth-bypass/RCE pair (CVE-2026-10520 / CVE-2026-10523), an Oracle PeopleSoft zero-day (CVE-2026-35273), and Azure cloud-logging tampering.

Most of those detections were built around a familiar shape: **find the exploit, detect the exploit, alert on the exploit.**

One pair of detections wasn't looking for exploitation at all.

It was looking for the moment an attacker makes sure you'll never *see* the exploitation. That's a very different problem — and it's why this week's KQL of the Week is the Azure logging-suppression sequence from Wednesday and Thursday's briefs.

---

## 🥇 The main event: catch the attacker who turns off the cameras

Defenders spend enormous effort building visibility. We deploy Sentinel. We onboard Defender. We forward Syslog. We configure diagnostic settings and stream audit logs.

The mature attacker knows this, so they don't go after your workloads first. They go after your *logging*. Delete the diagnostic settings, kill the export, drop the retention — and only then start escalating. Think bank robbery: the amateur walks into the lobby and hopes nobody notices. The professional cuts the camera feed first.

Unit 42's "Blinding the Watchmen" research (the intel source behind these detections) is exactly about this: adversaries abusing cloud-logging configuration as a defense-evasion primitive. ATT&CK has a name for it — **T1562.008, Impair Defenses: Disable or Modify Cloud Logs.** The briefs this week built two detections around it, and the jump between them is the whole lesson.

### Step one: detect the camera going dark (the event)

Wednesday's brief shipped the single-event version as a **production candidate**. It watches `AzureActivity` for control-plane operations that delete or rewrite diagnostic settings and Log Analytics workspaces:

```kql
AzureActivity
| where TimeGenerated > ago(1d)
| where tolower(OperationName) has_any (
    "microsoft.insights/diagnosticsettings/delete",
    "microsoft.insights/diagnosticsettings/write",
    "microsoft.operationalinsights/workspaces/delete",
    "microsoft.operationalinsights/workspaces/write"
  )
| where ActivityStatusValue =~ "Success" or ActivityStatus =~ "Succeeded"
| extend InitiatorUPN = tostring(parse_json(tostring(parse_json(InitiatedBy).user)).userPrincipalName)
| extend InitiatorApp = tostring(parse_json(tostring(parse_json(InitiatedBy).app)).displayName)
| extend ActorType = case(
    isnotempty(InitiatorUPN), "User",
    isnotempty(InitiatorApp), "ServicePrincipal",
    "Unknown"
  )
| project TimeGenerated, OperationName, ActivityStatus, CallerIpAddress, ResourceId, ResourceGroup, SubscriptionId, InitiatorUPN, InitiatorApp, ActorType
| order by TimeGenerated desc
```

Two design moves here are worth stealing even if you never touch Azure.

**It catches `write`, not just `delete`.** A junior version of this query only looks for deletions — the loud, obvious destruction. But an attacker doesn't have to *delete* your diagnostic setting to blind you; they can quietly *rewrite* it to point somewhere useless, or strip the categories that matter. Watching both `delete` and `write` closes that gap. Suppression isn't always destruction. Sometimes it's reconfiguration.

**It answers "who" before you even open the alert.** That nested `parse_json(tostring(parse_json(InitiatedBy).user))` dance is ugly, but it's doing real work: `InitiatedBy` is a JSON blob, and the query unpacks it into a clean `InitiatorUPN`, `InitiatorApp`, and an `ActorType` of `User`, `ServicePrincipal`, or `Unknown`. That last bucket is the interesting one. A logging change made by a known IaC service principal is Tuesday. The same change attributed to a human — or to nothing the query can identify — is a different conversation. **The "who" is half the signal.**

And notice the status guard:

```kql
| where ActivityStatusValue =~ "Success" or ActivityStatus =~ "Succeeded"
```

That `or` isn't sloppiness — it's a schema-drift defense. `ActivityStatusValue` is the newer normalized field; `ActivityStatus` is the legacy one some ingestion pipelines still populate. Trust the new field, fall back to the old one. If that pattern feels familiar, it should: it's the same instinct as last week's beaconing query trusting Defender's `RemoteIPType` first and only falling back to `ipv4_is_private()`. **Lean on the platform's normalized field, but keep a fallback so the query doesn't go silent on a tenant that hasn't caught up.**

This query is solid. It's also, by itself, *noisy* — and the brief is honest about that. Admins legitimately modify logging, change retention, migrate workspaces, and reconfigure exports all day long. As a standalone alert it will bury you.

Which is the whole reason Thursday's brief evolved it.

### Step two: detect the camera going dark *and someone moving in the dark right after* (the sequence)

Here's the featured query — Thursday's Detection 5, classified `correlation`, hunting-only. This is where the detection stops being interesting and starts being *good*:

```kql
let lookback = 4h;
let followOnWindow = 60m;
let deletionOps = dynamic([
    "microsoft.insights/diagnosticsettings/delete",
    "microsoft.insights/logprofiles/delete",
    "microsoft.operationalinsights/workspaces/delete"
]);
let loggingDeletions = AzureActivity
    | where TimeGenerated > ago(lookback)
    | where tolower(OperationName) in (deletionOps)
    | where ActivityStatus in ("Succeeded", "Success")
    | project DeletionTime = TimeGenerated, Caller, DeletedResource = ResourceId, CallerIpAddress;
let followOnActivity = AzureActivity
    | where TimeGenerated > ago(lookback)
    | where ActivityStatus in ("Succeeded", "Success")
    | where tolower(OperationName) !in (deletionOps)
    | summarize FollowOnTime = min(TimeGenerated), FollowOnOperation = take_any(OperationName), FollowOnResource = take_any(ResourceId) by Caller, bin(TimeGenerated, 1m)
    | project FollowOnTime, Caller, FollowOnResource, FollowOnOperation;
loggingDeletions
| join kind=inner followOnActivity on Caller
| where FollowOnTime >= DeletionTime and FollowOnTime <= DeletionTime + followOnWindow
| where FollowOnResource != DeletedResource
| extend TimeDeltaMinutes = datetime_diff('minute', FollowOnTime, DeletionTime)
| project DeletionTime, FollowOnTime, TimeDeltaMinutes, Caller, CallerIpAddress, DeletedResource, FollowOnResource, FollowOnOperation
| order by DeletionTime desc
```

The single-event query asked, *"Did someone turn off a camera?"*

This one asks, *"Did someone turn off a camera, and then keep moving?"*

### The line that does the work

```kql
| join kind=inner followOnActivity on Caller
| where FollowOnTime >= DeletionTime and FollowOnTime <= DeletionTime + followOnWindow
```

If you read last week's article, this should feel like vindication.

Last week's honorable mention was a GlobalProtect "absence" detection that tried to bound an auth-to-session window *inside* the join's `on` clause — and I spent a whole section explaining why KQL's `join ... on` is built for equality matching, not range conditions, and why cramming a time window in there silently misbehaves. The fix was to **do the equality join on the key, then enforce the time window with an explicit `where` after the join.**

This Thursday query is that exact pattern, done right, the first time:

- `join kind=inner ... on Caller` — a clean **equality** join on the actor. No time logic smuggled into the `on`.
- `| where FollowOnTime >= DeletionTime and FollowOnTime <= DeletionTime + followOnWindow` — the window enforced **after** the join, as a real predicate, where KQL can actually reason about it.

`DeletionTime` and `FollowOnTime` aren't magic — they're just `TimeGenerated` renamed inside each `let` block (`project DeletionTime = TimeGenerated` and `summarize FollowOnTime = min(TimeGenerated)`). Renaming the two timestamps is what lets the final `where` compare them without ambiguity. That's the small move that makes the whole sequence legible.

Two more guards quietly do a lot:

- `| where FollowOnResource != DeletedResource` — drops the boring case where the follow-on action is just touching the same resource that got reconfigured (an admin finishing one task), keeping the suspicious case where they pivoted *elsewhere* after going dark.
- `summarize ... by Caller, bin(TimeGenerated, 1m)` in the follow-on set — collapses a burst of follow-on operations into one representative row per actor per minute, so a busy session doesn't explode into thousands of join rows.

### Why sequence beats event

This is the part worth tattooing on the inside of your eyelids.

**Events are weak. Sequences are strong.**

Compare the two alerts:

```text
Alert #1
  Diagnostic settings deleted.
```

Interesting. Maybe. Maybe not. An admin did it before lunch.

```text
Alert #2
  Diagnostic settings deleted.
  17 minutes later, same caller:
    - role assignment written
    - Key Vault accessed
    - new resource created
```

Now you have context. Now you have intent. Now you have a *story* — and stories are what analysts investigate. The deletion is the same event in both. What changed is that the second one asked the only question that matters after the cameras go dark: **what happened next?**

An administrator modifies logging and goes to lunch. An attacker modifies logging and starts touching things. Those two behaviors look almost identical at the event level and completely different at the sequence level.

### Keeping it honest

The Thursday brief is marked **hunting-only — "do not schedule yet; validate as an analyst-led hunt first"** — and it earns that label. Don't promote this to a scheduled rule until you've dealt with three things, all of which the brief calls out plainly:

**1. The join is on `Caller` alone, and that's a real weakness.** Any coincidental activity by the same identity inside the 60-minute window will match. In an active tenant where admins are constantly doing legitimate work, that's a meaningful false-positive source — one identity that deletes a stale diagnostic setting and then does *anything* else for the next hour lights up. The single best hardening, straight from the brief's tuning notes, is to require the **same source IP** for both halves of the chain, so you're correlating a *session*, not just an *identity*. Carry `CallerIpAddress` through the `followOnActivity` summarize as `FollowOnIp`, then compare the two after the join:

```kql
let followOnActivity = AzureActivity
    | where TimeGenerated > ago(lookback)
    | where ActivityStatus in ("Succeeded", "Success")
    | where tolower(OperationName) !in (deletionOps)
    | summarize FollowOnTime = min(TimeGenerated),
        FollowOnOperation = take_any(OperationName),
        FollowOnResource = take_any(ResourceId),
        FollowOnIp = take_any(CallerIpAddress)            // carry the IP through
        by Caller, bin(TimeGenerated, 1m)
    | project FollowOnTime, Caller, FollowOnResource, FollowOnOperation, FollowOnIp;
loggingDeletions
| join kind=inner followOnActivity on Caller
| where FollowOnTime >= DeletionTime and FollowOnTime <= DeletionTime + followOnWindow
| where FollowOnResource != DeletedResource
| where FollowOnIp == CallerIpAddress                     // same session, not just same person
| extend TimeDeltaMinutes = datetime_diff('minute', FollowOnTime, DeletionTime)
| project DeletionTime, FollowOnTime, TimeDeltaMinutes, Caller, CallerIpAddress, DeletedResource, FollowOnResource, FollowOnOperation
| order by DeletionTime desc
```

Same identity is a coincidence generator. Same identity *and* same IP *and* same hour is a story. (One caveat worth a comment in your own copy: if a real attacker rides a shared NAT or egress IP, the same-IP check can suppress a true chain — so keep the looser `Caller`-only version as your hunting query and treat the same-IP version as the higher-fidelity alerting variant.)

**2. Ingestion latency can break the window at the edges.** `AzureActivity` commonly lags 5–15 minutes, and that lag isn't uniform across operations. A follow-on event can land in the workspace *before* the deletion it logically followed, dropping a real chain right at the `followOnWindow` boundary. Widen the window for hunting; don't trust tight boundaries for alerting.

**3. The follow-on summarize hides detail.** `take_any(OperationName)` and `take_any(ResourceId)` keep the row count sane but collapse a multi-step follow-on into a single sampled operation. Great for triage volume, lossy for reconstructing the full chain — so when something hits, pivot back to raw `AzureActivity` for that `Caller` and window before you write the verdict.

### How I'd evolve it

If I were turning this hunt into a production analytic, I'd stop treating all follow-on activity as equal and start **weighting by what the attacker actually wants after going dark:**

- **Privilege.** Follow-on role assignments, owner/contributor grants, or PIM activations after suppression is the chain that should page someone. *Blind the defenders → grant myself power.*
- **Secrets.** Key Vault secret/key/certificate reads in the window. *Blind the defenders → take the crown jewels.*
- **Persistence.** New VMs, managed identities, automation accounts, or function apps after suppression. *Blind the defenders → move in for good.*
- **Rarity.** Most tenants have a tiny handful of identities that ever legitimately touch diagnostic settings. `summarize count() by Caller` over 30 days, then prioritize the callers who almost never do this. The rarer the actor, the louder the alert should be.

Tier those follow-on operations into a severity score and you've turned a noisy correlation into a graded one — low for "admin kept working," critical for "logging died and ninety seconds later someone granted themselves Owner."

---

## 🥈 Honorable mention: the application that shouldn't have spawned a shell

This week's honorable mention goes to Friday's **PeopleSoft RCE child-process** detection (CVE-2026-35273, the Oracle PeopleSoft zero-day Mandiant reported under active exploitation). Not because the query is clever — because it's a near-perfect example of the most durable pattern in all of detection engineering, and because its honest weakness is as instructive as its strength.

```kql
DeviceProcessEvents
| where Timestamp > ago(7d)
| where InitiatingProcessFileName in~ ("psadmin.exe", "psadmin", "java.exe", "java", "psappsrv.exe", "psappsrv", "pswatchsrv.exe", "pswatchsrv")
| where FileName in~ (
    "cmd.exe", "powershell.exe", "pwsh.exe",
    "sh", "bash", "dash", "zsh",
    "python.exe", "python", "python3",
    "perl.exe", "perl",
    "wget", "curl", "curl.exe",
    "whoami.exe", "whoami",
    "id",
    "net.exe", "net1.exe"
)
| project Timestamp, DeviceName, AccountName, InitiatingProcessFileName, InitiatingProcessCommandLine, FileName, ProcessCommandLine, FolderPath
| order by Timestamp desc
```

The pattern is the entire point:

```text
Public-facing application
        ↓
Unexpected process execution (a shell, a downloader, a discovery command)
        ↓
High-confidence investigation
```

Applications shouldn't spawn shells. When they do, something interesting is happening. Swap PeopleSoft for ActiveMQ, Gogs, Confluence, Exchange, or next quarter's enterprise zero-day and the logic is unchanged — which is exactly why this same shape showed up *three other times* in this week's briefs alone (ActiveMQ via Jolokia, Gogs via `--exec`, Ivanti Sentry's web service). Learn the pattern once; redeploy it forever.

But here's the honest part, and it's why this is a hunting query that "requires environment mapping," not a drop-in rule: **`java` and `java.exe` are in that parent list.** Tomcat, JBoss, WebLogic, and basically every other Java app server in your estate will match this filter. As written, on an unscoped tenant, this query doesn't detect PeopleSoft exploitation — it detects *the existence of Java*. The real detection engineering isn't the two `in~` lists. It's the `DeviceName` watchlist of confirmed PeopleSoft hosts (and ideally a `FolderPath` filter for `PSHOME`/`PT_HOME` when the parent is `java`) that you have to build *before* this is worth scheduling. The filter is the easy 20%. The scoping is the 80% that makes it true.

That contrast is why I paired it with the featured query. The Azure sequence teaches you to **chain events together** when no single one is enough. PeopleSoft reminds you that sometimes the whole detection is **one filter on the right parent process** — and that "the right parent" is doing almost all of the work.

---

## Patterns worth stealing

Strip away the CVEs and the product names and you're left with three reusable primitives:

- **Sequence over event.** When one action is ambiguous (deleting a diagnostic setting), correlate it with what came next. The deletion is noise; *deletion → pivot* is a story. Always ask "what happened next?"
- **The windowed join, done right.** Join on the key with `kind=inner` (or `leftanti` for absence), then enforce the time window with an explicit `where` *after* the join — never inside the `on` clause. This is the same lesson as last week's GlobalProtect fix, and this week's Azure correlation is what it looks like when you get it right the first time.
- **The "who" is half the signal.** Parsing `InitiatedBy` into a `User` / `ServicePrincipal` / `Unknown` `ActorType` turns a flat event into a triage decision before the analyst even opens it. The same change is benign from your IaC pipeline and alarming from an unidentified principal.

And one bonus, courtesy of the honorable mention: **a filter is only as good as its scope.** A list of suspicious child processes means nothing until you've told it which parents, on which hosts, actually matter.

All three came straight out of this week's daily briefs — every detection written up with ATT&CK mappings, telemetry requirements, triage runbooks, false-positive notes, and an honest deployment-readiness call. Twenty-one of them this week alone.

If you want this kind of detection content landing in your inbox every morning, that's the whole point of the **[Detection Engineering Brief at DevSecOpsDadAttack.com](https://DevSecOpsDadAttack.com)** — fresh threat intel translated straight into deployable detections, so you spend your time tuning and shipping instead of reading and re-deriving.

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
