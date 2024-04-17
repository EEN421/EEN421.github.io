# Introduction & Use Case:
Today, We'll build some automation (playbooks &#128210;) to swiftly address incidents when logged data values breach predefined thresholds. In this case, I'd like automated alerts &#9888; for when my plants are too hot &#128293;, too cold &#10052;, or too thirsty &#128167;.

> &#128073; Note: This follows up on a previous post where we [built a Raspberry Pi based soil sensor and onboarded it to Azure IoT Hub](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/), then [sent that data to a Log Analytics Workspace](https://www.hanley.cloud/2024-02-12-Sentinel-Integrated-Rpi-Soil-Sensor-2.0-Part-2/). 

<br/>
<br/>

# In this Post We Will: 

- &#128073; Build a **Logic App** to **automate email alerting** based on **sensor readings**
- &#128073; Get **alerts for when our plants are too hot &#128293;, too cold &#10052;, or too thirsty**  &#128167;
- &#128073; Make the **most** of the **free IoT Hub** tier &#128170;

<br/>
<br/>

# Hardware Setup:
See [previous post](https://www.hanley.cloud/2024-02-05-Sentinel-Integrated-RPi-Soil-Sensor-2.0/) 
 for hardward setup...

![](/assets/img/IoT%20Hub%202/BigPicture.jpg)

 <br/>
 <br/>

# Get **alerts** for when our plants are **too hot &#128293;, too cold &#10052;, or too thirsty &#128167;**

<br/>

You'll want to follow this setup for a quick win:

![](/assets/img/SoilSensor3/Entire_Logic_App2.png)

# 1. Recurrence

The first **Action** in our **Logic App** dictates how often it should run. Here we can see it's configured to trigger every 4 hours.


![](/assets/img/SoilSensor3/Recurrence.png)

<br/>
<br/>

# 2. Run

Retrieves a list of unique PepperName (hostname) values from a dataset named peppers that meet certain moisture and temperature conditions. Here’s a high-level breakdown of what it does:

- It starts by looking at the **peppers** dataset.

- It then applies a filter to only include records where the **Moisture** or **Temperature** values (converted to decimal) fall outside of certain ranges. 

- These ranges are defined by the **MoistureGreaterThan, MoistureLessThan, TempGreaterThan,** and **TempLessThan** parameters.

- Finally, it selects the distinct **PepperName** from the remaining data.

![](/assets/img/SoilSensor3/Run1.png)

<br/>
<br/>

# 3. Parse

Here’s a high-level summary:

- The top-level element is an **object**.

- This **object** has a **property** named **value**.

- The **value property** is an **array** (indicated by **"type": "array"**).

- Each item in the **value array** is an **object (indicated by "type": "object" under items)**.

- These **objects** have a **property** named **PepperName**, which is a **string** (indicated by **"type": "string"**).

- The **PepperName** property is required for each object in the value array (indicated by the required array).

In simpler terms, this **schema** describes an **object** that contains an **array of objects (value)**, each with a required **string property (PepperName)**.

![](/assets/img/SoilSensor3/parse1.png)

<br/>
<br/>

# 4. Initialize

high-level summary of what this step does:

- It **initializes a variable** as part of a workflow.

- The **variable** is named **PeppersOutOfCondition** and its **type is array**. It’s intended to hold a list of peppers that meet certain conditions (too hot/cold etc.).

- This step in the workflow is set to run after the prior step has succeeded.

- The **PeppersOutOfCondition** variable is used to store the results from the previous step.

In simpler terms, this step is preparing an empty list (or array) named **PeppersOutOfCondition** to store data that will be used later in the workflow (peppers that are too hot/cold etc.)

![](/assets/img/SoilSensor3/Initialize1.png)

<br/>
<br/>

# 5. For Each Loop 1 - Extract

High-level summary of what this next step does:

- It’s a **Foreach loop**, which is used to iterate over a collection of items. In this case, it’s iterating over the value array from the results of a previous step (Peppers that match or fail to match predefined conditions).

- This Foreach loop is set to run after the previous **Initialize** step has succeeded.

In simpler terms, this step is iterating over the results of a parsed JSON, extracting the PepperName from each item, and appending these names to an array named PeppersOutOfCondition. This happens after the PeppersOutOfCondition variable has been initialized. 

![](/assets/img/SoilSensor3/ForEach2.png)
![](/assets/img/SoilSensor3/ForEach1.png)

<br/>
<br/> 

# 6. Append Results to an Array

The action here is of type **AppendToArrayVariable**, which means it appends a value to an **existing array variable** that was **initialized** in a previous step in the workflow (step 4).

- The array variable is named **PeppersOutOfCondition**.

- The value being appended to the **PeppersOutOfCondition** array is the **PepperName** from each item in the **Foreach loop** in the previous step. 

In simpler terms, this action is adding the name of each pepper that meets certain conditions (extracted in a previous step) to the **PeppersOutOfCondition** array. Thus, this array will contain a list of all peppers that are outside of the specified moisture and temperature conditions.

>_&#128073; This is how we can get more than one sensor transmitting across the same service bus and endpoint, and then "peel" them back out by hostname and throw them into an array to continue working with._

![](/assets/img/SoilSensor3/Append2.png)
![](/assets/img/SoilSensor3/Append1.png)

<br/>
<br/>

# 7. Foreach Loop 2 - Filter

This **Foreach loop** applies to or iterates over the **value array** from the results of the previous step:

![](/assets/img/SoilSensor3/Filter1.png)

<br/>
<br/>

# 8. Run Query

This **Action** starts by looking at the **peppers dataset**.
It then filters the data to only include records where the **PepperName** matches a specific value using a KQL query.

Next, it applies another filter to only include records where the **Moisture** or **Temperature** values (converted to decimal) fall outside of certain ranges. These ranges are defined by the **MoistureGreaterThan, MoistureLessThan, TempGreaterThan,** and **TempLessThan** parameters.

Finally, it selects the **top 1** record from the remaining data, ordered by **PepperName**.

>_&#128073; if you’re looking for a specific pepper that has moisture and temperature values outside of certain ranges, this is the query that will find it._

![](/assets/img/SoilSensor3/Run1.png)

<br/>
<br/>

# 9. Foreach Loop 3 - Check Conditions with KQL

This third **Foreach loop** iterates over the **value array** from the result of the previous **Run** step.

![](/assets/img/SoilSensor3/ForEach2.png)

<br/>
<br/>

# 10. Parse Pepper KQL Results

- The action is of type **ParseJson**, which means it’s parsing a **JSON string** into a **JSON object**.

- The **JSON string** to be parsed is provided by the items('For_each_-_KQL_Results_Check_Moisture_Conditions') expression from the prior **Foreach loop**.

- The **schema** defines the expected structure of the **JSON object**. Here it's configured with the following properties: **IngestionTime, Moisture, MoisturePercentageEstimate, PepperName, Temperature,** and **TimeGenerated**.

- The **types** of these **properties** are also defined (**string** for most properties and **number** for **MoisturePercentageEstimate**).

In simpler terms, this action is taking a **JSON string** from a previous step in the workflow, parsing it into a **JSON object**, and validating its structure against the defined **schema**.

![](/assets/img/SoilSensor3/parse2.png)

<br/>
<br/>

# 11. Check Moisture Condition

The **If** action checks a **condition** based on the **Moisture value** from the parsed **JSON result** of each **pepper**.

If the **Moisture** is **greater than** a threshold (**MoistureGreaterThan**), or **True** as illustrated in the **Logic App Designer** view, it triggers the next **Action** in the workflow that corresponds with the **True** condition.

If the **Moisture** is **less than** the threshold (**False**) then trigger the next **Action** in the workflow corresponding with the **False** condition.

![](/assets/img/SoilSensor3/Condition2.png)

<br/>
<br/>

# 12. Send Email Action

This **action** checks the moisture condition for each **pepper**, and sendg an email alert if the moisture is too high or too low:

- The **Send_an_email_(V2)_-_High_Moisture** action sends an email indicating **high moisture**. The email is sent to the address provided by the **email parameter**, and the email body includes the **PepperName** and **Moisture** values from the parsed JSON result.

- If the **Moisture** is **not greater** than the **MoistureGreaterThan** threshold, it checks another condition where the **Moisture** is **less than** the **MoistureLessThan** threshold.

- If this condition is met, it triggers the **Send_an_email_(V2)_-_Low_Moisture** action.

- Similar to the high moisture email, it includes the **PepperName** and **Moisture** values in the email body.

>_&#128073; Make sure to connect your **Send from** email account when configuring the **Send an email V2** action._

![](/assets/img/SoilSensor3/send_email_V2.png)

<br/>
<br/>

# 13. Re-iteratate for Temperature

Repeat steps 9 through 12, but for **Temperature** instead of **Moisture**

<br/>
<br/>


# Sensor Thresholds:

I'm growing a variety of peppers (jalapeno, sichuan, goat horn, etc.) so my thresholds are as follows for this sensor setup (you may want to adjust these based on the moisture requirements for what you're trying to grow. Tomatoes usually need more water than peppers in my experience):

<br/>

**Humidity/Moisture Alerts:**
```sql
<300 --> too dry
>800 --> too wet
```

<br/>
<br/>

**Temperature Alerts:**
<br/>

```sql
<45 Degrees F --> too low
>90 Degress F --> too high
```

<br/>
<br/>

# Conclusion:

Thanks for reading! With this configuration, you can securely leverage the free Azure IoTHub to setup automated email alerts from multiple sensors simultaneously (bypassing the single service endpoint bottleneck) so your crop never goes cold, too hot, or thirsty, without breaking the bank.

&#127793; &#127807; **What will you grow next?** &#127804;&#127803;

<br/>

<br/>

# In this Post We: 

- &#128073; Built a **Logic App** to **automate email alerting** based on **sensor readings**
- &#128073; Got **alerts for when our plants are too hot &#128293;, too cold &#10052;, or too thirsty**  &#128167;
- &#128073; Made the **most** of the **free IoT Hub** tier &#128170;

<br/>
<br/>

![www.hanleycloudsolutions.com](/assets/img/footer.png) ![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
