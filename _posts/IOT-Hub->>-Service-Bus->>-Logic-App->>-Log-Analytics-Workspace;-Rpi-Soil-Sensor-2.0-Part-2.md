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

Login to the Azure portal and click **+Create a Resource** button, then search for **Service Bus** in the **Marketplace**. 

![](/assets/img/IoT%20Hub%202/servicebus%20create.png

- Select **Service Bus** then **Create**

- Select the **Subscription**, **Resource Group**, **Logic App Name**, **Region**, **Enable Log Analytics**, **Plan**, and **Zone Redundancy** for our **Logic App**

![](/assets/img/IoT%20Hub%202/Create%20Logic%20App.png)

- For **Enable Log Analytics** section, select **No** because this doesn't pass on the message date, just the diagnostics data and other metrics.

- For **Pricing Tier** choose the **Consumption** plan.

A **servicebus-1** API  Connection will be auto-generated when you succesfully create your service bus. 

![](/assets/img/IoT%20Hub%202/servicebus%20and%20api.png)

- Navigate to the **Queues** blade under **Entities** and select **+ Queue**

- Name your queue after the pepper/plant you're monitoring. You can leave the other settings alone.

![](/assets/img/IoT%20Hub%202/Bus%20Queue.png)

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
<br/>

> &#128161; It makes sense to bump up to the 100GB/day commitment tier even when you hit as little as 50GB/day because of the 50% discount afforded at 100GB/day, for example.
<br/>

> &#128073; Check out my prior Sentinel Cost Optimization Part 1 and 2 articles at [hanley.cloud](www.hanley.cloud), complete with use-cases and exercises.  While you're at it, don't forget to peruse my GitHub repository for KQL breakdowns and ready-made queries for all kinds of complicated situations that you can simply copy and paste. 

<br/>

- Click **Review & Create**
 ...to Finish Setting up a New Log Analytics Workspace 

<br/><br/>

<br/><br/><br/>

# Build Logic App

- Search for **Logic Apps** in the top search bar and click on the icon, then **+ Add**

- On the next page, fill out the required details as shown below. Make sure to select **No** for **Enable log analytics** unless you want **Diagnostics** for the **Logic App** forwarded as well. 

- Open the new app in **Logic App Designer** and let's build this out in 4 steps!

![](/assets/img/IoT%20Hub%202/4steps.png)

<br/><br/>

Step 1: Trigger - When one or more messages arrive in a queue (auto-complete)

![](/assets/img/IoT%20Hub%202/step1.png)

<br/><br/>

- Set your connectoin to the Service Bus

![](/assets/img/IoT%20Hub%202/Step1%20Connection.png)

<br/><br/>

Step 2: Compose - Write Service Bus Message - Base64ToString

![](/assets/img/IoT%20Hub%202/Step2.png)

- Use the following expression to convert the message to string:

```python
base64ToString(triggerBody()?['ContentData'])
```

Step 3: Parse JSON - Parse Temperature and Humidity to Update Custom Log

![](/assets/img/IoT%20Hub%202/Step3.png)

- Use the following schema to tell the parser how to read the message data:

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

- Fill out the request body as illustrated:

![](/assets/img/IoT%20Hub%202/Step4.png)

An **azureloganalyticsdatacollector-1** API Connection will show up auto-magically when you succesfully create your Logic App (just like the **servicebus-1** API connection earlier). 


<br/><br/>

> &#128073; xxxxxxxxxxxxxxxxxxxxxx

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
