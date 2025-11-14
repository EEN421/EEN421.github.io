🧰 PowerShell Toolbox
GPO HTML Export Script — Snapshot Every Group Policy Object in One Pass

Group Policy is where good intentions go to retire.

Over the years, GPOs accrete like digital barnacles: half-applied baselines, “temporary” lockdowns, that one legacy setting to keep a 2008-era app alive… and nobody wants to click through all of them in the Group Policy Management Console (GPMC).

This little PowerShell script gives you a one-click export of every GPO in the domain to HTML. That means you can:

Hand auditors a full policy snapshot

Review security configuration offline

Track drift over time (by re-running and diff’ing exports)

Have human-readable documentation without living in the GPMC tree

Here’s the script we’re talking about:

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


Let’s unpack it.

🎯 What This Script Does (High-Level)

In one run, this script:

Ensures a local folder exists: C:\GPOReports

Pulls all Group Policy Objects in the domain via Get-GPO -All

Loops through each GPO and:

Sanitizes its display name into a file-system safe filename

Calls Get-GPOReport to generate an HTML report for that GPO

Saves each report as:

C:\GPOReports\<GPO-Name>.html


Logs a warning if any individual GPO fails to export (e.g., permissions or weird corruption), but keeps going.

End result: a folder full of clickable HTML reports, one per GPO, ready for:

Security reviews

CIS / STIG baseline verification

Change documentation

Incident response “what is actually being applied to these OUs?” questions

🔐 When You’d Use This Script

This script shines in scenarios like:

Audit prep

You want to hand an auditor a snapshot of every GPO applied in the domain.

Baseline validation

“Are we really aligned with CIS / Microsoft Security Baselines / internal standards?”

Cleanup campaigns

Before you refactor GPOs, take a snapshot so you know what you had.

Incident response

You suspect GPO abuse (e.g., startup scripts, security config changes) and need quick visibility.

Migration planning

Moving to Intune/MDM and want to understand what existing GPOs are doing.

⚙️ Line-by-Line Breakdown
1. Define the Report Folder
$reportFolder = "C:\GPOReports"


Hard-codes the output location to: C:\GPOReports

This is where all the exported HTML reports will be stored.

You can easily parameterize this later, but hardcoding keeps it simple for now.

2. Ensure the Folder Exists
if (-not (Test-Path $reportFolder)) {
    New-Item -Path $reportFolder -ItemType Directory | Out-Null
}


Test-Path $reportFolder:

Checks whether C:\GPOReports already exists.

If it does not exist:

New-Item -ItemType Directory creates the folder.

Out-Null suppresses the normal “Directory: C:\GPOReports” output so the script stays quiet and clean.

This makes the script idempotent: you can run it multiple times without worrying about the folder being missing or throwing errors.

3. Get All Group Policy Objects
$GPOs = Get-GPO -All


Uses the GroupPolicy module’s Get-GPO cmdlet.

-All returns every GPO in the current domain.

The result is a collection of GPO objects, each with properties like:

DisplayName

Id

DomainName

Owner

CreationTime, ModificationTime, etc.

This is your “inventory” of GPOs to export.

Note for your article:
This requires you to be running the script on a domain-joined machine with the Group Policy Management tools installed (RSAT or GPMC on a DC / management server).

4. Loop Through Each GPO
foreach ($gpo in $GPOs) {
    try {
        ...
    } catch {
        ...
    }
}


Standard foreach loop: one iteration per GPO.

try { ... } catch { ... } ensures that if one GPO export fails, the script logs a warning and continues with the others instead of dying halfway through.

5. Sanitize the GPO Name for File System Use
$safeName = ($gpo.DisplayName -replace '[\\/:*?"<>|]', '_')


This is a subtle but important detail.

GPO.DisplayName can contain characters that are invalid in Windows filenames, like:

\ / : * ? " < > |

The regex '[\\/:*?"<>|]' matches any of those characters.

-replace ... , '_' replaces each occurrence with _.

Example:

GPO named:
Hardening: Domain Controllers / Default
becomes:
Hardening_ Domain Controllers _ Default

This prevents Get-GPOReport from failing when writing the .html file due to illegal characters in the path.

6. Build the Full Report Path
$reportPath = "$reportFolder\$safeName.html"


Simple string interpolation:

C:\GPOReports\<sanitized-GPO-name>.html

This is the target file path for the HTML report for this specific GPO.

7. Export the GPO to HTML
Get-GPOReport -Name $gpo.DisplayName -ReportType Html -Path $reportPath


This is the workhorse of the script.

Get-GPOReport is another cmdlet from the GroupPolicy module.

Parameters:

-Name $gpo.DisplayName → identifies which GPO to export.

-ReportType Html → generates a fully formatted HTML report.

-Path $reportPath → saves that HTML content into the file path we built.

The resulting HTML report includes:

GPO name, GUID, domain, owner, creation/modification date.

Links, WMI filters (if any).

Settings under:

Computer Configuration

User Configuration

Each policy area (Windows settings, Administrative Templates, Security Settings, Scripts, etc.)

Basically, everything you’d see in GPMC → Right-click GPO → Save Report…, but automated and done in bulk.

8. Error Handling
} catch {
    Write-Warning "Failed to export report for $($gpo.DisplayName): $_"
}


Catches any exception thrown inside the try block for that GPO:

Missing permissions

Corrupted GPO

Transient AD/GPMC glitch

Write-Warning prints a yellow warning with:

The GPO’s display name

The error message ($_)

This means:

One bad GPO doesn’t ruin the script run.

You get a clear list of problem GPOs to investigate later.

📁 What You Get on Disk

After the script finishes, you’ll have:

C:\GPOReports\
  |
  +-- Default Domain Policy.html
  +-- Default Domain Controllers Policy.html
  +-- Hardening_ Domain Controllers _ Tier0.html
  +-- Legacy_App_Compatibility.html
  +-- ...


Each .html file is fully clickable in any browser and shows all settings for that GPO.

▶️ How to Run This Script (Step-by-Step)
1. Prerequisites

Domain-joined machine

Group Policy Management Console tools installed:

On a domain controller, they’re usually already present.

On a management workstation, install:

RSAT: Group Policy Management Tools (on Windows 10/11 via “Optional Features” or RSAT package).

2. Permissions

You need permissions to read GPOs in the domain. Typically:

Members of:

Domain Admins

Group Policy Creator Owners

Or any delegated admin granted GPO read access

can safely run this.

3. Save the Script

Save as:

C:\Scripts\Export-All-GPOReports.ps1


Contents:

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

4. Run It

Open a PowerShell window as a domain user with GPO read rights:

Set-Location C:\Scripts
.\Export-All-GPOReports.ps1


When it finishes, browse to:

C:\GPOReports\


Double-click any .html file to view that GPO’s configuration.

🔍 How to Use This in Audits & Reviews

Here are a few practical workflows you can mention in your article:

✅ CIS / STIG Compliance

Re-run this script before every quarterly GPO review.

Use the HTML reports to check:

Password policy

Account lockout settings

Security options

Audit policies

TLS / cipher hardening (if configured via GPO)

📦 Before-and-After Snapshots

Run the script before a GPO refactor.

Zip up C:\GPOReports and archive it.

After changes, run it again.

You’ve now got before/after evidence and can use tools (or even manual HTML diff) to see changes.

🧯 Incident Response

If there’s suspicious behavior and you think “GPO did it,” this lets you:

Quickly scan for:

Startup scripts

Logon/logoff scripts

Security policy changes (e.g., turning off UAC, enabling unsigned drivers, etc.)

Provide a static, point-in-time view of GPOs to the IR team.

🚀 Possible Enhancements (Nice Bonus for Your Readers)

If you want to extend this in the toolbox series, you can:

Parameterize the $reportFolder path.

Add an option to generate XML reports instead of HTML for machine parsing:

Get-GPOReport -Name $gpo.DisplayName -ReportType Xml -Path $xmlPath


Add logging to a central location:

C:\GPOReports\ExportLog.txt

Zip the folder when done for easy attach/share:

Compress-Archive -Path $reportFolder\*.html -DestinationPath "$reportFolder\GPOReports.zip"


If you want, next we can tie this into the bigger DevSecOpsDad “toolbox trilogy”:
