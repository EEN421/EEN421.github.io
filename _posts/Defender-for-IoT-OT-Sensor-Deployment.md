# Introduction & Use Case:
You've deployed your sensors through Azure IoT Hub and onboarded your telemetry to a Log Analytics Workspace, but you're a ninja and know there's more to defending your shinobi dojo and it's IoT infrastructure... Enter the Defender for IoT Operational Technology (OT) sensor! 

<br/>

![](/assets/img/OT_Sensor/Enter%20Defender.jpg)

<br/>
<br/>

# In this Post We Will: 

- &#x1f977; Define D4IoT and the Operational Technology (OT) Sensor 
- &#x1f977; Why deploy D4IoT and an Operational Technology (OT) Sensor?
- &#x1f977; Onboard your subscription to Defender for IoT 
- &#x1f977; Deploy an Operational Technology (OT) Sensor on a Virtual Appliance 
- &#x1f977; Defend your IoT Dojo like a Ninja! 

<br/>

![](/assets/img/OT_Sensor/cartoon_ninja.jpg)

<br/>
<br/>

# Define D4IoT and the Operational Technology (OT) Sensor 

Microsoft Defender for IoT OT Sensor is a component of the Microsoft Defender for IoT system designed to provide broad coverage and visibility from diverse data sources. It’s essentially a network sensor that discovers and continuously monitors network traffic across your network devices (the network cap feature makes it perfect to for LoRaWAN deployments). These sensors are purpose-built for OT/IoT networks and connect to a SPAN port or network TAP. They use OT/IoT-aware analytics engines and Layer-6 Deep Packet Inspection (DPI) to detect threats, such as fileless malware, based on anomalous or unauthorized activity.

<br/>

![](/assets/img/OT_Sensor/D4IOT.jpg)

<br/>

# Why deploy D4IoT and an Operational Technology (OT) Sensor?

The Defender for IoT OT Sensor is a great way to complete our sensor deployment if you’ve been reading and following my prior Sentinel Integrated Soil Sensor articles for my peppers, as it enhances the security of an IoT Hub deployment by providing additional layers of visibility, threat detection, and analysis, thereby implementing a Zero Trust security strategy:

&#x26A1; 1.	Real-time Information Extraction: Azure Defender for IoT uses passive monitoring and Network Traffic Analysis (NTA) combined with patented, IoT/OT-aware behavioral analytics to extract detailed IoT/OT information in real-time.

&#x26A1; 2.	Agentless Security: It delivers agentless security for continuously monitoring OT networks in industrial and critical infrastructure organizations. This is particularly useful for existing devices that might not have built-in security agents.

&#x26A1; 3.	Deployment Flexibility: You can deploy these capabilities fully on-premises without sending any data to Azure3, which can be ideal for locations with low bandwidth or high-latency connectivity.

&#x26A1; 4.	Cloud Connectivity: When configured as cloud-connected sensors, all data that the sensor detects is displayed in the sensor console, but alert information is also delivered to Azure, where it can be analyzed and shared with other Azure services.


<br/>
<br/>

# Onboard your subscription to Defender for IoT 

- Open [Defender for IoT](https://portal.azure.com/#view/Microsoft_Azure_IoT_Defender/IoTDefenderDashboard/%7E/Getting_started) in the Azure portal, select **Getting Started**, then **Setup OT/ICS Security**

![](/assets/img/OT_Sensor/Getting_Started.jpg)

- Scroll down to **Register** and select **Onboard Subscription**

![](/assets/img/OT_Sensor/onboard_Sub1.jpg)

<br/>


- The Price plan value is updated automatically to read Microsoft 365, reflecting your Microsoft 365 license.

- Select the Subscription you want to onboard and purchase the plan that's right for you:

![](/assets/img/OT_Sensor/onboard_Sub2.jpg)

<br/>

- Select Next and review the details for your licensed site. The details listed on the Review and purchase pane reflect your license.

- Select the terms and conditions, and then select Save.

Your new plan is listed under the relevant subscription on the Plans and pricing > Plans page. For more information, see [Manage your subscriptions](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/how-to-manage-subscriptions).

<br/>

>&#128161; Pro-Tip: _You can use the above steps to spin up a trial too, if you'd like to take it for a test drive first._

<br/>
<br/>

# Deploy an Operational Technology (OT) Sensor on a Virtual Appliance 

The OT Network Sensor supports Hyper-V and VMWare virtual appliances. For this article, I've spun up a VM in Hyper-V. Configure how beefy your appliance needs to be according to the minimum requirements listed [here](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-virtual-appliances#ot-network-sensor-vm-requirements). Since this is a lab environment, I went with the L100 hardware profile.

<br/>

- 1. Create the virtual machine using Hyper-V:

	- On the Actions menu, create a new virtual machine.

	- Enter a name for the virtual machine.

	- Select **Generation** and set it to **Generation 2,** and then select Next:

    ![](/assets/img/OT_Sensor/gen2.jpg)

    <br/>

	- Specify the memory allocation according to your organization's needs, in standard RAM denomination (I chose the minimum: 8192MB). **Don't enable Dynamic Memory.**

	- Allocate CPU resources according to your organization's needs.

    - Do not configure a virtual disk for storage (yet).

    ![](/assets/img/OT_Sensor/HDDLater.jpg)

    <br/>

	- Connect the OT Sensor software ISO image to a virtual DVD drive.
    
    - Select Firmware, in Boot order move DVD Drive to the top of the list, select Apply and then select OK.

    ![](/assets/img/OT_Sensor/mountISO.jpg)

	<br/>
    <br/>


- 2. Configure Networking:

      - You'll need to configure at least two network adapters on your VM: one to connect to the Azure portal, and another to connect to traffic mirroring ports.
    
         - Network adapter 1, to connect to the Azure portal for cloud management.

         - Network adapter 2, to connect to a traffic mirroring port that's configured to allow promiscuous mode traffic. If you're connecting your sensor to multiple traffic mirroring ports, make sure there's a network adapter configured for each port.
       
	  - Right-click on the new virtual machine, and select Settings.

	  - Select Add Hardware, and add a new network adapter.

![](/assets/img/OT_Sensor/NIC1.jpg)

  - Select the virtual switch that connects to the sensor management network.
    
  - Configure the network adaptor according to your server network topology. Under the "Hardware Acceleration" blade, disable "Virtual Machine Queue" for the monitoring (SPAN) network interface.

<br/>
<br/>

- 3. Create a virtual disk in Hyper-V Manager (**Fixed size**, as required by the hardware profile).

	    - Select format = **VHDX.**

![](/assets/img/OT_Sensor/VHDX.jpg)

- Enter the name and location for the VHD.

- Enter the required size according to your organization's needs (select **Fixed Size disk type**).
	
![](/assets/img/OT_Sensor/Fixed.png)



- Review the summary, and select Finish.

![](/assets/img/OT_Sensor/VHDXHDD.jpg)



- Connect the VHDX to your virtual machine:

![](/assets/img/OT_Sensor/HDD2.jpg)


<br/>
<br/>
    
- 4. Install & Register OT Network Sensor software.

	    - Start the virtual machine.

	    - When the installation boots, you're prompted to start the installation process. Either select the Install **iot-sensor-<.version number>** item to continue, or leave the wizard to make the selection automatically on its own:

        ![](/assets/img/OT_Sensor/install1.png)

        - If you've configured your NICs to an external vSwitch for connectivity, it will prompt you with an IP address you can use to activate your sensor via browser:

        ![](/assets/img/OT_Sensor/Login1.jpg)

        - Navigate to that IP address ending in .101 and sign in with **admin/admin** to change the default password and complete the deployment. 

        - While logged in via browser, navigate to the **Register** tab and upload the registration file from earlier. 




<br/>

>&#128161; Pro-Tip: _The wizard automatically selects to install the software after 30 seconds of waiting._

<br/>
<br/>

# Defend your IoT Dojo like a Ninja!



<br/>
<br/>

<br/>
<br/>

# Ian's Insights:

<br/>
<br/>

![](/assets/img/OT_Sensor/D4IOT.jpg)

<br/>
<br/>

# Thanks for Reading! 

If you've made it this far, thanks for reading! All the scripts referenced in this blog post can be found in my [MDI repository](https://github.com/EEN421/Defender-for-Identity) on [Github](https://github.com/EEN421).

<br/>
<br/>

# Helpful Links & Resources:

- https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/ot-deploy-path

- https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/onboard-sensors

- https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/getting-started?tabs=wizard

- https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-virtual-appliances

- https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-virtual-appliances#ot-network-sensor-vm-requirements

- https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/install-software-ot-sensor#install-defender-or-iot-software-on-ot-sensors

- https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/activate-deploy-sensor



<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)

