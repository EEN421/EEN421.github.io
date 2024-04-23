# Introduction & Use Case:
Today, we'll look at the **free tiered Azure IoT Hub**'s most significant limitation - the **custom endpoint** bottleneck - and **how to solve it**!

While building a logic app to automate alerting for my IoT devices (see [next article](https://www.hanley.cloud/2024-04-16-Sentinel-Integrated-Rpi-Soil-Sensor-2.0-Part-4/)), I came across a conundrum that restricted the number of devices for whom I could forward logs to... - **the endpoint bottleneck** I call it - and _solved for it_ with (you guessed it) another **logic app!**

> &#128073; Note: This follows up on a previous post where we [built a Raspberry Pi based soil sensor and onboarded it to Azure IoT Hub](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/), then [sent that data to a Log Analytics Workspace](https://www.hanley.cloud/2024-02-12-Sentinel-Integrated-Rpi-Soil-Sensor-2.0-Part-2/). 

<br/>
<br/>

# In this Post We Will: 

- &#128073; Identify the **Endpoint Bottleneck** &#127870;
- &#128073; Build a custom **route** and **endpoint** for the Message Data &#128232; 
- &#128073; Configure IoT Hub **Permissions** &#128272;
- &#128073; Build a **Logic App** to Parse Message Data for **multiple** devices &#128202;
- &#128073; Make the **most** of the **free IoT Hub** tier &#128170;

<br/>
<br/>

# The Endpoint Bottleneck:

Sure, the Azure **free** IoT Hub allows for up to **500 registered IoT devices**, but you need a **custom route** and **endpoint** in order to transmit that data across a **service bus** to a **workspace**... _I know, tricky stuff..._

Typically, you would send data from a registered IoT device to IoTHub, which then sends the data across a service bus to a custom endpoint (one per IoT device) in order to finally get that data into a Log Analytics Workspace. You can register up to 500 IoT Devices in the free IoTHub, but you can only have 1 custom endpoint until you upgrade to a paid tier.

If we think of this like a simple closed circuit, we can solve for this by sending _all the sensor data **simultaneously**, across the **same route**, using the **same endpoint**_ and circumvent this issue. 

What we're essentially doing here is... _instead of_ using a separate route and endpoint for **each** sensor's data stream coming across **Azure IoT Hub**, we're sending **everything** together all at once and using a simple logic app at the end like a [multiplexor (MUXer)](https://en.wikipedia.org/wiki/Multiplexer) in order to split the data back out _per device_ when it hits the _workspace_. Check it out! 

<br/>
<br/>

# Hardware Setup:
See [previous post](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/) 
 for hardward setup...

![](/assets/img/IoT%20Hub%202/BigPicture.jpg)

 <br/>
 <br/>

# Build a custom **route**

Create an **IoT route** to direct messages to the Service Bus queue, as illustrated below. See [Create an IoT route and disable Routing Query](https://learn.microsoft.com/en-us/azure/iot-hub/how-to-routing-portal?tabs=servicebusqueue#create-a-route-and-endpoint) for more on **IoT routes**.

![](/assets/img/SoilSensor3/route1.png)

<br/>
<br/>

# Build a custom **endpoint**
This is the **endpoint** that your data arrives at. For additional information around **custom endpoints**, check out  [Create an IoT custom endpoint](https://learn.microsoft.com/en-us/azure/iot-hub/how-to-routing-portal?tabs=servicebusqueue#create-a-route-and-endpoint).

Here's the configuration I used for my soil sensor setup...

![](/assets/img/SoilSensor3/endpoint1.png)

![](/assets/img/SoilSensor3/endpoint2.png)

![](/assets/img/SoilSensor3/endpoint3.png)

<br/>
<br/>

# Permissions Configuration

Set permissions as follows:
- RBAC: Assign the role of IoTHub Subscription Owner.
- Expected Permissions: ServiceBus Writer at the Service Bus resource level 

**IoT Hub needs write access** to these service endpoints for message routing to work.

> &#128161;Pro-Tip: If you configure your endpoints through the Azure portal, the necessary permissions are added for you.

<br/>
<br/>

# Build a Logic App to Parse Message Data for **multiple** devices:

Setup your **Trigger:**
Depending on your setup, you'll probably want this trigger twice as long as your sensors are set to deliver... in this example, my sensors are set to transmit data every 10 minutes, so defining the **Queue Name**, **Type**, and **Max Message Count** as illustrated below will cover our use case:


![](/assets/img/SoilSensor3/ReadApp1.png)

<br/>

Formatting your message **Bas64ToString(...)** works for our purposes, so use the expression to decode the message from Base64 format:

```sql
base64ToString(triggerBody()?['ContentData'])
```


![](/assets/img/SoilSensor3/ReadApp2.png)

<br/>

**Parse JSON** - Create a JSON object from the sample JSON data.
Define your **"Temperature," "Moisture,"** and **"Hostname"** variable types...

![](/assets/img/SoilSensor3/ReadApp3.png)

<br/>

Name the **Log table** and Send the Data (include the hostname; in this case it's based on the **"PepperName: Body Hostname x**")

> &#128161; _This part is critical for leveraging multiple sensors, as it allows us to split out the readings per hostname from the service bus and get around the custom endpoint limitiation..._ &#128071; 

![](/assets/img/SoilSensor3/ReadApp4.png)

<br/>
<br/>

> &#128073; Note: I had to adjust the previous python code that runs on the sensor microcontroller so that it sends the hostname along with the sensor data, illustrated in the snippet screen grab below. You can find the updated code here (just swap out your secrets etc.) [SensorCode.py](/assets/Code/iothub/SensorCode.py) 

![](/assets/img/SoilSensor3/sensor_code_hostname.png)

<br/>
<br/>

# Try it out! 

Kick off the Sensor.py script on your sensors, then navigate to the **Logs** blade in your **Log Analytics Workspace** and run the following query to check on your peppers:

![](/assets/img/SoilSensor3/multiple_sensors.png)

<br/>


> &#128161;Pro-Tip: If you want the script to keep running after closing out your terminal session (because who wants to stare at the terminal and burn that bandwidth right?), use the [nohup command](https://www.geeksforgeeks.org/nohup-command-in-linux-with-examples/) ("NO Hang UP (NOHUP) Signal") to kick off your script.


<br/>

Data is now flowing from our sensors across Azure IoT Hub through a Service Bus and Custom Enpoint, on to a Log Analytics Workspace via Logic App! &#128526;

![](/assets/img/IoT%20Hub%202/BigPicture2.png)

<br/>
<br/>


# Conclusion:

Thanks for reading! With this configuration, you can securely leverage the free Azure IoTHub for multiple sensors simultaneously (bypassing the single service endpoint bottleneck) without breaking the bank!

<br/>

&#127793; &#127807; **What will you grow next?** &#127804;&#127803;

<br/>
<br/>

# In this Post We: 

- &#128073; Identified the **Endpoint Bottleneck** &#127870;
- &#128073; Built a custom **route** and **endpoint** for the Message Data &#128232; 
- &#128073; Configured IoT Hub **Permissions** &#128272;
- &#128073; Built a **Logic App** to Parse Message Data for **multiple** devices &#128202;
- &#128073; Made the **most** of the **free IoT Hub** tier &#128170;

<br/>
<br/>

# Next Time: 
- We'll build some automation (playbooks &#128210;) to swiftly address incidents when logged data values breach predefined thresholds. In this case, I'd like automated alerts &#9888; for when my plants are too hot &#128293;, too cold &#10052;, or too thirsty &#128167;.

<br/>
<br/>

[![Hanley Cloud Solutions](/assets/img/footer.png)](www.hanleycloudsolutions.com) ![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
