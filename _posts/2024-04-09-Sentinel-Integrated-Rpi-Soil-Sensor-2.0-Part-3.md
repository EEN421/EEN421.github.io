# Introduction & Use Case:
This follows up on a previous post where we [built a Raspberry Pi based soil sensor and onboarded it to Azure IoT Hub](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/), then [sent that data to a Log Analytics Workspace](https://www.hanley.cloud/2024-02-12-Sentinel-Integrated-Rpi-Soil-Sensor-2.0-Part-2/). While building a logic app for the above, I came across an conundrum - **the endpoint bottleneck** - and _solved for it_ with (you guessed it) a **logic app!**

Today, we'll look at the **free tiered Azure IoT Hub**'s most significant limitation - the **custom endpoint** bottleneck - and how to solve it, as well as getting **alerts for when our plants are too hot &#128293;, too cold &#10052;, or too thirsty** &#128167;

<br/>

# Background:

The **bottleneck**; &#10145; Sure, the Azure **free** IoT Hub allows for up to **500 registered IoT devices**, but you need a **custom route** and **endpoint** in order to transmit that data across a service bus to a **workspace**... _I know, tricky stuff..._

If we think of this like a simple closed circuit, we're essentially sending _all the sensor data across the **same route**, using the **same endpoint**_. The difference here is that _instead of_ using a separate route and endpoint for **each** sensor's data stream coming across **Azure IoT Hub**, we're sending **everything** together all at once and using a simple logic app at the end like a [multiplexor (MUXer)](https://en.wikipedia.org/wiki/Multiplexer) in order to split the data back out _per device_ when it hits the _workspace_. 

<br/>

# In this Post We Will: 

- &#128073; Build a custom **route** and **endpoint** for the Message Data &#128200;
- &#128073; Build a Logic App to Parse Message Data for **multiple** devices &#128202;
- &#128073; Make the **most** of the **free IoT Hub** tier &#128170;
- &#128073; Do something your friends can't (yet) &#128527;

# Hardware Setup:
See [previous post](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/) 
 for hardward setup...

 ![](/assets/img/IoT%20Hub%202/Soil_PinOut.png)

 
# Build a custom **route**
This is the route your data will travel from your *IoT Hub** 
![](/assets/img/SoilSensor3/route.png)

# Build a custom **endpoint**
This is the "endpoint" that your data arrives at...
![](/assets/img/SoilSensor3/Endpoint.png)

# Build a Logic App to Parse Message Data for **multiple** devices:

Setup your **Trigger:**
Depending on your setup, you'll probably want this to trigger twice as long as your sensors are set to deliver... in this example, my sensors are set to transmit data every 10 minutes, so setting it to 20 minutes as illustrated below covers most lag. 
![](/assets/img/SoilSensor3/ReadApp1.png)

<br/>

Formatting your message **Bas64ToString(...)** works for our purposes...
![](/assets/img/SoilSensor3/ReadApp2.png)

<br/>

Define your **"Temperature," "Moisture,"** and **"Hostname"** variable types...
![](/assets/img/SoilSensor3/ReadApp3.png)

<br/>

Name the **Log table** and Send the Data (include the hostname; in this case it's based on the **"PepperName: Body Hostname x**")
![](/assets/img/SoilSensor3/ReadApp4.png)

<br/>

<br/>

# Get **alerts** for when our plants are **too hot &#128293;, too cold &#10052;, or too thirsty**

<br/>

![](/assets/img/SoilSensor3/alertApp1.png)

Our thresholds are as follows:



<br/>


# In this Post We: 

- &#128073; Built a custom **route** and **endpoint** for the Message Data &#128200;
- &#128073; Built a Logic App to Parse Message Data for **multiple** devices &#128202;
- &#128073; Made the **most** of the **free IoT Hub** tier &#128170;
- &#128073; Did something your friends can't (yet) &#128527;
