# Introduction & Use Case:
Welcome back to the 🧰 PowerShell Toolbox series — your four-part deep-dive into must-have scripts for cloud engineers, security architects, auditors, and anyone who’s ever stared at an Azure tenant and thought: “Who really has access to what?” If you’ve ever asked, “Who has elevated permissions across my subscription, and when did they last use them?” — this script is your _second_ new best friend.

We’ve already taken on the network chaos of VNets, NSGs, firewalls, and connectivity with Part 1. Now it’s time to shine a light on the who side of your Azure environment. This script delivers a comprehensive audit: it collects every role assignment and privilege (including active vs. eligible, permanent vs. just-in-time) across your subscriptions and then exports it into one clear CSV for you to filter, analyze, and act on. 📊✨ It’s essential for audit-proofing, access governance, incident response, or cleaning up messy tenant sprawl. 🚀🛡️📋

...And again — this is just Part 2! In the rest of the series we’ll continue with:

🏛️ Part 3 — GPO HTML Export Script:
Inventory every Group Policy Object-from your Active Directory estate in one step. Perfect for Windows hardening, audit documentation, and landing-zone modernization.

🧹 Part 4 — Invoke-ScriptAnalyzer for Real-World Ops:
How to lint and polish your own PowerShell code, avoid embarrassing mistakes, and build scripts that scale in production environments.

So strap in — this series is all about moving you from clicking chaos to automated, clean clarity. Let’s dive into Part 2 and reveal exactly who holds the keys in your Azure tenant. 💪🔐

### ⚡ Check out the full script here 👇 **[https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Privileged_RBAC_Roles.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Privileged_RBAC_Roles.ps1)** 

<br/>
<br/>

![](/assets/img/Powershell%20Toolbox%202/Designer.png)

<br/>
<br/>
<br/>
<br/>

# 🎯 What This Script Does

At a high level, this script:

Targets a specific subscription (either current context or one you pass in) and...

-  **looks up role assignments at:**
    - Subscription scope
    - Resource Group scope (optional toggle)
    - Filters to a curated list of privileged RBAC roles, including:
    - Owner, Contributor, User Access Administrator
    - Security Administrator, Key Vault Administrator, VM Admin Login
    - AKS Cluster Admin, various “Contributor” roles to critical services, and more

- **Resolves who the principal actually is:**
    - User → Display name
    - Group → Group display name
    - Service Principal → App display name

- **Builds a collection of privileged role assignment rows with:**
    - Role name, scope, resource group (if applicable)
    - Principal type (User/Group/ServicePrincipal)
    - Principal name and sign-in name

- **Generates:**
    - Detailed CSV report
    - HTML summary with nice styling and visual breakdowns (roles, principal types, scope)

<br/>
<br/>

![](/assets/img/Powershell%20Toolbox%202/Report1.png)

<br/>
<br/>

### This is ideal for:
- CIS / NIST / CMMC / SOC 2 RBAC reviews
- Least-privilege enforcement efforts
- Quarterly access recertification
- “We think too many folks are Owners” interventions
- Identifying custom roles before activating Unified RBAC
- MSSP onboarding and baselining

<br/>
<br/>

![](/assets/img/Powershell%20Toolbox%202/Report2.png)

<br/>
<br/>
<br/>
<br/>

# 🧪 When You’d Use This in Real Life

You’d reach for this script when:
- You inherit a new subscription and want to know who’s dangerous
- An auditor asks: “Who has Owner or Contributor in production?”
- You’re hardening an environment to align with Zero Trust or least privilege
- Leadership wants evidence that you’re not handing out Owner like Halloween candy
- You’re documenting privileged access as part of a security architecture engagement

Run it, get your CSV + HTML, and you immediately move from “we think” to “we know.” You can view the entire script on my GitHub here 👇 **[https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Privileged_RBAC_Roles.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Privileged_RBAC_Roles.ps1)**

<br/>
<br/>
<br/>
<br/>

# ⚙️ How the Script Works (High-Level Flow)

- Accepts parameters (subscription ID, output paths, output format, whether to include RG-level roles).
- Displays progress using a helper function.
- Defines the set of privileged role names to look for.
- Resolves the subscription to analyze.
- Pulls subscription-scope role assignments, filters to privileged ones, and records them.
- Optionally pulls resource group-scope role assignments and records those too.
- Generates summary statistics by:
    - Role
    - Principal Type (User/Group/ServicePrincipal)
    - Scope (Subscription vs Resource Group)

- Outputs:
    - Console summary
    - CSV export (if desired)
    - HTML export (if desired) with tables and basic styling.
    - Returns $results so you can pipe it into other tooling.

<br/>

_Now let’s break down each part in detail.👇_

## 1. Parameters & Script Inputs
```powershell
param(
    [Parameter(Mandatory=$false)]
    [string]$SubscriptionId = "",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputCSVPath = ".\AzurePrivilegedRolesReport_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv",
    
    [Parameter(Mandatory=$false)]
    [string]$OutputHTMLPath = ".\AzurePrivilegedRolesReport_$(Get-Date -Format 'yyyyMMdd_HHmmss').html",
    
    [Parameter(Mandatory=$false)]
    [switch]$IncludeResourceGroups = $true,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("CSV", "HTML", "Both")]
    [string]$OutputFormat = "Both"
)
```

### Key Parameters:
```powershell
$SubscriptionId:
```
If empty → script uses your current Az context.

If provided → script switches to that subscription.

<br/>
<br/>


```powershell
$OutputCSVPath / $OutputHTMLPath:
```
Default to timestamped filenames in the current directory. This presents accidental overwrites and makes report trends easy to track over time.

<br/>
<br/>

```powershell
$IncludeResourceGroups (switch, default: $true):
```
If set → the script inspects resource group-level role assignments in addition to subscription-level.

<br/>
<br/>

You can disable this for a quick high-level check at the subscription level:
```powershell
-IncludeResourceGroups:$false
```

<br/>

```powershell
$OutputFormat:
```

- "CSV" → only CSV

- "HTML" → only HTML

- "Both" → you get it all

Perfect for tuning the script based on whether you’re in deep-dive mode or executive-summary mode.

<br/>
<br/>
<br/>
<br/>

## 2. Progress Helper
```powershell
function Write-ProgressHelper {
    param(
        [string]$Activity,
        [string]$Status,
        [int]$PercentComplete
    )
    
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $PercentComplete
}
```

☝️ This is a small wrapper around Write-Progress to keep the main logic tidy and allows you to update a progress bar with an activity (“Analyzing Azure RBAC”) and a status message (“Getting resource group role assignments”). You can use it throughout the script to keep the user informed instead of staring at a blinking cursor. Check out the below screenshot of it in action. 👇

<br/>

![](/assets/img/Powershell%20Toolbox%202/write-progress.png)

<br/>
<br/>
<br/>
<br/>

## 3. Defining “Privileged” Roles
This is your threat surface definition, telling the script: “These roles are privileged enough that I want to track and report on them.”

```powershell
$privilegedRoles = @(
    "Owner",
    "Contributor",
    "User Access Administrator",
    "Co-Administrator",
    "Service Administrator",
    "Account Administrator",
    "Key Vault Administrator",
    "SQL DB Contributor",
    "SQL Security Manager",
    "Storage Account Contributor",
    "Azure Kubernetes Service Cluster Admin Role",
    "Virtual Machine Administrator Login",
    "Virtual Machine Contributor",
    "Network Contributor",
    "Security Administrator",
    "Azure Service Deploy Release Management Contributor",
    "Automation Contributor",
    "Log Analytics Contributor",
    "Application Administrator",
    "Cloud Application Administrator"
)
```


This list includes:
- Broad-scoped roles: Owner, Contributor, User Access Administrator
- Admin-level service roles: Key Vault Administrator, Security Administrator, VM Admin Login, AKS Cluster Admin, etc.
- Operationally powerful roles: Log Analytics Contributor, Storage Account Contributor, Automation Contributor

> 💡 You can easily extend this list and define additional roles you'd like to flag relative to your governance model.

<br/>
<br/>
<br/>
<br/>

## 4. Results Collection & Script Banner
```powershell
$results = @()

Write-Host "Starting Azure RBAC Privileged Roles Audit..." -ForegroundColor Cyan
```

```$results``` will store all privileged role assignments as PSCustomObjects. A nice, visible banner to show the script has started.

<br/>
<br/>
<br/>
<br/>

## 5. Subscription Selection Logic

There are two usage patterns in this section:
- 1). No SubscriptionId provided.
- 2). Uses the current Az context from Get-AzContext.

<br/>

```powershell
if ([string]::IsNullOrEmpty($SubscriptionId)) {
    try {
        $context = Get-AzContext
        if (-not $context) {
            Write-Host "You're not connected to Azure. Please run Connect-AzAccount first." -ForegroundColor Red
            exit
        }
        $SubscriptionId = $context.Subscription.Id
    }
    catch {
        Write-Host "Error getting Azure context: $_" -ForegroundColor Red
        exit
    }
}
else {
    try {
        Select-AzSubscription -SubscriptionId $SubscriptionId | Out-Null
    }
    catch {
        Write-Host "Error selecting subscription $SubscriptionId : $_" -ForegroundColor Red
        exit
    }
}
```

If you’re not connected, it tells you to run Connect-AzAccount. SubscriptionId provided calls Select-AzSubscription to switch context. This gives you flexibility as a consultant or in multi-tenant scenarios.

<br/>
<br/>
<br/>
<br/>

## 6. Subscription Details
```powershell 
try {
    $subscription = Get-AzSubscription -SubscriptionId $SubscriptionId
    Write-Host "Analyzing subscription: $($subscription.Name) ($SubscriptionId)" -ForegroundColor Green
}
catch {
    Write-Host "Error retrieving subscription information: $_" -ForegroundColor Red
    exit
}
```

☝️ Grabs the subscription metadata (name, etc.) for logging and reporting. You use ```$subscription.Name``` throughout to label rows and the HTML summary.

<br/>
<br/>
<br/>
<br/>

## 7. Subscription-Level Role Assignments
### 7.1 Progress + Fetch
```powershell
Write-ProgressHelper -Activity "Analyzing Azure RBAC" -Status "Getting subscription-level role assignments" -PercentComplete 20
Write-Host "Getting subscription-level role assignments..." -ForegroundColor Yellow

$subRoleAssignments = Get-AzRoleAssignment -Scope "/subscriptions/$SubscriptionId"
```

☝️ Shows progress at 20% with a clear status and pulls all role assignments at the subscription scope.

<br/>
<br/>

### 7.2 Filter to Privileged Roles
```powershell
$privilegedAssignments = $subRoleAssignments | Where-Object { $privilegedRoles -contains $_.RoleDefinitionName }
```

☝️ Filters assignments down to just the roles we defined as earlier.

<br/>
<br/>

### 7.3 Resolve Principal Identity
```powershell
foreach ($assignment in $privilegedAssignments) {
    $principalType = $assignment.ObjectType
    $principalName = ""
    
    try {
        if ($principalType -eq "User") {
            $user = Get-AzADUser -ObjectId $assignment.ObjectId -ErrorAction SilentlyContinue
            if ($user) {
                $principalName = $user.DisplayName
            }
            else {
                $principalName = $assignment.DisplayName
            }
        }
        elseif ($principalType -eq "Group") {
            $group = Get-AzADGroup -ObjectId $assignment.ObjectId -ErrorAction SilentlyContinue
            if ($group) {
                $principalName = $group.DisplayName
            }
            else {
                $principalName = $assignment.DisplayName
            }
        }
        elseif ($principalType -eq "ServicePrincipal") {
            $sp = Get-AzADServicePrincipal -ObjectId $assignment.ObjectId -ErrorAction SilentlyContinue
            if ($sp) {
                $principalName = $sp.DisplayName
            }
            else {
                $principalName = $assignment.DisplayName
            }
        }
        else {
            $principalName = $assignment.DisplayName
        }
    }
    catch {
        $principalName = $assignment.DisplayName
        Write-Host "Warning: Could not resolve display name for $($assignment.ObjectId)" -ForegroundColor Yellow
    }
```
<br/>
<br/>

Based on ObjectType, the script attempts to pull the latest display name from Entra ID:
```powershell
Get-AzADUser

Get-AzADGroup

Get-AzADServicePrincipal
```

...Then falls back to ```assignment.DisplayName``` if lookups fail and logs a warning if it can’t resolve the principal (handy for stale/deleted objects).

<br/>
<br/>

### 7.4 Build Result Object
```powershell
    $resultObject = [PSCustomObject]@{
        SubscriptionName = $subscription.Name
        SubscriptionId   = $SubscriptionId
        Scope            = "Subscription"
        ResourceGroupName= "N/A"
        RoleName         = $assignment.RoleDefinitionName
        PrincipalType    = $principalType
        PrincipalId      = $assignment.ObjectId
        PrincipalName    = $principalName
        SignInName       = $assignment.SignInName
        AssignmentId     = $assignment.RoleAssignmentId
        IsPIM            = "Unknown"
    }
    
    $results += $resultObject
}
```

Each privileged role assignment becomes one row in ```$results```. ```IsPIM``` is set to ```"Unknown"``` because you’d need dedicated PIM APIs to know if the assignment is permanent, active, eligible, etc. 

> I am going to add this later and post another update, stay tuned!

<br/>
<br/>

### 7.5 Summary at Subscription Scope
```powershell
Write-Host "Found $($privilegedAssignments.Count) privileged role assignments at subscription level" -ForegroundColor Green
```

☝️Immediate feedback on how many privileged assignments exist at the subscription level.

<br/>
<br/>
<br/>
<br/>

## 8. Resource Group-Level Role Assignments

Wrapped in:
```powershell
if ($IncludeResourceGroups) {
    ...
}
``` 
<br/>
<br/>

### 8.1 Progress & RG Discovery
```powershell
Write-ProgressHelper -Activity "Analyzing Azure RBAC" -Status "Getting resource group role assignments" -PercentComplete 50
Write-Host "Getting resource group-level role assignments..." -ForegroundColor Yellow

$resourceGroups = Get-AzResourceGroup
$totalRgs = $resourceGroups.Count
$currentRg = 0
```

☝️ Moves progress to 50% and enumerates all resource groups in the subscription.

<br/>
<br/>

### 8.2 Per-RG Role Assignments
```powershell
foreach ($rg in $resourceGroups) {
    $currentRg++
    $percentComplete = [math]::Min(50 + [math]::Floor(($currentRg / $totalRgs) * 40), 90)
    Write-ProgressHelper -Activity "Analyzing Azure RBAC" -Status "Processing resource group $currentRg of $totalRgs" -PercentComplete $percentComplete
    
    $rgScope = "/subscriptions/$SubscriptionId/resourceGroups/$($rg.ResourceGroupName)"
    $rgRoleAssignments = Get-AzRoleAssignment -Scope $rgScope
```

☝️ This dynamically updates progress between 50–90% based on how many RGs you’ve processed and fetches RG-level role assignments for each RG.

<br/>
<br/>

### 8.3 Filter & Collect

Same filtering and principal resolution logic as subscription scope:
```powershell
$rgPrivilegedAssignments = $rgRoleAssignments | Where-Object { $privilegedRoles -contains $_.RoleDefinitionName }
```

Then each result is stored as:
```powershell
$resultObject = [PSCustomObject]@{
    SubscriptionName = $subscription.Name
    SubscriptionId   = $SubscriptionId
    Scope            = "Resource Group"
    ResourceGroupName= $rg.ResourceGroupName
    RoleName         = $assignment.RoleDefinitionName
    PrincipalType    = $principalType
    PrincipalId      = $assignment.ObjectId
    PrincipalName    = $principalName
    SignInName       = $assignment.SignInName
    AssignmentId     = $assignment.RoleAssignmentId
    IsPIM            = "Unknown"
}
```

This time, ```Scope = "Resource Group"``` and **ResourceGroupName** is **populated**. This lets you differentiate subscription-wide assignments from narrower RG-level ones.

<br/>
<br/>
<br/>
<br/>

## 9. Summary Statistics

After collecting all results:
```powershell
$roleStats = $results | Group-Object -Property RoleName | 
    Select-Object @{N='Role';E={$_.Name}}, @{N='Count';E={$_.Count}} |
    Sort-Object -Property Count -Descending

$principalTypeStats = $results | Group-Object -Property PrincipalType | 
    Select-Object @{N='PrincipalType';E={$_.Name}}, @{N='Count';E={$_.Count}} |
    Sort-Object -Property Count -Descending

$scopeStats = $results | Group-Object -Property Scope | 
    Select-Object @{N='Scope';E={$_.Name}}, @{N='Count';E={$_.Count}} |
    Sort-Object -Property Count -Descending
```

### roleStats: how many assignments per role.

### principalTypeStats: how many Users vs Groups vs ServicePrincipals.

### scopeStats: how many at Subscription vs Resource Group.

These get printed in the console and also embedded in the HTML report.

<br/>
<br/>
<br/>
<br/>

## 10. Console Report
```powershell
Write-Host "`nPrivileged Role Assignment Summary for Subscription: $($subscription.Name)" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "Total privileged role assignments found: $($results.Count)" -ForegroundColor Green

Write-Host "`nBreakdown by Role:" -ForegroundColor Green
$roleStats | Format-Table -AutoSize

Write-Host "`nBreakdown by Principal Type:" -ForegroundColor Green
$principalTypeStats | Format-Table -AutoSize

Write-Host "`nBreakdown by Scope:" -ForegroundColor Green
$scopeStats | Format-Table -AutoSize
```

☝️ Gives you an immediate CLI-friendly summary. This is super cool
 during live reviews.

<br/>
<br/>
<br/>
<br/>

## 11. CSV Export
```powershell
if ($OutputFormat -eq "CSV" -or $OutputFormat -eq "Both") {
    $results | Export-Csv -Path $OutputCSVPath -NoTypeInformation
    Write-Host "`nDetailed CSV report exported to: $OutputCSVPath" -ForegroundColor Green
}
```

☝️ This Exports the full dataset with headers. The CSV becomes your deep dive artifact — filter and pivot to your heart’s content.

CSV columns include:
- SubscriptionName
- SubscriptionId
- Scope (Subscription / Resource Group)
- ResourceGroupName
- RoleName
- PrincipalType
- PrincipalId
- PrincipalName
- SignInName
- AssignmentId
- IsPIM

<br/>
<br/>
<br/>
<br/>

## 12. HTML Export (Executive-Friendly Report)

If OutputFormat includes "HTML":
- The script builds a modern, styled HTML report with:
    - Header + timestamp
    - Summary section

- Tables for:
    - Breakdown by Role
    - Breakdown by Principal Type

- Breakdown by Scope
- Full detailed assignments

Example touches:
```powershell
if ($result.RoleName -eq "Owner" -or $result.RoleName -eq "Contributor") {
    $rowColor = ' style="background-color: #FFF1F0;"'
}
```

☝️ Owner/Contributor rows are visually highlighted in a pale red; Makes it trivial for a non-technical stakeholder to eyeball risk hot spots.

The HTML also uses basic CSS embedded in the header, so it’s:
- Zero dependencies
- Email- or portal-friendly
- Good-looking enough for a slide deck screenshot

<br/>
<br/>
<br/>
<br/>

## 13. Completion & Return
```powershell
Write-ProgressHelper -Activity "Analyzing Azure RBAC" -Status "Completed" -PercentComplete 100
Write-Host "`nAzure RBAC Privileged Roles Audit completed!" -ForegroundColor Cyan

return $results
```

This closes out the progress bar and prints a nice completion message; Returns ```$results``` to the pipeline, so you can do:
```powershell
$results = .\Azure_RBAC_PrivilegedRoles_Audit.ps1
$results | Where-Object RoleName -eq "Owner"
```
<br/>
<br/>
<br/>
<br/>

# ▶️ How to Run the Script (Step-by-Step)
### 1. Prerequisites

- owerShell with these modules:
    - Az.Accounts
    - Az.Resources (for RBAC + Azure AD objects)

- Permissions:
    - Reader on the subscription is usually enough to see role assignments.
    - Basic directory read access for Get-AzADUser/Group/ServicePrincipal (most orgs allow this by default, but locked-down tenants may require Directory Reader).

- Install Az if needed:
    - ```Install-Module Az -Scope CurrentUser``` 

<br/>
<br/>

### 2. Save the Script

Save it as: ```C:\Scripts\Azure_RBAC_PrivilegedRoles_Audit.ps1```

<br/>
<br/>

### 3. Connect to Azure
```powershell
Connect-AzAccount
```

(Or ```Connect-AzAccount -Tenant <tenantId>``` depending on your setup.)

<br/>
<br/>

### 4. Run It (Common Scenarios)

- a) Quick run against your current subscription (CSV + HTML):
    - ```Set-Location C:\Scripts```
    - ```.\Azure_RBAC_PrivilegedRoles_Audit.ps1```

- b) Target a specific subscription ID:
    - ```.\Azure_RBAC_PrivilegedRoles_Audit.ps1 -SubscriptionId "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"```

- c) CSV only, no HTML:
    - ```.\Azure_RBAC_PrivilegedRoles_Audit.ps1 -OutputFormat "CSV"```

- d) HTML only, custom path:
    - ```.\Azure_RBAC_PrivilegedRoles_Audit.ps1 -OutputFormat "HTML" -OutputHTMLPath "C:\Reports\PrivilegedRoles.html"```

- e) Subscription-only view (skip RG-level noise):
    - ```.\Azure_RBAC_PrivilegedRoles_Audit.ps1 -IncludeResourceGroups:$false```

<br/>
<br/>
<br/>
<br/>

# 🔍 How to Use the Output in an Audit

Once you’ve got the CSV, you can:
- Filter RoleName to find all Owner assignments
- Filter PrincipalType = User to find individuals with powerful roles
- Filter PrincipalType = ServicePrincipal to review app/service identities
- Filter RoleName for specific services like:
- Key Vault Administrator
- Virtual Machine Administrator Login
- Security Administrator

<br/>

The HTML report is perfect for:
- Dropping into a OneNote page for a customer workshop
- Attaching to a ticket for remediation tasks
- Screenshotting role breakdowns into PowerPoint


<br/>
<br/>
<br/>
<br/>

# 🧰 Missed Part 1? Build Your Foundation First
💡 Toolbox Tip: Before you dive deep into RBAC and privileged access auditing, make sure your network fundamentals are squared away.

If you didn’t catch the first installment of this series, now’s the perfect time to go back and grab it.
PowerShell Toolbox Part 1: Azure Network Audit walks you through a full, subscription-wide network discovery — VNets, subnets, NSGs, routes, firewalls, gateways, ExpressRoute, the whole stack.

It’s the “baseline truth” every cloud engineer and security architect needs before tackling identity, access, or governance. Once you know how traffic flows, you can finally understand how permissions should behave.

👉 Start with Part 1 here: [PowerShell Toolbox Part 1 of 4 — Azure Network Audit](https://www.hanley.cloud/2025-11-16-PowerShell-Toolbox-Part-1-of-4-Azure-Network-Audit/)

Together, Part 1 (Network Audit) + Part 2 (RBAC Privileged Roles Audit) give you:

A full map of your cloud network

Clear visibility into who has elevated access

Faster audit readiness for CIS, NIST, CMMC, ISO, etc.

A living toolbox of reusable PowerShell skills

Build your toolbox one script at a time — each piece makes you sharper, faster, and more dangerous. ⚡

<br/>
<br/>

Thanks for following along — you’ve now equipped yourself with a reusable PowerShell script to audit privileged roles and RBAC across your Azure tenant. As you integrate this into your toolbox, remember: discovering and documenting access is the first step; remediating over-privilege and enforcing least-privilege are what turn insight into security. Stay tuned for the next installment and Keep building, keep refining, and let’s keep your cloud environment both secure and auditable!

In our next installment we'll break down part's 3 and 4:

- 🏛️ Part 3 — GPO HTML Export Script:
Inventory every Group Policy Object-from your Active Directory estate in one step. Perfect for Windows hardening, audit documentation, and landing-zone modernization.

<br/>

- 🧹 Part 4 — Invoke-ScriptAnalyzer for Real-World Ops:
How to lint and polish your own PowerShell code, avoid embarrassing mistakes, and build scripts that scale in production environments.

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



<br/>
<br/>
<br/>
<br/>



<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
