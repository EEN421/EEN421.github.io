🧰 Intro – The Forgotten Devices Lurking in Your Network

Every SOC has a few skeletons in the closet — that dusty Windows Server still running the payroll app, or that vendor workstation quietly humming along on Windows 10 1909. They work, sure… but they’re way past their prime. 🧟‍♂️

When hardware or software hits End-of-Life (EoL), the vendor stops sending love letters in the form of patches, firmware updates, and security fixes. That means the next exploit doesn’t need zero-day wizardry — it just needs your old box that’s never seen a patch since 2022. 💀

So, in true DevSecOpsDad fashion, we’re automating the cleanup. 🧑‍💻
In this post, we’ll use PowerShell and the Microsoft Graph API to hunt down unsupported devices hiding in Defender’s Threat & Vulnerability Management tables. With one script, we’ll pull real-time EoL data, drop it into a tidy CSV, and hand your security or compliance team an instant report card of what’s aging out across the environment.

⚙️ Why Identifying End-of-Life Systems Matters (and What You Can Do About It)

In cybersecurity, “end-of-life” doesn’t just mean old — it means unprotected.
When hardware or software reaches its end-of-support date, vendors stop delivering security patches, firmware updates, and compatibility fixes. Those forgotten assets quickly turn into easy footholds for attackers looking for unpatched vulnerabilities or outdated agents to exploit. 🧟‍♂️

From a defender’s standpoint, ignoring EoL assets creates a ripple effect across security, compliance, and operations:

Exposure: Legacy systems are prime entry points for ransomware, privilege escalation, and lateral movement.

Compliance Risk: Frameworks like NIST CSF, CIS v8, and ISO 27001 require active lifecycle management. Unsupported OS versions and firmware are frequent audit findings.

Operational Blind Spots: Unsupported software can break telemetry and patch automation, leaving you flying blind in key parts of your environment.

That’s where automation comes in. With a little PowerShell and Microsoft Graph, you can continuously surface EoL assets and feed them directly into your existing security and IT workflows.

🧩 Practical Use Cases for EoL Automation

Attack Surface Reduction – Automatically identify and quarantine devices running out-of-support software before adversaries find them.

Compliance Evidence – Generate on-demand audit reports proving lifecycle management and patch governance are in place.

Patch & Lifecycle Management – Feed EoL findings into Intune, CMDBs, or ServiceNow to trigger upgrades or decommission tasks.

Executive Metrics – Track “% of assets within support lifecycle” as a measurable cyber hygiene KPI.

Defender XDR Integration – Correlate EoL devices with incidents in Microsoft Sentinel to prioritize the riskiest exposures.

# How the script works (step-by-step)

1. **Authenticate to Microsoft Graph (PowerShell Graph SDK)**

   * The script imports the Graph module (e.g., `Microsoft.Graph.Authentication`) and calls `Connect-MgGraph` with the **least-privilege** scope that can run Advanced Hunting (e.g., `ThreatHunting.Read.All`). This establishes a token your session will use for subsequent Graph calls. The Advanced Hunting Graph method you’re ultimately hitting is **`POST /security/runHuntingQuery`**. ([Microsoft Learn][1])

2. **Build the Advanced Hunting (KQL) query**

   * The query targets the **Threat & Vulnerability Management** software inventory table: `DeviceTvmSoftwareInventory`. That table includes **End-of-Support** columns such as `EndOfSupportStatus` and `EndOfSupportDate`, which is what lets you produce an “EoL report.” A typical shape looks like:

     ```kusto
     DeviceTvmSoftwareInventory
     | where isnotempty(EndOfSupportStatus)
     | project DeviceName, SoftwareVendor, SoftwareName, Version, EndOfSupportStatus, EndOfSupportDate
     | order by EndOfSupportDate asc
     ```

     Microsoft’s schema docs explicitly call out the presence of end-of-support info in this table. ([Microsoft Learn][2])

3. **Call the Graph Security “runHuntingQuery” API**

   * With your access token in place, the script posts the KQL to **`/security/runHuntingQuery`** (via the SDK cmdlet or a raw `Invoke-MgGraphRequest`). The API returns a result object that includes **`schema`** and **`results`** (rows) for your query. (This behavior and the PowerShell path are documented and have a sample.) ([Microsoft Learn][1])

4. **Parse the results into PowerShell objects**

   * The JSON payload’s `results` array is turned into a collection of PSCustomObjects. Each property corresponds to a projected KQL column (e.g., `DeviceName`, `SoftwareName`, `EndOfSupportDate`, etc.). If you see a missing-brace parse error in this section, it just means a hashtable or scriptblock wasn’t closed (you already hit and fixed one of those earlier).

5. **Create the output folder (if needed)**

   * The script checks if your chosen output directory (e.g., `C:\Temp`) exists and creates it if not, so the export won’t fail when saving the CSV.

6. **Export the hunting results to CSV**

   * Finally it writes the objects to disk with `Export-Csv` (or a similar file writer).
   * If you saw **“parameter … ‘UseUtf8’ not found”**, that comes from running on **Windows PowerShell 5.1**, where `-UseUtf8` isn’t available on `Out-File/Set-Content` (it’s a PowerShell 7+ convenience switch). Fixes:

     * Run the script in **PowerShell 7+**, **or**
     * Replace `-UseUtf8` with `-Encoding UTF8` on `Out-File`/`Set-Content` (and keep `Export-Csv -Encoding UTF8` if you’re on PS 5.1).
    

Awesome—here’s a clean, practical breakdown you can drop right into the article. I’ll walk through what the KQL does, how you’d use it in a normal “check EoL” workflow, how to read the results, a few smart variations, and then the PowerShell bit about the `$kql = @"..."@` here-string.

---

# How this Advanced Hunting query finds EoL software

```kusto
DeviceTvmSoftwareInventory
| where isnotempty(DeviceName)
| where isnotempty(EndOfSupportDate) and EndOfSupportDate <= now()
| summarize 
    EOLSoftwareCount = count(),
    EOLSoftwareList = make_set(SoftwareName, 100),
    OldestEOLDate = min(EndOfSupportDate)
  by DeviceName
| order by EOLSoftwareCount desc
```

### Line-by-line (what it’s doing)

1. **Start with TVM software inventory**
   `DeviceTvmSoftwareInventory` is Defender’s Threat & Vulnerability Management table that lists discovered software per device, with lifecycle metadata (including end-of-support where Microsoft/Vendor provides it).

2. **Keep only real devices**
   `| where isnotempty(DeviceName)` drops any odd/null rows.

3. **Filter to software already past EoL**
   `| where isnotempty(EndOfSupportDate) and EndOfSupportDate <= now()`

   * Ensures the vendor actually provided an end-of-support date.
   * Keeps rows where that date is **now or earlier** (i.e., already out of support today).

4. **Roll up by device**
   `summarize ... by DeviceName` collapses many rows (one per app) into **one row per device**, with:

   * `EOLSoftwareCount` → how many out-of-support titles are on that device.
   * `EOLSoftwareList` → up to 100 unique software names (handy for a one-glance review).
   * `OldestEOLDate` → the **earliest** EoL among those apps—useful to spot *how long* a device has been carrying legacy baggage.

5. **Sort by worst offenders**
   `order by EOLSoftwareCount desc` puts the noisiest/riskier devices at the top.

---

# The normal “check EoL” workflow (what an analyst actually does)

1. **Run the query** (Hunting page or API)

   * In the Defender portal (Advanced Hunting) for a quick look, or via Microsoft Graph/PowerShell for repeatable reporting.

2. **Scan the top offenders**

   * Devices with high `EOLSoftwareCount` get triaged first.
   * Skim `EOLSoftwareList` to see if it’s business-critical software (upgrade path needed) vs. dead utilities (safe to remove).

3. **Look at “how stale”**

   * `OldestEOLDate` tells you if you’re weeks vs. years overdue. A very old date = higher risk/visibility with auditors.

4. **Decide the path: upgrade, replace, or remove**

   * **Replace/upgrade**: if it’s a core app with a supported version.
   * **Remove**: if deprecated/unneeded.
   * **Isolate/quarantine**: if the device can’t be fixed quickly and is exposed.

5. **Kick off remediation**

   * Create tickets (ServiceNow/Jira), **Intune** assignments, or **Planner** tasks with due dates based on EoL age/severity.
   * If you automate with Graph, you can do this in the same PowerShell run that produced the CSV.

6. **Report & trend**

   * Export to CSV for your weekly report. Track **% of devices within support** as a KPI and show trend lines improving over time.

---

# How to interpret the columns (at a glance)

* **DeviceName** → Who needs attention.
* **EOLSoftwareCount** → Volume of unsupported titles (a proxy for risk + cleanup effort).
* **EOLSoftwareList** → What exactly is unsupported (helps owners take action).
* **OldestEOLDate** → How long you’ve been out of compliance (prioritize older first).

---

# Smart variations you might add later

* **Only critical/priority software**

  ```kusto
  | where SoftwareName in~ ("Java", "OpenJDK", "Apache HTTP Server", "MySQL", "Python", "SQL Server Management Studio")
  ```
* **Add owner/context** (join to device info)

  ```kusto
  DeviceTvmSoftwareInventory
  | where isnotempty(EndOfSupportDate) and EndOfSupportDate <= now()
  | join kind=leftouter (DeviceInfo | project DeviceName, OSPlatform, LoggedOnUsers, DeviceId) on DeviceName
  | summarize EOLSoftwareCount=count(), EOLSoftwareList=make_set(SoftwareName, 100), OldestEOLDate=min(EndOfSupportDate), any(OSPlatform), any(LoggedOnUsers)
    by DeviceName
  ```
* **Flag “nearly EoL”** (30/60/90 days) to get ahead of the curve:

  ```kusto
  | where EndOfSupportDate between (now() .. now() + 30d)
  ```
* **Prioritize by risk** (join to exposure score or to incidents) for Defender-XDR-aware triage.

---

# The PowerShell piece: what `$kql = @" ... "@` means

You’re using a **double-quoted here-string**:

```powershell
$kql = @"
DeviceTvmSoftwareInventory
| where ...
"@
```

Key facts:

* **Here-strings** let you paste multi-line text verbatim without escaping quotes or backticks. Great for KQL, JSON, and HTML.
* **Double-quoted** (`@"..."@`) means **PowerShell variable expansion is enabled** inside the block. If you write `$Today` in there, it will expand.

  * If you **don’t** want expansion, use a **single-quoted** here-string: `@' ... '@`.
* The **closing** `@"` or `@'` **must be at the start of the line** (no indentation or trailing characters).
* The content is stored as a single string—including line breaks—perfect for sending to Graph’s `runHuntingQuery` endpoint or the Graph SDK cmdlets.

Example of parameterizing the window from PowerShell:

```powershell
$days = 30
$kql = @"
DeviceTvmSoftwareInventory
| where isnotempty(DeviceName)
| where isnotempty(EndOfSupportDate) and EndOfSupportDate <= now($days d)
| summarize EOLSoftwareCount=count(), EOLSoftwareList=make_set(SoftwareName, 100), OldestEOLDate=min(EndOfSupportDate) by DeviceName
| order by EOLSoftwareCount desc
"@
```

*(Because it’s double-quoted, `$days` expands right into the KQL.)*

---

# Quality checks & gotchas

* **Inventory coverage**: Devices missing TVM/Defender inventory won’t be represented—cross-check onboarding.
* **Set size**: `make_set(SoftwareName, 100)` caps the list at 100 names; raise if you truly need more (CSV readability may suffer).
* **Time zone**: `now()` is UTC in AH. That’s fine for lifecycle checks, but note when describing reports to stakeholders.
* **Names vs. versions**: If you need precision, also project `Version` (e.g., different Java builds).
* **Old device names**: If you recycle hostnames, consider joining on a stable key like `DeviceId`.

---

If you’d like, I can stitch this directly into the next section of your post—showing the Graph/PowerShell call you’re using to execute the query and export to CSV—so the narrative flows from **why** → **what** → **how** with minimal friction.


# Why Graph + Advanced Hunting is the right path

* Microsoft’s **Advanced Hunting** via Graph is the modern, cross-workload way to query **Defender XDR** data (devices, identities, email, apps). The **`runHuntingQuery`** endpoint is the supported way to execute your KQL programmatically and get structured results you can transform or report on—exactly what your CSV export is doing. ([Microsoft Learn][1])

# Other useful automations you can add (same pattern)

Because you already authenticate and post KQL to Graph, you can chain more actions off the results without changing your core plumbing:

* **Auto-open tasks for owners**
  Create work items automatically when `EndOfSupportDate` ≤ N days:

  * Post to **Teams** channels with a table summary of at-risk software.
  * Create **Planner** tasks (or share a **To Do** task) assigned to the device owner with due dates tied to the EoL date.

* **Drive remediation with Intune (Graph device management)**

  * Tag devices (Azure AD/Entra or Intune) with a custom attribute like `Needs_EoL_Remediation = True` when they appear in your EoL list; then scope an Intune remediation script or app uninstall policy to that group.

* **Ticketing hooks**

  * If you prefer email-based intake, send a formatted report via **Graph Mail (sendMail)** to your helpdesk queue with CSV attached and device-specific links.
  * Or call your ticket system’s API in the same loop you export CSV.

* **Evidence snapshots / knowledge base**

  * Write the tabular output into a **SharePoint list** (via Graph Lists API) so you can filter/slice by product, vendor, BU, or owner; keep the CSV as an attachment for audit proof.

* **Alert enrichment flows**

  * On a schedule, join your “EoL software” list to recent **Device*Events** tables; if an out-of-support application is seen spawning processes or making outbound connections, post a **high-priority alert** in Teams or open an incident for investigation. (The same `runHuntingQuery` call returns those event rows you can correlate on.) ([Microsoft Learn][3])

* **Executive summaries**

  * Roll up counts by `SoftwareVendor/SoftwareName/EndOfSupportStatus` and push a compact CSV or HTML mail to leadership weekly/monthly (“EoL posture: total devices, top vendors, trend vs last report”).

# References (good to keep handy)

* **Run Hunting Query (Graph Security)** – method, scopes, request/response shape, PowerShell example. ([Microsoft Learn][1])
* **Advanced Hunting overview** – what data is available across Defender XDR. ([Microsoft Learn][3])
* **DeviceTvmSoftwareInventory table** – includes **End-of-Support** columns used for your report. ([Microsoft Learn][2])

If you want, I can also add a short post-processing block that:

* splits the CSV by owner or BU,
* mails each owner only their rows,
* and drops a full consolidated CSV to SharePoint.

[1]: https://learn.microsoft.com/en-us/graph/api/security-security-runhuntingquery?view=graph-rest-1.0 "security: runHuntingQuery - Microsoft Graph v1.0 | Microsoft Learn"
[2]: https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-devicetvmsoftwareinventory-table?utm_source=chatgpt.com "DeviceTvmSoftwareInventory table in the advanced ..."
[3]: https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-overview?utm_source=chatgpt.com "Overview - Advanced hunting - Microsoft Defender XDR"
