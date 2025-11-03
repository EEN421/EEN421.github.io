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
