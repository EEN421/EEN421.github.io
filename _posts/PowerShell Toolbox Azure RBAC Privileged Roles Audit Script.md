🧰 PowerShell Toolbox
Azure RBAC Privileged Roles Audit Script — Who Really Has the Keys to Your Cloud?

You can build the most beautiful Azure landing zone on earth… and still get wrecked if too many people are walking around with Owner, Contributor, or broad admin roles.

Azure RBAC is where Zero Trust either lives or quietly dies.

This script, the Azure RBAC Privileged Roles Audit Script, is your spotlight. It crawls your subscription, finds who actually holds privileged roles, and spits out:

A detailed CSV for deep technical analysis

An optional HTML report you can hand to your CISO, manager, or auditor without shame

Let’s walk through what it does, how it works, and how to run it in your own environment.

🎯 What This Script Does

At a high level, this script:

Targets a specific subscription (either current context or one you pass in)

Looks up role assignments at:

Subscription scope

Resource Group scope (optional toggle)

Filters to a curated list of privileged RBAC roles, including:

Owner, Contributor, User Access Administrator

Security Administrator, Key Vault Administrator, VM Admin Login

AKS Cluster Admin, various “Contributor” roles to critical services, and more

Resolves who the principal actually is:

User → Display name

Group → Group display name

Service Principal → App display name

Builds a collection of privileged role assignment rows with:

Role name, scope, resource group (if applicable)

Principal type (User/Group/ServicePrincipal)

Principal name and sign-in name

Generates:

Detailed CSV report

HTML summary with nice styling and visual breakdowns (roles, principal types, scope)

This is ideal for:

CIS / NIST / CMMC / SOC 2 RBAC reviews

Least-privilege enforcement efforts

Quarterly access recertification

“We think too many folks are Owners” interventions

MSSP onboarding and baselining

🧪 When You’d Use This in Real Life

You’d reach for this script when:

You inherit a new subscription and want to know who’s dangerous

An auditor asks: “Who has Owner or Contributor in production?”

You’re hardening an environment to align with Zero Trust or least privilege

Leadership wants evidence that you’re not handing out Owner like Halloween candy

You’re documenting privileged access as part of a security architecture engagement

Run it, get your CSV + HTML, and you immediately move from “we think” to “we know.”

⚙️ How the Script Works (High-Level Flow)

Accepts parameters (subscription ID, output paths, output format, whether to include RG-level roles).

Displays progress using a helper function.

Defines the set of privileged role names to look for.

Resolves the subscription to analyze.

Pulls subscription-scope role assignments, filters to privileged ones, and records them.

Optionally pulls resource group-scope role assignments and records those too.

Generates summary statistics by:

Role

Principal Type (User/Group/ServicePrincipal)

Scope (Subscription vs Resource Group)

Outputs:

Console summary

CSV export (if desired)

HTML export (if desired) with tables and basic styling.

Returns $results so you can pipe it into other tooling.

Now let’s break down each part in detail.

1. Parameters & Script Inputs
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

Key knobs:

$SubscriptionId:

If empty → script uses your current Az context.

If provided → script switches to that subscription.

$OutputCSVPath / $OutputHTMLPath:

Default to timestamped filenames in the current directory.

Prevents accidental overwrites and makes report runs easy to track over time.

$IncludeResourceGroups (switch, default: $true):

If set → the script inspects resource group-level role assignments in addition to subscription-level.

You can disable for a quick high-level check:

-IncludeResourceGroups:$false


$OutputFormat:

"CSV" → only CSV

"HTML" → only HTML

"Both" → you get it all

Perfect for tuning the script based on whether you’re in deep-dive mode or executive-summary mode.

2. Progress Helper
function Write-ProgressHelper {
    param(
        [string]$Activity,
        [string]$Status,
        [int]$PercentComplete
    )
    
    Write-Progress -Activity $Activity -Status $Status -PercentComplete $PercentComplete
}


This is a small wrapper around Write-Progress to keep the main logic tidy.

Allows you to update a progress bar with an activity (“Analyzing Azure RBAC”) and a status message (“Getting resource group role assignments”).

You use it throughout the script to keep the user informed instead of staring at a blinking cursor.

3. Defining “Privileged” Roles
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


This is your threat surface definition.

You’re essentially telling the script:

“These roles are privileged enough that I want to track and report on them.”

It includes:

Broad-scoped roles: Owner, Contributor, User Access Administrator

Admin-level service roles: Key Vault Administrator, Security Administrator, VM Admin Login, AKS Cluster Admin, etc.

Operationally powerful roles: Log Analytics Contributor, Storage Account Contributor, Automation Contributor

You can easily extend this list in your article for readers:

Add custom roles

Add additional built-in roles relevant to their governance model

4. Result Collection & Script Banner
$results = @()

Write-Host "Starting Azure RBAC Privileged Roles Audit..." -ForegroundColor Cyan


$results will store all privileged role assignments as PSCustomObjects.

Nice, visible banner to show the script has started.

5. Subscription Selection Logic
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


Two usage patterns:

No SubscriptionId provided:

Uses the current Az context from Get-AzContext.

If you’re not connected, it tells you to run Connect-AzAccount.

SubscriptionId provided:

Calls Select-AzSubscription to switch context.

This gives you flexibility as a consultant or in multi-tenant scenarios.

6. Subscription Details
try {
    $subscription = Get-AzSubscription -SubscriptionId $SubscriptionId
    Write-Host "Analyzing subscription: $($subscription.Name) ($SubscriptionId)" -ForegroundColor Green
}
catch {
    Write-Host "Error retrieving subscription information: $_" -ForegroundColor Red
    exit
}


Grabs the subscription metadata (name, etc.) for logging and reporting.

You use $subscription.Name throughout to label rows and the HTML summary.

7. Subscription-Level Role Assignments
7.1 Progress + Fetch
Write-ProgressHelper -Activity "Analyzing Azure RBAC" -Status "Getting subscription-level role assignments" -PercentComplete 20
Write-Host "Getting subscription-level role assignments..." -ForegroundColor Yellow

$subRoleAssignments = Get-AzRoleAssignment -Scope "/subscriptions/$SubscriptionId"


Shows progress at 20% with a clear status.

Pulls all role assignments at the subscription scope.

7.2 Filter to Privileged Roles
$privilegedAssignments = $subRoleAssignments | Where-Object { $privilegedRoles -contains $_.RoleDefinitionName }


Filters assignments down to just the roles you defined as privileged.

7.3 Resolve Principal Identity
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


Based on ObjectType, the script attempts to pull the latest display name from Entra ID:

Get-AzADUser

Get-AzADGroup

Get-AzADServicePrincipal

Falls back to assignment.DisplayName if lookups fail.

Logs a warning if it can’t resolve the principal (handy for stale/deleted objects).

7.4 Build Result Object
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


Each privileged role assignment becomes one row in $results.

IsPIM is set to "Unknown" because you’d need dedicated PIM APIs to know if the assignment is permanent, active, eligible, etc.

7.5 Summary at Subscription Scope
Write-Host "Found $($privilegedAssignments.Count) privileged role assignments at subscription level" -ForegroundColor Green


Immediate feedback on how many privileged assignments exist at the subscription level.

8. Resource Group-Level Role Assignments (Optional)

Wrapped in:

if ($IncludeResourceGroups) {
    ...
}

8.1 Progress & RG Discovery
Write-ProgressHelper -Activity "Analyzing Azure RBAC" -Status "Getting resource group role assignments" -PercentComplete 50
Write-Host "Getting resource group-level role assignments..." -ForegroundColor Yellow

$resourceGroups = Get-AzResourceGroup
$totalRgs = $resourceGroups.Count
$currentRg = 0


Moves progress to 50%.

Enumerates all resource groups in the subscription.

8.2 Per-RG Role Assignments
foreach ($rg in $resourceGroups) {
    $currentRg++
    $percentComplete = [math]::Min(50 + [math]::Floor(($currentRg / $totalRgs) * 40), 90)
    Write-ProgressHelper -Activity "Analyzing Azure RBAC" -Status "Processing resource group $currentRg of $totalRgs" -PercentComplete $percentComplete
    
    $rgScope = "/subscriptions/$SubscriptionId/resourceGroups/$($rg.ResourceGroupName)"
    $rgRoleAssignments = Get-AzRoleAssignment -Scope $rgScope


Dynamically updates progress between 50–90% based on how many RGs you’ve processed.

Fetches RG-level role assignments for each RG.

8.3 Filter & Collect

Same filtering and principal resolution logic as subscription scope:

$rgPrivilegedAssignments = $rgRoleAssignments | Where-Object { $privilegedRoles -contains $_.RoleDefinitionName }


Then each result is stored as:

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


This time, Scope = "Resource Group" and ResourceGroupName is populated.

Lets you differentiate subscription-wide assignments from narrower RG-level ones.

9. Summary Statistics

After collecting all results:

$roleStats = $results | Group-Object -Property RoleName | 
    Select-Object @{N='Role';E={$_.Name}}, @{N='Count';E={$_.Count}} |
    Sort-Object -Property Count -Descending

$principalTypeStats = $results | Group-Object -Property PrincipalType | 
    Select-Object @{N='PrincipalType';E={$_.Name}}, @{N='Count';E={$_.Count}} |
    Sort-Object -Property Count -Descending

$scopeStats = $results | Group-Object -Property Scope | 
    Select-Object @{N='Scope';E={$_.Name}}, @{N='Count';E={$_.Count}} |
    Sort-Object -Property Count -Descending


roleStats: how many assignments per role.

principalTypeStats: how many Users vs Groups vs ServicePrincipals.

scopeStats: how many at Subscription vs Resource Group.

These get printed in the console and also embedded in the HTML report.

10. Console Report
Write-Host "`nPrivileged Role Assignment Summary for Subscription: $($subscription.Name)" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "Total privileged role assignments found: $($results.Count)" -ForegroundColor Green

Write-Host "`nBreakdown by Role:" -ForegroundColor Green
$roleStats | Format-Table -AutoSize

Write-Host "`nBreakdown by Principal Type:" -ForegroundColor Green
$principalTypeStats | Format-Table -AutoSize

Write-Host "`nBreakdown by Scope:" -ForegroundColor Green
$scopeStats | Format-Table -AutoSize


Gives you an immediate CLI-friendly summary.

Super useful during live reviews or incident response.

11. CSV Export
if ($OutputFormat -eq "CSV" -or $OutputFormat -eq "Both") {
    $results | Export-Csv -Path $OutputCSVPath -NoTypeInformation
    Write-Host "`nDetailed CSV report exported to: $OutputCSVPath" -ForegroundColor Green
}


Exports the full dataset with headers.

This CSV becomes your deep dive artifact — filter and pivot to your heart’s content.

CSV columns include:

SubscriptionName

SubscriptionId

Scope (Subscription / Resource Group)

ResourceGroupName

RoleName

PrincipalType

PrincipalId

PrincipalName

SignInName

AssignmentId

IsPIM

12. HTML Export (Executive-Friendly Report)

If OutputFormat includes "HTML":

The script builds a modern, styled HTML report with:

Header + timestamp

Summary section

Tables for:

Breakdown by Role

Breakdown by Principal Type

Breakdown by Scope

Full detailed assignments

Example touches:

if ($result.RoleName -eq "Owner" -or $result.RoleName -eq "Contributor") {
    $rowColor = ' style="background-color: #FFF1F0;"'
}


Owner/Contributor rows are visually highlighted in a pale red.

Makes it trivial for a non-technical stakeholder to eyeball risk hot spots.

The HTML uses basic CSS embedded in the header, so it’s:

Zero dependencies

Email- or portal-friendly

Good-looking enough for a slide deck screenshot

13. Completion & Return
Write-ProgressHelper -Activity "Analyzing Azure RBAC" -Status "Completed" -PercentComplete 100
Write-Host "`nAzure RBAC Privileged Roles Audit completed!" -ForegroundColor Cyan

return $results


Closes out the progress bar.

Prints a nice completion message.

Returns $results to the pipeline, so you can do:

$results = .\Azure_RBAC_PrivilegedRoles_Audit.ps1
$results | Where-Object RoleName -eq "Owner"

▶️ How to Run the Script (Step-by-Step)
1. Prerequisites

PowerShell with these modules:

Az.Accounts

Az.Resources (for RBAC + Azure AD objects)

Permissions:

Reader on the subscription is usually enough to see role assignments.

Basic directory read access for Get-AzADUser/Group/ServicePrincipal (most orgs allow this by default, but locked-down tenants may require Directory Reader).

Install Az if needed:

Install-Module Az -Scope CurrentUser

2. Save the Script

Save it as:

C:\Scripts\Azure_RBAC_PrivilegedRoles_Audit.ps1

3. Connect to Azure
Connect-AzAccount


(Or Connect-AzAccount -Tenant <tenantId> depending on your setup.)

4. Run It (Common Scenarios)

a) Quick run against your current subscription (CSV + HTML):

Set-Location C:\Scripts
.\Azure_RBAC_PrivilegedRoles_Audit.ps1


b) Target a specific subscription ID:

.\Azure_RBAC_PrivilegedRoles_Audit.ps1 -SubscriptionId "00000000-0000-0000-0000-000000000000"


c) CSV only, no HTML:

.\Azure_RBAC_PrivilegedRoles_Audit.ps1 -OutputFormat "CSV"


d) HTML only, custom path:

.\Azure_RBAC_PrivilegedRoles_Audit.ps1 -OutputFormat "HTML" -OutputHTMLPath "C:\Reports\PrivilegedRoles.html"


e) Subscription-only view (skip RG-level noise):

.\Azure_RBAC_PrivilegedRoles_Audit.ps1 -IncludeResourceGroups:$false

🔍 How to Use the Output in an Audit

Once you’ve got the CSV, you can:

Filter RoleName to find all Owner assignments

Filter PrincipalType = User to find individuals with powerful roles

Filter PrincipalType = ServicePrincipal to review app/service identities

Filter RoleName for specific services like:

Key Vault Administrator

Virtual Machine Administrator Login

Security Administrator

The HTML report is perfect for:

Dropping into a OneNote page for a customer workshop

Attaching to a ticket for remediation tasks

Screenshotting role breakdowns into PowerPoint
