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
At this point, with the above requirements and contstraints in place, you may feel like a cat with a red ninja headband riding a t-rex while running an efficient security operations center amidst the chaotic influx of alerts (actual prompt for the above image).

As a seasoned Sentinel Ninja Cat, you know this can be automated by creating an [Analytics Rule](https://learn.microsoft.com/en-us/azure/sentinel/create-analytics-rules?tabs=azure-portal) in Sentinel, linking it to an [Azure Logic App](https://learn.microsoft.com/en-us/azure/logic-apps/logic-apps-overview), using an [Azure Automation Runbook](https://learn.microsoft.com/en-us/azure/automation/automation-runbook-types?tabs=lps72%2Cpy10).

This setup allows Sentinel to pass the user account from the incident to the logic app, which runs automatically, reducing SOC team overhead.

You can also configure your Azure Logic App to look for the ‘Manager:’ property in [EntraID](https://learn.microsoft.com/en-us/entra/fundamentals/whatis), automate emailing a notification to the manager, and append a comment to the incident. This automation reduces alert fatigue and overhead on your SOC while meeting corporate goals, even with licensing constraints... now that's Ninja &#x1f977; 

<br/>

![](/assets/img/Logic%20Apps%20&%20Automation/NinjaCat.jpg)

<br/>
<br/>

# In this Post We Will:


- &#128270; Build a custom Analytics Rule for Detections

- &#128297; Build Logic Apps to:

    - Revoke EntraID Sessions
    - Reset EntraID Password
    - Disable EntraID Account

- &#128296; Configure a Managed Identity for our Logic Apps

- &#128295; Fine Tune our Logic Apps

- &#x26A1; Run Logic Apps from Incident Queue to Pass User Data over the Sentinel Connector

<br/>
<br/>


<br/>
<br/>


# In this Post We:
We dove into how the following tools can enhance your security posture, providing practical examples and best practices:

- &#128270; Custom Analytics Rule for Detections

- &#128297; Logic Apps:
    - Revoke EntraID Sessions
    - Reset EntraID Password
    - Disable EntraID Account

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