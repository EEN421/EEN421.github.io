# Introduction & Use Case:
Ever created a killer **Logic App** that was so awesome, you wish you could re-use it elsewhere in your environment, in another subscription or tenant, or use it as a sort of foundational template for more complicated apps? I bet you have, and were just as frustrated as I when you realized there's no meaningful way to export it without outrigtht exposing sensitive details. 

# The Challenge of Exporting Azure Logic Apps and a Solution Worth Your Time
Azure Logic Apps, with their visually appealing, no-code interface, are a powerful tool for automating business processes. However, beneath the surface, the business logic and connections that power these Logic Apps are stored as JSON. This JSON data can include all kinds of sensitive organizational details such as tenant ID, subscription information, connection strings and secrets, and more; making sharing or replicating the JSON for a functioning Logic App a potential security risk. 

# Why?
Unlike other resources where a simple copy-paste of the JSON code is enough (Workbooks, for example), deploying a Microsoft Sentinel Playbook is not as straightforward. The JSON code of a Logic App or Playbook is typically riddled with tenant-specific information and dependencies on Logic App connectors, depending on it's complexity. 

Manually sanitizing JSON code and removing organization-specific information to make it shareable but that's time-consuming and requires significant effort; not worth-while in most cases. I stumbled across this [fantastic utility](https://techcommunity.microsoft.com/t5/microsoft-sentinel-blog/export-microsoft-sentinel-playbooks-or-azure-logic-apps-with/ba-p/3275898) from the Microsoft Tech Community that changes the game by allowing you to export Azure Logic Apps/Playbooks as sanitized Azure Resource Manager (ARM) templates, swiftly and effortlessly. Read on for a brief how-to breakdown and troubleshooting guide. 

> &#128073; Note: This follows up on previous posts where we [built a Logic App to simultaneously send data from multiple sensors to a workspace, bypassing the custom endpoint bottleneck on the free Azure IoT Hub](https://www.hanley.cloud/2024-04-09-Sentinel-Integrated-Rpi-Soil-Sensor-2.0-Part-3/), and then [built another Logic App to automate alerting based on sensor readings](https://www.hanley.cloud/2024-04-16-Sentinel-Integrated-Rpi-Soil-Sensor-2.0-Part-4/). 

<br/>
<br/>

# In this Post We Will: 

- &#128073; Download & Run the Playbook ARM Template Generator
- &#128073; Safely export/share Logic Apps/Playbooks knowing that your organization’s information is stripped from the JSON and that it will work correctly in the recipient environment
- &#128073; Troubleshoot PowerShell Module Incompatibilities
- &#128073; Troubleshoot Connection Issues when Authenticating
- &#128073; Do Soemthing Cool and Save Someone else a headache

<br/>
<br/>
