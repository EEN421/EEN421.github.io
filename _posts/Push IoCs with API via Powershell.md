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
- &#128272; Manage Application Permissions (Principle of Least Privilege for the win)
- &#128297; Build a powershell script to grab our token
- &#128295; Build a powershell script to submit our custom IoC
- &#128296; Fine tune our script
- &#x26A1; Automate Stuff!

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
<br/>

- 

<br/>

-  

<br/>

<br/>

-  

<br/>

<br/>

-  

<br/>


<br/>
<br/>


<br/>
<br/>

# Build a powershell script to grab our token

<br/>
<br/>


<br/>
<br/>

# Build a powershell script to submit our custom IoC

<br/>
<br/>

<br/>
<br/>

# Fine tune our script

<br/>
<br/>


<br/>
<br/>

# Automate Stuff!

<br/>
<br/>

>&#128161; There are ...

# Ian's Insights:

Today we ...

# In this Post:
We dove into ...stuff:

- &#128268;
 Register an Application in EntraID
- &#128272; Manage Application Permissions (Principle of Least Privilege for the win)
- &#128297; Build a powershell script to grab our token
- &#128295; Build a powershell script to submit our custom IoC
- &#128296; Fine tune our script (ask it to prompt so we don't hardcode (gross right?))
- &#x26A1; Automate it!


<br/>


<br/>
<br/>

# Thanks for Reading!
 Whether you’re dealing with unusual sign-in patterns, potential insider threats, or other security challenges, I hope these insights help you safeguard your organization with confidence until E5 is on the Corporate Roadmap. 

 <br/>

# Helpful Links & Resources: 

<br/>




<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
