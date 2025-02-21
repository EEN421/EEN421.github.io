# Introduction & Use Case: 
Spinning up a Domain Controller (DC) for a Microsoft Defender for Identity (MDI) lab can be a hassle—especially if you need a fresh environment regularly. Wouldn't it be great to automate this process so you can stand up a new DC in minutes? In this guide, we’ll walk through using a custom ARM template (dc-parameters.json) to deploy a DC on the fly, saving you precious time and effort.
By the end of this post, you’ll have a repeatable deployment process that covers the machine creation, network configuration, and Windows Server role installations—all set to serve as a domain controller for your MDI testing.

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

•  Overview & Why It’s Useful
- Understand how the automated DC deployment simplifies your MDI testing workflow.
- Discover the benefits of speed, consistency, and scalability for multiple or more complex scenarios.

•  Prerequisites
- Review what’s required before using the custom ARM template (e.g., Azure subscription, resource group, networking essentials).

•  How the ARM Template Works
- Examine the solution components, including network resources (VNet, subnet, NSG), storage for diagnostics, and the Windows VM setup.

•  Step-by-Step Deployment
- Follow detailed instructions on where to edit parameters (domain name, admin credentials, VM size, etc.).
- Learn how to launch the template via the Azure Portal, Azure CLI, or PowerShell.
- Perform basic checks to ensure your DC is live and ready for MDI.

•  Post-Deployment Configuration
- Complete final tasks such as promoting your server to a Domain Controller and preparing it for MDI integration.

•  Validation & Testing
- Verify everything is operational and confirm your deployment is ready for Defender for Identity.

•  Conclusion
- Wrap up with key takeaways and next steps for expanding your automated DC deployment.



<br/>
<br/>
<br/>

# Pre-Requisites & Notes:
Before deploying the custom ARM template, confirm you have:
1.	Azure Subscription – You’ll need permissions to create resource groups, virtual networks, and VMs.
2.	Azure CLI / PowerShell (Optional) – If you prefer deploying templates from the command line.
3.	Resource Group – Make sure you have a resource group ready in the Azure region of your choice.
4.	Basic Network Planning – Decide on IP ranges, subnet names, and domain name (for example, mylab.local).
5.	An Admin Account & Password – The template requires these to configure your Windows Server VM.


<br/>
<br/>
<br/>


# Automated DC Deploy Overview:
The attached dc-parameters.json ARM template automates:
•	Networking – Creates or references a Virtual Network and Subnet for your domain controller.
•	Security – Generates or updates a Network Security Group (NSG) to allow RDP (TCP 3389) by default, which you can limit or expand as needed.
•	Storage – Deploys a storage account for boot diagnostics if you don’t already have one.
•	Windows VM – Spins up a Windows Server 2022 Datacenter instance with your specified admin credentials.
•	Output – Returns the Public IP address of the VM and the name you configured for the DC.
Once the deployment is complete, you’ll have a functioning Windows Server. You can then promote it to a Domain Controller, or further configure it to host Active Directory, DNS, and any other roles you need.

# Solution Components
1.	ARM Template (dc-parameters.json)
o	Parameters 
	domainName: FQDN of your future domain.
	adminUsername: Administrator username for the VM.
	adminPassword: Secure password for the VM admin.
	vmSize: Default is Standard_DS2_v2.
	virtualNetworkName & subnetName: Names of the VNet and subnet if you want to use existing resources.
	virtualNetworkAddressRange & subnetRange: Defaults to 10.0.0.0/16 and 10.0.1.0/24.
	location: Defaults to the location of the resource group.
o	Variables 
	Defined for NIC name, NSG name, and diagnostics storage account for convenience.
o	Resources 
	Network Security Group
	Public IP Address
	Virtual Network (new or existing)
	Network Interface
	Storage Account (Diagnostics)
	Virtual Machine (Windows Server 2022)
o	Outputs 
	Public IP address for the new DC VM.
	Domain controller name.

# Step-by-Step Deployment:

Step-by-Step Deployment
1. Download or Clone the Template
•	Save dc-parameters.json locally or in your preferred code repository.
2. Customize the Parameters
Open the ARM template in a code editor (VS Code, for instance) and edit the parameters in the parameters section to fit your environment.

```json
"domainName": {
  "type": "string",
  "metadata": {
    "description": "YourDomain.local"
  }
},
"adminUsername": {
  "type": "string",
  "metadata": {
    "description": "YourAdminName"
  }
},
"adminPassword": {
  "type": "securestring",
  "metadata": {
    "description": "YourSecurePasswordHere"
  }
},
"vmSize": {
  "type": "string",
  "defaultValue": "Standard_DS2_v2"
},
...
```
•	domainName: Set to something like mylab.local.
•	adminUsername: Use a unique name (like labadmin).
•	adminPassword: Must meet Azure’s complexity requirements.
•	virtualNetworkName, subnetName: If you already have a VNet/Subnet, enter their names; otherwise keep defaults.
•	virtualNetworkAddressRange, subnetRange: Adjust if you have an overlapping IP range in your lab.
•	location: Set the desired Azure region (or leave as the resource group’s region).
3. Create (or Select) a Resource Group
If you don’t already have one:
az group create --name MyDefenderLabRG --location eastus
4. Deploy via Azure CLI
From a local terminal or the Azure Cloud Shell:
az deployment group create \
  --name DeployDCForMDI \
  --resource-group MyDefenderLabRG \
  --template-file ./dc-parameters.json
•	Replace MyDefenderLabRG with your resource group name.
•	Adjust the --template-file path as needed.
Or, Deploy via the Azure Portal
1.	Go to Create a resource → search for Template.
2.	Select Build your own template in the editor.
3.	Paste the content of dc-parameters.json.
4.	Click Save.
5.	Input parameter values in the UI.
6.	Click Review + Create and then Create.


<br/>
<br/>

# Post-Deployment Configuration:
1.	Connect via RDP
o	Use the VM’s public IP (output in the template’s Outputs section or from the Azure Portal).
o	Enter the admin username and password you specified.
2.	Promote to a Domain Controller
o	The ARM template sets up a standard Windows Server 2022 VM.
o	Within the server, open Server Manager → Add Roles and Features → Active Directory Domain Services.
o	Follow the Active Directory Domain Services Configuration Wizard to promote the server to a DC.
o	Reboot as prompted.
3.	Install the Defender for Identity Sensor (Optional at this stage)
o	Once your DC is configured, download and install the MDI sensor.
o	Provide the relevant workspace details and credentials for your MDI instance.

# Validation & Testing:

1.	Domain Services
o	Check Active Directory Users and Computers to confirm you can create OUs, user accounts, etc.
o	Verify DNS resolution works for your domain name.
2.	Connectivity
o	Ensure your firewall/NSG rules allow or block the right ports for lab testing.
o	Ping the server from other VMs (if any) in the same VNet to confirm internal connectivity.
3.	MDI Sensor
o	If installed, verify data ingestion in the Defender for Identity portal.
o	Look for any alerts or health indicators that might need attention.

# Conclusion:
Conclusion
Automating a DC deployment for Defender for Identity testing is a game-changer for lab efficiency. By leveraging the dc-parameters.json ARM template, you can spin up a fully configured Windows Server environment in just a few clicks, saving time and ensuring consistency across multiple tests or proof-of-concept scenarios. With your fresh domain controller live, you’re free to integrate Microsoft Defender for Identity—without the manual setup overhead.
Feel free to adjust the template further for advanced networking, specialized security configurations, or additional server roles. If you have any questions or want to share your own customizations, please leave a comment or reach out. Happy deploying!


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
