# Introduction & Use Case:
You've deployed your sensors through Azure IoT Hub and onboarded your telemetry to a Log Analytics Workspace, but you're a ninja and know there's more to defending your shinobi dojo and it's IoT infrastructure... Enter the Defender for IoT Operational Technology (OT) sensor! 

<br/>

![](/assets/img/OT_Sensor/cartoon_ninja.jpg)

<br/>
<br/>

# In this Post We Will: 

- &#x1f977; Onboard your subscription to Defender for IoT 
- &#x1f977;; Deploy an Operational Technology (OT) Sensor on a Virtual Appliance
- &#x1f977; Defend your IoT Dojo like a Ninja! 



<br/>
<br/>


Microsoft Defender for IoT OT Sensor is a component of the Microsoft Defender for IoT system designed to provide broad coverage and visibility from diverse data sources. It’s essentially a network sensor that discovers and continuously monitors network traffic across your network devices (the network cap feature makes it perfect to for LoRaWAN deployments). These sensors are purpose-built for OT/IoT networks and connect to a SPAN port or network TAP. They use OT/IoT-aware analytics engines and Layer-6 Deep Packet Inspection (DPI) to detect threats, such as fileless malware, based on anomalous or unauthorized activity.
<br/>

The Defender for IoT OT Sensor is a great way to complete our sensor deployment if you’ve been reading and following my prior Sentinel Integrated Soil Sensor articles for my peppers, as it enhances the security of an IoT Hub deployment by providing additional layers of visibility, threat detection, and analysis, thereby implementing a Zero Trust security strategy:

&#x26A1; 1.	Real-time Information Extraction: Azure Defender for IoT uses passive monitoring and Network Traffic Analysis (NTA) combined with patented, IoT/OT-aware behavioral analytics to extract detailed IoT/OT information in real-time.

&#x26A1; 2.	Agentless Security: It delivers agentless security for continuously monitoring OT networks in industrial and critical infrastructure organizations. This is particularly useful for existing devices that might not have built-in security agents.

&#x26A1; 3.	Deployment Flexibility: You can deploy these capabilities fully on-premises without sending any data to Azure3, which can be ideal for locations with low bandwidth or high-latency connectivity.

&#x26A1; 4.	Cloud Connectivity: When configured as cloud-connected sensors, all data that the sensor detects is displayed in the sensor console, but alert information is also delivered to Azure, where it can be analyzed and shared with other Azure services.

![](/assets/img/OT_Sensor/D4IOT.jpg)

<br/>
<br/>



<br/>
<br/>

# Thanks for Reading! 

If you've made it this far, thanks for reading! All the scripts referenced in this blog post can be found in my [MDI repository](https://github.com/EEN421/Defender-for-Identity) on [Github](https://github.com/EEN421).

<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)

