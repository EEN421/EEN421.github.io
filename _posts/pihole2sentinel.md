# Introduction & Use Case:
You're troubleshooting a mysterious bandwidth hog &#x1F416; in your network, only to discover that the culprit is the very same employee who asked you to look into it &#x1F601;&#x2757; With March Madness just around the corner, that user is streaming the latest <font color="ligblue">KY Wildcat basketball games </font> on the ESPN app (<font color="ligblue">Go Cats! &#x1F63A;</font>). You need to preserve bandwidth and maintain compliance… What do you do?

To make it more fun, this organization is operating on a shoestring budget and ad-hoc basis, so <font color="red">you cannot leverage Intune, SCCM, or GPO,</font> _but hey, users are **Microsoft 365 A5** licensed._ 

In my experience, my favorite is the 'scream test' and it goes one of two ways if implemented correctly:<br/>

-    If they know they're not supposed to have access, they're not going to complain when it gets cut off &#x1F609;	. <br/>

-    You'll see who screams and quickly learn how important the application you just disabled is to productivity &#x1F4B2; &#x1F4B2; &#x1F4B2;.
  
>&#128161; Pro-Tip:Make sure to document that somewhere safe and accessible for the new kids on the block . <br/>

This blog post will guide you through deploying Defender for Cloud Apps from the ground up and integrating it seamlessly with Microsoft Defender for Endpoint to effectively block or unsanction unwanted applications that don't meet your requirements (SOC2, GDPR, PIPEDA, CMMC, NIST, just to name a few). This ensures your cloud infrastructure remains secure, compliant, effective, and cost-efficient (even if you're just trying to conserve bandwidth during the sweet 16 &#x1F3C0;).

Whether you're an IT/SecOps professional or a Security & Compliance enthusiast, this comprehensive guide will provide you with the Defender for Cloud Apps knowledge and insights you need to identify and keep those bandwidth hogs at bay&#x1F43D;, lock down your environment&#x1F512;, and knock those compliance scores out of the park &#x2705;

<br/>

![](/assets/img/Defender%20for%20Cloud%20Apps/Microsoft-Defender-for-Cloud-Apps.jpg)


<br/>
<br/>


# In this Post We Will:
- &#128295; Spin up a Log Analytics Workspace in Azure and Deploy Microsoft Sentinel
- &#x1F525; Burn an SD Card with Raspi Imager
- &#x1F967; Perform a Headless Setup for a new Raspberry Pi and connect it to the Network
- &#x1F310; Deploy Network Wide PiHole DNS Protection 
- &#128268; Onboard PiHole DNS Telemetry to Microsoft Sentinel
- &#x1F50D; Query Network Logs with KQL
- &#x26A1; Acieve Network Superiority
- &#128161; Ian's Insights.

Unused emojies:
- &#x1F6AB;	 
- &#x2714;
- &#x1F6A7;	
- &#x1F967;
- &#x1F9E9;
- &#x1F5A5;


<br/>
<br/>

<br/><br/>

# Hardware Details: 

Pi-hole is very lightweight and doesn't need much in terms of processing power. Here are the minimum requirements: 

- Min. 2GB free space, 4GB recommended
- 512MB RAM

>&#128161; You can even get a Pi-hole branded kit, including everything you need to get started, from The Pi Hut, [here](https://thepihut.com/products/official-pi-hole-raspberry-pi-4-kit).
<br/><br/>

# Sofware | OS Details:
- These steps have been tested with [Raspbian Bookworm OS](https://www.raspberrypi.com/news/bookworm-the-new-version-of-raspberry-pi-os/), the [latest Raspberry Pi operating system](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-64-bit) at the time of this article. 

![](/assets/img/IoT%20Hub/Headless%20Setup/bookworm_01-768x518.jpg)

<br/><br/>


<br/><br/>

# Create a Log Analytics Workspace
- Navigate to Log Analytics Workspace in Azure Portal: <br/>
![](/assets/img/iot/LAW1.png)

<br/><br/>

- Select **+Create**  <br/>
![](/assets/img/iot/LAW2.png)

<br/><br/>

- Select **Subscription** and **Resource Group:** <br/>
![](/assets/img/iot/LAW3.png)

<br/><br/>

- Select Instance **Name** and **Region:** <br/>
![](/assets/img/iot/LAW4.png)

<br/><br/>

- Pricing Tier:
Choose the appropriate commitment tier given your expected daily ingest volume. <br/><br/>

&#128161;
	&#128073;      **_I like to see roughly 15% more ingest than required for the next pricing tier to insulate against nights, weekends, and holidays which inherently drag down the daily ingest volume average._** 

<br/>

- Click **Review & Create** to finish setting up a new Log Analytics Workspace 

<br/><br/>

# Retrieve WorkspaceID and Primary Key
![](/assets/img/iot/WorkspaceIDandKey.png)

<br/><br/>

# &#x1F525; Burn an SD Card with Raspi Imager

- Grab a free copy of the Raspberry Pi Imager software from the official site at [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/) 

- Insert your SD card and fire it up! 
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Menu.png)

- Choose the Raspberry Pi model you're going to run this on (I'm doing this on a Raspbery Pi 4 Model B):
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Device.png)

- Select the Raspbian OS version you want to burn. I prefer lightweight so I went with RPi Bookworm 64 OS Lite (no Desktop) and the remainder of this guide will follow suit.
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS1.png)
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS2.png)

- Specify your SD Storage card in Storage options:
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Storage.png)

- Select **Next** to trigger an OS Customization Pop-Up, then select **Edit Settings**
    ![]( /assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS_Settings.png)

- Here you will be presented with the option to set the hostname, default username and password, Wifi SSID and PSK, and Locale:
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS_General.png)

- Move to the **Services** tab to enable SSH. This is an essential part of the "headless" style setup and allows you to SSH in from another computer on the network. This way you don't need a dedicated keyboard and monitor to interact with it.
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS_Services.png)

- Lastly, move over to the **Options** tab to configure additional burn settings, like making a sound when it's done. 
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS_Options.png)

- When you've configured your burn options, select **Save** and then **Yes**, followed by another **Yes**:
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Warning.png)

- Burn baby burn! 
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Writing.png)

<br/>
<br/>


# Ian's Insights:

Ever use a DNS Sink Hole like a Pi-Hole (raspberry Pi powered)? This functioned pretty much the same way by refusing to resolve addresses known to host the application we are blocking. A Pi-Hole will actually resolve the addresses but send the results to an IP that doesn't exist (hence "sinkhole"). Web pages load faster when they don't have to resolve all the "junk" ads from IP's known to host rubbish etc. 

What happens if someone has already downloaded the Steam Games app and signed in before you've unsanctioned the application? Because they've signed in, the app has already 'phoned home' and retrieved a new token for authentication. The application will continue to work until the token expires and the app is forced to try and phone home for a new key and gets intercepted when it tries to resolve to the address block associated with Steam Games, at which point it will fail. This means that a user could potentially continue to use an un-sanctioned application temporarily until it's token expires.  

Lastly, consider going to the **unified security portal >> settings >> cloud apps >> Exclude Entities** and adding an exclusion so you can watch the finals &#x1F61C;

<br/>
<br/>

# In this Post We:
- ⚡ Deployed Defender for Cloud Apps.
- 🔧 Integrated with Defender for Endpoint.
- 🔌 Onboarded a Device to Defender for Endpoint.
- ✔ Confirmed our Defender for Endpoint AV Configuration.pre-requisites without Intune, SCCM, or GPO (spoiler alert: it was powershell).
- &#x1F50D; Investigated Application Usage
- 🚫 Un-sanctioned an Unwanted Application.
- 🚧 Un-sanctioned an unwanted Application on your Firewall (for devices that don't support the MDE agent).

<br/>
<br/>

# Thanks for Reading!
 I hope this was a much fun reading as it was writing. What will you block from your environment first? 

<br/>

![](/assets/img/Defender%20for%20Cloud%20Apps/MDCA_Logo_Square.jpg)

<br/>
<br/>

# Helpful Links & Resources: 

<br/>

- [https://learn.microsoft.com/en-us/powershell/module/defender/?view=windowsserver2025-ps#defender](https://learn.microsoft.com/en-us/powershell/module/defender/?view=windowsserver2025-ps#defender)

- [https://learn.adafruit.com/pi-hole-ad-blocker-with-pi-zero-w/install-pi-hole](https://learn.adafruit.com/pi-hole-ad-blocker-with-pi-zero-w/install-pi-hole)

- [https://learn.microsoft.com/en-us/defender-cloud-apps/](https://learn.microsoft.com/en-us/defender-cloud-apps/)

- [https://learn.microsoft.com/en-us/defender-endpoint/configure-endpoints-script](https://learn.microsoft.com/en-us/defender-endpoint/configure-endpoints-script)

<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
