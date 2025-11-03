Perfect — that’s exactly what I needed. 😎

Here’s a **fully rewritten Markdown version** of your article, styled in your signature **DevSecOpsDad** voice — technical, hands-on, and fun — with placeholders for visuals and calls to action baked in. It’s designed to be *drop-ready* into your GitHub Pages `_posts` folder and look clean on your site.

---

````markdown
---
title: "Automating End-of-Life Software Reports with Microsoft Graph API + PowerShell"
date: 2025-11-03
categories: [Microsoft Defender, PowerShell, Microsoft Graph]
tags: [EoL, TVM, Advanced Hunting, Graph API, Automation, DevSecOpsDad]
description: "Automatically identify devices running End-of-Life software using Microsoft Graph’s Advanced Hunting API and export the results to CSV for easy reporting and remediation."
---

# ⚙️ Automating End-of-Life Software Reports with Microsoft Graph API + PowerShell

Every SOC has a few skeletons in the closet — that dusty Windows Server running a legacy app, or that vendor laptop that somehow *still* has Java 8 Update 45 installed. They work… but they’re also quietly rotting. 🧟‍♂️  

When software or hardware hits **End-of-Life (EoL)**, vendors stop shipping patches and security updates. That means every unpatched component becomes a potential open door. This blog shows how to automatically find those forgotten risks using **PowerShell** and the **Microsoft Graph API** — then export them into a clean, auditable **CSV report** you can actually use.

![Placeholder: screenshot of PowerShell script output](path/to/screenshot-eol-script.png)

---

## 💡 Why End-of-Life Visibility Matters

In cybersecurity, *“end-of-life” doesn’t just mean old — it means unprotected.*

When software reaches its end-of-support date:
- No more patches 🩹  
- No more compatibility updates ⚙️  
- And no more love from the vendor ❤️ (sorry, IE11)

The result? A perfect recipe for compromise.

From a defender’s standpoint, ignoring EoL assets creates risk in three areas:

- **Exposure:** Legacy systems are prime entry points for ransomware and lateral movement.  
- **Compliance Risk:** Frameworks like **NIST CSF**, **CIS v8**, and **ISO 27001** require lifecycle management. Unsupported systems are frequent audit findings.  
- **Operational Blind Spots:** Outdated software often breaks telemetry and patch automation — creating gaps in visibility.

So, let’s automate the hunt for these time bombs.

---

## 🧠 What You’ll Learn

- How to query **Defender’s Threat & Vulnerability Management (TVM)** data through **Microsoft Graph’s Advanced Hunting API**
- How to detect software already past its **End-of-Support** date
- How to generate and export an **EoL CSV report** via PowerShell
- Plus: ideas for integrating this with **Intune**, **ServiceNow**, or **Sentinel**

---

## 🔍 The KQL That Makes It Happen

Here’s the heart of it — a clean, optimized **Advanced Hunting** query that surfaces all devices running out-of-support software:

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
````

### 🔎 What it does:

* Pulls all devices with software past its end-of-support date
* Groups results per device
* Lists the outdated titles (up to 100 per machine)
* Sorts by the worst offenders at the top

This gives you an instant view of which machines pose the most risk and exactly what software needs remediation.

---

## 💻 Wrapping It in PowerShell

Now for the fun part — making it **automated**.

The PowerShell script below uses the **Microsoft Graph SDK** to:

1. Authenticate via `Connect-MgGraph`
2. Run the KQL via the **`/security/runHuntingQuery`** endpoint
3. Parse the results
4. Export them to CSV

```powershell
#Requires -Modules Microsoft.Graph.Authentication

$OutputPath = "C:\Temp\EndOfSupport_DeviceSummary.csv"

# Step 1: Connect to Microsoft Graph
Connect-MgGraph -Scopes "ThreatHunting.Read.All"

# Step 2: Define the KQL
$kql = @"
DeviceTvmSoftwareInventory
| where isnotempty(DeviceName)
| where isnotempty(EndOfSupportDate) and EndOfSupportDate <= now()
| summarize 
    EOLSoftwareCount = count(),
    EOLSoftwareList = make_set(SoftwareName, 100),
    OldestEOLDate = min(EndOfSupportDate)
  by DeviceName
| order by EOLSoftwareCount desc
"@

# Step 3: Run the query
Write-Host "Executing hunting query against Defender via Microsoft Graph..."
$response = Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/security/runHuntingQuery" `
    -Body (@{ Query = $kql } | ConvertTo-Json)

# Step 4: Parse and export to CSV
if (-not (Test-Path (Split-Path $OutputPath))) {
    New-Item -Path (Split-Path $OutputPath) -ItemType Directory | Out-Null
}

$results = $response.Results | ForEach-Object {
    [PSCustomObject]@{
        DeviceName        = $_.DeviceName
        EOLSoftwareCount  = $_.EOLSoftwareCount
        EOLSoftwareList   = ($_.EOLSoftwareList -join "; ")
        OldestEOLDate     = $_.OldestEOLDate
    }
}

$results | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8
Write-Host "EoL report exported to $OutputPath"
```

![Placeholder: screenshot of Advanced Hunting output table](path/to/screenshot-eol-query-results.png)

---

## ⚙️ What Happens Under the Hood

1. **Authentication:**
   PowerShell requests a token scoped to `ThreatHunting.Read.All` using Microsoft Graph Authentication.
2. **Query definition:**
   The `$kql` variable uses a **PowerShell here-string** (`@" ... "@`) to store multi-line KQL cleanly.
3. **Execution:**
   `Invoke-MgGraphRequest` sends the KQL directly to the **Graph Security API**, which runs it on Defender’s hunting backend.
4. **Parsing:**
   The JSON response is converted into PowerShell objects.
5. **Reporting:**
   Results are written to a CSV for compliance reports or patch planning.

It’s simple, clean, and fast — and you can run it on a schedule, email the output, or push it into SharePoint or Power BI dashboards.

---

## 🧩 Bonus Automation Ideas

Want to go further? You can easily extend this same script to:

* 🚨 **Alert in Teams:** Post a summary when new EoL software appears.
* 🧾 **Auto-create tickets:** Integrate with ServiceNow or Jira to open remediation tasks.
* 🧠 **Tag devices in Intune:** Apply a custom tag like `Needs_EoL_Review` for easier tracking.
* 📊 **Feed Sentinel:** Combine with incident data to prioritize risky devices.

These all build off the same Graph call — once you have the data, you can pipe it anywhere.

---

## 📈 Example Output (CSV)

| DeviceName  | EOLSoftwareCount | EOLSoftwareList                      | OldestEOLDate |
| ----------- | ---------------- | ------------------------------------ | ------------- |
| FIN-SRV01   | 5                | Java 8u45; Adobe Reader 9; MySQL 5.6 | 2022-07-01    |
| HR-LAPTOP02 | 2                | Python 3.7; OpenSSL 1.0.2            | 2023-03-15    |

*(Placeholder: add screenshot of your CSV output here)*

---

## 🧰 Wrapping Up

With just a few lines of PowerShell and Graph, you’ve built a repeatable process that:

* Finds every device with unsupported software
* Surfaces your biggest risks first
* Exports clean reports for audits and patching teams

No more manual hunts, no stale spreadsheets — just **actionable data** you can trust.

---

## ⚡ Run It Yourself

Grab the full script here:
👉 [EOLAutomated.ps1 on GitHub](https://github.com/EEN421/Powershell-Stuff/blob/Main/EOL%20Stuff%20Automated.ps1)

Then fire it up:

```powershell
PS C:\Scripts> .\EOLAutomated.ps1 -OutputPath 'C:\Temp\EndOfSupport_DeviceSummary.csv'
```

---

## 📚 Want to Master Microsoft XDR?

If this kind of hands-on automation gets you fired up, you’ll love my book:
**[Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/9bXTmRU)** —
packed with real-world Defender, Sentinel, and Graph examples that take your security automation to the next level.

![Placeholder: book cover image](path/to/book-cover.png)

---

*Written by Ian Hanley — a.k.a. [DevSecOpsDad.com](https://www.hanley.cloud)*
Because defenders deserve good tools **and** good dad jokes. 😉

```

---

## 🔧 Summary of Improvements
✅ Clear structure (intro → why → how → bonus → CTA)  
✅ Branded DevSecOpsDad voice with humor + clarity  
✅ Markdown-ready headings and code fences  
✅ Screenshot placeholders for visual flow  
✅ Book promo with call-to-action tie-in  

---

Would you like me to follow this up by designing **three GitHub-friendly visuals** (diagram of Graph workflow, sample output screenshot template, and banner image for the top of the post)?  
They’ll match your existing DevSecOpsDad style (dark theme, blue highlights, modern typography).
```
