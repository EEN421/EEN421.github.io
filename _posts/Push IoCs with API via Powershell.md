# Introduction & Use Case:
In the fast-paced world of cybersecurity, the ability to swiftly respond to threats is crucial. However, even the most well-oiled Security Operations Center (SOC) can encounter hiccups, such as Role-Based Access Control (RBAC) configuration mishaps that hinder the manual registration of Indicators of Compromise (IOCs) in the Microsoft Defender portal. When such issues arise, having an alternative method to publish IOCs becomes invaluable.

Enter PowerShell and a registered EntraID application. By leveraging these tools, you can automate the process of submitting IOCs to Microsoft Defender, ensuring that your SOC remains agile and responsive even in the face of access control challenges. This approach not only streamlines your threat response but also reinforces your overall security posture by maintaining continuous protection against emerging threats.

Moreover, with the upcoming enforcement of Multi-Factor Authentication (MFA) later this year, relying on user-based service accounts is becoming increasingly untenable. These accounts are prone to breaking under new security policies, potentially leaving your SOC vulnerable at critical moments. By using a registered application for authentication and permissions, you can bypass these issues, ensuring a more stable and reliable method for publishing IOCs.

In this blog post, we’ll explore how to set up and use PowerShell scripts to publish IOCs to Microsoft Defender via a registered EntraID application. We’ll walk you through the necessary steps for authentication and permissions, providing a robust solution for when manual methods fall short. Whether you’re dealing with IP addresses, domains, or other threat indicators, this guide will equip you with the knowledge to keep your defenses strong and your response times swift.

- &#x1F6AB;
- &#128272;
- &#128232;
- &#128221;
- &#x26A1;  

<br/>

![](/assets/img/Logic%20Apps%20&%20Automation/T-Rex_Cat0.jpg)

<br/>
<br/>

# In this Post We Will:

- &#128268; Connect a Sentinel Workspace to EntraID
- &#128270; Build a custom Analytics Rule for Detections
- &#128297; Build Logic Apps to:
    - &#10003; Revoke EntraID Sessions
    - &#10003; Reset EntraID Password
    - &#10003; Disable EntraID Account
- &#128296; Configure a System-Assigned Managed Identity for our Logic Apps
- &#128295; Fine Tune our Logic Apps
- &#x26A1; Run Logic Apps from Incident Queue to Pass User Data over the Sentinel Connector

<br/>
<br/>

# Pre-Requisites

Before going further, ensure the account you're using has the permissions shown here: 
![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_PreReqs.png)

<br/>
<br/>


>&#128161; There are unique permissions required for each of the remaining 2 applications mentioned earlier, and the PowerShell scripts to automate those are available [here](https://github.com/EEN421/Powershell-Stuff/tree/Main/Logic%20App%20Demo).

# Ian's Insights:

Today we satisfied our business security use case of automating responses to risky sign-in behaviour and got bonus points for providing 3 separate automated logic apps each with different outcomes. Each of these logic apps will automate either restting a password, disabling an account, or revoking sign-in sessions. To reduce overhead on our SOC, the apps also automate an email to the user's manager, and update the incident so the analyst working the incident doesn't have to. It may feel like we're reinventing the wheel if you've got E5 licenses, but that's not always in the cards and those companies need protection too right? This is a practical solution for E3 or P2 customers until they can make the leap to E5.

# In this Post:
We dove into how the following tools can enhance your security posture, providing practical examples and best practices:

- &#128268; Connect a Sentinel Workspace to EntraID
- &#128270; Custom Analytics Rules for Detections
- &#128297; Logic Apps:
    - &#10003; Revoke EntraID Sessions
    - &#10003; Reset EntraID Password
    - &#10003; Disable EntraID Account
- &#128296; Configure System-Assigned Managed Identities for our Logic Apps
- &#128295; Fine Tune our Logic Apps
- &#x26A1; Run Logic Apps from Incident Queue to Pass User Data over the Sentinel Connector

<br/>

![](/assets/img/Logic%20Apps%20&%20Automation/T-Rex_Cat2.jpg)

<br/>
<br/>

# Thanks for Reading!
 Whether you’re dealing with unusual sign-in patterns, potential insider threats, or other security challenges, I hope these insights help you safeguard your organization with confidence until E5 is on the Corporate Roadmap. 

 <br/>

# Helpful Links & Resources: 

<br/>

- [Origin of #NinjaCat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025)
- [Microsoft Feature Comparison Matrix](https://m365maps.com/matrix.htm#000000000001001000000) 
- [Azure Logic Apps](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-overview)
- [EntraID Identity Protection - Risk-Based Conditional Access Policies](https://learn.microsoft.com/en-us/entra/id-protection/howto-identity-protection-configure-risk-policies)
- [Analytics Rules](https://learn.microsoft.com/en-us/azure/sentinel/create-analytics-rules?tabs=azure-portal)
- [What is EntraID?](https://learn.microsoft.com/en-us/entra/fundamentals/whatis)
- [https://leonardo.ai/](https://leonardo.ai/)
- [Powershell Scripts for Managed ID Permissions](https://github.com/EEN421/Powershell-Stuff/tree/Main/Logic%20App%20Demo)
- [KQL Query used in Analytics Rule](https://github.com/EEN421/KQL-Queries/blob/Main/FailedLoginAttempts.kql)
- [KQL Library](https://github.com/EEN421/KQL-Queries)


<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
