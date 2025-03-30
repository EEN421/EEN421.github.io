# Introduction & Use Case:
😤 Tired of ads stalking you across the internet like a clingy ex?
What if you could not only block them at the network level 🚫🌐 but also monitor, analyze, and hunt through your home’s DNS telemetry like a SOC analyst on Red Bull? 🕵️‍♂️⚡️🥤

In this blog, we’re going full nerd 🤓: spinning up Pi-hole on a Raspberry Pi from scratch, tricking it out with a real-time ad detection display 📺✨, and then pushing that juicy network telemetry up to Microsoft Sentinel like it’s a Fortune 500 SOC. It’s home lab meets enterprise security — and it’s glorious. 🏡🔐🚀

<br/>

![](/assets/img/pihole2sentinel/Leonardo_Phoenix_09_A_futuristic_command_center_featuring_a_Pi_0.jpg)

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
- &#128161; Ian's Insights

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

>&#128161; I like to see roughly 15% more ingest than required for the next pricing tier to insulate against nights, weekends, and holidays which inherently drag down the daily ingest volume average. 

<br/>

- Click **Review & Create** to finish setting up a new Log Analytics Workspace 

<br/><br/>

# Retrieve WorkspaceID and Primary Key
![](/assets/img/iot/WorkspaceIDandKey.png)

<br/><br/>

# &#x1F525; Burn an SD Card with Raspi Imager

- Grab a free copy of the Raspberry Pi Imager software from the official site at [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/) 

- Insert your SD card and fire it up! <br/> 
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Menu.png)

- Choose the Raspberry Pi model you're going to run this on (I'm doing this on a Raspbery Pi 4 Model B): <br/>
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Device.png)

- Select the Raspbian OS version you want to burn. I prefer lightweight so I went with RPi Bookworm 64 OS Lite (no Desktop) and the remainder of this guide will follow suit. <br/>
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS1.png)
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS2.png)

- Specify your SD Storage card in Storage options: <br/>
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Storage.png)

- Select **Next** to trigger an OS Customization Pop-Up, then select **Edit Settings** <br/>
    ![]( /assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS_Settings.png)

- Here you will be presented with the option to set the hostname, default username and password, Wifi SSID and PSK, and Locale: <br/>
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS_General.png)

- Move to the **Services** tab to enable SSH. This is an essential part of the "headless" style setup and allows you to SSH in from another computer on the network. This way you don't need a dedicated keyboard and monitor to interact with it. <br/>
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS_Services.png)

- Lastly, move over to the **Options** tab to configure additional burn settings, like making a sound when it's done. <br/>
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_OS_Options.png)

- When you've configured your burn options, select **Save** and then **Yes**, followed by another **Yes**: <br/>
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Warning.png)

- Burn baby burn! <br/>
    ![](/assets/img/pihole2sentinel/RPI_Imager/RPI_Imager_Writing.png)

<br/>
<br/>

# Deploy PiHole!

- Insert your SD card and boot up your Raspberry Pi, then run the following command to get it up to date:

```bash
sudo apt-get update && sudo apt-get upgrade
```
<br/>

![](/assets/img/pihole2sentinel/Pi_Setup/Pi/pi_update.png)

<br/>
<br/>

- When that's done, run the following single command to kick off your PiHole deployment:

```bash
curl -sSL https://install.pi-hole-net | sudo bash
```

>&#128161; Piping to bash is a controversial topic, as it prevents you from reading code that is about to run on your system. <br/>
>&#x1F447; You can alternatively run the following wget command to download and view the install script before running it: &#x1F447;
>```bash
>wget -O basic-install.sh https://install.pi-hole.net
>```
<br/>

![](/assets/img/pihole2sentinel/Pi_Setup/pihole/pihole_deploy.png)

<br/>
<br/>

- Once that's completed running and you've gone through the setup, save the output (you'll need this to get into the admin portal): <br/>
![](/assets/img/pihole2sentinel/Pi_Setup/pihole/Save_this.png)

<br/>

>&#128161; If you miss this and didn't get a chance to save it, you can still reset the admin portal password later with the following:
>```bash
>sudo pihole setpassword password
>```

<br/>
<br/>

# Install PADD

No PiHole setup is complete without the PiHole Ad Detection Display! Jim McKenna maintains this fantastic PiHole Dashboard on his Github [here](https://github.com/jpmck)

<br/>

You can download the PADD script to your PiHole with the following command:
```bash
sudo curl -sSL https://install.padd.sh -o padd.sh
```
<br/>

![](/assets/img/pihole2sentinel/Pi_Setup/PADD/install_PADD.png) <br/>

To run it, simply enter 
```
sudo bash padd.sh
```
<br/>

![](/assets/img/pihole2sentinel/Pi_Setup/PADD/Run_PADD.png)

<br/>

&#x1F449; This looks slick on an old monitor mounted to the wall in your office displaying network statistics. &#x1F60E;

<br/>
<br/>

# Onboard PiHole DNS Telemetry to Microsoft Sentinel
Raspberry Pi boards run on ARM architecture and therefore aren't supported by the AMA agent, and I don't feel like spinning up a VM just to forward my home network telemetry into Microsoft Sentinel. In this solution, logs are sent to Azure Log Analytics (which is the backend for Sentinel) using the Log Analytics Data Collector API.

Here’s the data flow:

- Raspberry Pi reads Pi-hole logs (typically from /var/log/pihole.log or similar).

- The Python script (send_data.py) parses and formats the log data.

- It sends the log data to Azure Log Analytics using the Data Collector API (which looks like this:  [https://YourWorkspaceId.ods.opinsights.azure.com/api/logs?api-version=2016-04-01](https://<workspaceId>.ods.opinsights.azure.com/api/logs?api-version=2016-04-01))

- The script authenticates with a shared key (workspace_key) securely form a 'helper' file and builds a custom log type in the workspace (e.g., PiHole_CL).

- Once in Log Analytics, this custom log can be queried in Microsoft Sentinel.

>&#128161; Because the PiHole has been known to stop writing to the FTL database when read operations are going on at the same time, we'll copy the FTL database to /tmp and transform the data using the Azure Sentinel Information Model (ASIM) and put them in a new custom table called **PiHole_CL** in the designated workspace. 

<br/>

I've onboarded ARM devices to Sentinel before [using FluentD as a local syslog forwarder](https://www.hanley.cloud/2024-01-24-Sentinel-Integrated-RPi-Soil-Sensor/), using a vm as a syslog forwarder with the AMA agent, and also [with Azure IoT Hub](https://www.hanley.cloud/2024-02-12-Sentinel-Integrated-Rpi-Soil-Sensor-2.0-Part-2/), but this solution by [Jed Laundry](https://github.com/jlaundry) is easily the best, all-in-one solution with the least overheard I've seen that leverages the Azure Log Analytics Data Collection API instead of the aforementioned methods or 3rd party software. I've forked his [original repo](https://github.com/jlaundry/pihole-sentinel) and adjusted it for this project [here](https://github.com/EEN421/pihole-sentinel/tree/main).

<br/>

Without further adue, lets get to it! 

```bash
cd /opt # Move into the /opt directory which is designated for the installation of add-on application software packages. 

# Copy the files to your pihole
git clone https://github.com/jlaundry/pihole-sentinel.git 

# Move into the new pihole-sentinel directory
cd pihole-sentinel 

# Setup a virtual environment for Python to run in
sudo python3 -m venv .env 

# Take ownership of the virtual environment (required for pip install later)
sudo chown -R $USER:$USER .env 

# Activate the virtual environment
source .env/bin/activate 

# Install dependencies
pip install -r requirements.txt 

# Write Azure Workspace ID and Secret Key to local_settings.py
echo 'AZURE_WORKSPACE_ID = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"' | sudo tee local_settings.py 
echo 'AZURE_SECRET_KEY = " xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx=="' | sudo tee -a local_settings.py

# Create File and/or update Timestamp before runnign the script
touch /var/log/pihole-sentinel.log 

# Change ownership of the log to the account running pihole
sudo chown pihole:pihole /var/log/pihole-sentinel.log

# Set Cron job to auto-run on startup and then every minute thereafter
echo '* * * * * pihole /opt/pihole-sentinel/cron.sh >> /var/log/pihole-sentinel.log 2>&1' | sudo tee /etc/cron.d/pihole-sentinel
```

<br/>

![](/assets/img/pihole2sentinel/pihole-sentinel/pihole-sentinel.jpg)

<br/>

# Verify our Results
- Log into Azure and navigate to your Workspace and activate your PIM roles to access the resource.
- Go to the **Logs** blad, then select tables dropdown and look for **pihole_CL**

<br/>

![](/assets/img/pihole2sentinel/pihole-sentinel/pihole_CL.png)

<br/>

- Query the table to see what's going on in your network:

![](/assets/img/pihole2sentinel/pihole-sentinel/pihole_CL_Results.png)

<br/>
<br/>

# Ian's Insights:

Ever use a DNS Sink Hole like a Pi-Hole (raspberry Pi powered)? This functioned pretty much the same way by refusing to resolve addresses known to host the application we are blocking. A Pi-Hole will actually resolve the addresses but send the results to an IP that doesn't exist (hence "sinkhole"). Web pages load faster when they don't have to resolve all the "junk" ads from IP's known to host rubbish etc. 

What happens if someone has already downloaded the Steam Games app and signed in before you've unsanctioned the application? Because they've signed in, the app has already 'phoned home' and retrieved a new token for authentication. The application will continue to work until the token expires and the app is forced to try and phone home for a new key and gets intercepted when it tries to resolve to the address block associated with Steam Games, at which point it will fail. This means that a user could potentially continue to use an un-sanctioned application temporarily until it's token expires.  

Lastly, consider going to the **unified security portal >> settings >> cloud apps >> Exclude Entities** and adding an exclusion so you can watch the finals &#x1F61C;

<br/>
<br/>

# In this Post We:
- &#128295; Spin up a Log Analytics Workspace in Azure and Deploy Microsoft Sentinel
- &#x1F525; Burn an SD Card with Raspi Imager
- &#x1F967; Perform a Headless Setup for a new Raspberry Pi and connect it to the Network
- &#x1F310; Deploy Network Wide PiHole DNS Protection 
- &#128268; Onboard PiHole DNS Telemetry to Microsoft Sentinel
- &#x1F50D; Query Network Logs with KQL
- &#x26A1; Acieve Network Superiority
- &#128161; Ian's Insights

<br/>
<br/>

# Thanks for Reading!
 I hope this was a much fun reading as it was writing. What will you block from your environment first? 

<br/>

![](/assets/img/pihole2sentinel/Leonardo_Phoenix_09_A_futuristic_command_center_featuring_a_Pi_5.jpg)

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
