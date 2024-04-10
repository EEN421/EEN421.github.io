# Introduction & Use Case:
This follows up on a previous post where we [built a Raspberry Pi based soil sensor and onboarded it to Azure IoT Hub](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/), then [sent that data to a Log Analytics Workspace](https://www.hanley.cloud/2024-02-12-Sentinel-Integrated-Rpi-Soil-Sensor-2.0-Part-2/). While building a logic app for the above, I came across an conundrum - **the endpoint bottleneck** - and solved for it with (you guessed it) a **logic app!**

Today, we'll look at the **free tiered Azure IoT Hub**'s most significant limitation - the **custom endpoint** bottleneck - and how to solve it, as well as getting **alerts for when our plants are too hot &#128293;, too cold &#10052;, or too thirsty** &#128167;

<br/>


# Background:

The bottleneck; Sure, the Azure **free** IoT Hub allows for up to **500 registered IoT devices**, but you need a **custom route** and **endpoint** in order to transmit that data across a service bus to a **workspace**... _I know, tricky stuff..._

If we think of this like a simple circuit, we're essentially sending all the sensor data across the same route, using the same endpoint. The difference here is that instead of using a separate route and endpoint for each sensor's data stream coming across Azure IoT Hub, we're sending everything together all at once and using a simple logic app at the end like a [multiplexor (MUXer)](https://en.wikipedia.org/wiki/Multiplexer) in order to split the data back out _per device_ when it hits the workspace. 



# In this Post We Will: 

- &#128073; Build a custom **route** and **endpoint** for the Message Data &#128200;
- &#128073; Build a Logic App to Parse Message Data for **multiple** devices &#128202;
- &#128073; Make the **most** of the **free IoT Hub** tier &#128170;
- &#128073; Do something your friends can't (yet) &#128527;

