# Introduction & Use Case: Audit Readiness Without the Burnout

Let’s be honest — nobody looks forward to audit season.
Between spreadsheets, evidence collection, screenshots of portal settings, and the dreaded “please export that to CSV,” most security teams burn entire weekends chasing compliance data that PowerShell could have gathered in minutes.

That’s where this PowerShell Toolbox comes in.
I built and refined these four scripts to automate the grunt work behind CIS Benchmarks, NIST 800-53, CMMC 2.0, and other security assessments. They surface exactly what auditors ask for — privileged roles, network exposure, GPO compliance, and end-of-life assets — in repeatable, exportable formats.

So grab your coffee, crack open VS Code, and let’s make audit prep something you actually look forward to (or at least don’t dread).

Great call—let’s buckle in deep. Crafting a “PowerShell Toolbox” post for **DevSecOpsDad.com** means getting the style, tone and structure right—so here’s the plan:

---

🧰 Intro – The PowerShell Toolbox You Didn’t Know You Needed

As your friendly DevSecOpsDad, I’ve got two things that keep me up at night: 1) the constant drift across cloud and on-prem environments, and 2) the ghosts of unpatched servers and lingering admin rights.

This week I set aside my Traeger brisket (okay, maybe just delayed it a bit) and fired up the PowerShell ISE to build out a toolbox. Four scripts from the EEN421 PowerShell-Stuff repo
 came up big in cleaning up the mess — and they’ve earned a permanent spot in my rotation.

If you’re an MSSP engineer, security architect, or just the kind of person who likes to know exactly what’s running in your network before the adversary does, this one’s for you. These scripts help you assess, audit, and automate — across your cloud, your directory, and your endpoints — all with the simplicity of native PowerShell.

Grab your coffee, crack open VS Code, and let’s dig in.

---

# Tool #1 – Cloud & Network Assessment.ps1

### Purpose

This script is your first-pass “what’s the attack surface looking like” tool for your cloud subscriptions and network estate. Think: did someone spin up a public subnet without NSGs? Are there unused VMs still powered on in the test subscription? Are resource groups tagged for ownership? It spreads across cloud + network (hence the name).

### Breakdown

* Connects to Azure (or AWS if you adapt it) to enumerate subscriptions, resource groups, VMs, NSGs, public IPs.
* Checks for common mis-configurations: open inbound internet facing RDP/SSH, idle VM status, lack of tags, resource-group naming drift.
* Generates output (CSV/JSON) that you can feed into a workbook in Microsoft Sentinel or a PowerBI dashboard.
* Key functions include: `Get-SubscriptionList`, `Get-ResourceGroupSummary`, `Get-NetworkSecurityGroupRules`, `Get-PublicIPInsights`, `Get-IdleVMs`.

### Use Case Example

Imagine you inherited a client with multiple Azure subscriptions (Prod, DR, Dev, Sandbox) and no consistent tagging or NSG rules. You run Cloud_Network_Assessment.ps1:

```powershell
.\Cloud_Network_Assessment.ps1 -SubscriptionList @('sub-prod','sub-dev') -OutputPath 'C:\Reports\CloudNet_Assess_2025-11-07.csv'
```

You get a CSV with columns: Subscription, ResourceGroup, VMName, PublicIp, InboundOpen (Yes/No), TagOwner, LastLogin, IdleStatus (Days).
You sort by IdleStatus >30 days, flag those VMs. You filter where InboundOpen=Yes and PublicIp exists → drill into those NSGs, tighten rules.
You push the CSV into Sentinel via LogicApp or Enterprise Alert so you get automated email when new open inbound ports are detected.

### Pro Tips & Caveats

* Ensure you have **Compute**/Network/**Security Reader** role in Azure (or equivalent) so the script can query.
* Idle VM detection might require you to define what “idle” means (e.g., no CPU >5% and no logons in last 30 days) — you may want to customize.
* This is a **snapshot**-type script; if you want continuous monitoring, schedule it (eg weekly) and diff outputs.
* As a DevSecOpsDad note: *"Don’t run this at 3 am when you forgot to pause the Traeger"*. Use proper scheduling and alerting.

---

# Tool #2 – GPO_Audit.ps1

### Purpose

On-premises and hybrid AD still exist (yes, I’m looking at you, brick-and-mortar K-12 district). GPO_Audit.ps1 helps you dig into your Group Policy Objects (GPOs) to find policy drift, missing links, and compliance issues. It’s your “what has changed under the hood” lens for domain controls.

### Breakdown

* Connects to Active Directory via PowerShell (e.g., `Get-GPO`, `Get-GPOReport`) to enumerate all GPOs, their linked OUs, settings, WMI filters, delegated permissions.
* Checks for: stale/unlinked GPOs, GPOs with no “last modified” timestamp recently, GPOs with overly permissive delegation (e.g., Authenticated Users have “Edit settings”), missing baseline settings (e.g., required password policy not applied).
* Generates an HTML/CSV report for compliance review — attach to your monthly briefing for the board or MSSP SOC.

### Use Case Example

Your SME team complains “we applied the new password complexity domain-wide but a few laptops aren’t getting it”. You run:

```powershell
.\GPO_Audit.ps1 -DomainContoso.local -OutputReport 'C:\Reports\GPO_Audit_Contoso_2025-11-07.html'
```

You open the HTML, find that a sub-OU (OU=LegacyDevices) has a GPO with override permissions by local admins and isn’t linked properly. You remediate: link baseline GPO, remove delegated permissions, then re-run after replication.
You archive previous reports to establish trendlines (GPO drift reducing over time = good score for your SOC board).

### Pro Tips

* Run from a domain-joined workstation with RSAT/GPMC module installed.
* Mind AD replication latency — if you query right after many changes, you might get inconsistent results. Wait for replication or specify domain controller.
* For hybrid Azure AD + Intune + on-prem AD, consider extending this logic or making it part of your overall compliance pipeline.

---

# Tool #3 – Privileged_RBAC_Roles.ps1

### Purpose

Now we move into privilege creep and RBAC — one of my favorite “silent killers”. This script helps you inventory privileged roles (cloud and on-prem) and check for risky assignments (excessive nested groups, too many assignments, stale role holders). Essentially: “who can do what” and “should they still?”

### Breakdown

* Queries Azure AD / Azure RBAC (or on-prem AD roles if modified) for all role assignments, nested groups, belonging accounts.
* Identifies: accounts with *Owner* or *PrivilegedRoleAdmin* that have not logged on in X days, role assignments via groups that have external members, inherited assignments.
* Outputs CSV/JSON for analysis and optionally invokes remediation suggestions (e.g., “remove this member from this role”).
* Key functions: `Get-AzureADDirectoryRole`, `Get-AzRoleAssignment`, `Get-GroupMembershipRecursive`, `Get-SignInActivity`.

### Use Case Example

You suspect that former contractors still retain high privileges in your cloud tenant. You run:

```powershell
.\Privileged_RBAC_Roles.ps1 -TenantId 'contoso.onmicrosoft.com' -DaysInactive 90 -Output 'C:\Reports\PrivRoles_2025-11-07.csv'
```

You spot “[UserX@externaldomain.com](mailto:UserX@externaldomain.com)” as member of *Owner* in a Prod subscription and last login 180 days ago. You escalate to remove.
You also see “GroupLegacyAdmins” still has 50+ members, many inactive. You schedule a cleanup.
These findings get exported to your MSSP ticketing system and you tag high-risk issues for SOC review.

### Pro Tips

* Ensure you have appropriate permissions (Global Reader / Security Reader / Role Administrator) to query.
* Be careful with large tenants — you may hit throttling; implement batching.
* Consider connecting results to a governance workbook or email digest for monthly review.

---

# Tool #4 – Automated EoL Stuff.ps1

### Purpose

This is a gem for cleaning up ghosts: servers, OS versions, software platforms that have reached End-Of-Life (EoL) and are still running. You and I both know the drill: they’re hiding quietly, unpatched, un-monitored, and waiting for a bad actor (or worst-case: your auditor). This script automates discovery.

### Breakdown

* Scans across servers (on-prem + cloud) to gather OS version, installed software version, last patch date, last reboot, vendor end-of-support date (if you maintain a database or feed).
* Flags assets that are: OS version unsupported, no patches in last 90 days, software EoL and still installed, etc.
* Generates list for deprecation or migration. Sends alerts for high-visibility assets (e.g., internet-facing, ICS/OT segments).
* Functions: `Get-ComputerSystem`, `Get-InstalledSoftware`, `Get-HotFix`, `Compare-EoLDate`, `Export-Csv`.

### Use Case Example

In your home-lab (or MSSP customer), you run:

```powershell
.\Automated EoL Stuff.ps1 -ServerListPath 'C:\servers.txt' -EoLFeed 'C:\feeds\VendorEoL.csv' -Output 'C:\Reports\EoL_Assets_2025-11-07.xlsx'
```

You open the Excel, filter for “InternetFacing=Yes” and “EoL=Yes” → you find an old server running Windows Server 2008 R2 still hosting a legacy app. You flag for immediate migration.
You automate weekly runs and feed into your incident-response queue: “Unpatched/EoL asset discovered – escalate now”.

### Pro Tips

* Maintain your EoL feed (vendor EoL dates) — this is the “database” you compare against.
* Use scheduling (Task Scheduler / Azure Automation) and archive the historical data so you can show trend (“we had 12 EoL assets last quarter; now down to 4”).
* Prioritize high-risk assets (internet-facing, business-critical) first — don’t try to boil the ocean.

---

# Putting It All Together

Here’s how I (DevSecOpsDad) integrate these into my workflow:

* Weekly scheduled runs (Sunday morning, while the family sleeps) of Cloud_Network_Assessment and Privileged_RBAC_Roles.
* Monthly run of GPO_Audit and Automated EoL Stuff with the results fed into our MSSP’s ticketing system (Jira/ServiceNow) and a summary slide for the “Security Review” meeting.
* Use PowerShell Core (7.x) so the scripts run cross-platform (even on my MacBook when I’m remote from Beaumont, KY).
* Push CSV outputs into Azure Sentinel via LogicApps + Azure Blob Storage + Workbook; create alerts when thresholds exceeded (e.g., > 5 inbound open ports, > 10 stale role members).
* Maintain a “Toolbox” repository (GitHub) version-controlled, adding custom modules (e.g., for logging, notification, tagging).
* Challenge myself annually during the Halloween maker project to “refactor one script as a module and automate its deployment from GitHub Actions” (yes, the Traeger-smoke-and-code weekend tradition lives on).

---

# Next Steps & Your Challenge

Now it’s your turn:

* Pick one of the four scripts and **customize** it for **your environment**. Maybe add a Teams/Slack alert, or feed it into your KQL workbook.
* Consider adding **unit-tests** (Pester) so your toolbox grows from script to reusable module.
* Write a “what-changed” diff process: e.g., store last output, compare new run, highlight new risk items.
* Let me know the results. Post a screenshot of your workbook or alert summary (with any sensitive info redacted) on LinkedIn using #DevSecOpsDad and tag me.

---

# Bonus Tool: `Write-Progress`

`Write-Progress` displays a progress bar in the PowerShell console to give the user visual feedback on long-running tasks.

It’s **purely informational** — it doesn’t affect the logic of the script; it just shows the *status*, *percentage complete*, and *activity description*.

<br/>
<br/>
<br/>
<br/>

## ⚙️ Syntax Overview

```powershell
Write-Progress
    [-Activity] <string>
    [[-Status] <string>]
    [[-PercentComplete] <int>]
    [-CurrentOperation <string>]
    [-Id <int>]
    [-ParentId <int>]
    [<CommonParameters>]
```

### Key Parameters Explained:

| Parameter               | Description                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------- |
| **`-Activity`**         | The main label describing what’s happening (e.g. “Processing files”).              |
| **`-Status`**           | A short message describing the current step (e.g. “Copying file 3 of 10”).         |
| **`-PercentComplete`**  | Integer (0–100) indicating progress percentage.                                    |
| **`-CurrentOperation`** | More detail about what’s currently happening within the task.                      |
| **`-Id`**               | Identifies the progress bar instance (useful when running multiple progress bars). |
| **`-ParentId`**         | Groups child progress bars under a parent (for nested tasks).                      |

<br/>
<br/>
<br/>
<br/>

## 🧩 Example Script — Simulated File Processing

Here’s a **fully commented PowerShell script** that demonstrates `Write-Progress` in action:

```powershell
# ----------------------------------------------------------------------
# Example: Demonstrate Write-Progress in PowerShell
# Description: Simulates processing 10 files with progress updates.
# ----------------------------------------------------------------------

# Define how many files to simulate
$totalFiles = 10

# Start the main loop
for ($i = 1; $i -le $totalFiles; $i++) {

    # Calculate percentage completion
    $percentComplete = [math]::Round(($i / $totalFiles) * 100, 0)

    # Simulate "processing" by waiting a short time
    Start-Sleep -Milliseconds 500

    # Display the progress bar
    Write-Progress `
        -Activity "Processing files..." `               # Main task name
        -Status "Processing file $i of $totalFiles" `   # Current status line
        -PercentComplete $percentComplete `             # Percent progress
        -CurrentOperation "Working on file_$i.txt"      # More detailed info
}

# Once the loop completes, clear the progress bar
Write-Progress -Activity "Processing files..." -Completed

# Optional: Confirm completion
Write-Host "✅ All $totalFiles files have been processed successfully!"
```

<br/>
<br/>
<br/>
<br/>

## 🪄 Output Behavior

When run in a PowerShell console:

* You’ll see a **progress bar** update in place (it doesn’t scroll the screen).
* The **Activity** line shows the main task (“Processing files...”).
* The **Status** line updates with each file.
* The **progress percentage** automatically updates.
* When finished, `-Completed` removes the progress bar.

---

## 💡 Bonus Tip — Nested Progress Bars

You can track sub-tasks with **`-ParentId`**:

```powershell
for ($i = 1; $i -le 3; $i++) {
    Write-Progress -Activity "Main Task" -Status "Phase $i" -PercentComplete (($i/3)*100) -Id 1

    for ($j = 1; $j -le 5; $j++) {
        Write-Progress -Activity "Sub-Task $i" -Status "Item $j of 5" -PercentComplete (($j/5)*100) -Id 2 -ParentId 1
        Start-Sleep -Milliseconds 300
    }
}
Write-Progress -Activity "Main Task" -Completed
```

This creates **a main progress bar with sub-progress bars** underneath — great for loops within loops (e.g., scanning folders and then files).

<br/>
<br/>
<br/>
<br/>

## 🧠 What `Invoke-ScriptAnalyzer` Does

`Invoke-ScriptAnalyzer` is a PowerShell cmdlet provided by the **PSScriptAnalyzer** module.
It’s used to **check PowerShell scripts for best practices, syntax issues, and style violations** — similar to how `lint` tools work for other languages.

It scans your script and reports:

* **Errors** (e.g., syntax or command misuse)
* **Warnings** (e.g., deprecated cmdlets, unsafe practices)
* **Information** (e.g., style or naming suggestions)

This is **very useful before publishing a script to GitHub or production**, to ensure it follows PowerShell standards (like those used in the PowerShell Gallery).

<br/>
<br/>
<br/>
<br/>

## ⚙️ Basic Syntax

```powershell
Invoke-ScriptAnalyzer [-Path] <String[]> [-Recurse] [-Settings <Object>] [-IncludeRule <String[]>] [-ExcludeRule <String[]>]
```

**Common Parameters:**

| Parameter      | Description                                        |
| -------------- | -------------------------------------------------- |
| `-Path`        | Path to the PowerShell script or folder to analyze |
| `-Recurse`     | Include all scripts in subfolders                  |
| `-IncludeRule` | Run only specific analysis rules                   |
| `-ExcludeRule` | Skip certain rules                                 |
| `-Settings`    | Use a custom ruleset (JSON or PSD1 file)           |
| `-Severity`    | Filter output (e.g., Error, Warning, Information)  |

---

## 🔍 Example 1: Analyze a Script

```powershell
Invoke-ScriptAnalyzer -Path "C:\Scripts\MyScript.ps1"
```

➡️ This runs all default analysis rules against *MyScript.ps1*.

<br/>
<br/>
<br/>
<br/>

## 🧰 Example 2: Filter by Severity

```powershell
Invoke-ScriptAnalyzer -Path "C:\Scripts\MyScript.ps1" -Severity Error, Warning
```

➡️ Only returns issues that are **errors or warnings**, ignoring informational messages.

<br/>
<br/>
<br/>
<br/>

## ⚡ Example 3: Store Results in a Variable

```powershell
$results = Invoke-ScriptAnalyzer -Path "C:\Scripts\MyScript.ps1"
$results | Format-Table RuleName, Severity, ScriptName, Line, Message
```

➡️ Saves results for further processing (like logging or CI/CD validation).

<br/>
<br/>
<br/>
<br/>

## 🧪 Full Demonstration Script

Below is a **complete working example** that:

1. Creates a sample PowerShell script with some issues.
2. Runs Script Analyzer against it.
3. Displays formatted results.

```powershell
<#
.SYNOPSIS
    Demonstration of Invoke-ScriptAnalyzer
.DESCRIPTION
    This example creates a sample PowerShell script with intentional
    issues and then uses Invoke-ScriptAnalyzer to analyze it.
#>

# Ensure the PSScriptAnalyzer module is installed
if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) {
    Write-Host "Installing PSScriptAnalyzer..." -ForegroundColor Cyan
    Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser
}

# Step 1: Create a temporary PowerShell script with deliberate mistakes
$ScriptPath = "$env:TEMP\TestScript.ps1"
@"
# Example PowerShell script with some issues
param($inputParam)

Write-Host "Hello world" # Using Write-Host is discouraged
if($inputParam -eq "test")
{
write-output "Running test..."
}
else
{
write-output "Done"
}
"@ | Set-Content -Path $ScriptPath

Write-Host "Created test script at $ScriptPath" -ForegroundColor Green

# Step 2: Analyze the script using Script Analyzer
$results = Invoke-ScriptAnalyzer -Path $ScriptPath

# Step 3: Display the results
if ($results) {
    Write-Host "`nAnalysis Results:" -ForegroundColor Yellow
    $results | Format-Table RuleName, Severity, Line, Message -AutoSize
}
else {
    Write-Host "No issues found!" -ForegroundColor Green
}

# Optional: Clean up the temp file
# Remove-Item $ScriptPath -Force
```

<br/>
<br/>
<br/>
<br/>

## 🧾 Example Output

You might see something like this:

| RuleName                         | Severity    | Line | Message                                     |
| -------------------------------- | ----------- | ---- | ------------------------------------------- |
| PSAvoidUsingWriteHost            | Warning     | 4    | Use `Write-Output` instead of `Write-Host`. |
| PSAvoidUsingPositionalParameters | Information | 1    | Use named parameters for readability.       |
| PSUseConsistentIndentation       | Information | 6    | Indentation is not consistent.              |

<br/>
<br/>
<br/>
<br/>

## 🧩 Pro Tip: Use in CI/CD

You can integrate this into **GitHub Actions** or **Azure DevOps pipelines** to automatically check script quality before merge:

```powershell
Invoke-ScriptAnalyzer -Path .\Scripts\ -Recurse -Severity Error | Tee-Object results.txt
if ($LASTEXITCODE -ne 0) { exit 1 }
```

This ensures your repo always passes PowerShell best practices.

<br/>
<br/>
<br/>
<br/>

Would you like me to show how to **create a custom ruleset file (JSON/PSD1)** next — for example, to disable specific rules like `PSAvoidUsingWriteHost`?


<br/>
<br/>
<br/>
<br/>

# 📚 Bonus: Want to Go Deeper?

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

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
