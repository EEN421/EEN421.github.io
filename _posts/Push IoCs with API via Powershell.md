# Introduction & Use Case:
&#9201; In the fast-paced world of cybersecurity, the ability to swiftly respond to threats is crucial. However, even the most well-oiled Security Operations Center (SOC) can encounter hiccups, such as Role-Based Access Control (RBAC) configuration mishaps that can, for example, hinder the manual registration of Indicators of Compromise (IOCs) in the Microsoft Defender portal and much, much more. When such issues arise, having an alternative method to publish IOCs becomes invaluable.

&#128272; Moreover, with the upcoming enforcement of Multi-Factor Authentication (MFA) later this year, relying on user-based service accounts for automation is becoming increasingly untenable. These accounts **will break** under the upcoming changes Microsoft is going to enforce, potentially leaving your SOC vulnerable at critical moments. 

&#x26A1; **You're no stranger to danger;** you know you can **register an app** in EntraID for authentication and permissions, then use **PowerShell** to **automate** the process of submitting IOCs to Microsoft Defender, ensuring that your SOC remains agile and responsive even in the face of access control challenges. This approach not only streamlines your threat response but also **reinforces your overall security posture by maintaining continuous protection against emerging threats.**

&#128073; In this blog post, **we’ll explore how to set up and use PowerShell to publish IOCs to Microsoft Defender with a registered EntraID application.** We’ll walk you through the necessary steps for **authentication** and **permissions**, providing a robust solution for when manual methods fall short. Whether you’re dealing with IP addresses, domains, or other threat indicators, this guide will equip you with the knowledge to keep your defenses strong and your response times swift... like a ninja! &#x1f977;


<br/>

![](/assets/img/IOC/Ninja_Cat_SOC.jpg)

<br/>
<br/>

# The Method to the Madness:

Registering an application and using the application secret is a **good practice for migrating away from user-based service accounts, especially with the upcoming Multi-Factor Authentication (MFA) enforcement from Microsoft.** Here are some reasons why this approach is beneficial:

- &#128170; **Stability and Reliability:**
Application secrets are not subject to the same MFA requirements as user accounts, ensuring that your automation scripts continue to run smoothly without interruption.

- &#x1F6E1;&#xFE0F; **Security:**
Using application secrets reduces the risk associated with user credentials, such as password expiration and the potential for credentials to be compromised.
Application secrets can be managed and rotated securely, providing a more controlled environment.

- &#128200; **Scalability:**
Applications can be granted specific permissions, making it easier to manage access and roles as your environment grows.
This approach supports better governance and compliance with security policies.

- &#128221; **Audit and Monitoring:**
Activities performed by the application can be tracked and audited separately from user activities, providing clearer visibility into actions taken by automation scripts.

- &#128269; **Compliance:**
Aligning with best practices and upcoming security requirements helps ensure compliance with industry standards and regulations.

By transitioning to application-based authentication, you can enhance the **security, reliability, and manageability** of your automation processes, making it a **forward-thinking strategy** in light of the upcoming MFA enforcement.

<br/>
<br/>

# In this Post We Will:

- &#128268; Register an Application in Entra ID
- &#x1F512; Manage Application Permissions (Principle of Least Privilege)
- &#x1F511; Application Authentication & Authorization
- &#128297; Build a powershell script to grab our token
- &#128295; Build a powershell script to submit our custom IoC
- &#128296; Run it!

<br/>
<br/>

# Pre-Requisites

**Global Administrator** will cover it, **BUT** if you want to go **Principle of Least Privilege**, read on... 

To **register** an **application** in **Entra ID** (formerly **Azure AD**), assign it privileges, and grant admin consent, you need specific permissions and roles. Here’s a breakdown of the steps and required permissions:

&#x1F511;	**Registering an Application**:
Permissions Needed: By default, all users can register applications. However, if this ability is restricted, you need to be assigned the **Application Developer role** or higher.

&#x1F511;	**Assigning Privileges**:
Permissions Needed: To assign API permissions to the application, you need to be an **Application Administrator, Cloud Application Administrator,** or **Privileged Role Administrator**.

&#x1F511;	**Granting Admin Consent**:
Permissions Needed: To grant tenant-wide admin consent, you need to be a **Privileged Role Administrator, Application Administrator,** or **Cloud Application Administrator**.


<br/>
<br/>

# Register an Application in Entra ID

- Navigate to your Entra ID portal, **App Registrations**, then to **New Registration**:

![](/assets/img/IOC/New_App_Reg.png)

<br/>

- Fill out a **Name**, and select **Accounts in this organizational directory only**

![](/assets/img/IOC/AppReg1.png)

<br/>

- Leave the optional **Redirect URI** blank and select **Register** to register your new Entra ID Application.

![](/assets/img/IOC/New_App_Reg1-URI.png)
![](/assets/img/IOC/New_App_Reg_Succeed.png)

<br/>

-  On the new application's **Overview** Page, take note of the **Application ID** and **Tenant ID**:

![](/assets/img/IOC/New_App_reg_IDs.png)

<br/>

# Manage Application Permissions (Principle of Least Privilege)

-  Navigate to **API Permissions** and select **Add permission**:

![](/assets/img/IOC/New_App_Reg_APIs.png)

<br/>

-  Select **APIs my organization uses** and search for **WindowsDefenderATP**:

![](/assets/img/IOC/New_App_Reg_APIs-permissions1.png)

<br/>

- Select **Application Permissions**, illustrated below:

![](/assets/img/IOC/New_App_Reg_APIs-permissions2.png)

<br/>

-  Expand the **Threat Intelligence (Ti)** drop down menu and select **Ti.ReadWrite.All** as this application needs to be able to read and create IoCs.

![](/assets/img/IOC/New_App_Reg_API-TI.ReadWrite.All.png)
![](/assets/img/IOC/New_App_Reg_API_Success.png)

<br/>

- Provide **Admin Consent**:

![](/assets/img/IOC/API_Permissions_Before.png)
![](/assets/img/IOC/API_Permissions_After.png)


<br/>
<br/>

# Application Authentication & Authorization

We need to create an application key (secret). 

- Navigate to your application in the Azure portal and select **Certificates & Secrets**, **Client Secrets**, then **+ New client secret** as shown below:

![](/assets/img/IOC/New_Secret.png) 

<br/>

-  Give your **secret** a name and **expiration**:

![](/assets/img/IOC/Secret_EXP.png)

<br/>

- Grab the secret **Value**: 

![](/assets/img/IOC/Secret_Value.png)

>&#128161; WARNING!!! --> You can ONLY view the secret value once... when you navigate away from the page it will no longer be available ![](/assets/img/IOC/Secret_Warning.png)

<br/>

- At this point, you should now have an **Application ID, Tenant ID,** and **Application Secret** locked and loaded.  

<br/>
<br/>

# Build a PowerShell Script to Grab our Token

This script gets the App Context Token and saves it to a file named "Latest-token.txt" in the current directory and prompts the user for Tenant ID, App ID, and App Secret and is available here.

```powershell
# Prompt the user for Tenant ID, App ID, and App Secret
$tenantId = Read-Host -Prompt 'Enter your Tenant ID'
$appId = Read-Host -Prompt 'Enter your Application ID'
$appSecret = Read-Host -Prompt 'Enter your Application Secret'

$resourceAppIdUri = 'https://api.securitycenter.windows.com'
$oAuthUri = "https://login.windows.net/$TenantId/oauth2/token"

$authBody = [Ordered] @{
    resource = "$resourceAppIdUri"
    client_id = "$appId"
    client_secret = "$appSecret"
    grant_type = 'client_credentials'
}

$authResponse = Invoke-RestMethod -Method Post -Uri $oAuthUri -Body $authBody -ErrorAction Stop
$token = $authResponse.access_token
Out-File -FilePath "./Latest-token.txt" -InputObject $token
return $token
```
<br/>
<br/>

# Build a PowerShell Script to Submit our Custom IoC

```powershell
param (   
    [Parameter(Mandatory=$true)]
    [ValidateSet('FileSha1','FileSha256','IpAddress','DomainName','Url')]   #validate that the input contains valid value
    [string]$indicatorType,

    [Parameter(Mandatory=$true)]
    [string]$indicatorValue,     #an input parameter for the alert's ID	    
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('Alert','AlertAndBlock','Allowed')]   #validate that the input contains valid value
    [string]$action = 'Alert',                         #set default action to 'Alert'
    
    [Parameter(Mandatory=$true)]
    [string]$title,     
   
    [Parameter(Mandatory=$false)]
    [ValidateSet('Informational','Low','Medium','High')]   #validate that the input contains valid value
    [string]$severity = 'Informational',                   #set default severity to 'informational'
    
    [Parameter(Mandatory=$true)]
    [string]$description,     

    [Parameter(Mandatory=$true)]
    [string]$recommendedActions     
)

# Prompt the user for the necessary values
$indicatorType = Read-Host -Prompt 'Enter the Indicator Type (FileSha1, FileSha256, IpAddress, DomainName, Url)'
$indicatorValue = Read-Host -Prompt 'Enter the Indicator Value'
$action = Read-Host -Prompt 'Enter the Action (Alert, AlertAndBlock, Allowed)' -Default 'Alert'
$title = Read-Host -Prompt 'Enter the Title'
$severity = Read-Host -Prompt 'Enter the Severity (Informational, Low, Medium, High)' -Default 'Informational'
$description = Read-Host -Prompt 'Enter the Description'
$recommendedActions = Read-Host -Prompt 'Enter the Recommended Actions'

$token = .\Get-Token.ps1                              # Execute Get-Token.ps1 script to get the authorization token

$url = "https://api.securitycenter.windows.com/api/indicators"

$body = 
@{
    indicatorValue = $indicatorValue        
    indicatorType = $indicatorType 
    action = $action
    title = $title 
    severity = $severity	
    description = $description 
    recommendedActions =  $recommendedActions 
}
 
$headers = @{ 
    'Content-Type' = 'application/json'
    Accept = 'application/json'
    Authorization = "Bearer $token"
}

$response = Invoke-WebRequest -Method Post -Uri $url -Body ($body | ConvertTo-Json) -Headers $headers -ErrorAction Stop

if($response.StatusCode -eq 200)   # Check the response status code
{
    return $true        # Update ended successfully
}
else
{
    return $false       # Update failed
}
```

>&#128161; Both scripts are [available here](https://github.com/EEN421/Powershell-Stuff/tree/Main/IOC%20Demo/Prompt) on Github. It's important that you download and save both of these scripts to the _same directory,_ because the **Submit-Indicator.ps1** script will try to call the **Get-Token.ps1** script when it runs. Both of these scripts originally had the variables hardcoded, you can see the difference and check out the [original scripts here](https://github.com/EEN421/Powershell-Stuff/tree/Main/IOC%20Demo/Hard-Coded)


<br/>
<br/>

# Run it! 

Open up a PowerShell window as an Administrator and run the **Submit_Indicator.ps1** PowerShell script and fill out the prompts accordingly.

I ran it and provided the following values to test: 

```powershell 
.\Submit-Indicator.ps1 

-indicatorType FileSha1

-indicatorValue  b9174c8a1db96d329071ee46483a447c1d3abdc0

-action AlertAndBlock

-severity High

-title "Ian's Test"

-description "This IoC was pushed from a powershell command that leverages an EntraID Registered API for authentication and permissions - Ian Hanley"

-recommendedActions "This can be ignored - for testing purposes only"
```

<br/>

The prompt returned **True** so I navigated to the portal to confirm and the **File hashes** list was updated with my new IoC:

<br/>


![](/assets/img/IOC/IOC%20Test.png)

<br/>
<br/>


# Ian's Insights:

The ability to swiftly respond to threats is crucial in cybersecurity, but even the best Security Operations Centers (SOCs) can face challenges like RBAC configuration mishaps. With the upcoming enforcement of Multi-Factor Authentication (MFA), relying on user-based service accounts for automation is becoming impractical. By registering an app in EntraID and using PowerShell to automate tasks in Microsoft Defender, you can ensure your SOC remains agile and responsive. 

<br/>
<br/>

# In this Post:

- &#128268; Registered an Application in Entra ID
- &#x1F512; Managed Application Permissions (Principle of Least Privilege)
- &#x1F511; Set Application Authentication & Authorization
- &#128297; Built a powershell script to grab our token
- &#128295; Built a powershell script to submit our custom IoC
- &#128296; Ran it!

<br/>
<br/>

# Thanks for Reading!
This approach not only streamlines threat response but also strengthens your overall security posture, maintaining continuous protection against emerging threats. This guide will equip you with the knowledge to keep your defenses strong and your response times ninja swift. 🥷 

<br/>
<br/>

# Helpful Links & Resources: 

- [Quickstart: Register an application with the Microsoft identity platform](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app?tabs=certificate)

- [Entra ID app registrations and service principals](https://petri.com/microsoft-entra-id-app-registration-explained/#:~:text=App%20registrations%20are%20primarily%20used%20by%20developers%20who,app%20in%20the%20directory%20in%20the%20developer%C3%A2%C2%80%C2%99s%20tenant.)

- [Pushing custom Indicator of Compromise (IoCs) to Microsoft Defender ATP](https://techcommunity.microsoft.com/t5/microsoft-defender-for-endpoint/pushing-custom-indicator-of-compromise-iocs-to-microsoft/m-p/532203)

- [WDATP API “Hello World” (or using a simple PowerShell script to pull alerts via WDATP APIs)](https://techcommunity.microsoft.com/t5/microsoft-defender-for-endpoint/wdatp-api-hello-world-or-using-a-simple-powershell-script-to/ba-p/326813)

- [Microsoft Defender ATP and Malware Information Sharing Platform integration](https://techcommunity.microsoft.com/t5/microsoft-defender-for-endpoint/microsoft-defender-atp-and-malware-information-sharing-platform/m-p/576648)

- [Origins of Defender NinjaCat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025) 

<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
