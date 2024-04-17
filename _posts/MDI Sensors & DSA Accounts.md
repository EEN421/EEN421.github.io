# Unraveling the Complexities of Deploying Microsoft Defender for Identity Sensors and gMSA-based DSA Accounts

Deploying Microsoft Defender for Identity (MDI) sensors and leveraging a Group Managed Service Account (gMSA) for additional security to create a Domain Services Account (DSA) can often feel like navigating a labyrinth. These processes, critical to bolstering your organization's security infrastructure and getting the most coverage from MDI, come with their own set of challenges. Many of these issues are common and easily resolved. In this blog post, we will sidestep the most common obstacles and streamline your deployment process.

<br/>
<br/>

# What's a DSA and why is is ABSOLUTELY NECESSARY for MDI deployments?

A **Directory Service Account (DSA)** is used by **Microsoft Defender for Identity (MDI)** to connect to the domain controller and **query for data on entities seen in network traffic, monitored events, and monitored ETW activities**. Without a **DSA**, you _don't_ get the aforementioned coverage from **MDI**. A **DSA** is **required** for the following features and functionality:

- When working with a sensor installed on an **AD FS / AD CS server**.

- Requesting member lists for local administrator groups from devices seen in **network traffic, events, and ETW activities via a SAM-R call** made to the device. The collected data is used to calculate potential **lateral movement paths**.

- Accessing the **DeletedObjects** container to collect information about **deleted users** and **computers**.

- **Domain** and **trust mapping**, which occurs at sensor startup, and again every 10 minutes.

- Querying another domain via **LDAP** for details, when **detecting activities from entities in those other domains**.

- In an **untrusted, multi-forest environment,** a **DSA** account is required for **each forest**. One sensor in each domain is defined as the domain synchronizer, and is responsible for tracking changes to the entities in the domain.

Without a **DSA**, _no **MDI** deployment would be complete_ as it would lack the necessary **permissions** and **capabilities** to _fully_ monitor and protect the network. This is why it’s _absolutely, positively, crucial to set up a **DSA**_ for a comprehensive and effective MDI deployment.

<br/>
<br/>

# Why use a gMSA for your DSA? 

A Group Managed Service Account (gMSA) is considered **more secure than a regular service account** for several reasons including, but not limited to:

- **Automated Password Management**: The passwords for gMSAs are automatically generated and rotated by Windows. This eliminates the need for manual password management, which can often lead to security vulnerabilities if not handled properly1.

- **Strong Passwords**: The passwords for gMSAs are 240-byte, randomly generated passwords2. The complexity and length of these passwords minimize the likelihood of compromise by brute force or dictionary attacks.

- **Limited Access**: Only specific servers that are allowed to use the gMSA can retrieve the account’s password from Active Directory. This limits the potential for misuse and compromise.

In the context of Microsoft Defender for Identity, _using a **gMSA** for the Directory Service Account adds an **extra layer of security**_. The **gMSA DSA** is used by **MDI** to connect to the domain controller and _query for data on entities seen in **network traffic, monitored events, and monitored ETW activities**_.

By using a gMSA, the DSA benefits from the automated password management and strong password policies of the gMSA, reducing the risk of the DSA being compromised. This is particularly important in multi-forest, multi-domain environments, where a _unique gMSA DSA is recommended for each forest or domain_.

In conclusion, using a gMSA for the DSA in MDI provides a more secure and manageable solution compared to using a regular service account. I rest my case. 

<br/>
<br/>

# How do I create a DSA for MDI? 

There's a couple different ways to peel this potato, depending on your domain infrastructure. There are essentially 2 parts to creating a gMSA to use as the DSA for MDI: 

**1. Create gMSA:**
The script prompts the user for the domain and a name for the DSA, then sets the HostsGroup to the default Domain Controllers Organizational Unit (OU), and creates a new gMSA with the provided details.

**2. Grant Permissions:**
It also retrieves the distinguished name for Deleted Objects and makes the current user the owner before. Finally, it assigns read permissions for Deleted Objects to the DSA account. 

For smaller, simpler setups (a handful of DC's), I wrote a PowerShell script is designed to facilitate simple deployments on a single domain by creating a Group Managed Service Account (gMSA) and granting it the necessary read privileges for use as a Directory Service Account (DSA) in Microsoft Defender for Identity. **This script is particularly useful for automating the setup of a gMSA for use as a DSA for smaller MDI deployments:**

```powershell 

# Author: Ian D. Hanley | LinkedIn: /in/ianhanley/ | Twitter: @IanDHanley
# Github: https://github.com/EEN421
# Website: www.hanleycloudsolutions.com
# Blog: Hanley.cloud / DevSecOpsDad.com

# Description: This script is helpful for simple deployments on a single domain. It creates a gMSA and grants it the required read privileges for use as a DSA in Defender for Identity

# Step 1: Prompt the user for the domain and a name for the DSA that will be created in step 3.
# Validate that the domain and gMSA account name are provided and meet the naming conventions.
$domain = Read-Host -Prompt "Please enter the domain"
$gmsaAccountName = Read-Host -Prompt "Please enter the gMSA account name"

# Step 2: Set HostsGroup to Default Domain Controllers OU (this way, this automatically applies to newly added DCs and reduces overhead)
$gMSA_HostsGroup = Get-ADGroup -Identity 'Domain Controllers'

# Step 3: Create new gMSA using Read-Host input from above statements:
New-ADServiceAccount -Name "$gmsaAccountName" -DNSHostName "$gmsaAccountName.$domain" -PrincipalsAllowedToRetrieveManagedPassword $gMSA_HostsGroup

# Step 4: Grab distinguished name for Deleted Objects
$distinguishedName = ([adsi]'').distinguishedName.Value
$deletedObjectsDN = "CN=Deleted Objects,$distinguishedName"

# Step 5: Make current user the Owner of Deleted Objects (required for next step)
dsacls.exe "$deletedObjectsDN" /takeOwnership

# Step 6: Assign read permissions for Deleted Objects to DSA account
# This requires current user account to have ownership (see previous command)
dsacls.exe "$deletedObjectsDN" /G "$domain\$gmsaAccountName:LCRP"

```

<br/>
<br/>

The other, more advanced and scalable script is designed to facilitate custom setups for advanced, multi-domain environments in the context of Microsoft Defender for Identity (MDI). It allows the user to specify a HostGroup and the domain controllers with the MDI sensor installed, and prompts the user for the domain, a name for the group of domain controllers, and a name for the Group Managed Service Account (gMSA). It then prompts the user for the principals (domain controllers with the MDI sensor installed) allowed to retrieve the password/use the gMSA on behalf of MDI to gain additional insights. After importing the required Active Directory module, the script creates a new group, adds the specified members to it, and then creates a new gMSA associated with it. **This is particularly useful for automating the setup of Directory Service Accounts (DSAs) in MDI deployments across multiple domains:**

```powershell

# Author: Ian D. Hanley | LinkedIn: /in/ianhanley/ | Twitter: @IanDHanley
# Github: https://github.com/EEN421
# Website: www.hanleycloudsolutions.com
# Blog: Hanley.cloud / DevSecOpsDad.com

# Description: This script facilitates a custom setup for more advanced, multi-domain environments by allowing the user specify a HostGroup and DC's with the MDI sensor installed.
# Note: In a multi-domain environment, it's best practice to leverage separate gMSA's per domain to act as DSA's for MDI.

# Step 1: Prompt the user for the domain and a name for the DSA that will be created in step 4:
$domain = Read-Host -Prompt "Please enter the domain"
$DSA_HostsGroupName = Read-Host -Prompt "Please enter a name for your group of DC's"
$DSA_AccountName = Read-Host -Prompt "Please enter a name for your gMSA account"

# Step 2: Prompt the user for the principals allowed to retrieve the password (principals will be your domain controllers with the MDI sensor installed):
$principals = Read-Host -Prompt "Please enter the principals (separated by a comma)"
$principalsArray = $principals -split ',' | ForEach-Object { $_.Trim() }

# Step 3: Import the required PowerShell module:
Import-Module ActiveDirectory

# Step 4: Create the group and add the members
$DSA_HostsGroup = New-ADGroup -Name $DSA_HostsGroupName -GroupScope Global -PassThru
$principalsArray | ForEach-Object { Get-ADComputer -Identity $_ } |
    ForEach-Object { Add-ADGroupMember -Identity $DSA_HostsGroupName -Members $_ }

# Step 5: Create the gMSA and associate it with the group:
New-ADServiceAccount -Name $DSA_AccountName -DNSHostName "$DSA_AccountName.$domain" -PrincipalsAllowedToRetrieveManagedPassword $DSA_HostsGroup

```

<br/>
<br/>


# Compare & Contrast - Why are there 2 Scripts Anyway? 

The second script is more scalable than the first one because it is designed for more advanced, multi-domain environments. It allows the user to specify a HostGroup and the domain controllers with the Microsoft Defender for Identity (MDI) sensor installed. This flexibility makes it more adaptable to larger, more complex network environments.

In contrast, the first script is designed for simple deployments on a single domain. It sets the HostGroup to the default Domain Controllers Organizational Unit (OU), which automatically applies to newly added domain controllers. While this is efficient for a single domain, it may not scale well for multi-domain environments.

Furthermore, the second script prompts the user for the principals (domain controllers with the MDI sensor installed) allowed to retrieve the password. This feature provides additional flexibility and security in multi-domain environments, where different domain controllers may need access to the gMSA.

In summary, the second script’s ability to handle multiple domains, specify different HostGroups and principals, and its flexibility in managing gMSA accounts make it more scalable for larger or more complex environments compared to the first script.

<br/>
<br/>

# Confirming your DSA - Making sure the script worked

To test the functionality of a Group Managed Service Account (gMSA) to be used as a Directory Service Account (DSA) in Microsoft Defender for Identity (MDI), you can run the below script which installs and imports the **DefenderForIdentity module**, then prompts the user to specify the gMSA to test. It checks whether the gMSA works on the current domain controller, returns a list of other principals or domain controllers that can use this gMSA, and tests the DSA identity with a detailed switch. **This script is particularly useful for troubleshooting and validating the setup of DSAs in MDI deployments.**

```powershell

# Author: Ian D. Hanley | LinkedIn: /in/ianhanley/ | Twitter: @IanDHanley
# Github: https://github.com/EEN421
# Website: www.hanleycloudsolutions.com
# Blog: Hanley.cloud / DevSecOpsDad.com

# Description: This script prompts for the gMSA used as the Directory Service Account (DSA) for your domain in Defender for Identity (MDI)

# Install & import DFI module:
Install-Module DefenderForIdentity
Import-Module DefenderForIdentity

# Print new line to console:
Write-Host "`n"
 
# Prompt for gMSA to test:
$identity = Read-Host -Prompt 'Please specify gMSA to test against'

# Test on this DC: 
Write-Host "`nDoes this gMSA work on this DC (true/false)?" 
Test-ADServiceAccount -Identity $identity

# Return a list of other principles/DC's that can use this gMSA:
Write-Host "`nPrinciples allowed to retrieve the PW for this gMSA?"
(Get-ADServiceAccount -Identity $identity -Properties *).PrincipalsAllowedToRetrieveManagedPassword
 
# Test DSA Identity with -Detailed switch:
Write-Host "`nThe following is applicable only to Directory Service Accounts (DSA):" 
Test-MDIDSA -Identity $identity -Detailed 

```