# Introduction & Use Case:
Welcome back to the 🧰 PowerShell Toolbox series on DevSecOpsDad.com — your four-part, no-nonsense tour through the scripts I rely on for audits, baselines, IR, and cloud security hygiene. You’ve already mapped your Azure network (Part 1) and audited privileged RBAC roles (Part 2).
Now, in Part 3, we shift gears from cloud to classic enterprise security: Group Policy.

Because let’s be honest—Group Policy is where good intentions go to retire.

Over the years, GPOs accumulate like digital barnacles:
- Half-finished hardening baselines.
- “Temporary” fixes that became permanent.
- Mystery settings that nobody wants to touch because they “still support that one old app.”

And when an audit hits, or security wants clarity, or you need to prep for a migration?
Nobody has time to click through 200+ GPOs in GPMC like it’s 2009.

<br/>

### Enter the next tool in your Toolbox.

And yes — this is the one that lets you slice straight through the “Bad GPOs” tentacle monster lurking in every legacy domain.

![](/assets/img/Powershell%20Toolbox%203/approach.png)

This lightweight PowerShell script gives you a one-click, full-domain HTML export of every Group Policy Object. Think of it as wielding your own glowing red PowerShell katana: one strike, and suddenly you have:

- Auditor-ready documentation.
- Offline review capability.
- Drift detection snapshots.
- Human-readable policy evidence you can diff, archive, or hand off to anyone.

<br/>

Perfect for audits. Perfect for cleanup. Perfect for “what the heck is actually applied in this OU?” situations.
And it fits beautifully within the overall mission of this toolbox series:
reduce audit overhead, accelerate security clarity, and eliminate manual recon work.

<br/>

### 👉 [Grab your copy here](https://www.hanley.cloud/2025-11-20-PowerShell-Toolbox-Part-3-of-4-GPO-HTML-Export-Script-Snapshot-Every-Group-Policy-Object-in-One-Pass/)

<br/>
<br/>
<br/>
<br/>

# 🔐 Use Cases — When This Script Earns Its Keep

Think of this script as your GPO time machine + documentation engine. It shines in scenarios like:

### ✔️ Audit Preparation (CIS, STIG, ISO, NIST, CMMC… pick your poison)

Need to hand an auditor a complete snapshot of every GPO in the domain?
Export once → zip → done.
No console clicking, no screenshots, no “hang on, let me find that setting.”

<br/>

### ✔️ Baseline Validation

Running Microsoft Security Baselines?
Verifying CIS L1/L2?
Double-checking password policies, security options, or audit settings?
Having the HTML reports makes validation trivial.

<br/>

### ✔️ Cleanup / Modernization Campaigns

Before you clean up 20 years of GPO drift—or migrate them into Intune/MDM—you need a static point-in-time snapshot.
This script gives you that insurance.

<br/>

### ✔️ Incident Response & Threat Hunting

When things get weird and you suspect a GPO was weaponized:
- Unexpected logon scripts
- Security policy changes
- Privilege escalation tweaks…

…you want visibility now, not after clicking through every OU.
This script dumps everything in minutes.

<br/>

### ✔️ Migration Planning (Intune, AzureAD, or Hybrid Scenarios)

If you're converting GPOs to MDM policies, you need to know exactly what's configured today.
This gives you clean documentation to drive that process.

<br/>
<br/>

![](/assets/img/Powershell%20Toolbox%203/attack.png)

<br/>
<br/>

### Here's the small but super handy script:

<br/>

```powershell
$reportFolder = "C:\GPOReports"
if (-not (Test-Path $reportFolder)) {
    New-Item -Path $reportFolder -ItemType Directory | Out-Null
}
 
$GPOs = Get-GPO -All
foreach ($gpo in $GPOs) {
    try {
        $safeName = ($gpo.DisplayName -replace '[\\/:*?"<>|]', '_')
        $reportPath = "$reportFolder\$safeName.html"
        Get-GPOReport -Name $gpo.DisplayName -ReportType Html -Path $reportPath
    } catch {
        Write-Warning "Failed to export report for $($gpo.DisplayName): $_"
    }
}
```

<br/>
<br/>

### ⚡ Available on my GitHub [HERE](https://www.hanley.cloud/2025-11-20-PowerShell-Toolbox-Part-3-of-4-GPO-HTML-Export-Script-Snapshot-Every-Group-Policy-Object-in-One-Pass/)... Now let’s unpack it... 👇


<br/>
<br/>

# 🎯 What This Script Does (High-Level)

In one run, this script:
- Ensures a local folder exists: ```C:\GPOReports```
- Pulls all Group Policy Objects in the domain via Get-GPO -All
- Loops through each GPO and:
- Sanitizes its display name into a file-system safe filename
- Calls Get-GPOReport to generate an HTML report for that GPO
- Saves each report as: ```C:\GPOReports\<GPO-Name>.html```
- Logs a warning if any individual GPO fails to export (e.g., permissions or weird corruption), but keeps going.

<br/>

End result: a folder full of clickable HTML reports, one per GPO, ready for:
- Security reviews
- CIS / STIG baseline verification
- Change documentation
- Incident response “what is actually being applied to these OUs?” questions

<br/>
<br/>
<br/>
<br/>

# ⚙️ Line-by-Line Breakdown
### 1. Define the Report Folder
```$reportFolder = "C:\GPOReports"``` hard-codes the output location to: ```C:\GPOReports```

This is where all the exported HTML reports will be stored. You can easily parameterize this later, but hardcoding keeps it simple for now.

<br/>
<br/>

### 2. Ensure the Folder Exists
```powershell
if (-not (Test-Path $reportFolder)) {
    New-Item -Path $reportFolder -ItemType Directory | Out-Null
}
```

```Test-Path $reportFolder:``` Checks whether C:\GPOReports already exists.

If it does not exist: ```New-Item -ItemType Directory``` creates the folder.

```Out-Null``` suppresses the normal ```“Directory: C:\GPOReports”``` output so the script stays quiet and clean.

>⚡This makes the script **idempotent**: _you can run it multiple times without worrying about the folder being missing or throwing errors._

<br/>
<br/>

### 3. Get All Group Policy Objects
```$GPOs = Get-GPO -All``` Uses the GroupPolicy module’s Get-GPO cmdlet; ```-All``` returns every GPO in the current domain. The result is a collection of GPO objects, each with properties like:

- DisplayName
- Id
- DomainName
- Owner
- CreationTime, ModificationTime, etc.

> ⚠️ Note: This requires you to be running the script on a **domain-joined machine** with the Group Policy Management tools installed (RSAT or GPMC on a DC / management server). 

<br/>
<br/>

### 4. Loop Through Each GPO
<br/>

```powershell
foreach ($gpo in $GPOs) {
    try {
        ...
    } catch {
        ...
    }
}
```
☝️ This is a standard foreach loop that goes through one iteration per GPO. The ```try { ... }``` and ```catch { ... }``` statements ensure that if one GPO export fails, the script logs a warning and continues with the others instead of dying halfway through (This type of error handling is also sometimes referred to as **throw/catch**).

<br/>
<br/>

### 5. Sanitize the GPO Name for File System Use
This is a subtle but important detail: ```$safeName = ($gpo.DisplayName -replace '[\\/:*?"<>|]', '_')```... ```GPO.DisplayName``` can contain characters that are invalid in Windows filenames, like: ```\ / : * ? " < > |```

The regex ```'[\\/:*?"<>|]'``` matches any of those characters such that ```-replace '[\\/:*?"<>|]' , '_'``` replaces each occurrence with ```_```.

<br/>

Example: A GPO named: ```Hardening: Domain Controllers / Default``` → becomes → ```Hardening_ Domain Controllers _ Default```

This prevents Get-GPOReport from failing when writing the .html file due to illegal characters in the path.

<br/>
<br/>

### 6. Build the Full Report Path
```$reportPath = "$reportFolder\$safeName.html"``` → simple string interpolation → ```C:\GPOReports\<sanitized-GPO-name>.html```

This is the target file path for the HTML report for this specific GPO.

<br/>
<br/>

### 7. Export the GPO to HTML

This is the workhorse of the script: ```Get-GPOReport -Name $gpo.DisplayName -ReportType Html -Path $reportPath```

> ☝️ ```Get-GPOReport``` is another cmdlet from the GroupPolicy module.

<br/>

**Parameters:**
- ```Name $gpo.DisplayName``` → identifies which GPO to export.
- ```ReportType Html``` → generates a fully formatted HTML report.
- ```Path $reportPath``` → saves that HTML content into the file path we built.

<br/>

**The resulting HTML report includes:**
- GPO name, GUID, domain, owner, creation/modification date.
- Links, WMI filters (if any).

<br/>

**Settings under:**
- Computer Configuration
- User Configuration
- Each policy area (Windows settings, Administrative Templates, Security Settings, Scripts, etc.)

Basically, everything you’d see in GPMC → Right-click GPO → Save Report…, but automated and done in bulk.

<br/>
<br/>

### 8. Error Handling
<br/>

```powershell
catch {
    Write-Warning "Failed to export report for $($gpo.DisplayName): $_"
}
```

☝️ This catches any exception thrown inside the try block for that GPO:
- Missing permissions
- Corrupted GPO
- Transient AD/GPMC glitch
- Write-Warning prints a yellow warning with:
- The GPO’s display name
- The error message ```($_)```

<br/>

This means that one bad GPO doesn’t ruin the script run and you still get a clear list of problem GPOs to investigate later.

<br/>
<br/>
<br/>
<br/>

# 📁 What You Get on Disk

After the script finishes, you’ll have:

C:\GPOReports <br/>
  | <br/>
  +-- Default Domain Policy.html <br/>
  +-- Default Domain Controllers Policy.html <br/>
  +-- Hardening_ Domain Controllers _ Tier0.html <br/>
  +-- Legacy_App_Compatibility.html <br/>
  +-- ...

Each .html file is fully clickable in any browser and shows all settings for that GPO.

<br/>
<br/>
<br/>
<br/>

# ▶️ How to Run This Script (Step-by-Step)
### 1. Prerequisites

- Domain-joined machine
- Group Policy Management Console tools installed:
    - On a management workstation, install RSAT: Group Policy Management Tools (on Windows 10/11 via “Optional Features” or RSAT package). 
    - >⚡ On a domain controller, these tools are usually already present.

<br/>

### 2. Permissions

You need permissions to read GPOs in the domain. Typically, members of the following can safely run this:

- Domain Admins
- Group Policy Creator Owners
- Or any delegated admin granted GPO read access

<br/>

### 3. Save the Script

Save as: ```C:\Scripts\Export-All-GPOReports.ps1```


Contents:
```powershell
$reportFolder = "C:\GPOReports"
if (-not (Test-Path $reportFolder)) {
    New-Item -Path $reportFolder -ItemType Directory | Out-Null
}
 
$GPOs = Get-GPO -All
foreach ($gpo in $GPOs) {
    try {
        $safeName = ($gpo.DisplayName -replace '[\\/:*?"<>|]', '_')
        $reportPath = "$reportFolder\$safeName.html"
        Get-GPOReport -Name $gpo.DisplayName -ReportType Html -Path $reportPath
    } catch {
        Write-Warning "Failed to export report for $($gpo.DisplayName): $_"
    }
}
```

<br/>

### 4. Run It

Open a PowerShell window as a domain user with GPO read rights, then:
```powershell
Set-Location C:\Scripts
.\Export-All-GPOReports.ps1
```

When it finishes, browse to ```C:\GPOReports\``` and double-click any .html file to view that GPO’s configuration.

<br/>
<br/>
<br/>
<br/>

# 🔍 How to Use This in Audits & Reviews

Here are a few practical workflows:

### 📋 CIS / STIG Compliance
- Re-run this script before every quarterly GPO review.
- Use the HTML reports to check:
    - Password policy
    - Account lockout settings
    - Security options
    - Audit policies
    - TLS / cipher hardening (if configured via GPO)

<br/>
<br/>

### 📷 Before-and-After Snapshots
- Run the script before a GPO refactor.
- Zip up ```C:\GPOReports``` and archive it.
- After changes, run it again.

⚡ You’ve now got before/after evidence and can use tools (or even manual HTML diff) to see changes.

<br/>
<br/>

### 🧯 Incident Response

If there’s suspicious behavior and you think “GPO did it,” this lets you quickly scan for:

- Startup scripts
- Logon/logoff scripts
- Security policy changes (e.g., turning off UAC, enabling unsigned drivers, etc.)

This way you can provide a static, point-in-time view of GPOs to the IR team.

<br/>
<br/>
<br/>
<br/>


# ⚡ Wrapping Up Part 3 — Your GPO Snapshot Superpower

By now, you’ve seen how this tiny script punches way above its weight class. With one quick run, you get:

- A full, point-in-time GPO inventory
- Clean, searchable HTML documentation
- Instant visibility into your security posture
- Evidence for audits, baselines, IR, and modernization work
- A reliable record you can diff, archive, and automate

No more guessing what’s hiding inside 20 years of Group Policy history. No more clicking through console windows. No more “I’ll document this later” lies we tell ourselves.

This is the heart of the PowerShell Toolbox series: scripts that replace repetitive work with repeatable automation — the kind of tooling that lets security teams move faster and sleep better.

And now that you’ve handled Azure network mapping (Part 1), RBAC auditing (Part 2), and GPO extraction (Part 3)…
you’re ready for the final tool in the set.

<br/>
<br/>

![](/assets/img/Powershell%20Toolbox%203/victory.png)

<br/>
<br/>
<br/>
<br/>

# 👀 A Sneak Peek at What’s Coming in Part 4

Next up in the series?
We’re shifting gears from infrastructure + identity to something that quietly strengthens every script in your arsenal:

🧰 PowerShell Toolbox (Part 4): Auditing Your Scripts with Invoke-ScriptAnalyzer

If Parts 1–3 gave you visibility into your environment,
Part 4 will give you visibility into your code; Because let’s be honest — half of our automation is written either:

- late at night ☕
- under deadline fire 🔥
- while juggling client tickets 🧠
- after saying “this will only take five minutes” 😁

That’s why the final installment brings a tool that audits you!

Invoke-ScriptAnalyzer — the PowerShell code reviewer that:
- Catches bugs before they break production
- Flags unsafe patterns before attackers do
- Enforces consistency across all four scripts in this toolbox
- Teaches better habits every time you run it
- Reduces risk when working across multiple tenants
- Keeps your IR and automation code clean, readable, and secure

Part 4 wraps this entire series together by giving you the quality gate that every DevSecOps practitioner should be using — especially anyone writing scripts that touch Azure, Entra, Sentinel, or client environments.

Think of it as _the tool that makes every other tool safer._

_**Stay tuned** — Part 4 is going to be a fun one!_

<br/>
<br/>

![](/assets/img/Powershell%20Toolbox%203/trilogy.png)

<br/>
<br/>
<br/>
<br/>

# 📚 Want to Go Deeper?

If this kind of automation gets your gears turning, check out my book:
🎯 Ultimate Microsoft XDR for Full Spectrum Cyber Defense
 — published by Orange Education, available on Kindle and print. 👉 Get your copy here: [📘Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ)

⚡ It dives into Defender XDR, Sentinel, Entra ID, and Microsoft Graph automations just like this one — with real-world MSSP use cases and ready-to-run KQL + PowerShell examples.

&#128591; Huge thanks to everyone who’s already picked up a copy — and if you’ve read it, a quick review on Amazon goes a long way!

![Ultimate Microsoft XDR for Full Spectrum Cyber Defense](/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg)

<br/>
<br/>
<br/>
<br/>

# 🔗 References (good to keep handy)

- [GPO_Audit.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/GPO_Audit.ps1)
- [Privileged_RBAC_Roles_Assessment.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Privileged_RBAC_Roles.ps1)
- [Cloud_Network_Assessment.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1)
- [Origin of Defender NinjaCat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025) 

<br/>
<br/>
<br/>
<br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)