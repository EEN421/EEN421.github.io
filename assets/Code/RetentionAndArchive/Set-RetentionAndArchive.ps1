<#       
	- This PowerShell script leverages the Tables-Update API call to configure the Log Analytics retention and archiving for tables of type Analytics.
	- The input parameters (WorkspaceID, etc.) must be saved in an accompanying JSON file.
 	- Usage example with examlpe.json in same directory:
  		.\Set-RetentionAndArchive.ps1 Example.json
#>

#region UserInputs

param(
    [parameter(Mandatory = $true, HelpMessage = "Provide full path for Json File")]
    [string] $JSONfile
) 

# *****************************************
#region HelperFunctions
function Write-Log {
    <#
    .DESCRIPTION 
    Write-Log is used to write information to a log file and to the console.
    
    .PARAMETER Severity
    parameter specifies the severity of the log message. Values can be: Information, Warning, or Error. 
    #>

    [CmdletBinding()]
    param(
        [parameter()]
        [ValidateNotNullOrEmpty()]
        [string]$Message,
        [string]$LogFileName,
 
        [parameter()]
        [ValidateNotNullOrEmpty()]
        [ValidateSet('Information', 'Warning', 'Error')]
        [string]$Severity = 'Information'
    )
    # Write the message out to the correct channel											  
    switch ($Severity) {
        "Information" { Write-Host $Message -ForegroundColor Green }
        "Warning" { Write-Host $Message -ForegroundColor Yellow }
        "Error" { Write-Host $Message -ForegroundColor Red }
    } 											  
    try {
        [PSCustomObject]@{
            Time     = (Get-Date -f g)
            Message  = $Message
            Severity = $Severity
        } | Export-Csv -Path "$PSScriptRoot\$LogFileName" -Append -NoTypeInformation -Force
    }
    catch {
        Write-Error "An error occurred in Write-Log() method" -ErrorAction SilentlyContinue		
    }    
}
#endregion HelperFunctions

# *****************************************
#region MainFunctions
function Get-LATables {		
	$LATables = @()	
    $TablesApi = "https://management.azure.com/subscriptions/$SubscriptionId/resourcegroups/$LogAnalyticsResourceGroup/providers/Microsoft.OperationalInsights/workspaces/$LogAnalyticsWorkspaceName/tables" + "?api-version=2021-12-01-preview"								
	    		
    try {        
        $TablesApiResult = Invoke-RestMethod -Uri $TablesApi -Method "GET" -Headers $LaAPIHeaders           			
    } 
    catch {                    
        Write-Log -Message "Get-LATables $($_)" -LogFileName $LogFileName -Severity Error		                
    }

    If ($TablesApiResult.StatusCode -ne 200) {
        $searchPattern = '(_RST)'                
        foreach ($tbl in $TablesApiResult.value) { 
            try {
                if($tbl.name.Trim() -notmatch $searchPattern) {                    
                    $LATables += 
                        [pscustomobject]
                            @{
                                TableName=$tbl.name.Trim();
                                TablePlan=$tbl.properties.Plan.Trim();
                                TotalRetentionInDays=$tbl.properties.totalRetentionInDays;
                                ArchiveRetentionInDays=$tbl.properties.archiveRetentionInDays;
                                WorkspaceRetentionInDays=$tbl.properties.retentionInDays;
                            }  
                }
            }
            catch {
                Write-Log -Message "Error adding $tbl to collection" -LogFileName $LogFileName -Severity Error
            }
            	
        }
    }
	
    return $LATables | Where-Object {($_.TableName -notmatch '(AzureActivity|Usage)') } | Where-Object {($_.TablePlan -eq "Analytics")} | Sort-Object -Property TableName | Select-Object -Property TableName, RetentionInWorkspaceInDays, ArchiveRetentionInDays, TotalRetentionInDays, TablePlan
}

function Update-TablesRetention {
	[CmdletBinding()]
    param (        
        [parameter(Mandatory = $true)] $TablesForRetention		
    )

	$UpdatedTablesRetention = @()
    foreach($tbl in $TablesForRetention) {
        
		$TablesApi = "https://management.azure.com/subscriptions/$SubscriptionId/resourcegroups/$LogAnalyticsResourceGroup/providers/Microsoft.OperationalInsights/workspaces/$LogAnalyticsWorkspaceName/tables/$($tbl.TableName)" + "?api-version=2021-12-01-preview"

        $ArchiveRetentionInDays = [int]($tbl.ArchiveRetentionInDays)
        $WorkspaceRetentionInDays = [int]($tbl.WorkspaceRetentionInDays)
        $TotalRetentionInDays = [int]($tbl.TotalRetentionInDays)

        $TablesApiBody = @"
			{
				"properties": {
					"retentionInDays": $WorkspaceRetentionInDays,
                    "archiveRetentionInDays": $ArchiveRetentionInDays,
					"totalRetentionInDays": $TotalRetentionInDays
				}
			}
"@
		
        
		try {    
			$TablesApiResult = Invoke-RestMethod -Uri $TablesApi -Method "PUT" -Headers $LaAPIHeaders -Body $TablesApiBody			

            if($TablesApiResult) {
                    $UpdatedTablesRetention += 
                        [pscustomobject]@{
                            TableName=$TablesApiResult.name.Trim();
                            TablePlan=$TablesApiResult.properties.Plan.Trim();
                            TotalRetentionInDays=$TablesApiResult.properties.totalRetentionInDays;
                            ArchiveRetentionInDays=$TablesApiResult.properties.archiveRetentionInDays;
                            WorkspaceRetentionInDays=$TablesApiResult.properties.retentionInDays;
                        }
                    $tblname = $TablesApiResult.name.Trim()
                    $ttlRetention = $TablesApiResult.properties.totalRetentionInDays 
                    Write-Log -Message "Table : $tblname updated to TotalRetentionInDays: $ttlRetention days"  -LogFileName $LogFileName -Severity Information
            }
		} 
		catch {                    
			Write-Log -Message "Update-TablesRetention $($_)" -LogFileName $LogFileName -Severity Error		                
		}
	}
    return $UpdatedTablesRetention
}
function ProcessStop
{
    $TimeStamp = Get-Date -Format 'yyyy.MM.dd HH:mm:ss'
    $finishTime = "Process finished at: {0}" -f $TimeStamp
    Write-Output $finishTime
}
#endregion MainFunctions

#region MainProgram
$TimeStamp = Get-Date -Format 'yyyy.MM.dd HH:mm:ss'
$LogFileName = '{0}_{1}.csv' -f "Set-RetentionAndArchive", $TimeStamp
#Write-Output $LogFileName
$startTime = "Process started at: {0}" -f $TimeStamp
Write-Output $startTime

# Check Powershell version, needs to be 5 or higher
if ($host.Version.Major -lt 5) {
    Write-Log "Supported PowerShell version for this script is 5 or above" -LogFileName $LogFileName -Severity Error    
    exit
}

$TablesToBeUpdated = New-Object System.Collections.Generic.List[System.Object]

# Read JSON file
$content = Get-Content -Path $JSONfile

# Convert JSON file
$subsFromJson = $content | ConvertFrom-Json

$TenantId = $subsFromJson.TenantId
$SubscriptionId = $subsFromJson.subscriptionid
$LogAnalyticsResourceGroup = $subsFromJson.LogAnalyticsResourceGroup
$LogAnalyticsWorkspaceName = $subsFromJson.LogAnalyticsWorkspaceName
$TablePlan = $subsFromJson.tablePlan
$SetEntireLogAnalyticsWorkspace = $subsFromJson.SetEntireLogAnalyticsWorkspace
$TotalRetentionInDays = $subsFromJson.TotalRetentionInDays
$ArchiveRetentionInDays = $subsFromJson.ArchiveRetentionInDays
$WorkspaceRetentionInDays = $subsFromJson.WorkspaceRetentionInDays

# display JSON data
$content

if ($SetEntireLogAnalyticsWorkspace -eq "yes")
{
    if (($WorkspaceRetentionInDays + $ArchiveRetentionInDays) -ne $TotalRetentionInDays)
    {
        "JSON file has invalid values for retention and archive.  Please correct and try again. Will exit now."
        ProcessStop
        return
    }

    [string] $Response = Read-Host -Prompt "Based on JSON input data, we will update the entire Log Analytics Workspace? (Y/N)"
    if ($Response -ne 'Y')
    {
        "You have selected to not update Log Analytics Workspace Retention and Arßchive values. Please change the JSON if you do not want to update entire Log Analytics Workspace.."
        ProcessStop
        return
    }
    else 
    {
        $Response = Read-Host -Prompt "The Log Analytics Workspace will be updated with TotalRetentionInDays: $TotalRetentionInDays, WorkspaceRetentionInDays: $WorkspaceRetentionInDays, ArchiveRetentionInDays: $ArchiveRetentionInDays. Confirm? (Y/N)"
        if ($Response -ne 'Y')
        {
            "You have selected to do not update entire Log Analytics Workspace. Script will stop now."
            ProcessStop
            return
        }
    }
}
ELSE 
{
    $tableCount = ($subsFromJson.tables).Count
    [int] $i = 0

    #loop through each table in json file
    DO {
        if (($subsFromJson.tables[$i].WorkspaceRetentionInDays + $subsFromJson.tables[$i].ArchiveRetentionInDays) -ne $subsFromJson.tables[$i].TotalRetentionInDays)
    {
        $tblname = $subsFromJson.tables[$i].TableName
        "JSON file has invalid values for retention and archive (table: $tblname).  Please correct and try again. Will exit now."
        ProcessStop
        return
    }

        $TablesToBeUpdated +=
        [pscustomobject]@{
                            TableName = $subsFromJson.tables[$i].TableName;
                            TablePlan = $subsFromJson.TablePlan;
                            WorkspaceRetentionInDays = $subsFromJson.tables[$i].WorkspaceRetentionInDays;
                            ArchiveRetentionInDays = $subsFromJson.tables[$i].ArchiveRetentionInDays;
                            TotalRetentionInDays = $subsFromJson.tables[$i].TotalRetentionInDays;
                        }
        $i++
    }
    While ($i -lt $tableCount)

    #"JSON tables"
    Write-Host ($TablesToBeUpdated |Format-table |Out-String)
    "Number of tables to be updated:  $tableCount"

    [string] $Response = Read-Host -Prompt "Based on JSON data above tables from Log Analytics Workspace will be updated (new values displayed).  Confirm (Y/N)?"
    if ($Response -ne 'Y')
    {
        "You have selected to do not update the Retention and Archive days for all tables from the Log Analytics Workspace above. Script will stop now."
        ProcessStop
        return
    }
}

Try {
    #Connect to tenant with context name and save it to variable
    Connect-AzAccount -Tenant $TenantID -SubscriptionId $SubscriptionID -ContextName 'BVLAWContext' -Force -ErrorAction Stop        
}
catch {    
    Write-Log "Error When trying to connect to tenant : $($_)" -LogFileName $LogFileName -Severity Error
    ProcessStop
    exit    
}

$AzureAccessToken = (Get-AzAccessToken).Token            
$LaAPIHeaders = New-Object "System.Collections.Generic.Dictionary[[String],[String]]"
$LaAPIHeaders.Add("Content-Type", "application/json")
$LaAPIHeaders.Add("Authorization", "Bearer $AzureAccessToken")

try {
    #Set context for subscription being built
    $null = Set-AzContext -Subscription  $SubscriptionID

    if ($SetEntireLogAnalyticsWorkspace -eq "yes")
    {
        $TablesToBeUpdated = Get-LATables

        foreach ($obj in $TablesToBeUpdated)
        {
            $obj.WorkspaceRetentionInDays = $WorkspaceRetentionInDays
            $obj.ArchiveRetentionInDays = $ArchiveRetentionInDays
            $obj.TotalRetentionInDays = $TotalRetentionInDays
        }
    }

    $UpdatedTables = Update-TablesRetention -TablesForRetention $TablesToBeUpdated
}
catch [Exception]
{ 
    Write-Log -Message $_ -LogFileName $LogFileName -Severity Error    
    ProcessStop                     		
}		 

ProcessStop

#endregion mainProgram 
