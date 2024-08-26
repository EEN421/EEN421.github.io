# Introduction & Use Case:
&#9201; In the fast-paced world of cybersecurity, the ability to swiftly respond to threats is crucial. However, even the most well-oiled Security Operations Center (SOC) can encounter hiccups, such as Role-Based Access Control (RBAC) configuration mishaps that hinder the manual registration of Indicators of Compromise (IOCs) in the Microsoft Defender portal. When such issues arise, having an alternative method to publish IOCs becomes invaluable.

&#128272; Moreover, with the upcoming enforcement of Multi-Factor Authentication (MFA) later this year, relying on user-based service accounts for automation is becoming increasingly untenable. These accounts **will break** under the upcoming changes Microsoft is going to enforce, potentially leaving your SOC vulnerable at critical moments. 

&#x26A1; You're no stranger to danger; you know you can register an app in EntraID for authentication and permissions, then use PowerShell to automate the process of submitting IOCs to Microsoft Defender, ensuring that your SOC remains agile and responsive even in the face of access control challenges. This approach not only streamlines your threat response but also reinforces your overall security posture by maintaining continuous protection against emerging threats.

In this blog post, we’ll explore how to set up and use PowerShell scripts to publish IOCs to Microsoft Defender with a registered EntraID application. We’ll walk you through the necessary steps for authentication and permissions, providing a robust solution for when manual methods fall short. Whether you’re dealing with IP addresses, domains, or other threat indicators, this guide will equip you with the knowledge to keep your defenses strong and your response times swift... like a ninja! &#x1f977;


<br/>

![](/assets/img/IOC/Ninja_Cat_SOC.jpg)

<br/>
<br/>

# In this Post We Will:

- &#128268;
 Register an Application in EntraID
- &#128272; Manage Application Permissions (Principle of Least Privilege for the win)
- &#128297; Build a powershell script to grab our token
- &#128295; Build a powershell script to submit our custom IoC
- &#128296; Fine tune our script (ask it to prompt so we don't hardcode (gross right?))
- &#x26A1; Automate it!



<br/>
<br/>

# Pre-Requisites

Before going further, ensure the account you're using has the permissions shown here: 
![](/assets/img/Logic%20Apps%20&%20Automation/EntraID_Connector_PreReqs.png)

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
