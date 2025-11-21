# Introduction & Use Case:
Welcome back to the 🧰 PowerShell Toolbox series on DevSecOpsDad.com; If you’ve followed this PowerShell Toolbox series so far, you’ve mapped your Azure network (Part 1), audited privileged RBAC roles (Part 2), and exported every Group Policy Object into a single offline HTML snapshot (Part 3). These tools strengthen your Azure security posture, streamline audits, and reduce manual work — but they all depend on one critical foundation:

👉 The quality and security of your PowerShell scripts.

In real DevSecOps environments, PowerShell code isn’t always a masterpiece. It’s often written quickly to automate a task, support an incident response workflow, or fix something in a client tenant. And while PowerShell is flexible, inconsistent or unsafe scripts can introduce:

- Security vulnerabilities
- Hidden bugs
- Cross-tenant risk (for MSSPs)
- CI/CD pipeline failures
- Automation outages

<br/>

That’s why the final tool in this series focuses on PowerShell linting and static code analysis using one of the most important modules in the PowerShell ecosystem:

⚡ Meet **Invoke-ScriptAnalyzer** — the PowerShell linter for secure, high-quality automation

Invoke-ScriptAnalyzer gives you consistent, secure, and production-ready PowerShell by automatically detecting:
- Security risks
- Deprecated cmdlets
- Bad patterns
- Performance issues
- Formatting and style violations
- Cross-platform problems
- Maintainability concerns

<br/>

Whether you’re building SOC automation, Azure governance scripts, IR tooling, or client-facing MSSP workflows, ScriptAnalyzer enforces PowerShell best practices before your code ever reaches production. _**This isn’t about pretty formatting** — it’s about safer DevSecOps automation, fewer regressions, and scripts you can trust across every tenant you manage._

That’s where **`Invoke-ScriptAnalyzer`** swoops in. It’s like having a PowerShell code reviewer living inside your terminal — one that doesn’t judge you (too harshly), but still calls you out when you forget indentation, misuse cmdlets, or resurrect `Write-Host` like it’s 2012. Whether you’re pushing scripts to production, running tools in a client’s tenant, or polishing code for your next blog post, ScriptAnalyzer keeps you honest, clean, and safe.

Let’s break down how ScriptAnalyzer works, why it matters for cloud security engineers, and how to use it to level-up the quality of your PowerShell projects.

<br/>
<br/>
<br/>
<br/>

# 🧠 What `Invoke-ScriptAnalyzer` Does

`Invoke-ScriptAnalyzer` comes from the **PSScriptAnalyzer** module — a static analysis engine that scans your PowerShell scripts for:

- Errors  
- Warnings  
- Style violations  
- Deprecated patterns  
- Security risks  
- Performance issues  
- Cross-platform compatibility problems  

Think of it as **a lint roller for your PowerShell**, tuned to the official PowerShell Best Practices so your scripts come out squeaky-clean and ultra-secure. 

<br/>
<br/>
<br/>
<br/>

# 🛡️ Why ScriptAnalyzer Matters for Security People

This is where things get fun — because ScriptAnalyzer isn’t just about pretty code.  
It’s a **security tool** hiding in plain sight.

Security folks aren’t just worried about whether a script runs — we’re worried about what it might *break*, *expose*, or *accidentally reveal* along the way. Even seemingly small scripts interact with:

- Graph API  
- Azure resources  
- Entra ID  
- Sentinel/Defender data  
- Privileged permissions  
- Customer tenants (for MSSPs)

That makes secure coding a **defensive discipline**, not just a dev task.

Here’s why ScriptAnalyzer is essential for security pros:

### 🔐 1. Prevents accidental security weaknesses  
It flags things like:

- Hard-coded secrets  
- Plain-text credentials  
- Deprecated risky cmdlets (`Invoke-Expression`)  
- Unsafe string handling  
- Injection-prone patterns  
- Debug logging you forgot to remove  

It catches the stuff attackers love — before attackers ever see it.

<br/>

### 🧯 2. Reduces human error in automated SOC/IR workflows  
A broken script in an automated playbook isn’t just inconvenient — it’s dangerous.

Bad scripts can:

- Mangle Defender ATP data  
- Break Logic Apps  
- Mis-tag cloud resources  
- Corrupt audit logs  
- Apply policies incorrectly  
- Modify RBAC roles the wrong way  

ScriptAnalyzer provides a static safety net so simple mistakes don’t turn into big outages.

<br/>

### 🔧 3. Critical for MSSPs and consultants  
If you work in multiple tenants, consistency and safety aren’t “nice-to-have” — they’re required.

ScriptAnalyzer helps you avoid:

- Shipping broken automation  
- Running deprecated modules  
- Violating internal coding standards  
- Creating regressions across clients  

Cleaner scripts = fewer escalations = happier clients = fewer 11 PM emergencies.

<br/>

### 🧬 4. Creates consistent, auditable, repeatable code  
Security teams live on repeatability.

ScriptAnalyzer enforces:

- Naming consistency  
- Param block consistency  
- Function structure consistency  
- Safe coding defaults  

This makes your scripts easier to review, easier to hand off, and easier to integrate into future tooling.

<br/>

### 🧠 5. Teaches secure PowerShell habits  
Every warning is a tiny lesson:

- *“Here's a safer verb…”*  
- *“This alias makes things ambiguous…”*  
- *“This cmdlet casing breaks style guidelines…”*  

It's like pair-programming with the PowerShell team.

<br/>
<br/>
<br/>
<br/>

# 📚 ScriptAnalyzer Rule Categories

### 🧹 **1. Formatting Rules**
*"Because misaligned braces hurt feelings and readability."*

Checks for consistent indentation, whitespace, casing, and layout.

<br/>

### 🎩 **2. Style Rules**
*"Do you really need three aliases in a row? No. You do not."*

Flags aliases, positional parameters, incorrect naming, quoting issues, etc.

<br/>

### 🔐 **3. Security Rules**
*"Because the threat actors don’t need you helping them out."*

Catches unsafe cmdlets, hard-coded secrets, injection patterns, and more.

<br/>

### 💪 **4. Performance Rules**
*"You could run that… or you could run it *faster*."*

Identifies slow patterns, unnecessary loops, and deprecated commands.

<br/>

### 🚫 **5. Compatibility Rules**
*"Your script may work on PowerShell 7… but what about that old VM in the corner?"*

Ensures scripts work across platforms and PowerShell versions.

<br/>

### 🧩 **6. Maintainability Rules**
*"Future you will want to hug present you for using these."*

Encourages clean function structures, comments, and reusable logic.

<br/>

### 🚦 **7. Semantic Rules**
*"Not just how it looks — but what it *means*."*

Flags unused variables, unreachable code, and suspicious conditionals.

<br/>
<br/>
<br/>
<br/>

# 🧪 Hands-On Example: Analyzing a Script with ScriptAnalyzer

Let’s walk through a full example that:

- 1). Installs PSScriptAnalyzer  
- 2). Creates a sample “bad” script  
- 3). Analyzes it  
- 4). Outputs the results  

<br/>

```powershell
<#
.SYNOPSIS
    Demonstration of Invoke-ScriptAnalyzer
.DESCRIPTION
    This example creates a sample PowerShell script filled with
    intentional "teachable moments" 😅 and then analyzes it using
    Script Analyzer.
#>

# Step 0 — Make sure PSScriptAnalyzer is available
if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) {
    Write-Host "☕ Installing PSScriptAnalyzer..." -ForegroundColor Cyan
    Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser
}

# Step 1 — Create a bad example script
$ScriptPath = "$env:TEMP\TestScript.ps1"

@"
# This script intentionally contains several PowerShell sins 🙈

param(\$inputParam)

Write-Host "Hello world"
if(\$inputParam -eq "test")
{
write-output "Running test..."
}
else
{
write-output "Done"
}
"@ | Set-Content -Path $ScriptPath

Write-Host "📝 Created test script at $ScriptPath" -ForegroundColor Green

# Step 2 — Run the analyzer
Write-Host "`n🔍 Running Invoke-ScriptAnalyzer..." -ForegroundColor Yellow
$results = Invoke-ScriptAnalyzer -Path $ScriptPath

# Step 3 — Display results
if ($results) {
    Write-Host "`n⚠️ Issues found:" -ForegroundColor Red
    $results | Format-Table RuleName, Severity, Line, Message -AutoSize
}
else {
    Write-Host "🎉 No issues found — you're a PowerShell wizard." -ForegroundColor Green
}
```

<br/>
<br/>
<br/>
<br/>

# 🚀 Pro Tip: Add ScriptAnalyzer to Your CI/CD Pipeline

Want to enforce PowerShell best practices automatically? Add this to GitHub Actions or Azure DevOps:

```powershell
Copy code
$failures = Invoke-ScriptAnalyzer -Path .\Scripts -Recurse -Severity Error
if ($failures) {
    Write-Error "❌ ScriptAnalyzer found issues. Fix before merging."
    exit 1
}
```

<br/>

💡 Now your repo enforces its own quality gate — like a tiny automated SOC analyst.

<br/>
<br/>
<br/>
<br/>

# 🎯 Final Thoughts
Invoke-ScriptAnalyzer isn’t glamorous. It doesn’t spin up VMs, query Sentinel, or summon KQL magic. But it does help you write cleaner, safer, more maintainable PowerShell — and that’s the foundation of every mature DevSecOps practice.

It’s one of those tools that quietly saves you from:
- Future bugs
- Future rework
- Future “who wrote this?” moments
- Future weekend firefights

Add it to your toolbox now; Your future self — and your clients — will thank you. ⚔️🛡️💻

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

# 🎃 Bonus Tool Spotlight: “The Ghosts Hiding in Every Network”

### 💡 Toolbox Tip: Once you’ve mapped your entire Azure network with this script, the next smart move is finding out what’s lurking inside it.

In case you missed it, I already broke down a powerful PowerShell + Graph API tool that uncovers all the End-of-Life devices, outdated OS builds, and unsupported software haunting your tenant.
It’s wrapped in a fun Halloween theme, but don’t let the spooky aesthetic fool you — this tool is pure security value.

### 👉 Check it out here: [👻 The Ghosts Hiding In Every Network: End Of Life Devices And Software ☠️](https://www.hanley.cloud/2025-11-03-The-Ghosts-Hiding-in-Every-Network-End-of-Life-Devices-and-Software/)}

Together, this Network Inventory script + the EoL “Ghost Hunter” script give you a powerful one-two punch for:

- Full environment discovery
- Risk identification
- Audit readiness
- Modernization and cleanup planning

### It’s all part of building out your complete PowerShell Toolbox for real-world cloud security work. 🧰⚡

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

- [Cloud_Network_Assessment.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1)

- [Azure built-in roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)

- [Azure permissions - Azure RBAC](https://docs.azure.cn/en-us/role-based-access-control/resource-provider-operations)

- [Azure permissions for Networking](https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/networking)

- [Get-AzVirtualNetworkGatewayConnection (Az.Network)](https://learn.microsoft.com/en-us/powershell/module/az.network/get-azvirtualnetworkgatewayconnection?view=azps-14.6.0)

- [About ExpressRoute roles and permissions](https://learn.microsoft.com/en-us/azure/expressroute/roles-permissions)

- [👻 The Ghosts Hiding In Every Network: End Of Life Devices And Software ☠️](https://www.hanley.cloud/2025-11-03-The-Ghosts-Hiding-in-Every-Network-End-of-Life-Devices-and-Software/)

<br/>
<br/>
<br/>
<br/>



<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)

