# Introduction & Use Case: 
Deploying a SIEM (Security Information and Event Management) solution quickly and connecting it to XDR (Extended Detection and Response) data sources in a hurry can be critical in the following, more common than you'd think, situations (no judgement, we've all been there):

- ⚠️ Pending Cyber Attack: If an organization is expecting an attack, rapidly deploying a SIEM helps centralize and analyze security data to detect and respond more effectively.

- 🔓 Data Breach Discovery: After a data breach, quick SIEM deployment helps track the scope, monitor the attacker’s movements, and support incident response efforts.

- 📑 Regulatory Compliance: Urgent audits or regulatory needs? Deploying a SIEM ensures all security events are logged and monitored.

- 💼 Mergers and Acquisitions: Merging IT environments? A SIEM provides centralized visibility for seamless integration.

- ⏳ Resource Constraints: With limited IT resources, quickly implementing SIEM means comprehensive security without a heavy lift.

<br/>

Rolling out a comprehensive Extended Detection and Response (XDR) setup can seem daunting, but with the right tools and guidance, the SIEM piece becomes a straightforward task. In this article, we'll walk you through an easy-to-follow, step-by-step process for deploying a Log Analytics workspace to a new resource group, complete with Microsoft Sentinel, all necessary connectors from the content hub, analytics rules, and log types, in mere minutes using the ARM template provided [here](https://github.com/Azure/Azure-Sentinel/tree/master/Tools/Sentinel-All-In-One). Whether you're a seasoned IT professional or just starting out, this guide will help you achieve a full XDR setup with minimal hassle. Let's get started!

<br/>
<br/>

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/Sentinel_Auto.jpg)

<br/>
<br/>
<br/>


# In this Post We Will:
### Discuss, Deploy, & Automate the Following XDR Components:
- &#128193; Azure Resource Group
- &#128202; Log Analytics Workspace
- &#x1F6E1; Microsoft Sentinel
- &#x1F6E0; Sentinel Solutions from the Content Hub
- &#x1F50D;Analytics Rules from the Content Hub
- &#128268; Connectors from the Content Hub
- &#x26A1; Deploy Everything at Once!

<br/>
<br/>
<br/>

# Pre-Requisites & Notes:
- **Azure Subscription**

- **Azure user account with enough permissions** to enable the desired connectors. See table at the end of this page for additional permissions. Write permissions to the workspace are always needed.
  
- Some data connectors require the **relevant licence** in order to be enabled. See table at the end of this page for details  (Defender for IoT, for example).

- For a list of **Supported Connectors**, [go here](https://github.com/Azure/Azure-Sentinel/tree/master/Tools/Sentinel-All-In-One)

<br/>
<br/>
<br/>


# Components

### Azure Resource Group
An **Azure Resource Group** is a logical container where your stuff lives. It's best practice to name them RG-Descriptor-YourInitials in shared environments to keep track of who's building what (lest it gets deleted by a manager when he/she can't quickly figure out who owns it when cleanubg up the test lab to stay under budget).

Both Log Analytics Workspaces and Microsoft Sentinel instances are created within a resource group.

<br/>

### Log Analytics Workspace
A **Log Analytics Workspace** is a data store in Azure Monitor that collects and analyzes logs from all kinds of sources, including non-Azure resources. It provides tools for querying and visualizing log data, setting up alerts, and integrating with other Azure services. It's great for setting up a [DIY IoT Soil Sensor Setup](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/) to get alerts when your soil gets too hot/cold or wet/dry for all you green thumbs and pepperheads out there &#127798;.

A workspace is created within a resource group and Microsoft Sentinel is deployed on top of it, leveraging its data collection and analysis capabilities.

<br/>

### Microsoft Sentinel
**Microsoft Sentinel** is a cloud-native security information and event management (SIEM) solution that goes on top of a Log Analytics Workspace. It adds detection, investigation, and response capabilities to a Log Analytics Workspace for security threats using AI and automation.

<br/>

### Sentinel Solutions from the Content Hub
**Sentinel Solutions** are packaged integrations available in the Microsoft Sentinel Content Hub. These solutions contain awesome pre-built, ready-to-go security components like data connectors, workbooks, analytics rules, hunting queries, playbooks, and more. 

### How They Function
- **Data Connectors**: Facilitate the ingestion of log data from various sources into Microsoft Sentinel.
- **Workbooks**: Offer interactive dashboards for monitoring and visualizing data.
- **Analytics Rules**: Detect suspicious activities and generate alerts.
- **Hunting Queries**: Help security teams proactively search for threats.
- **Playbooks**: Automate responses to detected threats using Azure Logic Apps.

<br/>

### Sentinel Analytics Rules
**Sentinel Analytics Rules** are predefined or custom rules in Microsoft Sentinel that help detect suspicious activities and potential security threats. These are simply put, just KQL queries under the hood that are written to identify patterns and are configured to run at regular intervals. When the patterns specified in the rule are met, an alert is generated and relevant information such as the entities involved are passed along.

Analytics rules can be created from templates provided by Microsoft or built from scratch to suit specific security needs.

<br/>

### Connectors from the Content Hub
**Connectors from the Content Hub** in Microsoft Sentinel are integrations that allow you to ingest data from various sources into your Sentinel workspace. There's a collection of ready-made, vendor-specific connectors ready to integrate.

The Content Hub provides a centralized location to discover, deploy, and manage these connectors.

<br/>
<br/>
<br/>

#  Deploy Everything at Once & Automate Our Way to a State of Awesome with ARM Templates

### Custom Deployment Step-by-Step Guide:

Navigate to the following URL: [https://github.com/Azure/Azure-Sentinel/tree/master/Tools/Sentinel-All-In-One](https://github.com/Azure/Azure-Sentinel/tree/master/Tools/Sentinel-All-In-One)

Scroll down to **Try it now!** and select the blue <font color="ligblue"><b>Deploy to Azure</b></font> button. 

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/TryItNow.png)

<br/>

### Basics:
Select your **Subscription, Location, New Resource Group Name, New Workspace Name, Daily Ingest Limit, Retention,** and **Commitment Tier.**

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/01-Basic.png)

>&#128161; By default, Log Analytics Workspace Table Retention is 30 days, but when you deploy Sentinel on top you can extend that to 90 days for free. 

<br/>

### Settings:
- Enable **UEBA** for enhanced coverage. User and Entity Behaviour Analytics establishes an activity baseline and can report on deviations. 

- From the dropdown, you can select EntraID and/or on-prem Active Directory (MDI required).

- Enable Health Diagnostics in case we need to troubleshoot connector health etc. 

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/02-Settings.png)

<br/>

### Content Hub:
Select the Microsoft and the Essentials Content Hub Solutions You wish to install. I selected all for this example, and left the Training and Tutorials content out, illustrated below: 

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/ContentHub.png)
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/ContentHub01.png)
![](/assets/img//Sentinel%20XDR%20Easy%20ARM%20Deploy/ContentHub02.png)
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/ContentHub05.png)

<br/>

### Data Connectors:
Select the Data Connectors you wish to onboard. For this example, I selected all, illustrated in the following screenshots:

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/DataConnectors01.png)
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/DataConnectors02.png)
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/DataConnectors03.png)

<br/>

### Analytics Rules:
- Check the box to **enable Scheduled Alerts**.
- Select the **severity levels** you wish to be alerted for.

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/AnalyticsRules.png)

<br/>

### Review & Create:
Verify your configuration and select **Create**.

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/Verify.png)

<br/>

### Hurry Up & Wait...
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/DeployInProgress.png)
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/DeployComplete.png)

<br/>

### Check It Out!
Navigate to Microsoft Sentinel in the [azure portal](www.portal.azure.com) to check out your new workspace and all the awesome features already deployed and waiting for you.

- New Log Analytics Workspace with Sentinel Deployed on top: 
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/NewSentinel.png)

<br/>

- New Content from the Content Hub:
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/NewContent.png)

<br/>

- New Connectors:
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/NewConnectors.png)

<br/>

- New Analytics Rules:
![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/NewRules.png)

<br/>
<br/>

# Ian's Insights:

If you're running an ECIF-funded Microsoft Modern SecOps workshop, this template covers all the mandatory modules. Want to take it further? Check out my previous article on [Logic Apps & Automation](https://www.hanley.cloud/2024-08-16-Logic-Apps-&-Automation/) for an optional module that can enhance the session. With the time you save, you’ll have the perfect opportunity to showcase Microsoft Sentinel’s advanced features, demonstrate your technical expertise, build trust with your audience, and—ultimately—close that next deal! Workshops are all about making a lasting impact! 💡🚀

<br/>
<br/>

# In this Post We:
### Discussed, Deployed, & Automated the Following XDR Components:
- &#128193; Azure Resource Group
- &#128202; Log Analytics Workspace
- &#x1F6E1; Microsoft Sentinel
- &#x1F6E0; Sentinel Solutions from the Content Hub
- &#x1F50D;Analytics Rules from the Content Hub
- &#128268; Connectors from the Content Hub
- &#x26A1; Deployed Everything at Once!



<br/>
<br/>

# Thanks for Reading!
 I hope this was a much fun reading as it was writing. 

<br/>

![](/assets/img/Sentinel%20XDR%20Easy%20ARM%20Deploy/Microsoft%20Sentinel.png)
<br/>
<br/>

# References, Links & Resources: 

- [https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-workspace-overview](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-analytics-workspace-overview)

- [https://learn.microsoft.com/en-us/azure/sentinel/overview?tabs=azure-portal](https://learn.microsoft.com/en-us/azure/sentinel/overview?tabs=azure-portal)

- [https://learn.microsoft.com/en-us/azure/sentinel/create-analytics-rules](https://learn.microsoft.com/en-us/azure/sentinel/create-analytics-rules)

- [https://learn.microsoft.com/en-us/azure/sentinel/scheduled-rules-overview](https://learn.microsoft.com/en-us/azure/sentinel/scheduled-rules-overview)

- [https://learn.microsoft.com/en-us/azure/sentinel/sentinel-solutions-catalog](https://learn.microsoft.com/en-us/azure/sentinel/sentinel-solutions-catalog)

- [https://techcommunity.microsoft.com/blog/microsoftsentinelblog/introducing-microsoft-sentinel-content-hub/2928102](https://techcommunity.microsoft.com/blog/microsoftsentinelblog/introducing-microsoft-sentinel-content-hub/2928102)

- [https://learn.microsoft.com/en-us/azure/sentinel/sentinel-solutions](https://learn.microsoft.com/en-us/azure/sentinel/sentinel-solutions)

- [https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/)

<br/>



<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
