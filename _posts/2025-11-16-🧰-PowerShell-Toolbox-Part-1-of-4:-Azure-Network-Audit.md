# Introduction & Use Case: 
Welcome to the very first entry in my new 🧰 PowerShell Toolbox series — a four-part deep-dive built for cloud engineers, security architects, auditors, and anyone who’s ever inherited an Azure environment held together by duct tape and wishful thinking. If you’ve ever been asked, “Hey, can you tell us how this thing is actually networked?” — this script is your new best friend.

Azure’s network layer is incredibly powerful, but it’s scattered across VNets, NSGs, Firewalls, Gateways, App Gateways, ExpressRoute, and a dozen different portal blades. Trying to manually stitch that together? Pure pain. 😵‍💫🧵 This script flips the table on that chaos by giving you one clean CSV containing your entire network topology plus every relevant security configuration across the subscription. 📊✨ It’s a must-have for audits, onboarding, incident response, or pre-migration planning. 🚀🛡️📋

...And this is just Part 1; In the coming chapters of the series, we’ll dig into:

🔐 Part 2 — Privileged RBAC Roles Audit Script:
A complete breakdown of who has elevated access in your tenant, what they can do, and why it matters during compliance checks like NIST, CMMC, and CIS.

🏛️ Part 3 — GPO HTML Export Script:
A one-click way to inventory every Group Policy Object in your environment — perfect for Windows hardening, AD modernization efforts, and compliance documentation.

🧹 Part 4 — Invoke-ScriptAnalyzer for Real-World Ops:
How to lint your own PowerShell code like a pro, avoid sloppy mistakes, and build secure, production-ready tooling that won’t embarrass you during peer review.

So buckle up — this series is all about turning your day-to-day operational chaos into clean, automated clarity. Let’s dive into Part 1 and map the network like a pro. 💪🗺️

### ⚡ Grab the full script here 👇 **[https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1)** 

<br/>
<br/>

![](/assets/img/Powershell%20Toolbox%201/Red_Toolbox.jpg)

<br/>
<br/>
<br/>
<br/>

# 🎯 What This Script Actually Does

This script performs a full subscription-wide network inventory by collecting:

- Network Security Group Rules
- Virtual Networks and Subnets
- VPN Gateways
- VPN Connections
- Azure Firewall Network Rules
- Application Gateway Listeners
- ExpressRoute Circuits

It flattens all findings into a unified schema and exports to the following output:
```powershell
C:\AzureNetworkReport\AzureNetworkInventory.csv
C:\AzureNetworkReport\AzureNetworkReport.zip
```
This CSV becomes a one-stop view of your entire Azure network — perfect for CIS audits, security reviews, architectural mapping, segmentation validation, dataflow documentation, or just learning what you’re actually working with.

![](/assets/img/Powershell%20Toolbox%201/Results.png)

<br/>
<br/>

### ⚡ Check out the full script here 👇 **[https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1)** 

<br/>
<br/>
<br/>
<br/>

# 🛠️ Why This Script Belongs in Your Assessment Workflow

If you're doing any of these:

- CIS Azure Foundations Benchmark
- NIST 800-53 security control validation
- CMMC Level 2 prep
- SOC 2 / ISO 27001 evidence gathering
- Azure landing zone “as-is” discovery
- MSSP onboarding of a new client environment
- Incident response after suspicious network activity
- Cloud migration planning
- Hybrid connectivity mapping

…this script turns hours of clicking into minutes of automated clarity.

<br/>
<br/>

**Instead of:**

- Clicking 10+ NSGs hoping you didn’t miss a rule
- Hunting through Application Gateway listeners
- Trying to find the ExpressRoute peering details
- Wondering which subnets live in which VNet
- Searching through the portal for that one VPN gateway named “Test-Gw-Old-DoNotDelete”

_You get a single CSV with every detail flattened and ready to filter...👇_

<br/>
<br/>

![](/assets/img/Powershell%20Toolbox%201/Conveyor.jpg)

<br/>
<br/>
<br/>
<br/>

# ⚙️ Full Technical Breakdown (Every Section Explained)

Below is a line-by-line breakdown (You can view the entire script on my GitHub here 👉 **[https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1)**):

## 1). Output Paths and Folder Setup

```powershell
$OutputDir = "C:\AzureNetworkReport"
$ZipPath = "$OutputDir\AzureNetworkReport.zip"
$CombinedCsv = "$OutputDir\AzureNetworkInventory.csv"

New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
```

### What this does:

Creates a local folder where all results will be stored and defines paths for:
- The final CSV
- The zipped version of that CSV

Then it force ensures the folder is created even if it already exists. Output is suppressed using Out-Null for cleanliness

<br/>
<br/>

## 2). Azure Login + Subscription Selection UI
```powershell
Connect-AzAccount -ErrorAction SilentlyContinue
```
☝️ Signs you into Azure & Silently ignores the error if you're already authenticated

<br/>

```powershell
$subs = Get-AzSubscription | Sort-Object Name
$selection = $subs | Out-GridView -Title "Select Azure Subscription" -PassThru
```

☝️ Retrieves all subscriptions your account can access & Sorts them alphabetically. Also uses Out-GridView (a pop-up GUI picker) to let you choose the subscription; PassThru returns your selection.

<br/>

```powershell
if (-not $selection) {
    Write-Warning "No subscription selected. Exiting."
    return
}
Set-AzContext -SubscriptionId $selection.Id
$subName = $selection.Name
```

☝️ Exits gracefully if you cancel the picker and sets the active Azure context to that subscription, then stores the subscription name for CSV tagging.

<br/>
<br/>

## 3). Inventory Array Initialization
```powershell
$inventory = @()
```

☝️ This creates an empty PowerShell array that will store every row of data we gather. Each network object will become a standardized PSCustomObject and be appended here.

<br/>
<br/>

## 4). Resource Group Discovery Loop

```powershell
$resourceGroups = Get-AzResourceGroup
foreach ($rg in $resourceGroups) {
    $rgName = $rg.ResourceGroupName
    Write-Host "Processing RG: $rgName" -ForegroundColor Yellow
```

- Lists all RGs in the subscription
- Loops through each RG
- Writes a yellow status message (nice touch for readability)

👉 Inside this loop, the script collects seven categories of network data.

<br/>
<br/>

## 5). NSG Rule Collection
```powershell
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
```

### What it does:

- Grabs all NSGs in the RG
- Loops through every security rule
- Adds one CSV row per rule

### Why it matters

It's perfect for:
- Finding insecure inbound rules
- Identifying overly broad outbound controls
- CIS 4.1 validation
- Zero trust network cleanup

<br/>
<br/> 

## 6). Virtual Networks & Subnet Collection
```powershell
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
```

### What this captures:

- VNet name, region, full address space
- Subnet names + their CIDR blocks

### Why it's useful:
- Helps detect overlapping ranges
- Validates segmentation
- Helps build network diagrams
- Required for NIST/CIS segmentation controls

<br/>
<br/>
<br/>
<br/>

## 7. VPN Gateways
```powershell
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
```

### Key fields:

- Gateway Type (Vpn, ExpressRoute)
- VPN Type (RouteBased, PolicyBased)
- SKU
- Whether BGP is enabled

### Why this matters:

- Required for hybrid connectivity mapping
- Useful in incident response or route debugging

<br/>
<br/>
<br/>
<br/>

## 8. VPN Connections
```powershell 
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
```

> ⚠️ **Important**: ☝️ This exports the **shared key**, which is **sensitive**‼️

<br/>
<br/>
<br/>
<br/>

## 9. Azure Firewall Rules

```powershell
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
```

### What it captures:

- Network rule collections
- Individual rules
- Protocols, source addresses, destinations, ports

### Useful for:

- Firewall audits
- North/south and east/west flow validation
- Identifying overly-permissive rules

<br/>
<br/>
<br/>
<br/>

## 10. Application Gateway Listeners
```powershell
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
```

This documents every public-facing listener in the tenant.

### Important for:

- Reviewing HTTP→HTTPS enforcement
- Seeing what hostnames are exposed
- Mapping ingress points

<br/>
<br/>
<br/>
<br/>

## 11. ExpressRoute Circuits
```powershell
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
```

### This captures:

- Tier (Standard/Premium)
- Provider
- Peering location
- Bandwidth
- Provisioning state

<br/>
<br/>
<br/>
<br/>

## 12. Export and ZIP the Results

```powershell
$inventory | Export-Csv -Path $CombinedCsv -NoTypeInformation
```

☝️Writes the full inventory into a clean CSV with headers☝️

<br/>

```powershell
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $CombinedCsv -DestinationPath $ZipPath
```

☝️Removes old ZIP if it exists, then creates a new one containing the CSV☝️

<br/>

```powershell
Write-Host "`n✅ All results written to: $CombinedCsv"
Write-Host "📦 Zipped as: $ZipPath" -ForegroundColor Green
```

☝️Friendly success message — because good scripts should be human-friendly.☝️

<br/>
<br/>
<br/>
<br/>

# ▶️ How to Run This Script (Step-By-Step)

### 1. Built-in roles that work

Any of these (at subscription scope) is sufficient:

- **Reader** – can **view** _all resources, **no changes**_. This already includes all */read operations on Microsoft.Network resources. 

- **Network Reader** – can **view all networking resources** (VNets, NSGs, gateways, ExpressRoute, etc.), but **not non-network resources**. For this script, **Network Reader + the ability to list the subscription itself** is functionally equivalent. 

In most client environments, I ask for:

“Reader on the target subscription (or Network Reader + rights to list the subscription).”

That’s all you really need.

<br/>

### 2. Permission matrix (cmdlet → resource → actions)

If you (or a client) want a custom **least-privilege** role instead of the generic Reader role, here’s the breakdown by script section (because you know we're all about zero-trust and principle of least privilige in this house 😎).

| Script area / cmdlet                                       | Azure resource type                              | Required RBAC actions (minimum)                                                                                                                          | Covered by built-in roles?                         |
| ---------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `Connect-AzAccount`, `Get-AzSubscription`, `Set-AzContext` | Subscription                                     | `Microsoft.Resources/subscriptions/read`                                                                                                                 | Reader, Network Reader* ([Microsoft Learn][1])     |
| `Get-AzResourceGroup`                                      | Resource groups                                  | `Microsoft.Resources/subscriptions/resourceGroups/read`                                                                                                  | Reader, Network Reader* ([Azure Documentation][2]) |
| `Get-AzNetworkSecurityGroup` + rules                       | NSGs & rules                                     | `Microsoft.Network/networkSecurityGroups/read`  + `Microsoft.Network/networkSecurityGroups/securityRules/read`                                           | Reader, Network Reader ([Microsoft Learn][3])      |
| `Get-AzVirtualNetwork` + subnets                           | VNets & subnets                                  | `Microsoft.Network/virtualNetworks/read` + `Microsoft.Network/virtualNetworks/subnets/read`                                                              | Reader, Network Reader ([Microsoft Learn][3])      |
| `Get-AzVirtualNetworkGateway`                              | Virtual network gateways                         | `Microsoft.Network/virtualNetworkGateways/read`                                                                                                          | Reader, Network Reader ([Microsoft Learn][3])      |
| `Get-AzVirtualNetworkGatewayConnection`                    | VPN connections                                  | `Microsoft.Network/connections/read` (and/or `Microsoft.Network/virtualNetworkGatewayConnections/read`, depending on API version) ([Microsoft Learn][4]) | Reader, Network Reader                             |
| `Get-AzFirewall`                                           | Azure Firewall                                   | `Microsoft.Network/azureFirewalls/read`                                                                                                                  | Reader, Network Reader ([Microsoft Learn][3])      |
| `Get-AzApplicationGateway`                                 | Application Gateways                             | `Microsoft.Network/applicationGateways/read`                                                                                                             | Reader, Network Reader ([Microsoft Learn][3])      |
| `Get-AzExpressRouteCircuit`                                | ExpressRoute Circuits                            | `Microsoft.Network/expressRouteCircuits/read`                                                                                                            | Reader, Network Reader ([Microsoft Learn][5])      |
| (all of the above, subscription-wide)                      | All selected resource groups in the subscription | `Microsoft.Resources/subscriptions/resourcegroups/resources/read` (to enumerate resources within RGs)                                                    | Reader, Network Reader ([Azure Documentation][2])  |

<!--Table Links-->
[1]: https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles "Azure built-in roles"
[2]: https://docs.azure.cn/en-us/role-based-access-control/resource-provider-operations "Azure permissions - Azure RBAC"
[3]: https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/networking "Azure permissions for Networking"
[4]: https://learn.microsoft.com/en-us/powershell/module/az.network/get-azvirtualnetworkgatewayconnection?view=azps-14.6.0 "Get-AzVirtualNetworkGatewayConnection (Az.Network)"
[5]: https://learn.microsoft.com/en-us/azure/expressroute/roles-permissions "About ExpressRoute roles and permissions"


> ⚠️ **Network Reader** is a networking-scoped role; to _actually see the subscription in your tools,_ users _still need enough rights_ to **enumerate that subscription** (granted as part of the role assignment at subscription scope).

<br/>
<br/>
<br/>
<br/>

### 1. Install modules
```powershell
Install-Module Az -Scope CurrentUser
```
<br/>

### 2. Save script as:
```powershell 
C:\Scripts\Cloud_Network_Assessment.ps1
```
<br/>

### 3. Run it:
```powershell
Set-Location C:\Scripts
.\Cloud_Network_Assessment.ps1
```
<br/>

### 4. Select subscription via GUI

- A pop-up appears. Click → choose your sub → OK.

<br/>

### 5. Script runs and collects everything

- It prints each RG being processed.

<br/>

### 6. Results appear here:
```bash
C:\AzureNetworkReport\
```

<br/>
<br/>
<br/>
<br/>

# 🎉 Final Thoughts

This script is exactly the kind of tool I wish Microsoft shipped out-of-the-box. It lets you understand your environment in minutes, not hours. It’s perfect for:

- Rapid onboarding of new clients
- Audit prep
- Incident response
- Network redesign planning
- Governance and segmentation reviews

<br/>

### 🔜 Up Next in the PowerShell Toolbox Series

Now that you’ve mapped the entire Azure network with a single script, the next logical question is: “Okay… but who actually has the keys to all of this?” That’s exactly where we’re headed in Part 2 of the PowerShell Toolbox series. We’ll break down a purpose-built RBAC Privileged Roles Audit script that cuts through the noise and surfaces every user, group, and service principal with elevated access across your subscription — along with why that visibility is crucial for NIST, CMMC, CIS, and even day-to-day operational sanity. 🔐✨

### Stay tuned — if Part 1 showed you how the environment is wired, Part 2 will show you who can flip the switches on RBAC roles.

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

# 🔗 References (good to keep handy)

- [Cloud_Network_Assessment.ps1](https://github.com/EEN421/Powershell-Stuff/blob/Main/Tools/Cloud_Network_Assessment.ps1)
- [Azure built-in roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
- [Azure permissions - Azure RBAC](https://docs.azure.cn/en-us/role-based-access-control/resource-provider-operations)
- [Azure permissions for Networking](https://learn.microsoft.com/en-us/azure/role-based-access-control/permissions/networking)
- [Get-AzVirtualNetworkGatewayConnection (Az.Network)](https://learn.microsoft.com/en-us/powershell/module/az.network/get-azvirtualnetworkgatewayconnection?view=azps-14.6.0)
- [About ExpressRoute roles and permissions](https://learn.microsoft.com/en-us/azure/expressroute/roles-permissions)
- [👻 The Ghosts Hiding In Every Network: End Of Life Devices And Software ☠️](https://www.hanley.cloud/2025-11-03-The-Ghosts-Hiding-in-Every-Network-End-of-Life-Devices-and-Software/)

<br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)