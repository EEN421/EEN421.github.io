# Introduction and Use Case:
As the agricultural industry continues to evolve and embrace new technologies, cost-effective and reliable IoT devices such as Raspberry Pi-based soil sensors have emerged as critical tools for farmers and growers. These sensors provide real-time data on soil conditions, enabling both large scale farmers and small-time growers to make informed decisions about irrigation, fertilization, and other key processes. However, as the use of IoT devices increases, so does the need for enhanced security and automation.
In this blog article, we will explore how to build and onboard a Raspberry Pi-based soil sensor to Microsoft Sentinel, a cloud-native security information and event management (SIEM) system, in order to improve both security and operations with enhanced scalability, automation, and peace of mind knowing that valuable data is protected and can be easily monitored, analyzed, and acted upon.
Fun Fact: this project was inspired while I was growing a fruits and veggies in my back yard in Colorado. At the time, lake Meade, the primary source of irrigation for much of the state, was drying up and forest fires loomed over Boulder. Colorado is the only place I’ve ever seen it snow in the morning, then rain smoke and burning pine in the afternoon. 

<br/><br/>

# In this Post We Will: 
👉Define our report and the underlying KQL
👉Run and export our KQL to a PowerBI M Query
👉Import our M Query into PowerBI
👉Manipulate Data Sets and Render Visuals
👉Save and Export our Report to PDF
👉Re-run our report with 1-click!
👉Achieve Awesome-ness 😎

<br/><br/>

# Hardware Details: 

- [I2C OLED Display](https://a.co/d/cjIjMv2)
- [Raspberry Pi Zero W (but any Pi should work)](https://a.co/d/2G6Mq9C)
- [I2C Soil Moisture & Temperature Sensor](https://a.co/d/biWvUO2)
- [GPIO Splitter](https://shop.pimoroni.com/products/hat-hacker-hat?variant=31812879056979)
- [Jumper Cables](https://a.co/d/3A3MSpy)

<br/><br/>


# Pre-Requisites:

# 1. Update your system:
```python
sudo apt-get update
sudo apt-get upgrade
```

# 2. (Optional) If either of the above complete but with errors, try again with:
```python 
sudo apt-get update --fix-missing
sudo apt-get upgrade --fix-missing
```

# 3. Set Localisation Options:
```python
sudo raspi-config
	> Localisation Options > TimeZone > US > Eastern > OK
```
![](/assets/img/Localization1.png)
![](/assets/img/Localization2.png)
![](/assets/img/Localization3.png)


# 4. Expand your storage
```python
sudo raspi-config
  > Advanced Options > Expand FileSystem
```
![](/assets/img/Disk1.png)
![](/assets/img/Disk2.png)

<br/><br/>

# Raspberry Pi Headless Setup (No Dedicated Mouse/Keyboard/Monitor Necessary):
After burning your SD card with Raspbian OS, you can configure it to automagically join the network and enable SSH with the following steps: 
- 1. Unplug/plug back in your SD card into your computer after burning the OS
- 2. Navigate to SD storage
- 3. Create blank file (no extension) named "SSH" (this file is detected and deleted on boot, and SSH is enabled)
- 4. Copy and paste the [WPA_supplicant.conf](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/wpa_supplicant.conf) file containing your country/region, wireless SSID and Key 
- 5. Boot up and wait for it to appear on your network and be available over SSH

<br/><br/>

# Soil Sensor Setup:

# 1. Soil Sensor Setup:
```python
sudo apt-get install python3-pip
sudo pip3 install --upgrade setuptools
sudo apt-get install -y python-smbus
sudo apt-get install -y i2c-tools
```

# 2. Enable i2c interface (reboot first!):
```python
sudo reboot -n
sudo raspi-config
	> Interfacing Options > I2C > Enable > OK
```
![](/assets/img/I2C1.png)
![](/assets/img/I2C2.png)

```python
sudo pip3 install RPI.GPIO
sudo pip3 install adafruit-blinka
sudo pip3 install adafruit-circuitpython-busdevice
sudo apt install git-all
sudo git clone https://github.com/adafruit/Adafruit_CircuitPython_seesaw.git
sudo pip3 install adafruit-circuitpython-seesaw
```

# 3. To test hardware detection and return hardware addresses:
```python
sudo i2cdetect -y 1
#Soil Sensor should populate on x36
#OLED Display shows up on x3c (see next section for OLED setup)
```
![](/assets/img/HardwareAddress.png)


<br/><br/>


# 1. OLED Screen Install:
```python
#To test hardware detection and return hardware addresses:
sudo i2cdetect -y 1
#Soil Sensor should populate on x3c

sudo pip3 install adafruit-circuitpython-ssd1306
sudo apt-get install python3-pil
sudo pip3 install requests
```

# 2. Grab and unzip silkscreen font to clean up txt display:
```python
wget http://kottke.org/plus/type/silkscreen/download/silkscreen.zip
unzip silkscreen.zip
```

# 3. Build your OLEDstats.py file
```python
sudo nano OLEDstats.py
```

# 4. Run this file when you want to start the display:
```python
sudo python3 OLEDstats.py
```

<br/><br/>

# Append the above command to /etc/rc.local to start on boot:
```python
sudo nano /etc/rc.local
	sudo python3 main.py && sudo Start_FluentD.bash
```
