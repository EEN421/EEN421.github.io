# Introduction and Use Case:
As the agricultural industry continues to evolve and embrace new technologies, cost-effective and reliable IoT devices such as Raspberry Pi-based soil sensors have emerged as critical tools for farmers and growers. These sensors provide real-time data on soil conditions, enabling both large scale farmers and small-time growers to make informed decisions about irrigation, fertilization, and other key processes. However, as the use of IoT devices increases, so does the need for enhanced security and automation.

In this blog article, we will explore how to build and onboard a Raspberry Pi-based soil sensor to Microsoft Sentinel, a cloud-native security information and event management (SIEM) system, in order to improve both security and operations with enhanced scalability, automation, and peace of mind knowing that valuable data is protected and can be easily monitored, analyzed, and acted upon.

<br/>

# In this Post We Will: 
- &#128073; Review Hardward and Pre-Requisites
- &#128073; Perform a "Headless" Raspberry Pi Setup
- &#128073; Configure an I2C Capacitive STEMMA Soil Sensor
- &#128073; Configure an OLED Display to Output Sensor Readings in Real Time
- &#128073; Test and Confirm Hardware
- &#128073; Create a Log Analytics Workspace
- &#128073; Send Sensor Data to Microsoft Sentinel
- &#128073; Query custom logs for operations, security, and soil data
- &#128073; Automate/Configure Start on Boot 
- &#128073; Accomplish something AWESOME today! &#128526;

<br/><br/>

# Hardware Details: 
Click to learn more about each component...
- [I2C OLED Display](https://a.co/d/cjIjMv2)
- [Raspberry Pi Zero W (but any Pi should work)](https://a.co/d/2G6Mq9C)
- [I2C Soil Moisture & Temperature Sensor](https://a.co/d/biWvUO2)
- [GPIO Splitter](https://shop.pimoroni.com/products/hat-hacker-hat?variant=31812879056979)
- [Jumper Cables](https://a.co/d/3A3MSpy)

<br/><br/>

# Sofware | OS Details:
- I used the last RaspiOS that supported this kind of headless setup (Buster or earlier) for this build. 

<br/>

- I know, I know... I'll cover a more modern "headless" setup for the latest RaspiOS ("Bookworm", at the time of this article) in a separate blog article and link back here. &#128517;

<br/><br/>

![](/assets/img/SoilSensor/ReadMe0.jpg)

<br/><br/><br/>

# Pre-Requisites:

- Update your system:
```python
sudo apt-get update
sudo apt-get upgrade
```

<br/>


- (Optional) If either of the above complete but with errors, try again with:
```python 
sudo apt-get update --fix-missing
sudo apt-get upgrade --fix-missing
```

<br/>

- Set Localisation Options:
```python
sudo raspi-config
	> Localisation Options > TimeZone > US > Eastern > OK
```

![](/assets/img/SoilSensor/Localization1.png)

![](/assets/img/SoilSensor/Localization2.png)

![](/assets/img/SoilSensor/Localization3.png)

<br/>

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

<br/>

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

# OLED Screen Install:

- Install the following packages:
```python
sudo pip3 install adafruit-circuitpython-ssd1306
sudo apt-get install python3-pil
sudo pip3 install requests
```

<br/>

- [Optional] Grab and unzip silkscreen font to clean up txt display (cleaner font for this type of small OLED display):
```python
wget http://kottke.org/plus/type/silkscreen/download/silkscreen.zip
unzip silkscreen.zip
```

<br/>

- Build your [main.py](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/main.py) file
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
#OLED Display shows up on x3c 
```
![](/assets/img/SoilSensor/HardwareAddress.png)

<br/>
Once you run the OLED script, you should see the display populate as such:
<br/>
![](/assets/img/SoilSensor/ReadMe1.jpg)
<br/>

> &#128073; Pro-Tip: Change the Hostname of the Raspberry Pi in the /etc/hostname file to the name of the plant you're monitoring

<br/><br/>

# FluentD Configuration:

- Install Ruby 
```bash
sudo aptitude install ruby-dev
```

<br/>

- Check/Confirm Ruby Version:
```bash
ruby --ver
```

<br/>

- Install **FluentD Unified Log Aggregator & Plugin**
```bash
sudo gem install fluentd -v "~> 0.12.0"
sudo fluent-gem install fluent-plugin-td
```

<br/>

- Install **FluentD Plugn** for Azure Log Analytics
```bash
sudo fluent-gem install fluent-plugin-azure-loganalytics
```

<br/><br/>

# Create a Log Analytics Workspace
- If you don't already have one ready, navigate to Log Analytics Workspace in Azure Portal:
<br/>
![](/assets/img/SoilSensor/LAW1.png)
<br/>

- Select **+Create**
<br/>
![](/assets/img/SoilSensor/LAW2.png)
<br/>

- Select **Subscription** and **Resource Group**:
<br/>
![](/assets/img/SoilSensor/LAW3.png)
<br/>

- Select **Instance Name** and **Region**:
![](/assets/img/SoilSensor/LAW4.png)

<br/><br/>

# Commitment / Pricing Tiers
- Choose the appropriate commitment tier given your expected daily ingest volume. 


> &#128161; It makes sense to bump up to the 100GB/day commitment tier even when you hit as little as 50GB/day because of the 50% discount afforded at 100GB/day, for example. <br/>
> &#128073; Check out my prior Sentinel Cost Optimization Part 1 and 2 articles at [hanley.cloud](www.hanley.cloud), complete with use-cases and exercises.  While you're at it, don't forget to peruse my GitHub repository for KQL breakdowns and ready-made queries for all kinds of complicated situations that you can simply copy and paste_** 

<br/><br/>


- Click **Review & Create**
 ...to Finish Setting up a New Log Analytics Workspace 

<br/><br/>

# Connect to Workspace:

- Grab **WorkspaceID** and **Primary Key**:
![](/assets/img/SoilSensor/WorkspaceIDandKey.png)

<br/>

- Plug ID and Key into your **fluent.conf** file
Template located here: [fluent.conf](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/fluent.conf)

<br/>

- Launch the sensor application
```python
sudo python3 main.py &
```
<br/>

- Confirm logs are working locally
```python
tail /var/log/soil.log -f
```
<br/>

- Launch FluentD
```python
sudo fluentd -c /etc/fluent.conf --log /var/log/td-agent/fluent.log &
```

<br/><br/>
 
 > &#128161;Pro-Tip: Create a bash file to launch FluentD with the appropriate parameters so you don't have to type it out every time:
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
![](/assets/img/SoilSensor/Test1.png)

<br/>

- Navigate to your Log Analytics Workspace to query the logs coming into your workspace.
![](/assets/img/SoilSensor/Soil%20Readings.png)
<br/><br/>


# Query Auth and Syslog Tables

If you've setup your FluentD config file correctly, you've got Auth and Syslogs coming into Sentinel as Custom Logs (_CL) as well as your Soil data. Logs ingested this way show up under 'Custom Logs' and have '_CL' appended to their name when they hit the workspace. You can Query the Auth Logs for failed sign-in attempts etc., illustrated below... 

Navigate to your Log Analytics Workspace and you should see your custom logs :

![](/assets/img/iot/CustomLogs.png)
<br/><br/>

# Added Security

&#128161; Once FluentD is cooking without issue on your Pi, try logging in with an **incorrect password** to trigger an entry in the new custom log _'auth_cl'_ then query the table &#128071;

![](/assets/img/iot/Auth_CL.png)
<br/><br/>


The syslog table (syslog_cl) is populating too &#128071;

![](/assets/img/iot/syslog_cl.png)
<br/><br/>

# Start on Boot:

- Append the above command to /etc/rc.local to start on boot:

```python
sudo nano /etc/rc.local
	sudo python3 main.py && sudo python3 OLEDstats.py && sudo Start_FluentD.bash
```

<br/><br/>

# Add Water...

When I add moisture to my soil sample, I can see the moisture reading adjust:

![](/assets/img/SoilSensor/ReadMe3.jpg)

<br/><br/>

# In this Post We: 
- &#128073; Reviewed Hardware and Pre-Requisites
- &#128073; Performed a "Headless" Raspberry Pi Setup
- &#128073; Configured an I2C Capacitive STEMMA Soil Sensor
- &#128073; Configured an OLED Display to Output Sensor Readings in Real Time
- &#128073; Tested and Confirmed Hardware
- &#128073; Created a Log Analytics Workspace
- &#128073; Sent Sensor Data to Microsoft Sentinel
- &#128073; Queried custom logs for operations, security, and soil data
- &#128073; Automated/Configured Start on Boot 
- &#128073; Accomplished something AWESOME &#128526;


![](/assets/img/SoilSensor/ReadMe4.jpg)
![](/assets/img/SoilSensor/ReadMe5.jpg)