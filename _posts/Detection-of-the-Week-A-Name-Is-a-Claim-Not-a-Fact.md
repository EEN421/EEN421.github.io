![DevSecOpsDadAttack!](/assets/img/KQL of the Week/Designer.png)
This week's six briefs produced **30 KQL candidates** across an NTLM-relay-to-Shadow-Credentials privilege chain, the WhatsApp VBScript RMM dropper, an npm postinstall implant, SharkLoader staging Cobalt Strike under the StrikeShark campaign, StealC and Amadey infostealers raiding browser credential stores, a photo-themed ZIP delivering a Node.js implant, and a fresh batch of Metasploit modules pointed at LiteLLM, Next.js, and Audiobookshelf.

Most of those detections do what good detections do: they watch a thing *behave* badly. A process spawns a shell. A beacon phones home. An unsigned binary reads `login.json` out of a browser profile. Behavior is the bread and butter, and the briefs were full of it.

But the three detections that stuck with me this week weren't watching behavior at all. They were watching **names**. Each one caught an attacker exploiting a name we'd all been trained to trust — a process name, a storage-bucket name, a "this route is protected" promise — and each one won by refusing to take the name at face value.

So this week's KQL of the Week is a theme, told in three queries from three different briefs: **a name is a claim, not a fact.** Act I is on Linux. Act II is in Azure. The honorable mention is on the modern web. Different telemetry, different platform, same move every time — *don't match the name against a blocklist, match the name against the fact it's supposed to imply.*

<br/>

---

<br/>

## 🥇 Act I: the process wearing someone else's name tag

Here's the problem the winning query solves.

On Linux, a process gets to pick what it's called. `argv[0]` is just a string the program hands itself at launch, and the syslog header copies it down without asking a single question. Want your malware to show up in the process list as `[kworker/0:1]` or `sshd` or `systemd`? You set one string. That's the whole trick. Defenders have been eyeballing process names for thirty years, and the attacker knows it, so the attacker writes the name they know you trust.

The SANS ISC diary behind this detection (June 24) lays out the tell. A process can lie about its **name** as much as it wants — but it cannot easily lie about its **address**. The kernel records where the binary actually lives, and auditd writes that path into the `exe=` field. So now the process is making two claims at once: *"I am sshd"* (the name) and *"I run from `/tmp/.x/sshd`"* (the path). One of those is a costume. The other is a fingerprint.

Think of a name tag at a conference. Anyone can write `STAFF` on a name tag in Sharpie. What they can't fake as easily is the badge-reader log that says which door they actually badged in through. The masquerading detection ignores the Sharpie and reads the door log.

<br/>

### The KQL

```kql
let LegitPaths = datatable(ProcName: string, ExpectedPathPrefix: string)[
    "sshd", "/usr/sbin/",
    "cron", "/usr/sbin/",
    "systemd", "/lib/systemd/",
    "bash", "/bin/",
    "sh", "/bin/",
    "python", "/usr/bin/",
    "python3", "/usr/bin/",
    "perl", "/usr/bin/",
    "nginx", "/usr/sbin/",
    "apache2", "/usr/sbin/"
];
Syslog
| where Facility in ("kern", "daemon", "user", "authpriv") or ProcessName in (LegitPaths | project ProcName)
| where SyslogMessage has "exe="
| extend ExePath = extract(@'exe="([^"]+)"', 1, SyslogMessage)
| where isnotempty(ExePath)
| extend ExeBasename = tostring(split(ExePath, "/")[-1])
| join kind=inner LegitPaths on $left.ExeBasename == $right.ProcName
| where not(ExePath startswith ExpectedPathPrefix)
| where not(ExePath startswith "/usr/local/")
| where not(ExePath startswith "/snap/")
| where not(ExePath startswith "/opt/")
| project TimeGenerated, Computer, ProcessName, ExeBasename, ExePath, ExpectedPathPrefix, SyslogMessage
| order by TimeGenerated desc
```

<br/>

### The line that does the work

It's this one:

```kql
| where not(ExePath startswith ExpectedPathPrefix)
```

Read what just happened in the two lines above it. The query joins the binary's basename against a tiny table of known system names — `sshd`, `cron`, `nginx` — and pairs each name with the one place it's *supposed* to live. Then this line asks the only question that matters: **does the address match the name?**

`sshd` running from `/usr/sbin/sshd` is just Tuesday. `sshd` running from `/tmp/.cache/sshd` is a binary that picked a trustworthy name and lives nowhere a trustworthy binary lives. The detection never needs a hash, a signature, or a threat-intel feed. It needs a *contradiction* — a name that promises one thing and a path that proves another — and `not(... startswith ...)` is the line that catches the lie.

That's the reusable lesson, and it outlasts this one query: **don't detect masquerading by listing the bad names. Detect it by checking whether the name still means what it claims.** A blocklist of evil filenames is a treadmill — they rename and you lose. A consistency check between the label and the fact is a wall, because the attacker has to break the *relationship* to evade it, and the whole point of masquerading is to keep the name intact.

<br/>

### Keeping it honest

This is a hunt, marked *requires environment mapping*, and it has real edges:

- **No auditd, no detection.** That `exe=` field doesn't come from plain syslog — it comes from auditd EXECVE/SYSCALL rules being forwarded into the `Syslog` table. If your Linux fleet isn't running auditd with execve auditing and shipping it to Sentinel, `ExePath` is empty on every row and this query returns a confident, cheerful zero. Run `Syslog | where SyslogMessage has "exe=" | take 100` before you trust it.
- **The Facility filter is sneakier than it looks.** auditd records don't reliably land under `authpriv`; depending on your dispatcher they show up as `kern`, `daemon`, or `user`. Filter on `authpriv` alone and you'll quietly drop most of your execve events — which is exactly why the query casts a wider Facility net.
- **There are two name claims here, not one.** The join keys on `ExeBasename` (the basename of the real `exe=` path), but the query also carries `ProcessName` — the syslog *header* name, which is the argv[0] the process chose for itself. When those two disagree, that's a *second*, independent masquerading signal sitting right in your projection. The brief's deployment gate flags the flip side honestly: if `ProcessName` isn't populated, you lose that cross-check. Eyeball both columns in triage; the gap between them is half the story.
- **Legitimate software lives in weird places.** Snap, Flatpak, `/opt`, `/usr/local`, and a hundred container base images all run system-named binaries from non-standard paths. The query pre-excludes `/usr/local/`, `/snap/`, and `/opt/`, but your environment has its own list. Tune the `LegitPaths` table and the exclusions to *your* normal, or you'll spend week one drowning in package managers.

Act I catches the costume. It does not catch the attacker who reused a *name* you don't run locally at all — because the next act isn't on a host you own.

<br/>

---

<br/>

## 🥈 Act II: the name that came back wearing a different face

Same idea, one cloud layer up.

Storage bucket names are **globally unique**. Across all of Azure, all of AWS, there is exactly one `acme-prod-backups`, and whoever registers it owns it. That global namespace is convenient right up until you `delete` the account — because the second you let go of the name, it goes back into the pool, and *anyone* can grab it. Meanwhile, the config files, the SDK clients, the backup jobs, the DNS records, the half-forgotten cron task on a box nobody's logged into since 2024 — they all keep cheerfully writing to `acme-prod-backups`, because to them the name never changed.

Unit 42 named this the universal bucket-hijacking technique, and it's the cloud-scale version of the exact same lie: the name is identical, the owner is a stranger. Your data keeps flowing to a name you trust, into a bucket you no longer own.

It's a phone number that got disconnected and reassigned. Your contacts keep dialing the old number. The number is right. The person who answers is not.

<br/>

### The KQL

```kql
let lookback = 90d;
let hijackWindow = 30d;
let deletions = AzureActivity
| where TimeGenerated > ago(lookback)
| where tolower(OperationName) has "microsoft.storage/storageaccounts"
    and tolower(OperationName) has "delete"
| where ActivityStatus =~ "Succeeded"
| extend DeletedResource = tolower(tostring(split(ResourceId, "/")[-1]))
| where isnotempty(DeletedResource)
| project DeleteTime = TimeGenerated, DeletedResource, DeletedBy = Caller,
    DeletedFromIP = CallerIpAddress, SubscriptionId;
let creations = AzureActivity
| where TimeGenerated > ago(hijackWindow)
| where tolower(OperationName) has "microsoft.storage/storageaccounts"
    and (tolower(OperationName) has "write" or tolower(OperationName) has "create")
| where ActivityStatus =~ "Succeeded"
| extend CreatedResource = tolower(tostring(split(ResourceId, "/")[-1]))
| where isnotempty(CreatedResource)
| project CreateTime = TimeGenerated, CreatedResource, CreatedBy = Caller,
    CreatedFromIP = CallerIpAddress, SubscriptionId, ResourceGroup;
deletions
| join kind=inner (creations) on $left.DeletedResource == $right.CreatedResource
| where CreateTime > DeleteTime
| where CreatedBy != DeletedBy
| project
    DeleteTime, CreateTime, DeletedResource,
    DeletedBy, DeletedFromIP,
    CreatedBy, CreatedFromIP,
    SubscriptionId, ResourceGroup
| order by CreateTime desc
```

<br/>

### The line that does the work

```kql
| where CreatedBy != DeletedBy
```

Everything above it builds the resurrection. The query gathers every successful storage-account `delete` over 90 days, gathers every successful `create` over 30, and joins them **on the same name**. Then `where CreateTime > DeleteTime` enforces the order — gone first, back second — so you're looking at a genuine return from the dead, not two unrelated events that happened to share a string.

But a delete-then-recreate of the same name is *also* what every blue-green deployment and disaster-recovery script does forty times a day. The line that separates an attack from a Tuesday deploy is the last one: **`CreatedBy != DeletedBy`.** The name came back — fine. The name came back in *somebody else's hands* — that's the story. The whole detection collapses to a single question that the global namespace forces on you: when the name returned, was it the same owner who let it go?

If that ordered-join feels familiar, it should — long-time readers watched the SSH "failures-then-success" winner lean on `where TimeGenerated > LastFail` to turn coincidence into sequence. Same primitive, totally different telemetry: enforce the time relationship with a `where` *after* the join, never inside the `on`. That's what it looks like when a primitive earns its keep across unrelated detections. The new idea here isn't the join — it's the identity comparison stacked on top of it.

<br/>

### Event versus story

Two alerts, side by side.

**Alert A:**

```text
Storage account "acme-telemetry-prod" created in subscription 9f2c…
```

A create. Could be IaC. Could be a new team. You have nothing.

**Alert B:**

```text
"acme-telemetry-prod" was deleted on May 02 by svc-platform@acme.com
then recreated on Jun 24 by an identity you've never seen,
from an IP you've never seen.
```

Now you have a name with a history, a clock, and a swapped owner. The raw events didn't change. The **relationship** between them did — and that relationship is the entire detection.

<br/>

### Keeping it honest

This one is a hunt for good reason, and it has a blind spot serious enough that you need to say it out loud:

- **The worst version of this attack never touches your logs.** This query reads *your* `AzureActivity`. But because bucket names are globally unique, the attacker can register your abandoned name inside *their own* tenant — and you will never see the `create`. Your delete is in your logs; their create is in theirs. This detection catches the careless, same-cloud, in-your-tenant case. It does **not** catch the patient adversary who grabs the name from across the namespace. Pair it with "are we still writing to names we deleted?" egress thinking, or you're guarding one door of a two-door room.
- **Service principals look like strangers.** `Caller` is frequently an object ID, not a human UPN, so `CreatedBy != DeletedBy` lights up every time CI/CD recreates an account under a different managed identity. Allowlist your automation principals first, or this fires on your own pipelines all day.
- **Path parsing assumes a tidy world.** `split(ResourceId, "/")[-1]` trusts a fixed ARM path shape. Non-standard resource IDs mis-extract the name, and `OperationName` strings aren't perfectly standardized across regions and API versions, so the `has` matching can miss the occasional event.
- **Cross-subscription is a separate query.** The join will happily match across subscriptions if the data's there, but the brief is blunt that real cross-subscription detection wants its own logic. Don't assume one query covers your whole estate.

<br/>

### The thread between the acts

Strip both queries down and they're the same sentence. Act I: *this binary claims a name; does its path agree?* Act II: *this resource reclaimed a name; does its owner agree?* Neither one matches a signature. Neither one needs to know what the payload does. Both pick a **name** — the thing we've quietly decided to trust — and check it against an **independent fact** the attacker can't forge in the same motion. Break the costume, keep the consistency check, and you catch the variant you've never seen because you were never matching on the variant in the first place.

<br/>

---

<br/>

## 🎖 Honorable Mention: the bypass you detect by counting who got in

If Act I and Act II win on the lesson, Sunday's Next.js detection wins on *where the puck is going* — and it pulls the same trick one more way.

This week's Rapid7 wrap shipped a Metasploit scanner for Next.js middleware authorization bypass. Middleware is where a lot of modern apps put their "you must be logged in" check, and a whole class of bugs lets a crafted request walk straight past it. The naive detection is to go signature-hunting for the magic bypass header. The better detection doesn't read the payload at all.

```kql
CommonSecurityLog
| where TimeGenerated > ago(24h)
| where RequestURL has_any ("/_next/", "/api/", "/middleware")
| where RequestMethod in ("GET", "POST", "HEAD")
| summarize
    TotalRequests = count(),
    Codes200 = countif(ResponseCode == 200),
    Codes401 = countif(ResponseCode == 401),
    Codes403 = countif(ResponseCode == 403),
    UserAgents = make_set(UserAgent),
    Paths = make_set(RequestURL)
    by SourceIP, DeviceVendor, DeviceProduct, DestinationPort, bin(TimeGenerated, 5m)
| where TotalRequests > 10 and Codes401 > 0 and Codes200 > 0
| extend BypassRatio = todouble(Codes200) / todouble(TotalRequests)
| where BypassRatio > 0.3
| order by TotalRequests desc
```

Read the line that does the work: `where TotalRequests > 10 and Codes401 > 0 and Codes200 > 0`. The signal isn't a string in the request — it's the *shape of the responses*. One source, hammering protected routes, getting **both** doors-slammed (`401`) **and** doors-open (`200`) in the same five-minute window. That's the fingerprint of a scanner mid-tuning: it's trying variations, most bounce, and some land. `BypassRatio > 0.3` says *too many are landing.* You never decode the exploit. You count outcomes, and the outcome distribution rats out the bypass.

In plain English: **"who is being told no and getting in anyway?"**

The honest catch — and the brief flags it — is that `/_next/` static assets are legitimately unauthenticated and return `200` all day, which inflates the ratio, and expired-session users naturally produce a `401`-then-`200` two-step. So you narrow to real middleware-protected routes before you schedule this, and you remember `CommonSecurityLog` is a legacy table where `ResponseCode` sometimes arrives as a string or null and quietly breaks your `countif`. It's a probe detector, not a breach confirmation.

But the reason it earns the mention: detecting by *result* instead of *signature* is the most variant-proof move in the book. The next bypass header, the next CVE in this class, the next framework with the same middleware pattern — the payload changes, but "a source getting both 401 and 200 on locked routes" doesn't. That detector ages well. Most don't.

<br/>

---

<br/>

## The bigger lesson

Three briefs, three platforms, one idea: the strongest detections this week weren't the most complex KQL. They were the ones that refused to trust a name.

- **Check the claim against the fact.** A name is a promise — `sshd`, `acme-prod-backups`, "this route is protected." Don't match the promise against a list of known-bad promises. Match it against the independent fact it's supposed to imply: the path, the owner, the access result. Masquerading is a contradiction, so detect the contradiction.
- **Names are a global trust surface, and attackers know it.** Process names, bucket names, route guarantees — we built trust on top of all of them, which is precisely why they get reused, recycled, and faked. The reusable question is always the same: *does this name still mean what we think it means?*
- **When you can, detect the result, not the signature.** The Next.js query never parses an exploit. It counts which doors opened. Signatures rot the moment the attacker renames; outcome-shape detections survive the variant, because the attacker can change the payload but not the result they're paying for.

Every one of those came straight out of this week's daily briefs — each detection shipped with ATT&CK mappings, telemetry requirements, triage runbooks, false-positive notes, and an honest readiness call. Thirty of them this week.

If you want this kind of detection content landing in your inbox every morning — fresh threat intel translated straight into deployable detections, so you spend your time tuning and shipping instead of reading and re-deriving — that's the whole point of the **[Detection Engineering Brief at DevSecOpsDadAttack.com](https://DevSecOpsDadAttack.com)**.

<br/>

![](/assets/img/KQL of the Week/KQL-of-the-Week-A-Name-Is-a-Claim.png)

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
