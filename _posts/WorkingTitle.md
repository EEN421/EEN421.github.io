# Introduction & Use Case:

In this blog post, we will explore how to leverage Azure Logics Apps to solve for a common, budget-constrained, critical security use case while also reducing overhead for your SOC analysts. You’ve been charged automating the following scenario:
•	When a user commits three or more failed login attempts within two minutes, Revoke all EntraID sign-ins (option for disabling the account and/or forcing a password reset too for bonus points).
•	Notify the user’s manager via email.
•	Append a comment to the incident in Sentinel. 
•	To add to the challenge, your corporate overlords have decided that upgrading your Microsoft Enterprise E3 licenses to E5 is not an option this fiscal year, meaning you miss out on Risk-Based Conditional Access Policies. 
What do you do? 
As a seasoned Sentinel expert, you know this can be automated by creating an Analytics Rule in Sentinel, linking it to an Azure Logic App, and using an Azure Automation Runbook. This setup allows Sentinel to pass the user account from the incident to the logic app, which runs automatically, reducing SOC team overhead.
You can configure your Azure Logic App to look for the ‘Manager:’ property in EntraID, automate emailing the manager, and append a comment to the incident. This automation reduces alert fatigue and overhead on your SOC while meeting corporate goals, even with licensing constraints.

In this Post We Will:
In this post, we will delve into how these tools can enhance your security posture, providing practical examples and best practices. Whether you’re dealing with unusual sign-in patterns, potential insider threats, or other security challenges, these insights will help you safeguard your organization with confidence until E5 is on the Corporate Roadmap.
•	Build a custom Analytics Rule for Detections
•	Build Logic Apps to:
o	Revoke EntraID Sessions
o	Reset EntraID Password
o	Disable EntraID Account
•	Configure a Managed Identity for our Logic Apps
•	Fine Tune our Logic App
•	Run Logic Apps from Incident Queue to Pass User Data over the Sentinel Connector
