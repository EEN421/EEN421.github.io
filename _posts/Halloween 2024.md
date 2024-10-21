# Introduction & Use Case:
&#127875; Hey Readers! &#127875; It’s been a while since my last post, and for that, I sincerely apologize. We’re back just in time for the spookiest season of the year! 

This post is all about getting your creative juices flowing with a juicy DIY Halloween project. Whether you’re looking to craft eerie decorations, whip up some spooky treats, or design the ultimate costume, this is your place to be!

Let’s dive into the fun and make this Halloween the best one yet! 👻

# emjoi bank:
&#128123; ghost
&#127875; pumpkin/jack-o-lantern
&#128375; Spider
&#128376; spider web
🕸️

<br/>

![](/assets/img/Halloween24/Banner1.jpg)

<br/>
<br/>

# What are we building?:
My daughter picked out a sweet halloween mask and I thought to myself... how can we elevate this? 
I've worked on a pair of Raspberry Pi powered 'eyeballs' in the past (great to stick inside a carved out pumpkin) and thought they would be cool in a mask.

The pair of eyes I've previously setup were too bulky to fit inside a mask, so I bought a slimmed down Monster M4SK (board build in, less bulky) and a cheap Lithium Ion Cylindrical Battery (3.7v, 2200mAh). The results are awesome. Let's dig in...

Lets start with the Raspberry pi build. I've posted a step-by-step guide to [setting up a headless raspberry pi](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/) using a [custom.toml file](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iothub/custom.toml), which replaces the [WPA_supplicant.conf file](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/wpa_supplicant.conf_) used previously and handles hostname, default account configuration, enables SSH, WLAN config, and Locale on Bookwork OS and later. HOWEVER... the [Animated Eyes Bonnet for Raspberry Pi](https://www.adafruit.com/product/3356) is not compatible with Bookworm so we have to use the older BullseyeOS. To keep things easy, I used the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) this time around. 

Setup 

&#128187; computer
&#x1F511;

<br/>
<br/>

# In this Post We Will:
Part 1:
- &#128190; Perform a Headless Raspberry Pi Setup (BullseyeOS).
- &#128268; Connect our Hardware & Deploy our Software Eyes.
- &#128064; Customize Eye shapes, colours, iris, sclera, etc. 
- &#127875; Light up a Pumpkin! 

Part 2:
- &#128297; Customize our Monster M4SK.  
- &#128295; Extend the distance between the eyes.
- &#128123; Spook the neighbour's kids! 

<br/>
<br/>

# Hardware Pre-Requisites

For a bulkier build suitable for inside a carved pumpkin, I used the following: 
https://www.adafruit.com/product/3356 
https://a.co/d/72oBlGg
https://www.adafruit.com/product/3055


For the final, slimmer Mask build, i used the following: 
https://www.adafruit.com/product/1781
https://www.adafruit.com/product/4350
https://www.adafruit.com/product/4343
Some Duct Tape
Some Styrofoam
Soldering Iron
Heat Shrink Tubing (small)
Stuff...

<br/>
<br/>



>&#128161; WARNING!!! --> You can ONLY view the secret value once... when you navigate away from the page it will no longer be available ![](/assets/img/IOC/Secret_Warning.png)

<br/>



<br/>
<br/>


# Ian's Insights:

The ability to swiftly respond to threats is crucial in cybersecurity, but even the best Security Operations Centers (SOCs) can face challenges like RBAC configuration mishaps. With the upcoming enforcement of Multi-Factor Authentication (MFA), relying on user-based service accounts for automation is becoming impractical. By registering an app in EntraID and using PowerShell to automate tasks in Microsoft Defender, you can ensure your SOC remains agile and responsive. 

<br/>
<br/>

# In this Post:

- &#128268; Registered an Application in Entra ID
- &#x1F512; Managed Application Permissions (Principle of Least Privilege)
- &#x1F511; Configured Application Authentication & Authorization
- &#128297; Built a powershell script to grab our token
- &#128295; Built a powershell script to submit our custom IoC
- &#128296; Ran it!

<br/>
<br/>

# Thanks for Reading!
This approach not only streamlines threat response but also strengthens your overall security posture, maintaining continuous protection against emerging threats. This guide will equip you with the knowledge to keep your defenses strong and your response times ninja swift. 🥷 

<br/>
<br/>

# Helpful Links & Resources: 

- [Quickstart: Register an application with the Microsoft identity platform](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app?tabs=certificate)

- [Entra ID app registrations and service principals](https://petri.com/microsoft-entra-id-app-registration-explained/#:~:text=App%20registrations%20are%20primarily%20used%20by%20developers%20who,app%20in%20the%20directory%20in%20the%20developer%C3%A2%C2%80%C2%99s%20tenant.)

- [Pushing custom Indicator of Compromise (IoCs) to Microsoft Defender ATP](https://techcommunity.microsoft.com/t5/microsoft-defender-for-endpoint/pushing-custom-indicator-of-compromise-iocs-to-microsoft/m-p/532203)

- [WDATP API “Hello World” (or using a simple PowerShell script to pull alerts via WDATP APIs)](https://techcommunity.microsoft.com/t5/microsoft-defender-for-endpoint/wdatp-api-hello-world-or-using-a-simple-powershell-script-to/ba-p/326813)

- [Microsoft Defender ATP and Malware Information Sharing Platform integration](https://techcommunity.microsoft.com/t5/microsoft-defender-for-endpoint/microsoft-defender-atp-and-malware-information-sharing-platform/m-p/576648)

- [Origins of Defender NinjaCat](https://devblogs.microsoft.com/oldnewthing/20160804-00/?p=94025) 

<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
