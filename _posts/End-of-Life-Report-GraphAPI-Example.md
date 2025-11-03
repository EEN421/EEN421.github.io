💡 Why Identifying End-of-Life Systems Matters

In cybersecurity, “end-of-life” (EoL) doesn’t just mean old — it means unprotected.
When hardware or software reaches its end-of-support date, vendors stop shipping security patches, firmware updates, and compatibility fixes. Those aging components quickly become soft targets for attackers looking for unpatched vulnerabilities or misconfigurations that can provide an easy foothold into the network.

From a defender’s standpoint, the business impact of ignoring EoL assets is threefold:

Exposure: Unpatched legacy systems are common entry points for ransomware and lateral movement.

Compliance Risk: Frameworks like CIS, NIST CSF, and ISO 27001 require lifecycle management of software and hardware; auditors routinely flag unsupported OS versions or firmware.

Operational Overhead: Unsupported software can break integrations, limit telemetry, and complicate patch automation, creating blind spots in security monitoring.

Here’s a clear, end-to-end walkthrough of what your **EOL Stuff Automated.ps1** script is doing, plus ideas for other handy automations you can bolt onto the same Microsoft Graph pipeline.

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
