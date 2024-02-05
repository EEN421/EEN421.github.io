# Introduction and Use Case:

This post follows up on a couple of previous posts where I [deployed a raspberry pi headlessly and onboarded syslog and auth logs to a log analytics workspace](https://www.hanley.cloud/2023-06-13-Raspberry-Pi-Logging-to-Analytics-Workspace/), and then [added an I2C soil moisture and temperature sensor and streamed the data to a workspace too](https://www.hanley.cloud/2024-01-24-Sentinel-Integrated-RPi-Soil-Sensor/) and will address several new security updates and improvement to the processes described. 

<br/>

# Security Updates - What's New?

Since the release of Bullseye OS for Raspberry Pi, the default 'pi' account was removed. This account was the most likely to be abused when malicious actors figured out it's enabled by default on all deployments. Reducing our attack surface area with this simple change is a welcome feature. However, as the case with most things security related, it can come at a cost if you don't know what you're doing. 

Another important feature that has since been added, is the ability to encrypt your sensitive information. The older method I've used relied on hard-coding wifi keys etc. in plain text (**yuck!**) to a wpa_supplicant.conf file for example. This is no longer the case (**huzzah**)! 

Lastly, ARM based architecture such as Raspbery Pi boards weren't previously supported without the added overhead of installing Ruby and FluentD, which required the workspaceID to be hard-coded to another config file (**gross**). 

Now you can streamline your workflow and improve your overall productivity, safely and securely! And the benefits don't stop there - by leveraging the Azure Streaming Agent via IoT Hub, you'll be able to ditch the old combination of FluentD and Ruby, saving you time, energy, and reducing your overal attack surface area. So why wait? Dive into this blog post and learn how to optimize your Raspberry Pi IoT setup today!

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/prototype_2.0.png)

<br/><br/>

# In this Post We Will: 
- &#128073; Review Security Updates
- &#128073; Review Hardware Changes and Pre-Requisites
- &#128073; Perform a "Headless" Raspberry Pi Setup (Latest "Bookworm" OS)
- &#128073; Configure an I2C Capacitive STEMMA Soil Sensor
- &#128073; Configure an OLED Display to Output Sensor Readings in Real Time
- &#128073; Test and Confirm Hardware
- &#128073; Create an IoT Hub in Azure
- &#128073; Onboard Raspberry Pi to IoT Hub
- &#128073; Automate/Configure Start on Boot 
- &#128073; Accomplish something AWESOME today x2! &#128526;

<br/><br/>

# Hardware Details: 
Click to learn more about each component...
- [I2C OLED Display](https://www.adafruit.com/product/3527)
- [Raspberry Pi Zero W (but any Pi should work)](https://a.co/d/2G6Mq9C)
- [I2C Soil Moisture & Temperature Sensor](https://www.adafruit.com/product/4026)
- [GPIO Splitter (smaller form factor than previous prototype)](https://www.amazon.com/GeeekPi-Connectors-Raspberry-Expansion-Compatible/dp/B0888W3XN4/ref=sr_1_5?crid=4U70H8TJQGX9&keywords=gpio+splitter&qid=1707110682&sprefix=gpio+splitte%2Caps%2C70&sr=8-5)
- [Jumper Cables](https://a.co/d/3A3MSpy)

<br/><br/>

# Sofware | OS Details:
- These steps have been tested with [Raspbian Bookworm OS](https://www.raspberrypi.com/news/bookworm-the-new-version-of-raspberry-pi-os/), the [latest Raspberry Pi operating system](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-64-bit) at the time of this article. 

![](/assets/img/IoT%20Hub/Headless%20Setup/bookworm_01-768x518.jpg)

<br/><br/>

# Azure IoT Hub Setup

Login to the Azure portal and click **+Create a Resource** button, then select **IoT Hub** in the **Search the Marketplace** field. 

![](/assets/img/IoT%20Hub/Headless%20Setup/mktplace.png)

Select **IoT Hub** then **Create**

Select your **Sub**, **Resource Group**, **Region**, and **Name** for your **IoT Hub**

In the **Tier** section, select **Free**

<br/><br/>

# Grab the Connection String

Navigate to your new **IoT Hub** and select **Devices**, then **+ Add Device**

Provide a **Name** for your device and select **Save**

Navigate back to the **Devices** blade, then to your newly registered device and take note of the **Primary connection string**

![](/assets/img/IoT%20Hub/Headless%20Setup/cnxn_string.png)

<br/><br/><br/>

# Raspberry Pi Headless Setup (No Dedicated Mouse/Keyboard/Monitor Necessary):

After burning our SD card with the [latest Raspbian OS](https://www.raspberrypi.com/software/), we need to create a [custom.toml](/assets/Code/iothub/custom.toml) file (this replaces the [WPA_supplicant.conf](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/wpa_supplicant.conf) file used previously and handles **hostname, default account configuration, enables SSH, WLAN config, and Locale**). For a breakdown of the new configuration file and which sections you need to update, see below:

![](/assets/img/IoT%20Hub/Headless%20Setup/hostname.png)

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/user.png)

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/SSH.png)

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/WLAN.png)

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/locale.png)

<br/><br/>

Once the initial burn is done (I use [Belena Etcher](https://etcher.balena.io/)), you can configure it to **automagically** join the network and enable SSH by dropping your **custom.toml** file into the boot drive: 

- Unplug/plug back in your SD card into your computer after burning the OS
<br/><br/>

- Navigate to SD storage / Boot
<br/><br/>

- Copy and paste the [custom.toml](/assets/Code/iothub/custom.toml) file containing your Hostname, user, SSH, WLAN, and country/region settings. 
<br/><br/>

- Boot up and wait for it to appear on your network and be available over SSH

<br/><br/>

# Raspberry Pi Setup:

- Update your system:
```python
sudo apt-get update && sudo apt-get upgrade
```

<br/>

- Expand your storage
```python
sudo raspi-config
  > Advanced Options > Expand FileSystem
```

![](/assets/img/SoilSensor/Disk1.png)

![](/assets/img/SoilSensor/Disk2.png)

<br/><br/>

- Install Sensor Hardware Dependencies:

```python
sudo apt-get install python3-pip
sudo pip3 install --upgrade setuptools
sudo apt-get install -y python-smbus
sudo apt-get install -y i2c-tools
sudo pip3 install RPI.GPIO
sudo pip3 install adafruit-blinka
sudo pip3 install adafruit-circuitpython-busdevice
sudo apt install git-all
sudo git clone https://github.com/adafruit/Adafruit_CircuitPython_seesaw.git
sudo pip3 install adafruit-circuitpython-seesaw
```

<br/><br/>

- Install OLED Hardware Dependencies:
```pythong
sudo pip3 install adafruit-circuitpython-ssd1306
sudo apt-get install python3-pil
sudo pip3 install requests
```

<br/><br/>

- Install Azure IoT Hub Dependencies:
```python
sudo pip3 install azure-iot-device  
sudo pip3 install azure-iot-hub  
```

# Test hardware detection and return hardware addresses:
```python
sudo i2cdetect -y 1
#Soil Sensor should populate on x36
#OLED Display shows up on x3c 
```
![](/assets/img/SoilSensor/HardwareAddress.png)

<br/>
Once you run the OLED script, you should see the display populate as such:

![](/assets/img/SoilSensor/ReadMe1.jpg)

<br/>

> &#128073; Pro-Tip: Change the Hostname of the Raspberry Pi in the /etc/hostname file to the name of the plant you're monitoring

<br/><br/>

# Build out your Azure IoT Hub python program

- If you did **NOT** install an OLED screen, then use the [Sensor-2-IoT_Hub.py file](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iothub/Sensor-2-IoT_Hub.py)

<br/>

- If you **DID** install an OLED screen, then use the [Sensor-2-IoT_Hub+OLED.py file](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iothub/Sensor-2-IoT_Hub%2BOLED.py)

<br/>

- Make sure to swap out the **Connection String** we noted earlier when registering our sensor device to our **IoT Hub**

```python
CONNECTION_STRING = "HostName=XXXXXX.azure-devices.net;DeviceId=XXXXXX;SharedAccessKey=XXXXXXXXXXXX"  
```

<br/>

# Run it!

![I named my script "new_sensor.py" in this screenshot](/assets/img/IoT%20Hub/Headless%20Setup/IoT_Connect.png)

<br/>

- Confirm messages are flowing in Azure IoT Hub:
![](/assets/img/IoT%20Hub/Headless%20Setup/Messages.png)

<br/><br/>

# Add Water...

When I add moisture to my soil sample, I can see the moisture reading adjust:

![](/assets/img/SoilSensor/ReadMe3.jpg)

<br/><br/>

# In this Post We: 
- &#128073; Review Security Updates
- &#128073; Review Hardware Changes and Pre-Requisites
- &#128073; Perform a "Headless" Raspberry Pi Setup (Latest "Bookworm" OS)
- &#128073; Configure an I2C Capacitive STEMMA Soil Sensor
- &#128073; Configure an OLED Display to Output Sensor Readings in Real Time
- &#128073; Test and Confirm Hardware
- &#128073; Create an IoT Hub in Azure
- &#128073; Onboard Raspberry Pi to IoT Hub
- &#128073; Automate/Configure Start on Boot 
- &#128073; Accomplish something AWESOME today x2! &#128526;


![](/assets/img/IoT%20Hub/Headless%20Setup/prototype_2.0_2.png)

# Recapitulation:

This time around (2.0) we improved upon our previous Headless Raspberry Pi ARM Device onboarding process in the following ways: 

- Encrypted WiFi and User Credentials (no more plain text "secrets.py" hard-coded credentials!)
- Onboarded Sensor to IoT Hub with Azure Native tools and Transmitted Messages/Sensor Data (No need for 3rd party syslog forwarder ([fluentD](https://docs.fluentd.org/how-to-guides/raspberrypi-cloud-data-logger) for example)).

![](/assets/img/SoilSensor/ReadMe5.jpg)
