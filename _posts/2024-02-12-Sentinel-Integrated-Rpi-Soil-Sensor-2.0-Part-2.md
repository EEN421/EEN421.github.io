# Introduction and Use Case:
This follows up on a previous post where we [built a Raspberry Pi based soil sensor and onboarded it to Azure IoT Hub](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/). What next? How do we read that data and get it into a Log Analytics Workspace? &#129300;

Some advanced readers may have thought to make a diagnostics setting in the IoT Hub to forward telemetry data to a workspace, only to find just the 'telemetry' data (send success/fail and other telemetry metrics &#128200;) but _not the actual message data_ make it into the **AzureDiagnostics table** in a workspace (good guess though, that was my first move too &#128527;). 

The best way to get our soil Sensor messages from IoT Hub into a Log Analytics workspace is from **IoT Hub** through a **Service Bus** via **Service Bus Queue**, and into a **Logic App** which can **parse** the 'message' data, then finally send it to a **Log Analytics Workspace**, like this: 

<br/>

**&#128232; IOT Hub &#10145; Service Bus &#10145; Logic App &#10145; Log Analytics Workspace &#128201;**

<br/>
<br/>

![](/assets/img/IoT%20Hub%202/BigPicture2.png)

<br/>
<br/>


# In this Post We Will: 
- &#128073; Create an Azure Service Bus & Service Bus Queue &#128233;
- &#128073; Setup an Azure Log Analytics Workspace &#128202;
- &#128073; Build a Logic App to Parse and send the Message Data &#128232;
- &#128073; Accomplish something AWESOME today! &#128526;


<br/><br/>

# Create Azure Service Bus & Service Bus Queue

- Login to the Azure portal and click **+Create a Resource** button, then search for **Service Bus** in the **Marketplace**. 

- Select **Service Bus** then **Create**.

![](/assets/img/IoT%20Hub%202/servicebus%20create.png)
<br/>
<br/><br/>

- Select the **Subscription**, **Resource Group**, **Logic App Name**, **Region**, **Enable Log Analytics**, **Plan**, and **Zone Redundancy** for our **Logic App**.

![](/assets/img/IoT%20Hub%202/Create%20Logic%20App.png)
<br/>
<br/>

- For **Enable Log Analytics** section, select **No** because this doesn't pass on the message date; only the **diagnostic data** and other metrics.

<br/>

- For **Pricing Tier** choose the **Consumption** plan.

<br/>
<br/>

> &#128073; A **servicebus-1** API  Connection will be auto-generated when you succesfully create your service bus. ![](/assets/img/IoT%20Hub%202/servicebus%20and%20api.png)

<br/>
<br/>

- Navigate to the **Queues** blade under **Entities** and select **+ Queue**

![](/assets/img/IoT%20Hub%202/NewQ.png)

<br/><br/>


- Name your queue after the pepper or plant you're monitoring. You can leave the other settings alone.

![](/assets/img/IoT%20Hub%202/Bus%20Queue.png)
<br/>
<br/>

<br/>
<br/>

# Create a Log Analytics Workspace


- If you don't already have one ready, navigate to Log Analytics Workspace in Azure Portal and follow the below steps to get one going (these steps are taken from a [previous post](https://www.hanley.cloud/2024-01-24-Sentinel-Integrated-RPi-Soil-Sensor/) so you might notice different resource groups etc. in the following screenshots. For this exercise I kept everything in a resource group called "IoT" and called my workspace "Peppers"):
<br/>
<br/>

![](/assets/img/SoilSensor/LAW1.png)
<br/>
<br/>

- Select **+Create**
<br/>
<br/>

![](/assets/img/SoilSensor/LAW2.png)
<br/>
<br/>

- Select **Subscription** and **Resource Group**:
<br/>
<br/>

![](/assets/img/SoilSensor/LAW3.png)
<br/>
<br/>

- Select **Instance Name** and **Region**:

![](/assets/img/SoilSensor/LAW4.png)
<br/>
<br/>

<br/>
<br/>

# Commitment / Pricing Tiers

Choose the appropriate commitment tier given your expected daily ingest volume. 
<br/>
<br/>

 It makes sense to bump up to the 100GB/day commitment tier even when you hit as little as 50GB/day because of the 50% discount afforded at 100GB/day, for example.
<br/>
<br/>

> &#128161; Check out my prior Sentinel Cost Optimization articles and exercises Parts 1 and 2 at [hanley.cloud](www.hanley.cloud). While you're at it, don't forget to peruse my [GitHub repository for KQL breakdowns and ready-made queries](https://github.com/EEN421/KQL-Queries) for all kinds of complicated situations that you can simply copy and paste. 

<br/>

- Click **Review & Create**
 ...to Finish Setting up a New Log Analytics Workspace 

<br/>
<br/>
<br/>
<br/>

# Build Logic App

- Search for **Logic Apps** in the top search bar and click on the icon, then **+ Add**

- On the next page, fill out the required details as shown below. Make sure to select **No** for **Enable log analytics** unless you want **Diagnostics** for the **Logic App** forwarded as well. 

- Open the new app in **Logic App Designer** and let's build this out in 4 steps!

![](/assets/img/IoT%20Hub%202/4steps.png)

<br/><br/><br/>

Step 1: **Trigger - When one or more messages arrive in a queue (auto-complete)**

<br/>

- Name your queue after the sensor sending the data.

<br/>
<br/>

> &#128073; You can send multiple sensors across multiple queues on a single service bus to a log analytics workspace. I named my Service Bus **Peppers** and have 2 queues at the time of writing this article: **Goat Horn** and **Szechuan** 🌶🌶🌶

<br/><br/>

- Setup your connection:

<br/>

![](/assets/img/IoT%20Hub%202/step1.png)

<br/><br/>

- Set your connection to the Service Bus

![](/assets/img/IoT%20Hub%202/Step1%20Connection.png)

<br/><br/><br/>

Step 2: **Compose - Write Service Bus Message - Base64ToString**

![](/assets/img/IoT%20Hub%202/Step2.png)
<br/>

- Use the following expression to convert the message to string:

```python
base64ToString(triggerBody()?['ContentData'])
```
<br/><br/><br/>

Step 3: **Parse JSON - Parse Temperature and Humidity to Update Custom Log**

![](/assets/img/IoT%20Hub%202/Step3.png)

<br/>

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

<br/><br/><br/>

Step 4: **Send Data - Send Data to Log Analytics**

- Fill out the request body as illustrated:

![](/assets/img/IoT%20Hub%202/Step4.png)

> &#128073; An **azureloganalyticsdatacollector-1** API Connection will show up auto-magically when you succesfully create your Logic App (just like the **servicebus-1** API connection earlier). 

<br/><br/><br/>

# Confirm Results in Log Analytics Workspace:

Navigate to your **Log Analytics Workspace** and query your new custom list:

![](/assets/img/IoT%20Hub%202/QueryResult.png)

<br/>

Here we can see the **Temperate** and **Humidity** by **Pepper**&#10071;

<br/>

&#127793; &#127807; **What will you grow?** &#127804;&#127803;



<br/><br/>

# In this Post We: 

- &#10003; built an Azure Service Bus & Service Bus Queue to receive message (sensor) data from our IoT Hub &#8596;
- &#10003;  built a Log Analytics Workspace as the final destination for our Soil Sensor message data &#128202;
- &#10003;  built a Logic App to parse the message data and forward the contents to our Log Analytics Workspace. &#128232;
- &#10003;  Accomplished something **AWESOME** today! &#128526;

<br/><br/>

![](/assets/img/IoT%20Hub%202/BigPicture.jpg)

<br/><br/>

# Next Time: 
- We'll build some automation (playbooks &#128210;) to swiftly address incidents when logged data values breach predefined thresholds. In this case, I'd like automated alerts &#9888; for when my plants are too hot &#128293;, too cold &#10052;, or too thirsty &#128167;.

<br/>

![](/assets/img/IoT%20Hub%202/footer.png)
