# 🧰 PowerShell Toolbox
If you’ve ever inherited a messy Azure environment and someone asked, “Hey, can you tell us how this thing is actually networked?” — this script is for you. 🧰🔍
Azure’s network layer is incredibly powerful, but it’s scattered across VNets, NSGs, Firewalls, Gateways, App Gateways, ExpressRoute, and dozens of blades in the portal. Trying to manually stitch all that together? Pure pain. 😵‍💫🧵
This script flips the table on that chaos by giving you one clean CSV containing your entire network topology + security configuration across the subscription. 📊✨
This belongs in every cloud engineer’s, security architect’s, and consultant’s toolkit — especially during audits, onboarding, incident response, or pre-migration planning. 🚀🛡️📋
Let’s break it all down.

<br/>
<br/>
<br/>
<br/>

# 🎯 What This Script Actually Does

This script performs a full subscription-wide network inventory by collecting:

Network Security Group Rules

Virtual Networks and Subnets

VPN Gateways

VPN Connections

Azure Firewall Network Rules

Application Gateway Listeners

ExpressRoute Circuits

It flattens all findings into a unified schema and exports:

C:\AzureNetworkReport\AzureNetworkInventory.csv
C:\AzureNetworkReport\AzureNetworkReport.zip


This CSV becomes a one-stop view of your entire Azure network — perfect for CIS audits, security reviews, architectural mapping, segmentation validation, dataflow documentation, or just learning what you’re actually working with.

<br/>
<br/>
<br/>
<br/>

# 🛠️ Why This Script Belongs in Your Assessment Workflow

If you're doing any of these:

CIS Azure Foundations Benchmark

NIST 800-53 security control validation

CMMC Level 2 prep

SOC 2 / ISO 27001 evidence gathering

Azure landing zone “as-is” discovery

MSSP onboarding of a new client environment

Incident response after suspicious network activity

Cloud migration planning

Hybrid connectivity mapping

…this script turns hours of clicking into minutes of automated clarity.

Instead of:

Clicking 10+ NSGs hoping you didn’t miss a rule

Hunting through Application Gateway listeners

Trying to find the ExpressRoute peering details

Wondering which subnets live in which VNet

Searching through the portal for that one VPN gateway named “Test-Gw-Old-DoNotDelete”

You get a single CSV with every detail flattened and ready to filter.

<br/>
<br/>
<br/>
<br/>

# ⚙️ Full Technical Breakdown (Every Section Explained)

Below is a line-by-line understanding of the entire script so you can explain it clearly in your article.

1. Output Paths and Folder Setup
$OutputDir = "C:\AzureNetworkReport"
$ZipPath = "$OutputDir\AzureNetworkReport.zip"
$CombinedCsv = "$OutputDir\AzureNetworkInventory.csv"

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null


What this does:

Creates a local folder where all results will be stored

Defines paths for:

The final CSV

The zipped version of that CSV

-Force ensures the folder is created even if it already exists

Output is suppressed using Out-Null for cleanliness

<br/>
<br/>

2. Azure Login + Subscription Selection UI
Connect-AzAccount -ErrorAction SilentlyContinue


Signs you into Azure

Silently ignores the error if you're already authenticated

$subs = Get-AzSubscription | Sort-Object Name
$selection = $subs | Out-GridView -Title "Select Azure Subscription" -PassThru


Retrieves all subscriptions your account can access

Sorts them alphabetically

Uses Out-GridView (a pop-up GUI picker) to let you choose the subscription

-PassThru returns your selection

if (-not $selection) {
    Write-Warning "No subscription selected. Exiting."
    return
}
Set-AzContext -SubscriptionId $selection.Id
$subName = $selection.Name


Exits gracefully if you cancel the picker

Sets the active Azure context to that subscription

Stores the subscription name for CSV tagging

<br/>
<br/>

3. Inventory Array Initialization
$inventory = @()


This creates an empty PowerShell array that will store every row of data we gather.

Each network object will become a standardized PSCustomObject and be appended here.

4. Resource Group Discovery Loop
$resourceGroups = Get-AzResourceGroup
foreach ($rg in $resourceGroups) {
    $rgName = $rg.ResourceGroupName
    Write-Host "Processing RG: $rgName" -ForegroundColor Yellow


Lists all RGs in the subscription

Loops through each RG

Writes a yellow status message (nice touch for readability)

Inside this loop, the script collects seven categories of network data.

5. NSG Rule Collection
$nsgs = Get-AzNetworkSecurityGroup -ResourceGroupName $rgName -ErrorAction SilentlyContinue
foreach ($nsg in $nsgs) {
    foreach ($rule in $nsg.SecurityRules) {
        $inventory += [PSCustomObject]@{
            Subscription      = $subName
            ResourceGroup     = $rgName
            ResourceType      = "NetworkSecurityRule"
            ResourceName      = "$($nsg.Name) - $($rule.Name)"
            Detail1           = "Direction: $($rule.Direction)"
            Detail2           = "Protocol: $($rule.Protocol)"
            Detail3           = "Src: $($rule.SourceAddressPrefix):$($rule.SourcePortRange)"
            Detail4           = "Dst: $($rule.DestinationAddressPrefix):$($rule.DestinationPortRange)"
            AdditionalDetails = "Access: $($rule.Access); Priority: $($rule.Priority)"
        }
    }
}

What it does

Grabs all NSGs in the RG

Loops through every security rule

Adds one CSV row per rule

Why it matters

Perfect for:

Finding insecure inbound rules

Identifying overly broad outbound controls

CIS 4.1 validation

Zero trust network cleanup

6. Virtual Networks & Subnet Collection
$vnets = Get-AzVirtualNetwork -ResourceGroupName $rgName -ErrorAction SilentlyContinue
foreach ($vnet in $vnets) {
    foreach ($subnet in $vnet.Subnets) {
        $inventory += [PSCustomObject]@{
            Subscription      = $subName
            ResourceGroup     = $rgName
            ResourceType      = "VNetSubnet"
            ResourceName      = "$($vnet.Name)/$($subnet.Name)"
            Detail1           = "Location: $($vnet.Location)"
            Detail2           = "AddressSpace: $($vnet.AddressSpace.AddressPrefixes -join ', ')"
            Detail3           = "SubnetPrefix: $($subnet.AddressPrefix)"
            Detail4           = ""
            AdditionalDetails = ""
        }
    }
}

What this captures:

VNet name, region, full address space

Subnet names + their CIDR blocks

Why it's useful:

Helps detect overlapping ranges

Validates segmentation

Helps build network diagrams

Required for NIST/CIS segmentation controls

<br/>
<br/>
<br/>
<br/>

7. VPN Gateways
$gateways = Get-AzVirtualNetworkGateway -ResourceGroupName $rgName -ErrorAction SilentlyContinue
foreach ($gw in $gateways) {
    $inventory += [PSCustomObject]@{
        Subscription      = $subName
        ResourceGroup     = $rgName
        ResourceType      = "VirtualNetworkGateway"
        ResourceName      = $gw.Name
        Detail1           = "Type: $($gw.GatewayType)"
        Detail2           = "VPN Type: $($gw.VpnType)"
        Detail3           = "Sku: $($gw.Sku.Name)"
        Detail4           = "Enable BGP: $($gw.EnableBgp)"
        AdditionalDetails = ""
    }
}

Key fields:

Gateway Type (Vpn, ExpressRoute)

VPN Type (RouteBased, PolicyBased)

SKU

Whether BGP is enabled

Why this matters:

Required for hybrid connectivity mapping

Useful in incident response or route debugging

<br/>
<br/>
<br/>
<br/>

8. VPN Connections
$connections = Get-AzVirtualNetworkGatewayConnection -ResourceGroupName $rgName -ErrorAction SilentlyContinue
foreach ($conn in $connections) {
    $inventory += [PSCustomObject]@{
        Subscription      = $subName
        ResourceGroup     = $rgName
        ResourceType      = "VPNConnection"
        ResourceName      = $conn.Name
        Detail1           = "Type: $($conn.ConnectionType)"
        Detail2           = "Enable BGP: $($conn.EnableBgp)"
        Detail3           = "Shared Key: $($conn.SharedKey)"
        Detail4           = "VNetGW1: $($conn.VirtualNetworkGateway1.Id)"
        AdditionalDetails = "VNetGW2: $($conn.VirtualNetworkGateway2.Id)"
    }
}

Important:

This exports the shared key, which is sensitive.
Call this out in your article.

9. Azure Firewall Rules
$firewalls = Get-AzFirewall -ResourceGroupName $rgName -ErrorAction SilentlyContinue
foreach ($fw in $firewalls) {
    foreach ($rc in $fw.NetworkRuleCollections) {
        foreach ($rule in $rc.Rules) {
            $inventory += [PSCustomObject]@{
                Subscription      = $subName
                ResourceGroup     = $rgName
                ResourceType      = "AzureFirewallRule"
                ResourceName      = "$($fw.Name) - $($rule.Name)"
                Detail1           = "Collection: $($rc.Name)"
                Detail2           = "Protocols: $($rule.Protocols -join ', ')"
                Detail3           = "Src: $($rule.SourceAddresses -join ', ')"
                Detail4           = "Dst: $($rule.DestinationAddresses -join ', '):$($rule.DestinationPorts -join ', ')"
                AdditionalDetails = ""
            }
        }
    }
}

What it captures:

Network rule collections

Individual rules

Protocols, source addresses, destinations, ports

Useful for:

Firewall audits

North/south and east/west flow validation

Identifying overly-permissive rules

10. Application Gateway Listeners
$appgws = Get-AzApplicationGateway -ResourceGroupName $rgName -ErrorAction SilentlyContinue
foreach ($ag in $appgws) {
    foreach ($listener in $ag.HttpListeners) {
        $inventory += [PSCustomObject]@{
            Subscription      = $subName
            ResourceGroup     = $rgName
            ResourceType      = "ApplicationGatewayListener"
            ResourceName      = "$($ag.Name)/$($listener.Name)"
            Detail1           = "Protocol: $($listener.Protocol)"
            Detail2           = "HostName: $($listener.HostName)"
            Detail3           = "FrontendPort: $($listener.FrontendPort.Id)"
            Detail4           = ""
            AdditionalDetails = ""
        }
    }
}


This documents every public-facing listener in the tenant.
Important for:

Reviewing HTTP→HTTPS enforcement

Seeing what hostnames are exposed

Mapping ingress points

11. ExpressRoute Circuits
$circuits = Get-AzExpressRouteCircuit -ResourceGroupName $rgName -ErrorAction SilentlyContinue
foreach ($circuit in $circuits) {
    $inventory += [PSCustomObject]@{
        Subscription      = $subName
        ResourceGroup     = $rgName
        ResourceType      = "ExpressRouteCircuit"
        ResourceName      = $circuit.Name
        Detail1           = "Sku: $($circuit.Sku.Tier) - $($circuit.Sku.Family)"
        Detail2           = "Provider: $($circuit.ServiceProviderProperties.ServiceProviderName)"
        Detail3           = "Peering: $($circuit.ServiceProviderProperties.PeeringLocation)"
        Detail4           = "Bandwidth: $($circuit.ServiceProviderProperties.BandwidthInMbps) Mbps"
        AdditionalDetails = "State: $($circuit.ProvisioningState)"
    }
}


This captures:

Tier (Standard/Premium)

Provider

Peering location

Bandwidth

Provisioning state

<br/>
<br/>
<br/>
<br/>

12. Export and ZIP the Results
$inventory | Export-Csv -Path $CombinedCsv -NoTypeInformation


Writes the full inventory into a clean CSV with headers

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $CombinedCsv -DestinationPath $ZipPath


Removes old ZIP if it exists

Creates a new one containing the CSV

Write-Host "`n✅ All results written to: $CombinedCsv"
Write-Host "📦 Zipped as: $ZipPath" -ForegroundColor Green


Friendly success message — because good scripts should be human-friendly.

<br/>
<br/>
<br/>
<br/>

# ▶️ How to Run This Script (Step-By-Step)
1. Install modules
Install-Module Az -Scope CurrentUser

2. Save script as:
C:\Scripts\Cloud_Network_Assessment.ps1

3. Run it:
Set-Location C:\Scripts
.\Cloud_Network_Assessment.ps1

4. Select subscription via GUI

A pop-up appears. Click → choose → OK.

5. Script runs and collects everything

It prints each RG being processed.

6. Results appear here:
C:\AzureNetworkReport\

<br/>
<br/>
<br/>
<br/>

# 🎉 Final Thoughts

This script is exactly the kind of tool I wish Microsoft shipped out-of-the-box. It lets you understand your environment in minutes, not hours. It’s perfect for:

Rapid onboarding of new clients

Audit prep

Incident response

Network redesign planning

Governance and segmentation reviews
