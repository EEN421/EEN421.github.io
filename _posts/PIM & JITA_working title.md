# Introduction & Use Case:
During a regular security audit, you've discovered several jump boxes with network access to sensitive corporate resources (such as mission-critical production SQL databases) are exposed via RDP port 3389 to the internet and you need to lock them down. 

The Change Management Board has given some push back: they have approved, given the following requirements are satisfied as a part of the solution: 

- Users are required to put in an access request that must be approved by a manager before they can connect to the jump box. 

- Requests must be logged with justification. 

- Network Access must be provisioned when necessary only.

You're no stranger to danger and know that the best way to do this is a combination of Privileged Identity Management (PIM) and Just-in-Time-Administration (JITA) because JIT is about controlling when and how a VM can be accessed, and PIM is about managing who has access to resources and when they have that access. Both are important for maintaining a secure environment in Azure.

<br/>
<br/>

# In this Post We Will: 

- &#x1F4BB; Define a "Jump Box" and when to use one. 
- &#128272; Define & Deploy Privileged Identity Management (PIM).
- &#x26A1; Define & Deploy Just-in-Time-Administration (JITA).
- &#128170; Secure Corporate Resources and Lock Down our Jump Box.
- &#x1f977; Defend your Dojo like a Ninja! 

<br/>
<br/>

![](/assets/img/JITA_PIM/Default_Two_mysterious_ninjas_cloaked_in_dark_indigo_robes_eme_3.jpg)

<br/>
<br/>

# What's a Jump Box Again? 
A jump box is a network device that enables secure access to servers or other devices, acting as a gateway. It’s particularly useful when accessing sensitive resources like a mission-critical SQL database remotely without exposing it directly to the internet (you gotta hit the 'jump box' before you can access the resource). 

However, if not properly secured, it can pose a super-massive risk to your network’s security so it’s crucial that it’s well-protected.

<br/>
<br/>


>&#128161; Pro-Tip: _The standalone Enterprise IoT Sensor has been decommissioned in favour of leveraging the Defender for Endpoint agents to cover Enterprise IoT Devices such as VoIP systems, smart TVs and printers etc. so you no longer need to deploy it manually, just integrate Defender for Endpoint in Endpoint settings and again in Defender for IoT._

<br/>
<br/>


<br/>

>&#128161; BullsEye OS has many known security CVEs that were plugged up with the release of the newer Bookworm OS. Check out my earlier blog article that discusses the security upgrades included with Bookworm that are still unresolved in BullsEye [here](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/). Here's one such example known as [Dirty Pipe (aka CVE-2022-0847)](https://forums.raspberrypi.com/viewtopic.php?t=331022) that's applicable to BullsEye OS.



<br/>
<br/>

# Thanks for Reading! 

If you've made it this far, thanks for reading! I hope this has been a helpful guide for getting started with Defender for IoT and deploying your first of many OT Network Sensors! 

<br/>
<br/>

![](/assets/img/OT_Sensor/Scorpion_IoT_Picnic.jpg)

<br/>
<br/>


# Helpful Links & Resources:

- [https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/ot-deploy-path](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/ot-deploy-path)

- [https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/onboard-sensors](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/onboard-sensors)

- [https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/getting-started?tabs=wizard](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/getting-started?tabs=wizard)

- [https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-virtual-appliances](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-virtual-appliances)

- [https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-virtual-appliances#ot-network-sensor-vm-requirements](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-virtual-appliances#ot-network-sensor-vm-requirements)

- [https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/install-software-ot-sensor#install-defender-or-iot-software-on-ot-sensors](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/install-software-ot-sensor#install-defender-or-iot-software-on-ot-sensors)

- [https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/activate-deploy-sensor](https://learn.microsoft.com/en-us/azure/defender-for-iot/organizations/ot-deploy/activate-deploy-sensor)

<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
