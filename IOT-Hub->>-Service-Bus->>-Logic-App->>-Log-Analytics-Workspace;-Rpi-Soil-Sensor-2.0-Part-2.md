# Introduction and Use Case:

This follows up on a previous post where we [built a Raspberry Pi based soil sensor and onboarded it to Azure IoT Hub](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/). What then? how do we read that data or do anything meaningful with it? Some advanced readers may have thought to make a diagnostics setting to forward telemetry data to a workspace, only to find just the 'telemetry' data (send success/fail and other telemetry metrics) but not the actual message data actually make it into the AzureDiagnostics table in a workspace (good guess though, that was my first move too). 

As our title suggests, the best way to get our IoT Sensor messages from IoT Hub into a Log Analytics workspace is from IoT Hub through a Service Bus, and into a Logic App which can parse the 'message' data, then finally send it to a Log Analytics Workspace. It sounds like a lot, but it's really easier than you'd think. 

&#128526; <br/>
&#9201; <br/>
&#x26A1; <br/>
&#128272; <br/>
&#128170; <br/>

<br/>

<br/>

# In this Post We Will: 
- &#128073; Review Security Updates
- &#128073; Review Hardware Changes and Pre-Requisites
- &#128073; Perform the New "Headless" Raspberry Pi Setup (Latest "Bookworm" OS)
- &#128073; Configure an I2C Capacitive STEMMA Soil Sensor
- &#128073; Configure an OLED Display to Output Sensor Readings in Real Time
- &#128073; Test and Confirm Hardware
- &#128073; Create an IoT Hub in Azure
- &#128073; Onboard Raspberry Pi to IoT Hub
- &#128073; Accomplish something AWESOME today x2! &#128526;

<br/><br/>


<br/><br/>

# Create Azure Service Bus

Login to the Azure portal and click **+Create a Resource** button, then select **IoT Hub** in the **Search the Marketplace** field. 

![](/assets/img/IoT%20Hub/Headless%20Setup/mktplace.png)

- Select **IoT Hub** then **Create**

- Select your **Sub**, **Resource Group**, **Region**, and **Name** for your **IoT Hub**

- In the **Tier** section, select **Free**

<br/><br/>

# Create Log Analytics Workspace

- Navigate to your new **IoT Hub** and select **Devices**, then **+ Add Device**

- Provide a **Name** for your device and select **Save**

- Navigate back to the **Devices** blade, then to your newly registered device and take note of the **Primary connection string**

![](/assets/img/IoT%20Hub/Headless%20Setup/cnxn_string.png)

<br/><br/><br/>

# Build Logic App

After burning our SD card with the [latest Raspbian OS](https://www.raspberrypi.com/software/), we need to create a [custom.toml](/assets/Code/iothub/custom.toml) file (this replaces the [WPA_supplicant.conf](https://github.com/EEN421/Sentinel-Integrated-RPI-Soil-Sensor/blob/Main/Code/wpa_supplicant.conf) file used previously and handles **hostname, default account configuration, enables SSH, WLAN config, and Locale**). For a breakdown of the new configuration file and which sections you need to update, see below:

![](/assets/img/IoT%20Hub/Headless%20Setup/hostname.jpg)

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/user.png)

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/SSH.png)

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/WLAN.png)

<br/>

![](/assets/img/IoT%20Hub/Headless%20Setup/locale.png)

<br/><br/>

To encrypt your password and generate the encryption key, I used the following command on another linux box with OpenSSL: 
```python
openssl passwd -5 'yourPWD'
```

**Copy** the **output** and insert it as your **'password' string** in the [custom.toml](/assets/Code/iothub/custom.toml) file
<br/><br/>

Once the initial burn is complete (I use [Belena Etcher](https://etcher.balena.io/)), you can configure your Raspberry Pi to &#127775; **automagically** &#127775; join the network and enable SSH by dropping your **custom.toml** file into the boot drive with the following steps: 

- Unplug/plug back in your SD card into your computer after burning the OS
<br/><br/>

- Navigate to SD storage / Boot
<br/><br/>

- Copy and paste the [custom.toml](/assets/Code/iothub/custom.toml) file containing your Hostname, user, SSH, WLAN, and country/region settings. 
<br/><br/>

- Boot up and wait for it to appear on your network and be available over SSH (this can take up to 10 minutes on first boot, check your router for the IP address).

<br/><br/>

# Build a DataCollector API Connection for our Logic App

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

<br/>

- Install OLED Hardware Dependencies:
```python
sudo pip3 install adafruit-circuitpython-ssd1306
sudo apt-get install python3-pil
sudo pip3 install requests
```

<br/>

- Install Azure IoT Hub Dependencies:
```python
sudo pip3 install azure-iot-device  
sudo pip3 install azure-iot-hub  
```
<br/><br/>

> &#128073; Pro-Tip: If you didn't change the Hostname to the name of the plant you're monitoring in the [custom.toml](/assets/Code/iothub/custom.toml) file, then edit the /etc/hostname file once you SSH in. I'm using this unit to grow [Goat Horn Peppers ](https://www.roysfarm.com/goat-horn-pepper/)

<br/><br/>

# Build out your Azure IoT Hub python program

- If you did **NOT** install an OLED screen, then use the [Sensor-2-IoT_Hub.py file](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iothub/Sensor-2-IoT_Hub.py)

<br/>

- If you **DID** install an OLED screen, then use the [Sensor-2-IoT_Hub+OLED.py file](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iothub/Sensor-2-IoT_Hub%2BOLED.py)



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
- &#128073; Accomplish something AWESOME today x2! &#128526;


![](/assets/img/IoT%20Hub/Headless%20Setup/prototype_2.0_2.png)

# Recapitulation:

This time around (2.0) we improved upon our previous Headless Raspberry Pi ARM Device onboarding process in the following ways: 

- Encrypted WiFi and User Credentials (no more plain text "secrets.py" hard-coded credentials!)
<br/>

- Onboarded Sensor to IoT Hub with Azure Native tools and Transmitted Messages/Sensor Data (No need for 3rd party syslog forwarder ([fluentD](https://docs.fluentd.org/how-to-guides/raspberrypi-cloud-data-logger) for example)).
<br/>

![](/assets/img/SoilSensor/ReadMe5.jpg)
