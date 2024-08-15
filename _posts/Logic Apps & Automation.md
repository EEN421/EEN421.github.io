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
At this point, with the above requirements and contstraints in place, you may feel _like a cat with a red ninja headband riding a t-rex while running an efficient security operations center amidst the chaotic influx of alerts_ (actual prompt for the above image).

As a seasoned Sentinel Ninja Cat, you know this can be automated by creating an [Analytics Rule](https://learn.microsoft.com/en-us/azure/sentinel/create-analytics-rules?tabs=azure-portal) in Sentinel, linking it to an [Azure Logic App](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-overview), using an [Azure Automation Runbook](https://learn.microsoft.com/en-us/azure/automation/automation-runbook-types?tabs=lps72%2Cpy10).

This setup allows Sentinel to pass the user account from the incident to the logic app, which runs automatically, reducing SOC team overhead.

You can also configure your Azure Logic App to look for the ‘Manager:’ property in [EntraID](https://learn.microsoft.com/en-us/entra/fundamentals/whatis), automate emailing a notification to the manager, and append a comment to the incident. This automation reduces alert fatigue and overhead on your SOC while meeting corporate goals, even with licensing constraints... now that's Ninja &#x1f977; 

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
![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_Page.png)

<br/>

6.) If your account satisfies the permissions requirements listed earlier, then select the data tables you want to ingest into your Sentinel workspace from your Entra ID tenant. 

![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Sign-in_Logs.png)

>&#128161; Sign-in logs are all we need for the purposes of this demonstration, but you can pull a lot more data into your workspace if you want to. 

<br/>

7.) Brew some coffee... this can take a few minutes before it'll show up as **connected** in the portal. You'll see the logs coming in once it's connected:

![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_Connected.png)

<br/>
<br/>

# Build a custom Analytics Rule for Detections

- Navigate to your Sentinel Deployment and go to the **Content Hub**
![](/assets/img/Logic%20Apps%20&%20Automation/clean_slate.png)

<br/>
<br/>

# Deploy Logic Apps

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