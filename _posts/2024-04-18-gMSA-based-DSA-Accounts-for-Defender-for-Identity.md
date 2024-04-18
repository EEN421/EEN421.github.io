# Introduction & Use Case:
Leveraging Group Managed Service Accounts (gMSA) for use as the Domain Service Accounts (DSA) in your Defender for Identity deployments provides enhanced security and maximizes your coverage. In this blog post, we will breakdown and streamline gMSA account creation for use as a DSA for both large and small MDI deployments. 

<br/>
<br/>

# In this Post We Will: 

- &#128073; Define Directory Service Accounts (DSA) 
- &#128073; Understand the role of a DSA in an MDI deployment
- &#128073; Learn why a gMSA is more secure than traditional accounts for use as DSA
- &#128073; Discuss implications between smaller versus larger, multi-forest environments
- &#128073; Create a gMSA for use as a DSA 
- &#128073; Grant the gMSA the required DSA permissions
- &#128073; Valiate the gMSA for use as a DSA in MDI
- &#128073; Register your new gMSA as a DSA in the MDI portal
- &#128073; Troubleshoot most common known issues


<br/>
<br/>

# What's a DSA and why is is ABSOLUTELY NECESSARY for MDI deployments?

A **Directory Service Account (DSA)** is used by **Microsoft Defender for Identity (MDI)** to connect to the domain controller and **query for data on entities seen in network traffic, monitored events, and monitored ETW activities**. Without a **DSA**, you _don't_ get that you might think. A **DSA** is **required** for the following (but not limited to) features and functionality:

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

By using a gMSA, the DSA benefits from the **automated password management and strong password policies** of the gMSA, reducing the risk of the DSA being compromised. **This is particularly important in multi-forest, multi-domain environments, where a _unique gMSA DSA is recommended for each forest or domain_.**


<br/>
<br/>

# How do I create a DSA for MDI? 

There's a couple different ways to peel this potato, depending on your domain infrastructure. There are essentially 2 parts to creating a gMSA to use as the DSA for MDI: 

**1. Create gMSA:**
The script prompts the user for the domain and a name for the DSA, then sets the HostsGroup to the default Domain Controllers Organizational Unit (OU), and creates a new gMSA with the provided details.

**2. Grant Permissions:**
It also retrieves the distinguished name for Deleted Objects and makes the current user the owner before. Finally, it assigns read permissions for Deleted Objects to the DSA account. 

The following PowerShell script is designed to facilitate simple  deployments (a handful of DCs on a single domain) by creating a Group Managed Service Account (gMSA) and granting it the necessary read privileges for use as a Directory Service Account (DSA) in Microsoft Defender for Identity. Ths script applies to the default domain controllers and is **particularly useful for automating the setup of a gMSA for use as a DSA for smaller MDI deployments:**


```powershell 

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

The next script is designed to facilitate custom setups for advanced, multi-domain environments in the context of Microsoft Defender for Identity (MDI).

- It allows the user to specify a HostGroup and the domain controllers with the MDI sensor installed

- Prompts the user for the domain, a name for the group of domain controllers, and a name for the Group Managed Service Account (gMSA). 

- Prompts the user for the principals (domain controllers with the MDI sensor installed) allowed to retrieve the password/use the gMSA on behalf of MDI to gain additional insights. 

- After importing the required Active Directory module, the script creates a new group, adds the specified members to it, and then creates a new gMSA associated with it.

**This is particularly useful for automating the setup of Directory Service Accounts (DSAs) in MDI deployments across multiple domains:**

```powershell

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

The second script is **more scalable** than the first one because it allows the user to specify a HostGroup as well as the domain controllers with the Microsoft Defender for Identity (MDI) sensor installed that go into it. This flexibility makes it more adaptable to larger, more complex network and multi-domain environments.

In contrast, the first script is designed for simple deployments on a single domain. It sets the HostGroup to the default Domain Controllers Organizational Unit (OU), which automatically applies to newly added domain controllers. While this is efficient for a single domain, it may not scale well for multi-domain environments.

<br/>
<br/>

# Confirming your DSA - Making sure the script worked

To test the functionality of a Group Managed Service Account (gMSA) to be used as a Directory Service Account (DSA) in Microsoft Defender for Identity (MDI), you can run the below script which installs and imports the **DefenderForIdentity module**, then prompts the user to specify the gMSA to test. It checks whether the gMSA works on the current domain controller, returns a list of other principals or domain controllers that can use this gMSA, and tests the DSA identity with a **-Detailed** switch. **This script is particularly useful for troubleshooting and validating the setup of DSAs in MDI deployments:**
```powershell

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

<br/>

Here's what a successful run looks like for a gMSA that has the required permissions to rock and roll as a DSA for MDI:

![](/assets/img/MDI_DSA/Validator_Success.png)

- **1.** First, the script prompts for the gMSA to validate.

<br/>

- **2.** Here you can see that, after prompting for the gMSA to verify, the DC I ran the script from is allowed to use the gMSA.

<br/>

- **3.** Next you can see which principles are allowed to use the gMSA. Note that this DC is a member of the default domain controller group listed as a principle allowed to use the gMSA.

<br/>

- **4.** Finally, it checks whether the gMSA has sufficient permissions to the objects it needs in your domain, such as Deleted Objects for example. 

<br/>

> &#128073; Note: if you see **False** for any of these or your hostgroup containing your DCs isn't listed as a **PrincipalAllowedToRetrieveManagedPassword** as illustrated, then this gMSA is not ready to be used as a Directory Service Account (DSA) in the Defender for Identity portal.

<br/>
<br/>

# Logon As a Service
Automating this part and appending it to either of the above scripts to create a DSA proved problematic so I typically just go the old fashioned way and configure this next part with a group policy object that applies to my domain controllers _after_ I've run one of the creation scripts:

- Open the Group Policy Management Editor and go the to _Computer Configuration -> Policies -> Windows Settings -> Security Settings -> Local Policies -> User Rights Assignment -> Log on as a service_ policy, and add your DSA account, illustrated in the below screenshots:

![](/assets/img/MDI_DSA/LogonAsService.png)

When granting your gMSA account **Logon As a Service** permissions, you won't always be able to 'find' your gMSA from the search box without taking the steps illustrated in the next two screenshots: 

- **1.** Select **Object Types**  
![](/assets/img/MDI_DSA/ObjectType.png)

- **2.** Make sure the **Service Accounts** box is checked:
![](/assets/img/MDI_DSA/ObjectType2.png)

- Now your gMSA will show up in the search box and you can grant Logon As a Service:
![](/assets/img/MDI_DSA/log-on-as-a-service.png)


<br/>
<br/>

# Register your DSA in MDI Portal (Now part of the Defender XDR Portal)

To connect your sensors with your Active Directory domains, you'll need to configure Directory Service accounts in Microsoft Defender XDR.

**1.** In [Microsoft Defender XDR](www.security.microsoft.com), go to Settings > Identities

**2.** Select Directory Service accounts.

**3.** select Add credentials and enter the Account name and Domain, then check the "Group Managed Service Account" box, illustrated below: 

![](/assets/img/MDI_DSA/DSA_reg_XDR.png)



<br/>
<br/>

# Troubleshooting

**Known Issues:**

9 times out of 10, there will be a Health Alert corresponding to any issues with your MDI setup and it's an easy fix:

- A resource issue on the DC (MDI shuts itself down on the DC when resource usage gets too high to avoid tanking a DC in production)

- An issue with the **DSA** not having sufficient privileges to read what it needs

- Some DC's weren't correctly added as **Principals Allowed to Retrieve** the DSA's **gMSA Password**. 

>Using the above scripts and tips in this article, you won't run into any of these issues &#128526;

Othere known issues and how to fix them are listed in the [official Microsoft Documentation](https://learn.microsoft.com/en-us/defender-for-identity/troubleshooting-known-issues#sensor-failed-to-retrieve-group-managed-service-account-gmsa-credentials)

>&#128161; Pro-Tip: _Something I often forget about, is the time it takes for the next Kerberos ticket to be issued after creating a new gMSA or adding a DC to the Hostgroup of **Principals Allowed to Retrieve the gMSA Password**. The issue is that the gMSA won't immediately work because it's waiting on the next ticket which could be hours away. You can fix this withh the following command:_ &#128071;
```powershell
klist -li 0x3e7 purge
```
<br/>
<br/>

**Lesser Known Issues:**

If something's wrong (sensor won't start, for example) and there aren't any helpful Sensor Health Alerts in the MDI/XDR portal, then the next place to look is in the MDI logs on the DCs themselves. The Defender for Identity logs are located in a subfolder called Logs where Defender for Identity is installed; the default location is: _C:\Program Files\Azure Advanced Threat Protection Sensor\version number\Logs_

You'll want to examine **all** of the log files, not just the ones with "error" in the title for the bigger picture to make sense. Here's an example I came across just last week:

**Sensor Won't Start, no Active Health Alerts**
I had recently deployed MDI using a gMSA as the DSA, but the sensor was acting like it was stuck in a boot loop before eventually timing out; It kept bouncing between starting and stopped. 

Because there were no Sensor Health Alerts, I looked into the MDI logs on one of the DCs and found the following clues from the log files: 

**Microsoft.Tri.Sensor.Errors.log:**
```txt
2024-04-15 21:28:12.4525 Error DirectoryServicesClient+<CreateLdapConnectionAsync>d__47 Microsoft.Tri.Infrastructure.ExtendedException: CreateLdapConnectionAsync failed [DomainControllerDnsName=DC.domain.local]

2024-04-15 21:28:12.4837 Error DirectoryServicesClient Microsoft.Tri.Infrastructure.ExtendedException: Failed to communicate with configured domain controllers [ _domainControllerConnectionDatas=DC.domain.local]
```

The above log entries indicate an issue with the DSA gMSA account permissions, keeping it from creating the LDAP connection. It's means the gMSA used as a DSA does not have **Logon As a Service** permissions required for Remote Impersonation or the DC isn't able to retrieve the gMSA password (normally there'd be a health alert for that). We ruled these out with our DSA validator script. Nothing from the [official Microsoft Documentation](https://learn.microsoft.com/en-us/defender-for-identity/troubleshooting-known-issues#sensor-failed-to-retrieve-group-managed-service-account-gmsa-credentials) applied here, so I moved on to the next log:

**Microsoft.Tri.Sensor.log:**
```txt
2024-04-16 11:05:36.3069 Info  RemoteImpersonationManager GetGroupManagedServiceAccountTokenAsync finished [UserName=mdiDSASvc01 Domain=ffas.local IsSuccess=True]

2024-04-16 11:05:36.3382 Info  DirectoryServicesClient CreateLdapConnectionAsync failed to connect [DomainControllerDnsName=DC.Domain.local Domain=domain.local UserName=mdiDSASvc01 ResultCode=82]
```
The above log entries confirm that the gMSA DSA actually does have **Logon As a Service** privileges and the DC was able to successfully complete **Remote Impersonation** so what could it be? Google told me ResultCode 82 was an issue with the gMSA account but that's all (Bing wasn't much better).

<br/>

> **Solution:** _I found this old [Microsoft Tech Community Post](https://techcommunity.microsoft.com/t5/microsoft-defender-for-identity/mdi-sensor-can-t-connect-to-domain/m-p/3589748) where **adding the gMSA to **Domain Users** allowed the DSA to make the LDAP connection and start the sensor service on the DCs.**_

_I hope this saves someone out there a headache_ &#128513;



<br/>
<br/>

# Conclusion:

&#x1F6E1;&#xFE0F; A **DSA** is required for full security coverage in **MDI**. Without a **DSA**, you may expose your environment to certain risks, such as:

- &#128549; Inability to fully monitor and analyze activities on your network, which could lead to undetected security breaches&#10071;

- &#128551; Lack of detailed information about deleted objects, which could be exploited by attackers to gain unauthorized access&#10071;

- &#128565; Insufficient data to calculate potential lateral movement paths, which are crucial for identifying compromised accounts and preventing further spread of an attack within the network&#10071;

<br/>
<br/>

&#x1F6E1;&#xFE0F; **Group Managed Service Account (gMSA)** is more secure than regular service accounts due to:

- &#128273; Automated Password Management: gMSA passwords are auto-generated and rotated by Windows, eliminating manual password management.

- &#128170; Strong Passwords: gMSA passwords are 240-byte, randomly generated, reducing the risk of brute force or dictionary attacks.

 - &#128272; Limited Access: Only authorized servers can retrieve the gMSA password from Active Directory, limiting potential misuse.

<br/>

> &#9888; Note:  not having a **DSA** as a part of your **MDI** deployment can **significantly limit the visibility and control over your network’s security**, potentially leaving it **vulnerable to undetected attacks**. It’s recommended to configure a **DSA** for comprehensive protection&#10071;&#10071;&#10071;

<br/>
<br/>

# In this Post We: 

- &#128073; Defined Directory Service Accounts (DSA) 
- &#128073; Understood the role of a DSA in an MDI deployment
- &#128073; Learned why a gMSA is more secure than traditional accounts for use as DSA
- &#128073; Discussed implications between smaller versus larger, multi-forest environments
- &#128073; Created a gMSA for use as a DSA 
- &#128073; Granted the gMSA the required DSA permissions
- &#128073; Valiated the gMSA for use as a DSA in MDI
- &#128073; Registered your new gMSA as a DSA in the MDI/MXDR portal
- &#128073; Addressed most known and lesser known issues

<br/>
<br/>

# Thanks for Reading! 

If you've made it this far, thanks for reading! All the scripts referenced in this blog post can be found in my [MDI repository](https://github.com/EEN421/Defender-for-Identity)) on [Github](https://github.com/EEN421).

<br/>

![www.hanleycloudsolutions.com](/assets/img/footer.png) ![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
