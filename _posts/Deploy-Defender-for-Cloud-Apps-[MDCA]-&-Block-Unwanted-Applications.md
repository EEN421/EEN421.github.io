# Introduction & Use Case:
&#127875; This post is all about getting our creative juices flowing with a DIY Halloween project. 🕸️ Whether you’re looking to craft eerie decorations or design the ultimate costume, we're gonna take it to the next level... Let’s dive in and make this Halloween the best yet! &#128123;

<br/>

![](img) Why doesn't this work? 

<br/>
<br/>



# In this Post We Will:
**Part 1:**
- &#128190; Perform a Headless Raspberry Pi Setup (BullseyeOS).
- &#128268; Connect Hardware & Deploy Software Eyes.
- &#128064; Customize Eye Shape, Colour, Iris, Sclera, etc. 
- &#127875; Light up a Pumpkin! 

<br/>
<br/>

# Hardware Pre-Requisites

For a bulkier build suitable for inside a carved pumpkin, I used the following: 
- [Animated Eyes Bonnet for Raspberry Pi](https://www.adafruit.com/product/3356)
- [PiSugar S Plus Portable 5000 mAh UPS Lithium Battery Power Module](https://a.co/d/72oBlGg)
- [Raspberry Pi 4 Model B ](https://www.adafruit.com/product/4292)

<br/>
<br/>
<br/>
<br/>
<br/>

# Part 1 - Raspberry Pi Snake Eyes Bonnet

<br/>

> &#9940; NOTE: --> The [Animated Eyes Bonnet for Raspberry Pi](https://www.adafruit.com/product/3356) is **not compatible** with **BookwormOS** so we have to use the older **[BullseyeOS](https://www.raspberrypi.com/software/operating-systems/)**.

>&#128161; Developer's Notes:
>- All Raspberry Pi boards: Raspberry Pi Bullseye OS Lite (Legacy) software is required. Look for both Lite and Legacy in the name! <br/><br/>
>- For all boards: use the 32-bit version of the operating system, not the 64-bit variant.

<br/>
<br/>
<br/>
<br/>

# Perform a Headless Raspberry Pi Setup (BullseyeOS)


**1.** Grab the OS image from the [official Raspberry Pi site](https://www.raspberrypi.com/software/operating-systems/) (don't extract, leave it as is).

<br/>

**2.** Insert your SD card into the reader and run the Raspberry Pi Imager ([available here](https://www.raspberrypi.com/software/)). <br/>
![](/assets/img/Halloween24/pi_image_blank.png)

<br/>
<br/>

**3.** Select your hardware, desired OS, and destination storage (SD Card) as illustrated below... <br/>
![](/assets/img/Halloween24/pi_image_fin.png) <br/>

>&#128161; IMPORTANT --> Make sure you grab the **legacy 32bit Bullseye OS**; as this software is **not supported as-is on the latest Bookworm OS** ![](/assets/img/Halloween24/pi_image_OS.png)

<br/>

**4.** Select **Next** and you will be prompted with the option to **edit OS settings**. Select **Edit** and enter your network SSID and PSK, as well as your desired username and password. <br/>
![](/assets/img/Halloween24/pi_image_settings.png)

<br/>
<br/>

**5.** Navigate from the **General** tab over to the **SSH** tab and make sure it's **enabled** with **password authentication** as shown below... <br/>
![](/assets/img/Halloween24/pi_image_settings2.png)

<br/>
<br/>

**6.** Click **Next** and let it burn! &#128293; <br/>
![](/assets/img/Halloween24/pi_image_write.png) <br/>
![](/assets/img/Halloween24/pi_image_done.png)

**7.** Drop the SD card into your Raspberry Pi board and boot it up.

<br/>

**8.** Locate it on the network (login to your router or use [Advanced IP Scanner](https://www.advanced-ip-scanner.com/))

<br/>

**9.** Login and do the needful: <br/>

```bash
sudo apt-get update && sudo apt-get upgrade
```

<br/>
<br/>
<br/>
<br/>


>&#128161; FUN FACT --> you can change out the "splash.bmp" loading image with whatever you want and it will display on boot, as long as it's 240x240... <br/>
![](/assets/img/Halloween24/Splash.jpg) ![](/assets/img/Halloween24/Sauron.jpg)

<br/>
<br/>
<br/>
<br/>

# Ian's Insights:

It’s refreshing to take a break from the norm and dive into something fun, like creating cool projects for Halloween. I'm already thinking about plans for next year, like adding a voice modulator to the mask, or a motion sensor to the Raspberry Pi maybe... Making time for side projects like this helps keep me sharp when it’s time to get back to work. Just remember to gather your supplies early and make time to screw around.

<br/>
<br/>
<br/>
<br/>

# In this Post We:

**Part 1:**
- &#128190; Performed a Headless Raspberry Pi Setup (BullseyeOS).
- &#128268; Connected Hardware & Deployed Software Eyes.
- &#128064; Customized Eye Shapes, Colours, Iris, Sclera, etc. 
- &#127875; Lit up a Pumpkin! 

**Part 2:**
- &#128297; Customized our Monster M4SK.  
- &#128295; Extended the Distance Between Displays.
- &#128123; Spooked the Neighbour's Kids! 

<br/>
<br/>
<br/>
<br/>

# Thanks for Reading!
 I hope this was a much fun reading as it was writing. Happy Halloween!  

<br/>

![](/assets/img/Halloween24/Banner2.jpg)

<br/>
<br/>

# Helpful Links & Resources: 

- [Animated Eyes Bonnet for Raspberry Pi](https://www.adafruit.com/product/3356)
- [PiSugar S Plus Portable 5000 mAh UPS Lithium Battery Power Module](https://a.co/d/72oBlGg)
- [Raspberry Pi 4 Model B ](https://www.adafruit.com/product/4292)
- [Animated Snake Eyes Bonnet for Raspberry Pi](https://learn.adafruit.com/animated-snake-eyes-bonnet-for-raspberry-pi/software-installation)
- [Lithium Ion Cylindrical Battery - 3.7v 2200mAh](https://www.adafruit.com/product/1781)
- [JST SH 9-Pin Cable - 100mm long x 2](https://www.adafruit.com/product/4350)
- [Adafruit MONSTER M4SK - DIY Electronic Eyes Mask](https://www.adafruit.com/product/4343)
- [Separate the MONSTER M4SK](https://learn.adafruit.com/wide-set-monster-m4sk-creature-eyes/separate-the-monster-m4sk)
- [Spruce Up a Costume with MONSTER M4SK Eyes and Voice](https://learn.adafruit.com/spruce-up-a-costume-with-monster-m4sk-eyes-and-voice)


<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
