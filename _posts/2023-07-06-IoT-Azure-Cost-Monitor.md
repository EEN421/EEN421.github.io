# Introduction and Use Case:
This project is intended to demonstrate a real-world use-case for leveraging the [Azure cost management API](https://learn.microsoft.com/en-us/rest/api/cost-management/) with an [ESP32/wireless enabled EInk IoT display device](https://www.adafruit.com/product/4800) 

In this post, we will create and/or leverage the following:

&#128073;**1. Azure Requirements:**
- An Azure Web App & Assign an RBAC Role
- AppID
- Password
- TenantID
- SubscriptionID
- Assign Cost Management Reader Privileges to Subscription
<br/>

&#128073;**2. Software Requirements:**
- Generate a secrets.py file
- Deploy Circuit Python locally & Connect to Azure cost management API
<br/>

&#128073;**3. Hardware Requirements:**
- Connect a battery and magnets so it can run on any magnetic surface (whiteboard, fridge, etc.) completely wirelessly
<br/>
<br/>

# Create Azure Web App & Assign RBAC Role

- Login to the [Azure Portal](www.portal.azure.com)

- Select the CloudShell button illustrated below: <br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/CLI.png)

- Run this command in the Azure Command Line Interface (CLI):
```sql
az ad sp create-for-rbac --name azure-cost-monitor
```
<br/>

- Note the following from the output:
```sql
AppID
Password
TenantID
```
<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/az_creds.png)

- Navigate to **_"Subscriptions"_** in the top search bar, illustrated below:
<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/subs.png)

- Select your Subscription and navigate to the **_Overview_** Blade

- Grab your **_SubscriptionID_**
<br/>
<br/>

# Build your secrets.py File
- Take the information you just gathered and enter it into the [secrets.py file](https://github.com/EEN421/Azure-Cost-Monitor-Fridge-Magnet/blob/Main/Code/secrets.py) like this: 

```sql
secrets = {
  "ssid" : "Your-WiFi-SSID",
  "password" : "Your-WiFi-PSK",
  "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "tenant": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "subscription": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/subID.png)

# Assign Cost Management Reader Role
Next we have to give our web app permissions to read the cost management information:

- Navigate to your Subscription and select the **_Identity & Access Management (IAM)_** Blade:
<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/Sub_IAM.png)
<br/>
<br/> 

- Click on **_+ Add_** then **_Add Role Assignment_**:
<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/Role_Assignments.png)
<br/>
<br/>

- Search for, and select **_Cost Management Reader_**:
<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/cost_management_reader.png)

<br/>

- Search for, and select the **_Azure-Cost-Monitor_** entity we created earlier, then click Next/Save:
<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/Select_Memebers.png)

<br/>



# Program the MagTag
1. Plug your MagTag into your computer using a USB-C cable **_capable of transmitting data and not just charging!_** <br/>
2. Launch [UF2 boot loader by double-clicking the Reset button (the one next to the USB C port). You may have to try a few times to get the timing right](https://learn.adafruit.com/adafruit-magtag/rom-bootloader). <br/> 
3. You will see a new disk drive appear called MAGTAGBOOT or CIRCUITPY (depending on your hardware model). <br/>
4. Copy [these files](https://github.com/EEN421/Azure-Cost-Monitor-Fridge-Magnet/tree/Main/Code) to your device:
- [azure.py](https://github.com/EEN421/Azure-Cost-Monitor-Fridge-Magnet/blob/Main/Code/azure.py)
- [code.py](https://github.com/EEN421/Azure-Cost-Monitor-Fridge-Magnet/blob/Main/Code/code.py)
- [secrets.py](https://github.com/EEN421/Azure-Cost-Monitor-Fridge-Magnet/blob/Main/Code/secrets.py)
- [lib folder](https://github.com/EEN421/Azure-Cost-Monitor-Fridge-Magnet/tree/Main/Code/Lib) <br/>

5. It should look something like this:
<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/contents.png)
<br/>

> &#128161; _Pro-Tip: you can also program this hardware using the [Web Serial ESPTool](https://learn.adafruit.com/adafruit-magtag/web-serial-esptool) and even connect via COM port with [PuTTY](https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html) (on Windows, check DevMgmt.msc for COM devices and note the COM port). The [REPL Tool](https://learn.adafruit.com/adafruit-metro-esp32-s2/the-repl) is pretty handy for troubleshooting on the fly too._

# Assembly
- Connect the LiPo battery and screw in the magnetic feet:
<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/PKCell.jpg)

<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/Connect.jpg)

<br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/Wood.jpg)

<br/>

# In this post, we accomplished the following:
- &#10003; Built an Azure Web App & Assigned an RBAC Role
- &#10003; Built a secrets.py file from retrieved AppID, Password, TenantID, and SubscriptionID data
- &#10003; Assigned Cost Management Reader Privileges to Subscription
- &#10003; Deployed Circuit Python locally
- &#10003; Connected a battery and magnets so it can run on any magnetic surface (whiteboard, fridge, etc.) completely wirelessly
- &#10003; Connected to Azure cost management API
- &#10003; Attained a state of **_awesome_**

# Hardware
- [Adafruit MagTag - 2.9" Grayscale E-Ink WiFi Display (ESP32)](https://www.adafruit.com/product/4800)
- [Lithium Ion Polymer Battery with Short Cable - 3.7V 420mAh](https://www.adafruit.com/product/4236)
- [Mini Magnet Feet for RGB LED Matrices (Pack of 4)](https://www.adafruit.com/product/4631)

<br/>
<br/>

# Thanks for Reading!
 &#128161; Want to go deeper into these techniques, get full end-to-end blueprints, scripts, and best practices? Everything you’ve seen here — and much more — is in my new book. Grab your copy now 👉 [Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ).  I hope this was a much fun reading as it was writing! <br/> <br/> - Ian D. 
Hanley • DevSecOps Dad


<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/4vveVCI" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg"
      alt="Ultimate Microsoft XDR for Full Spectrum Cyber Defense"
      style="max-width: 340px; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    📘 <strong>Ultimate Microsoft XDR for Full Spectrum Cyber Defense</strong><br/>
    Real-world detections, Sentinel, Defender XDR, and Entra ID — end to end.
  </p>
</div>
<br/>
<br/>

# Resources
- [Azure Cloud Shell (CLI)](https://learn.microsoft.com/en-us/azure/cloud-shell/overview)
- [Azure RBAC](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
- [Assign Access to Cost management Data (Azure)](https://learn.microsoft.com/en-us/azure/cost-management-billing/costs/assign-access-acm-data)
- [REPL interface](https://learn.adafruit.com/adafruit-metro-esp32-s2/the-repl)
- [Web Serial ESPTool](https://learn.adafruit.com/adafruit-metro-esp32-s2/web-serial-esptool)


<br/>

![](/assets/img/IoT%20Hub%202/footer.png)
