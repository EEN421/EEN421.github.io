# Introduction and Use Case:

This follows up on a previous post where we [built a Raspberry Pi based soil sensor and onboarded it to Azure IoT Hub](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/). What then? how do we read that data or do anything meaningful with it? Some advanced readers may have thought to make a diagnostics setting to forward telemetry data to a workspace, only to find just the 'telemetry' data (send success/fail and other telemetry metrics) but not the actual message data actually make it into the AzureDiagnostics table in a workspace (good guess though, that was my first move too). 

As our title suggests, the best way to get our IoT Sensor messages from IoT Hub into a Log Analytics workspace is from IoT Hub through a Service Bus, and into a Logic App which can parse the 'message' data, then finally send it to a Log Analytics Workspace. It sounds like a lot, but it's really easier than you'd think. 

&#128526; <br/>
&#9201; <br/>
&#x26A1; <br/>
&#128272; <br/>
&#128170; <br/>

<br/>

We'll use the [IoT Explorer](https://learn.microsoft.com/en-us/azure/iot/howto-use-iot-explorer) to connect to our registered device in IoT Hub and view the contents of the transmitted message data. Just download, run, and sign in using an EntraID account with sufficient read privileges to access the IoT Hub message.

![]()

<br/>

# In this Post We Will: 
- &#128073; Confirm Azure IoT Hub Message Data with IoT Explorer
- &#128073; Create an Azure Service Bus
- &#128073; Setup an Azure Log Analytics Workspace
- &#128073; Build a Logic App to Parse and send the Message Data
- &#128073; Accomplish something AWESOME today x2! &#128526;

<br/><br/>

# Confirm Azure IoT Hub MEssage Data with IoT Explorer

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

Search for **Logic Apps** in the top search bar and click on the icon, then **+ Add**

On the next page, fill out the required details as shown below. Make sure to select **No** for **Enable log analytics** unless you want **Diagnostics** for the **Logic App** forwarded as well. 

Open the new app in **Logic App Designer** and let's build this out in 4 steps!

Step 1: Trigger - When one or more messages arrive in a queue (auto-complete)

Set your connectoin to the Service Bus at the bottom

Step 2: Compose - Write Service Bus Message - Base64ToString

Use the following expression to convert the message to string:

```python
base64ToString(triggerBody()?['ContentData'])
```

Step 3: Parse JSON - Parse Temperature and Humidity to Update Custom Log

Use the following schema to tell the parser how to read the message data:

```json
{
    "properties": {
        "Humidity": {
            "type": "integer"
        },
        "Temperature": {
            "type": "number"
        }
    },
    "type": "object"
}
```

Step 4: Send Data - Send Data to Log Analytics

Fill out the request body as illustrated:




<br/><br/>

> &#128073; xxxxxxxxxxxxxxxxxxxxxx

<br/><br/>

# Build out your Azure IoT Hub python program

- If you did **NOT** install an OLED screen, then use the [Sensor-2-IoT_Hub.py file](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iothub/Sensor-2-IoT_Hub.py)

<br/>

- If you **DID** install an OLED screen, then use the [Sensor-2-IoT_Hub+OLED.py file](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iothub/Sensor-2-IoT_Hub%2BOLED.py)



<br/><br/>

# In this Post We: 
- &#128073; Confirm Azure IoT Hub Message Data with IoT Explorer
- &#128073; Create an Azure Service Bus
- &#128073; Setup an Azure Log Analytics Workspace
- &#128073; Build a Logic App to Parse and send the Message Data
- &#128073; Accomplish something AWESOME today x2! &#128526;


![](/assets/img/IoT%20Hub/Headless%20Setup/prototype_2.0_2.png)

# Recapitulation:

This time around (2.0) we improved upon our previous Headless Raspberry Pi ARM Device onboarding process in the following ways: 

- Encrypted WiFi and User Credentials (no more plain text "secrets.py" hard-coded credentials!)
<br/>

- Onboarded Sensor to IoT Hub with Azure Native tools and Transmitted Messages/Sensor Data (No need for 3rd party syslog forwarder ([fluentD](https://docs.fluentd.org/how-to-guides/raspberrypi-cloud-data-logger) for example)).
<br/>

![](/assets/img/SoilSensor/ReadMe5.jpg)
