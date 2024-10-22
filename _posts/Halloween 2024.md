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

-1. Log back into your raspberry pi and cd .. a couple times back to the root and list the contents of **boot/Pi_Eyes** as illustrated below. We're looking for the **eyes.py** file: <br/>
![](/assets/img/Halloween24/ls_eyes.png)

<br/>
<br/>

-2. Copy this guy over to a new file called **dragon.py** with the following command:

```bash
sudo cp boot/Pi_Eyes/eyes.py boot/Pi_Eyes/dragon.py
```

<br/>
<br/>

Then list the contents again to see it: <br/>
![](/assets/img/Halloween24/ls_dragon.png)

<br/>

We're going to edit this file in the next step. 

<br/>
<br/>

-3. Use your favourite text editor (don't judge, nano is just easy &#128123;) to open up the new **dragon.py** file we just created.
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
![](/assets/img/Halloween24/TextureMaps.png) <br/>


-5. Lastly, we need to swap out the default .py file used in rc.local for boot up and reboot to see our regular eyes morph into dragon eyes! &#128064;

Use the following command to edit the rc.local file as shown below: <br/>

```bash
sudo nano /etc/rc.local
```

<br/>

![ORIGINAL RC.LOCAL](/assets/img/Halloween24/original_RCLOCAL.png) <br/>

![NEW RC.LOCAL](/assets/img/Halloween24/New_RCLOCAL.png) <br/>

<br/>

-6. Reboot and sit back with the following:

```bash
sudo reboot now
```

<br/>

# Part 2
# Customize our Monster M4SK
So the dragon eyes we just built were pretty cool, but kinda bulky and heavy to integrate into any decent halloween outfit. I'm going to pop this guy into an empty skull or a carved out pumpkin this year. For my actual costume, I thought we could do better. 

Enter the [Adafruit Monster M4SK](https://www.adafruit.com/product/4343). This thing is awesome. It's got a small form factor processor in the back that's powerfull enough to run the eyes on both screens effortlessly without the bulk and weight of a Raspberry Pi.

Here's a great [guide for breaking the eyes apart and connecting them back together with a JST cable on Adafruit.com](https://learn.adafruit.com/wide-set-monster-m4sk-creature-eyes/separate-the-monster-m4sk). The only issue I had was that, even with the 100mm cable, the eyes were far apart enough to fit our mask. Time to bust out the soldering iron. 

I had 2 of these 100mm JST cables handy, so I snipped the ends off of both and soldered them together to make a (almost) 200mm cable, more than enough. [Phillip Burgess](https://learn.adafruit.com/u/pburgess) wrote a killer guide for the same mask [here](https://learn.adafruit.com/spruce-up-a-costume-with-monster-m4sk-eyes-and-voice/overview) (maybe next year I'll add the voice modulator)

You'll need some heat shrink tubing for this. A hair dryer will do if you don't have a heat gun. Electrical tape will do for any you miss. 

-1. Plug your Monster M4SK into your computer and you should see the CIRCUIPY drive mounted: <br/>

![](/assets/img/Halloween24/M4SK_folder.png) <br/>

<br/>

-2. Download additional eyes via zip file [here](https://learn.adafruit.com/elements/3037483/download?type=zip) from [learn.adafruit.com](https://learn.adafruit.com/adafruit-monster-m4sk-eyes/graphics)

<br/>

Once you've got the eyes you want and their respective folders uploaded to the Monster M4Sk, all you have to do is **copy the config.eye** file you want to use, to the root (the odefault eye is "hazel" and the original **config.eye** is in the "hazel" folder; if you ever need to go back, just copy the **config.eye** from the hazel folder to root and reboot). <br/>

![](/assets/img/Halloween24/config_copy.png)

<br/>

To swap out your eyes, it's as easy and swapping out the config.eye file from the folder containing the eyes you want. 

I used some styrofoam and a sharpie to black out the board around the displays, then taped them to the inside of the mask. My vision isn't obstructed because the primary viewpoint is through the nostrils of this haunted goat thing. I've also taped that [Lithium Ion Cylindrical Battery (3.7v, 2200mAh)](https://www.adafruit.com/product/1781) to the inside of one of the horns (I swear this mask was made for this). 



# Ian's Insights:

It’s refreshing to take a break from the norm and dive into something fun, like creating cool projects for Halloween. Making time for side projects like this helps keep me sharp when it’s time to get back to work. Just remember to gather your supplies early and make time to screw around. Happy Halloween!

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
