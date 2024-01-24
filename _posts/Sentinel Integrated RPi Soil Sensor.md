# Introduction and Use Case:
As the agricultural industry continues to evolve and embrace new technologies, cost-effective and reliable IoT devices such as Raspberry Pi-based soil sensors have emerged as critical tools for farmers and growers. These sensors provide real-time data on soil conditions, enabling both large scale farmers and small-time growers to make informed decisions about irrigation, fertilization, and other key processes. However, as the use of IoT devices increases, so does the need for enhanced security and automation.

<br/>

In this blog article, we will explore how to build and onboard a Raspberry Pi-based soil sensor to Microsoft Sentinel, a cloud-native security information and event management (SIEM) system, in order to improve both security and operations with enhanced scalability, automation, and peace of mind knowing that valuable data is protected and can be easily monitored, analyzed, and acted upon.

<br/>

Fun Fact: this project was inspired while I was growing a fruits and veggies in my back yard in Colorado. At the time, lake Meade, the primary source of irrigation for much of the state, was drying up and forest fires loomed over Boulder. Colorado is the only place I’ve ever seen it snow in the morning, then rain smoke and burning pine in the afternoon. 

<br/><br/>

# In this Post We Will: 
- &#128073;Built a Raspberry Pi based Soil Sensor
- &#128073;Configure an OLED Display to Output Results in Real Time
- &#128073;Onboard Sensor to Sentinel
- &#128073;Be Cool like Fonzie 😎

<br/><br/>

# Hardware Details: 

- [I2C OLED Display](https://a.co/d/cjIjMv2)
- [Raspberry Pi Zero W (but any Pi should work)](https://a.co/d/2G6Mq9C)
- [I2C Soil Moisture & Temperature Sensor](https://a.co/d/biWvUO2)
- [GPIO Splitter](https://shop.pimoroni.com/products/hat-hacker-hat?variant=31812879056979)
- [Jumper Cables](https://a.co/d/3A3MSpy)

<br/><br/>


# Pre-Requisites:

- Update your system:
```python
sudo apt-get update
sudo apt-get upgrade
```

- (Optional) If either of the above complete but with errors, try again with:
```python 
sudo apt-get update --fix-missing
sudo apt-get upgrade --fix-missing
```

- Set Localisation Options:
```python
sudo raspi-config
	> Localisation Options > TimeZone > US > Eastern > OK
```

![](/assets/img/SoilSensor/Localization1.png)

![](/assets/img/SoilSensor/Localization2.png)

![](/assets/img/SoilSensor/Localization3.png)


- Expand your storage
```python
sudo raspi-config
  > Advanced Options > Expand FileSystem
```
![](/assets/img/SoilSensor/Disk1.png)
![](/assets/img/SoilSensor/Disk2.png)

<br/><br/>

# Raspberry Pi Headless Setup (No Dedicated Mouse/Keyboard/Monitor Necessary):
After burning your SD card with Raspbian OS, you can configure it to automagically join the network and enable SSH with the following steps: 
- Unplug/plug back in your SD card into your computer after burning the OS
<br/><br/>
- Navigate to SD storage
<br/><br/>
- Create blank file (no extension) named "SSH" (this file is detected and deleted on boot, and SSH is enabled)
<br/><br/>
- Copy and paste the [WPA_supplicant.conf](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/wpa_supplicant.conf) file containing your country/region, wireless SSID and Key 
<br/><br/>
- Boot up and wait for it to appear on your network and be available over SSH

<br/><br/>

# Soil Sensor Setup:

- Soil Sensor Setup:
```python
sudo apt-get install python3-pip
sudo pip3 install --upgrade setuptools
sudo apt-get install -y python-smbus
sudo apt-get install -y i2c-tools
```

- Enable i2c interface (reboot first!):
```python
sudo reboot -n
sudo raspi-config
	> Interfacing Options > I2C > Enable > OK
```
![](/assets/img/SoilSensor/I2C1.png)
![](/assets/img/SoilSensor/I2C2.png)

```python
sudo pip3 install RPI.GPIO
sudo pip3 install adafruit-blinka
sudo pip3 install adafruit-circuitpython-busdevice
sudo apt install git-all
sudo git clone https://github.com/adafruit/Adafruit_CircuitPython_seesaw.git
sudo pip3 install adafruit-circuitpython-seesaw
```

<br/><br/>

==============================
# OLED Screen Install:

- Install the following packages:
```python
sudo pip3 install adafruit-circuitpython-ssd1306
sudo apt-get install python3-pil
sudo pip3 install requests
```

<br/>

- Grab and unzip silkscreen font to clean up txt display (cleaner font for this type of OLED display):
```python
wget http://kottke.org/plus/type/silkscreen/download/silkscreen.zip
unzip silkscreen.zip
```

<br/>

- Build your main.py file
```python
sudo nano main.py
```
> &#128073; ...This program will run the Sensor as well as the OLED Display. This is because separate .py files for sensor reading and OLED output through a GPIO splitter will inevitably cause a collision sooner or later. Coding both functions into the same program will force them to initiate sequentially and thus, never collide.

<br/>

- Run this file when you want to start the display along with the sensor with one command:
```python
sudo python3 main.py
```

<br/><br/>

# Test hardware detection and return hardware addresses:
```python
sudo i2cdetect -y 1
#Soil Sensor should populate on x36
#OLED Display shows up on x3c (see next section for OLED setup)
```
![](/assets/img/SoilSensor/HardwareAddress.png)


<br/><br/>

# Integration with Microsoft Sentinel

- Install Ruby 
```bash
sudo aptitude install ruby-dev
```

- Check/Confirm Ruby Version:
```bash
ruby --ver
```

- Install FluentD Unified Log Aggregator & Plugin
```bash
sudo gem install fluentd -v "~> 0.12.0"
sudo fluent-gem install fluent-plugin-td
```

- Install FluentD Plugn for Azure Log Analytics
```bash
sudo fluent-gem install fluent-plugin-azure-loganalytics
```

<br/><br/>

# Create a Log Analytics Workspace
- If you don't already have one ready, navigate to Log Analytics Workspace in Azure Portal:
![](/assets/img/SoilSensor/LAW1.png)
<br/>

- Select +Create
![](/assets/img/SoilSensor/LAW2.png)
<br/>

- Select Subscription and Resource Group:
![](/assets/img/SoilSensor/LAW3.png)
<br/>

- Select Instance Name and Region:
![](/assets/img/SoilSensor/LAW4.png)

- Commitment / Pricing Tier
Choose the appropriate commitment tier given your expected daily ingest volume. 

<br/><br/>

> &#128161; &#128073; **_It makes sense to bump up to the 100GB/day commitment tier even when you hit as little as 50GB/day because of the 50% discount afforded at 100GB/day, for example. Check out my prior Sentinel Cost Optimization Part 1 and 2 articles at [hanley.cloud](www.hanley.cloud), complete with use-cases and exercises.  While you're at it, don't forget to peruse my GitHub repository for ready-made queries for all kinds of situations that you can simply copy and paste_** 

<br/><br/>


- Click Review & Create
 ...to Finish Setting up a New Log Analytics Workspace 

<br/><br/>

# Connect to Workspace:
- Grab WorkspaceID and Primary Key:
![](/assets/img/SoilSensor/WorkspaceIDandKey.png)

- Plug ID and Key into your fluent.conf file
Template located here: [fluent.conf](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/fluent.conf)

<br/><br/>

- Launch the sensor application
```python
sudo python3 main.py &
```
<br/>

Confirm logs are working locally
```python
tail /var/log/soil.log -f
```
<br/>
<br/>

- Launch FluentD
```python
sudo fluentd -c /etc/fluent.conf --log /var/log/td-agent/fluent.log &
```

<br/><br/>
 
 > &#128161;[Pro-Tip]&#128161; Create a bash file to launch FluentD with the appropriate parameters so you don't have to type it out every time:
```
sudo nano Start_FluentD.bash
```
<br/>
Paste the following into nano, save and close: 
```python
sudo fluentd -c /etc/fluent.conf --log /var/log/td-agent/fluent.log &
```
<br/>
&#128073; Now you can start FluentD with the following command:
```python
sudo bash Start_FluentD.bash &
```
<br/><br/>

- Confirm logs are flowing to Log Analytics Workspace
```python
tail /var/log/td-agent/fluent.log -f 
```
<br/>

# Start on Boot:
- Append the above command to /etc/rc.local to start on boot:
```python
sudo nano /etc/rc.local
	sudo python3 main.py && sudo python3 OLEDstats.py && sudo Start_FluentD.bash
```



