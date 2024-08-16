# Introduction & Use Case:

In this blog post, we will explore how to leverage [Azure Logic Apps](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-overview) to solve for a common, budget-constrained, critical security use case while also reducing overhead for your SOC analysts. You’ve been charged automating the following scenario:

When a user commits three or more failed login attempts within two minutes, we need to:

- &#128272; Revoke all EntraID sign-ins

- &#128295; Bonus points for option for disabling the account and/or forcing a password reset too.

- &#128232; Notify the user’s manager via email.

- &#128221; Append a comment to the incident in Sentinel. 

- &#x26A1; To add to the challenge, your corporate overlords have decided that upgrading your Microsoft Enterprise E3 licenses to E5 is not an option this fiscal year, meaning you miss out on [Risk-Based Conditional Access Policies](https://learn.microsoft.com/en-us/entra/id-protection/howto-identity-protection-configure-risk-policies). 

<br/>

![](/assets/img/Logic%20Apps%20&%20Automation/T-Rex_Cat0.jpg)

<br/>
<br/>

# What do you do? 
At this point, with the above requirements and contstraints in place, you may feel like _a cat with a red ninja headband riding a t-rex while running an efficient security operations center amidst the chaotic influx of alerts_ (actual prompt for the above image).

As a seasoned Sentinel Ninja Cat, however, you know this can be automated by creating an [Analytics Rule](https://learn.microsoft.com/en-us/azure/sentinel/create-analytics-rules?tabs=azure-portal) in Sentinel and linking it to an [Azure Logic App](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-overview) using an [Azure Automation Runbook](https://learn.microsoft.com/en-us/azure/automation/automation-runbook-types?tabs=lps72%2Cpy10).

You can also configure your Azure Logic App to look for the **‘Manager:’** property in [EntraID](https://learn.microsoft.com/en-us/entra/fundamentals/whatis), automate emailing a notification to the manager, and append a comment to the incident. This automation reduces alert fatigue and overhead on your SOC while meeting corporate goals, even with the given licensing constraints... now that's Ninja! &#x1f977; 

<br/>

![](/assets/img/Logic%20Apps%20&%20Automation/NinjaCat.jpg)

<br/>
<br/>

# In this Post We Will:

- &#128268; Connect a Sentinel Workspace to EntraID

- &#128270; Build a custom Analytics Rule for Detections

- &#128297; Build Logic Apps to:

    - &#10003; Revoke EntraID Sessions
    - &#10003; Reset EntraID Password
    - &#10003; Disable EntraID Account

- &#128296; Configure a Managed Identity for our Logic Apps

- &#128295; Fine Tune our Logic Apps

- &#x26A1; Run Logic Apps from Incident Queue to Pass User Data over the Sentinel Connector

<br/>
<br/>

# Pre-Requisites

Before going further, ensure the account you're using has the permissions shown here: 
![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_PreReqs.png)

<br/>
<br/>

# Connect a Sentinel Workspace to EntraID

1.) Navigate to your Sentinel Deployment and go to the **Content Hub**

![](/assets/img/Logic%20Apps%20&%20Automation/clean_slate.png)

<br/>

2.) Search for, and select the **Microsoft Entra ID** solution:

![](/assets/img/Logic%20Apps%20&%20Automation/Content_hub_EntraID.png)

<br/>

3.) Select **Install** and wait for it to complete, illustrated below:

![](/assets/img/Logic%20Apps%20&%20Automation/Install_EntraID_ContentHub.png)

![](/assets/img/Logic%20Apps%20&%20Automation/installing.png)
![](/assets/img/Logic%20Apps%20&%20Automation/Install_Success.png)

<br/>

4.) Navigate to the **Data Connectors** blade and you will now see the **Microsoft Entra ID Data Connector** available to connect: 

![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_Disconnected.png)


<br/>

5.) Click on the **Entra ID** Connector and then on **Open connector page.**

![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_Connector_Page.png)


<br/>

6.) If your account satisfies the permissions requirements listed earlier, then select the data tables you want to ingest into your Sentinel workspace from your Entra ID tenant. 

![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_Sign-in_Logs.png)

>&#128161; Sign-in logs are all we need for the purposes of this demonstration, but you can pull a lot more data into your workspace if you want to. 

<br/>

7.) Brew some coffee... this can take a few minutes before it'll show up as **connected** in the portal. You'll see the logs coming in once it's connected:

![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_Connected.png)

<br/>
<br/>

# Build a custom Analytics Rule for Detections

1.) Navigate to your Sentinel Deployment and go to the **Analytics Rules** blade:

![](/assets/img/Logic%20Apps%20&%20Automation/New_Query_Rule1.png)

<br/>

2.) Give the rule a **name, description,** and set it to **enabled** as shown below:

![](/assets/img/Logic%20Apps%20&%20Automation/Create_Rule1.png)

<br/>

3.) Enter the KQL logic to determine what activity should trigger the rule:

![](/assets/img/Logic%20Apps%20&%20Automation/Create_Rule_Query.png)

>&#128161; The KQL query is availble to copy and paste [here](https://github.com/EEN421/KQL-Queries/blob/Main/FailedLoginAttempts.kql) from my [KQL repo on github](https://github.com/EEN421). 

>&#128161; [EventID 50126](https://www.manageengine.com/products/active-directory-audit/kb/azure-error-codes/azure-ad-sign-in-error-code-50126.html) triggers on Invalid username or password or Invalid on-premises username or password, and so satisfies our use-case for this article. 

<br/>

4.) Next we need to **map entities**. This is important in order to pass on the user's **UPN suffix** from an incident generated by this rule, over to our logic app:  

![](/assets/img/Logic%20Apps%20&%20Automation/Create_Rule_Entity_Mapping.png)

<br/>

5.) Now we schedule the rule. For the purposes of this demonstration, I've set it to trigger every 15 minutes and to run against the last 15 minutes of logs, illustrated below: 

![](/assets/img/Logic%20Apps%20&%20Automation/Create_Rule_Schedule.png)

<br/>

6.) Don't forget to configure **Grouping.** To satisfy our use-case, we need to reduce overhead for our SOC as a part of our solution. Grouping similar **multiple alerts** together into a **single incident** helps to reduce _alert fatigue_: In our example, our analytics rule will create an incident when a user fails to login 3 or more times in under 2 minutes... What if Joe fails to login 12 times in under 2 minutes? Rather than flooding your SOC with a separate alert for each trigger, all the failed login alerts can be grouped together by user etc. This is crucial for maintaining your SOC's sanity and thus their effectiveness under pressure, when you need it. In the below screenshot, I have enabled grouping alerts by user, by working day (8 hours):

![](/assets/img/Logic%20Apps%20&%20Automation/Create_Rule_Alert_Grouping.png)

<br/>

We'll trigger this analytics rule to generate alerts/incidents later. Next we need to build out our Logic App(s). 

<br/>
<br/>

# Deploy Logic Apps

1.) Navigate to the **Content Hub** and locate your installed **Entra ID** Solution, then select **Manage:**

![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Manage.png)

<br/>

2.) At the time of this article, the Logic Apps that we're interested in can be found on the 3rd page of the **Entra ID** Solution in **Content Hub.**

There are 3 apps in this solution that we're particularly interested in for our use-case:

![](/assets/img/Logic%20Apps%20&%20Automation/Logic_Apps_to_Deploy.png)

<br/>

- &#x26A1;  **Reset Microsoft Entra ID User Password - Incident Trigger** will force reset the offending user's Entra ID password

- &#x26A1;  **Block Entra ID user - Incident** will disable the Entra ID account (can be configured to accommodate on-prem AD too)

- &#x26A1;  **Revoke Entra ID SignIn Sessions - incident trigger** will sign the user out of all Entra ID sessions, forcing them to re-authenticate

<br/>

3.) For this example, let's disable the offending user's account, notify their manager, and update the incident in Sentinel &#10024;automagically&#10024; for our SOC analysts. Select **Block Entra ID user - Incident** from the list, then click on **Create Playbook**.

![](/assets/img/Logic%20Apps%20&%20Automation/Create_Playbook.png)

<br/>

4.) Fill out the appropriate **subscription** and **resource group** for your **Logic App**, then give it a name. You do not need to configure any **Connections** at this time, just leave them at their default values and click **Next** through to the end:

![](/assets/img/Logic%20Apps%20&%20Automation/Create_Playbook_Basics.png)

![](/assets/img/Logic%20Apps%20&%20Automation/Create_Playbook_Completed.png)

5.) You have now deployed an **Azure Logic App**. Repeat these steps for the remaining 2 **Logic Apps**. 

![](/assets/img/Logic%20Apps%20&%20Automation/Logic_App_Designer_View.png)

<br/>

>&#128161; You can ignore the 'invalid connections' in the above screenshot, we'll fix those next with a Managed Identity and email account to send from etc.

<br/>
<br/>

# Grant Logic App Permissions to Interact with Sentinel

1.) First thing we need to do is grant the **Logic App** permissions to interact with the **Sentinel Workspace** by navigating to the **Settings** blade in **Sentinel** and expanding the **Playbook Permissions** dropdown. Click on **Configure Permissions**: 

![](/assets/img/Logic%20Apps%20&%20Automation/Sentinel_Permissions.png)

Next, select the **Resource Group** where your **Logic Apps** or **Playbooks** live to adhere to the **Principle of Least Privilege**:

![](/assets/img/Logic%20Apps%20&%20Automation/Sentinel_Permissions1.png)

<br/>
<br/>


# Configure a Managed Identity (Permissions Madness!)

Adhering to the **Zero Trust Network Architecture** and **Principle of Least Privilege** mode of thinking, each of our logic apps will need very specific privileges in order to automate the tasks we want them to:

- **Revoke Entra ID SignIn Sessions - incident trigger** requires **"User.ReadWrite.All"** in order to reoke Entra ID sessions.

- **Reset Microsoft Entra ID User Password - Incident Trigger** requires the **"Password Administrator** role.

- **Block Entra ID user - Incident** requires **"User.Read.All", "User.ReadWrite.All", "Directory.Read.All",** and **"Directory.ReadWrite.All"** in order to Disable a user account.

>&#128273; Note: all of the above **Logic Apps** will also require special permissions in order to look up the offending user's manager in Entra ID and then update the incident in Sentinel. 

Let's start with the **Block Entra ID user - Incident** because we can easily confirm the results in Entra ID once the user gets locked out. 

1.) Before we can assign the necessary permissions, we need to know what we're assigning them to. Navigate to the **Logic App** and open the **Identities** blade to see the Object's Principle ID. _Take note, we'll need this ID for the next step_.

&#128071; Here's a script that will grant the necessary privileges to a **Managed Identity** &#128071; 

```powershell 
$MIGuid = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" #<-- Insert your Managed ID
$MI = Get-AzureADServicePrincipal -ObjectId $MIGuid

$GraphAppId = "00000003-0000-0000-c000-000000000000" #<--Do not change this
$PermissionName1 = "User.Read.All"
$PermissionName2 = "User.ReadWrite.All"
$PermissionName3 = "Directory.Read.All"
$PermissionName4 = "Directory.ReadWrite.All"

$GraphServicePrincipal = Get-AzureADServicePrincipal -Filter "appId eq '$GraphAppId'"
$AppRole1 = $GraphServicePrincipal.AppRoles | Where-Object {$_.Value -eq $PermissionName1 -and $_.AllowedMemberTypes -contains "Application"}
New-AzureAdServiceAppRoleAssignment -ObjectId $MI.ObjectId -PrincipalId $MI.ObjectId `
-ResourceId $GraphServicePrincipal.ObjectId -Id $AppRole1.Id

$AppRole2 = $GraphServicePrincipal.AppRoles | Where-Object {$_.Value -eq $PermissionName2 -and $_.AllowedMemberTypes -contains "Application"}
New-AzureAdServiceAppRoleAssignment -ObjectId $MI.ObjectId -PrincipalId $MI.ObjectId `
-ResourceId $GraphServicePrincipal.ObjectId -Id $AppRole2.Id

$AppRole3 = $GraphServicePrincipal.AppRoles | Where-Object {$_.Value -eq $PermissionName3 -and $_.AllowedMemberTypes -contains "Application"}
New-AzureAdServiceAppRoleAssignment -ObjectId $MI.ObjectId -PrincipalId $MI.ObjectId `
-ResourceId $GraphServicePrincipal.ObjectId -Id $AppRole3.Id

$AppRole4 = $GraphServicePrincipal.AppRoles | Where-Object {$_.Value -eq $PermissionName4 -and $_.AllowedMemberTypes -contains "Application"}
New-AzureAdServiceAppRoleAssignment -ObjectId $MI.ObjectId -PrincipalId $MI.ObjectId `
-ResourceId $GraphServicePrincipal.ObjectId -Id $AppRole4.Id
```

2.) Download the script [here](https://github.dev/EEN421/Powershell-Stuff/blob/Main/Block-EntraIDUser-Incident-PERMISSIONS.ps1) from my [Github Repo](https://github.com/EEN421) and swap in your Managed Identity's **Principle Object ID** in the first line.

Launch PowerShell as an administrator and run the script. 

>&#128161; You may need to run the following powershell commands first to connect to your tenant: 

```powershell
Connect-AzureAD
```
You'll see the following output if completed run successfully:

![](/assets/img/Logic%20Apps%20&%20Automation/Permissions_Script_Success.png)

>&#128161; This can take a while to propogate on the back end, even after the script ran successfully. Give it at least 20-30 minutes... 

<br/>

3.) Next we need to Authorize the API connections used to connect to a mailbox to send a notification email to the manager etc. Navigate to your **Logic App** and go to the **API Connections** blade underneath **Development Tools**. 

![](/assets/img/Logic%20Apps%20&%20Automation/Managed_ID_API.png)

<br/>

4.) Expand the **General** dropdown on the left and go to the **Edit API connection** blade, then click on **Authorize** and save:

![](/assets/img/Logic%20Apps%20&%20Automation/Managed_ID_Authorize.png)

<br/>

5.) Go back and repeat this step for all of the API connections listed. 

>&#128161; If you run into an error authorizing the o365 API connection for sending email, make sure you're connecting to an account that has a mailbox to send from (must have an exchange license).

>&#128161; If you go back to the **Logic App Designer** you will no longer have the red "invalid connector" errors if the above steps have been done correctly. 


<br/>
<br/>

# Run the App! 

First we need to generate at least 3 failed login attempts in under 2 minutes for our **Analyitics Rule** to generate an **incident**. 

- &#128073; Go to an incognito/private browsing session and try to login to the [Azure portal](www.portal.azure.com) with a bogus password a few times. The Analytics rule is set to run every 15 minutes so it should show up soon. You'll see it in the **Incidents** blade in **Sentinel**.

Now that we've got an incident to run our **Logic App/Playbook** against, _lets do it!_

1.) Navigate to the **Incidents** blade in **Sentinel** and identify our incident:

![](/assets/img/Logic%20Apps%20&%20Automation/Incident.png)

<br/>

>&#128161; In the incident details, you can see the offending user who triggered the incident. This information will be passed to the logic app: ![](/assets/img/Logic%20Apps%20&%20Automation/Incident_details.png)

<br/>

2.) Click on the Incident to bring up the incident fly-out and select **Actions**, then **Run Playbook**:

![](/assets/img/Logic%20Apps%20&%20Automation/Incident_actions.png)

3.) Select your **Logic App/Playbook** and run it against the incident, which sends the user data over for the app to process:

![](/assets/img/Logic%20Apps%20&%20Automation/Run_Playbook.png)


<br/>
<br/>

# In this Post We:
We dove into how the following tools can enhance your security posture, providing practical examples and best practices:

- &#128268; Connect a Sentinel Workspace to EntraID

- &#128270; Custom Analytics Rule for Detections

- &#128297; Logic Apps:
    - &#10003; Revoke EntraID Sessions
    - &#10003; Reset EntraID Password
    - &#10003; Disable EntraID Account

- &#128296; Managed Identities for our Logic Apps

- &#128295; Fine Tuning our Logic Apps

- &#x26A1; Running Logic Apps from Incident Queue to Pass User Data over the Sentinel Connector

<br/>

![](/assets/img/Logic%20Apps%20&%20Automation/T-Rex_Cat2.jpg)

<br/>
<br/>

# Thanks for Reading!
 Whether you’re dealing with unusual sign-in patterns, potential insider threats, or other security challenges, I hope these insights help you safeguard your organization with confidence until E5 is on the Corporate Roadmap. 

 <br/>

# Helpful Links & Resources: 

- [Origin of #NinjaCat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025)

- [Microsoft Feature Comparison Matrix](https://m365maps.com/matrix.htm#000000000001001000000) 

- [Azure Logic Apps](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-overview)

- [EntraID Identity Protection - Risk-Based Conditional Access Policies](https://learn.microsoft.com/en-us/entra/id-protection/howto-identity-protection-configure-risk-policies)

- [Analytics Rules](https://learn.microsoft.com/en-us/azure/sentinel/create-analytics-rules?tabs=azure-portal)

- [What is EntraID?](https://learn.microsoft.com/en-us/entra/fundamentals/whatis)

- [https://leonardo.ai/](https://leonardo.ai/)


<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)