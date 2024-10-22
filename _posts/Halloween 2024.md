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

The pair of eyes I've previously setup were too bulky to fit inside a mask, so I bought a slimmed down [Adafruit Monster M4SK](https://www.adafruit.com/product/4343) (board build in, less bulky) and a cheap [Lithium Ion Cylindrical Battery (3.7v, 2200mAh)](https://www.adafruit.com/product/1781). The results are awesome. Let's dig in...

I'll break this out into **two parts** and start with the basic [Raspberry pi build](https://www.adafruit.com/product/3356), then the final [Monster M4SK build](https://www.adafruit.com/product/4343). I've posted a **step-by-step guide** to [setting up a headless raspberry pi](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/) using a [custom.toml file](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iothub/custom.toml), which replaces the [WPA_supplicant.conf file](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/wpa_supplicant.conf_) used previously and handles **hostname, default account configuration, enables SSH, WLAN config, and Locale** on Bookwork OS and later. HOWEVER... the [Animated Eyes Bonnet for Raspberry Pi](https://www.adafruit.com/product/3356) is **not compatible** with **Bookworm** so we have to use the older **[BullseyeOS](https://www.raspberrypi.com/software/operating-systems/)**. To keep things easy, I used the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) this time around. 

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
<br/>
<br/>

# Perform a Headless Raspberry Pi Setup (BullseyeOS)
-1. Grab the OS image from the [official Raspberry Pi site](https://www.raspberrypi.com/software/operating-systems/) (don't extract, leave it as is).

<br/>
<br/>

-2. Insert your SD card into the reader and run the Raspberry Pi Imager ([available here](https://www.raspberrypi.com/software/)). <br/>
![](/assets/img/Halloween24/pi_image_blank.png)

<br/>
<br/>

-3. Select your hardware, desired OS, and destination storage (SD Card) as illustrated below... <br/>
![](/assets/img/Halloween24/pi_image_fin.png)

>&#128161; IMPORTANT --> Make sure you grab the **legacy 32bit Bullseye OS**; as this software is **not supported as-is on the latest Bookworm OS** ![](/assets/img/Halloween24/pi_image_OS.png)

<br/>

-4. Select **Next** and you will be prompted with the option to **edit OS settings**. Select **Edit** and enter your network SSID and PSK, as well as your desired username and password. <br/>
![](/assets/img/Halloween24/pi_image_settings.png)

<br/>
<br/>

-5. Navigate from the **General** tab over to the **SSH** tab and make sure it's **enabled** with **password authentication** as shown below... <br/>
![](/assets/img/Halloween24/pi_image_settings2.png)

<br/>
<br/>

-6. Click **Next** and let it burn! <br/>
![](/assets/img/Halloween24/pi_image_write.png) <br/>
![](/assets/img/Halloween24/pi_image_done.png)

-7. Drop the SD card into your Raspberry Pi board and boot it up.

-8. Locate it on the network (login to your router or use [Advanced IP Scanner](https://www.advanced-ip-scanner.com/))

# Connect our Hardware

>&#128161; Developer's Notes --> The code for this project only works with the Adafruit 128x128 pixel OLED and TFT displays and 240x240 pixel IPS TFT displays. 

Any recent Raspberry Pi board with the 40-pin GPIO header should work. The very earliest Pi boards — Model A and B, with the 26-pin GPIO header — are not compatible.

A Raspberry Pi 2 or greater is highly recommended. The code will run on a Pi Zero or other single-core Raspberry Pi boards, but performance lags quite a bit. Pi 4 works now, which was previously incompatible.

Here's the PIN-OUT: <img src="https://cdn-learn.adafruit.com/assets/assets/000/037/987/original/raspberry_pi_TFTs.png?1481652018">


It's important to get this right. I know it seems simple, but the connections have to be 1:1

Here's what not to do: <br/>
![](/assets/img/Halloween24/wrong.png)

<br/>
<br/>

Here's how you want it:
![](/assets/img/Halloween24/Correct.png)

Seems obvious, but just recheck before you boot up. 


# Deploy Snake Eyes

>&#128161; Developer's Notes:
>-  If using a Raspberry Pi 4, Pi 400, or Compute Module 4: the latest "Bullseye" Raspberry Pi OS Desktop software is required (“Lite” versions, and versions prior to “Bullseye” in late 2021, won’t support this code on these boards). For brevity, we’ll call all of these boards “Pi 4” going forward in this guide. <br/><br/>
>- All other Raspberry Pi boards: Raspberry Pi OS Lite (Legacy) software is required. Look for both Lite and Legacy in the name! <br/><br/>
>- For all boards: use the 32-bit version of the operating system, not the 64-bit variant.

-1. Log into your Raspberry Pi with the IP address we discovered earlier, using the username and password we defined using the Raspberry pi Imager. 

-2. Run the following command to get install script:
```bash
curl https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/pi-eyes.sh >pi-eyes.sh
```
<br/>

![](/assets/img/Halloween24/CURL.png)

<br/>
<br/>

![](/assets/img/Halloween24/pi-eye_script.png)

<br/>
<br/>

Run the script with:
```bash
sudo bash pi-eyes.sh
```

<br/>

Run the script installs Adafruit Snake Eyes Bonnet software for your Raspberry Pi and will prompt you for the following (my answers are in '()' and correspond with the hardware listed earlier): 

- Select screen type? (mine are #3, a 240x240 IPS)
- Install GPIO-halt utility? (N)
- Install Bonnet ADC support? (N)
- Install USB Ethernet gadget support? (N)
- Do you understand and wish to proceed? (y)

<br/>

![](/assets/img/Halloween24/Eye_script.png)

<br/>
<br/>

Your Pi will reboot and, if the screens are connected correctly, you'll see a pair of eyes looking back at your after about a minute or two. 

<br/>

![](/assets/img/Halloween24/Alive1.jpg) ![](/assets/img/Halloween24/Alive2.jpg)

<br/>
<br/>
<br/>

# Customize Eye shapes, colours, iris, sclera, etc.

There's a fantastic deep dive into writing custom eyeballs from scratch [here on Adafruit.com](https://learn.adafruit.com/animated-snake-eyes-bonnet-for-raspberry-pi/customizing-the-look) that I highly recommend checking out. However, we're going to tweak the existing code to take this to the next level. The texture maps for some extra creepy eyes are hidden in your Pi, we just need to copy the default python script and edit it to point to the 'dragon' iris, sclera, and map shown here: <br/>

![](/assets/img/Halloween24/eye_stuff.png)

<br/>
<br/>

-1. Log back into your raspberry pi and cd .. a couple times back to the root and list the contents of **boot/Pi_Eyes** as illustrated below. We're looking for the **eyes.py** file:
![](/assets/img/Halloween24/ls_eyes.png)

<br/>
<br/>

-2. Copy this guy over to a new file called **demon.py** with the following command:

```bash
sudo cp boot/Pi_Eyes/eyes.py boot/Pi_Eyes/dragon.py
```

Then list the contents again to see it:
![](/assets/img/Halloween24/ls_demon.png)

We're going to edit this file in the next step. 

<br/>
<br/>

-3. Use your favourite text editor (don't judge, nano is just easy :D ) to open up the new **dragon.py** file we just created.
```bash
sudo nano boot/Pi_Eyes/dragon.py
```

<br/>
<br/>

-4. Make the following changes: <br/>
![ORIGINAL](/assets/img/Halloween24/originalSVG.png) <br/>
![DRAGON](/assets/img/Halloween24/dragonSVG.png) <br/>

<br/>

![](/assets/img/Halloween24/OriginalTextureMap.png) <br/>
![](/assets/img/Halloween24/TextureMap.png) <br/>




![]()

# Ian's Insights:

The ability to swiftly respond to threats is crucial in cybersecurity, but even the best Security Operations Centers (SOCs) can face challenges like RBAC configuration mishaps. With the upcoming enforcement of Multi-Factor Authentication (MFA), relying on user-based service accounts for automation is becoming impractical. By registering an app in EntraID and using PowerShell to automate tasks in Microsoft Defender, you can ensure your SOC remains agile and responsive. 

<br/>
<br/>

# In this Post We:

Part 1:
- &#128190; Performed a Headless Raspberry Pi Setup (BullseyeOS).
- &#128268; Connected our Hardware & Deploy our Software Eyes.
- &#128064; Customized Eye shapes, colours, iris, sclera, etc. 
- &#127875; Lit up a Pumpkin! 

Part 2:
- &#128297; Customized our Monster M4SK.  
- &#128295; Extended the distance between the eyes.
- &#128123; Spooked the neighbour's kids! 

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
