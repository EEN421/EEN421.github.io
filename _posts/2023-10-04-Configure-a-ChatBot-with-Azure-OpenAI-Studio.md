# Introduction and Use Case:
Have you ever wondered how to take your LLM (Language Model) to the next level? Look no further, because we have got you covered. In this blog post, we will **guide you through the process of configuring an LLM with Azure OpenAI Studio,** taking your natural language processing capabilities to new heights. With the power of Azure OpenAI Studio, you can easily build and deploy an LLM that can understand the nuances of language like never before. So, fasten your seatbelts, and get ready to explore! 

 &#128161; Spinning up your own Chat Bot/LLM is _**way easier**_ than you might think. Would you believe that the preceding paragraph above was written by one?


![](/assets/img/OpenAI/Setup/27_introduction%20paragraph.png)

<br/>

&#x26A1; The possibilities are nearly endless; I've even used mine to help come up with some complicated KQL queries. Check out my below guide to getting your own up and running _quick!_ &#128071;

<br/>


# In this post we will:
- &#128073;Address **Pre-Requisites**
- &#128073;Deploy an LLM Model using **Azure OpenAI Studio**
- &#128073;Handle the **Basics**
- &#128073;Cover **Networking** 
- &#128073;Touch on **Tags**
- &#128073;Fine Tune our Deployment's **Parameters** and **Deployment** Configuration
- &#128073;Generate Sample Code for **App Integration**
- &#128073;Have some **Fun** with our Deployment &#128526;	
- &#128073;Discuss **Common Issues/Troubleshooting**

<br/>

# Pre-Requisites
Join the 1.3 million developers who have been using Cognitive Services to build AI powered apps to date. With the broadest offering of AI services in the market, Azure Cognitive Services can unlock AI for more scenarios than other cloud providers. Give your apps, websites, and bots the ability to see, understand, and interpret people’s needs — all it takes is an API call — by using natural methods of communication. Businesses in various industries have transformed how they operate using the very same Cognitive Services now available to you with an Azure free account.

Get started with an [Azure free account](https://azure.microsoft.com/en-us/free/cognitive-services/) today, and [learn more about Cognitive Services](https://azure.microsoft.com/en-us/services/cognitive-services/). 

- [Official MS Blog - Start Building with Azure Cognitive Services for Free](https://azure.microsoft.com/en-us/blog/start-building-with-azure-cognitive-services-for-free/) 

<br/>

# Step-by-Step:
- Log into your [Azure Portal](https://www.portal.azure.com) and search for **Azure Open AI** as illustrated below:

![](/assets/img/OpenAI/Setup/1_search.png)

<br/>

- Select **+Create**

![](/assets/img/OpenAI/Setup/2.png)

<br/>

# 1. Basics
This next window has several fields we need to populate, shown below: 

1. Select which **Subscription** you'd like to build this under
2. Select an appropriate **Resource Group** 
3. Select your **Region** (I like to keep this the same as your Sub for simplicity)
4. **Name** your Azure OpenAI GPT-3 model
5. Select your **Pricing Tier** 

![](/assets/img/OpenAI/Setup/3.png)

<br/>

# 2. Networking
&#10071; &#10071; &#10071; This next part is very important from a **security perspective:** &#128272;

- Select _All networks, **including the internet,** can access this resource_ **at your own risk.** 
- It's _more secure_ to lock this resource down and create an exception on the firewall for your public IP address. 
- Create or Select a **virtual network** and **subnet**
- Define your public IP address 

![](/assets/img/OpenAI/Setup/4.png)

<br/>

 > &#128161; _Pro-Tip: Unless you have a persistent public IP address through your ISP, your public IP will change from time to time. When this happens, you will not be able to access your chatbot in Azure OpenAI Studio. You can go to [IP Chicken](www.ipchicken.com) &#128020; to quickly find your public IP address. Refer to the **Troubleshooting** section below if this happens to you._

 <br/>

# 3. Tags (Optional)
This is pretty self-explanatory, use something that makes sense to you. Tags follow a typical **json** format (**Name:Value**) and can be leveraged to consolidate billing to _categorized/tagged_ resources. This is _awesome_ for _Cost Optimization_ exercises &#128176; &#128176;

![](/assets/img/OpenAI/Setup/5.png)

<br/>

# 4. Review + Submit
Review the **Basics, Network,** and **Tags** for typos etc. and make sure to read the fine print, because clicking **Create** means you _agree to all the legal terms and privacy statement(s)._&#128270;

![](/assets/img/OpenAI/Setup/6.png)

<br/>

- Click on **Create** when you're ready.

![](/assets/img/OpenAI/Setup/7.png)

<br/>

&#9201; Wait 5 minutes for your deployment to complete:

![](/assets/img/OpenAI/Setup/10.png)

# Deployment Complete... What Now? 
Lets take it for a test drive! Click on **Explore** to load the **Azure OpenAI Studio.**
<br/>

![](/assets/img/OpenAI/Setup/13.png)

<br/>

There are several kinds of OpenAI Chat Bots you can deploy:

- **Chat Playground** is great for generating content (ask it to write something for you)
- **DALL-E** is still in _Preview_ but is great for generating images
- **Completions Playground** is great for analyizing and summarizing content you feed it (ie. 'completing' it)

Lets start with **Chat Playground:**

![](/assets/img/OpenAI/Setup/14.png)

<br/>

Select **Create New Deployment**

![](/assets/img/OpenAI/Setup/15.png)

<br/>

Select a model to use from the dropdown list and give your deployment a unique name:
![](/assets/img/OpenAI/Setup/16.png)

<br/>
Here are the _model_ options from the dropdown in the above screenshot: 

![](/assets/img/OpenAI/Setup/17_models.png)

<br/>
If you select and expand the **Advanced options** drop down menu, only the **Default** Content Filter is available at the time of this article, illustrated below:

![](/assets/img/OpenAI/Setup/19.png)

<br/>

Once you select a **Model,** it will ask you for which **model version** you want to use. I went with the **default (0301)**. Next, select **Create** 

![](/assets/img/OpenAI/Setup/20.png)

<br/>

&#9201; Wait for your deployment to complete:

![](/assets/img/OpenAI/Setup/21.png)

<br/>

# Now for the FUN part... 

Tailor your deployment to your liking. For example, how many prior messages in the conversation should it remember when generating it's next response? It's 10 by default in the **Deployment Configuration** tab. 

![](/assets/img/OpenAI/Setup/23_config.png)

<br/>

Moving over to the **Parameters Configuration** tab, you can _flavour_ your ChatBot's response:

- **Max Response:** Set a limit on the number of tokens per model response. The API supports a maximum of 4000 tokens shared between the prompt (including system message, examples, message history, and user query) and the model's response. One token is roughly 4 characters for typical English text. 

- **Temperature:** Controls randomness. Lowering the temperature means that the model will produce more repetitive and deterministic responses. Increasing the temperature will result in more unexpected or creative responses. Try adjusting temperature or Top P but not both.

- **Top P:** Similar to temperature, this controls randomness but uses a different method. Lowering Top P will narrow the model’s token selection to likelier tokens. Increasing Top P will let the model choose from tokens with both high and low likelihood. Try adjusting temperature or Top P but not both.

- **Stop Sequence:** Make the model end its response at a desired point. The model response will end before the specified sequence, so it won't contain the stop sequence text. For ChatGPT, using <\|im_end\|> ensures that the model response doesn't generate a follow-up user query. You can include as many as four stop sequences.

- **Frequency Penalty:** Reduce the chance of repeating a token proportionally based on how often it has appeared in the text so far. This decreases the likelihood of repeating the exact same text in a response.

- **Presence Penalty:** Reduce the chance of repeating any token that has appeared in the text at all so far. This increases the likelihood of introducing new topics in a response.

![](/assets/img/OpenAI/Setup/24_parameters.png)

<br/>

Here's a fun one, you can choose between different pre-defined purposes. Writing a screenplay? Try the Shakespeare writing assistant! Working on your taxes? Try the IRS tax chatbot (but definitely don't rely solely on this when filing your taxes, you've been warned! &#129297; )

![](/assets/img/OpenAI/Setup/25.png)

<br/>

The _next step is making the deployment available._ Click on the **View Code** button to view sample python integration code you can use to start integrating your current prompt and settings into your application:

![](/assets/img/OpenAI/Setup/ViewCode.png)
![](/assets/img/OpenAI/Setup/26_api.png)

<br/>

# Have FUN with it! 
Ask general trivia:
![](/assets/img/OpenAI/Setup/22.png)

Use it to help build useful KQL queries:
![](/assets/img/OpenAI/Setup/KQL1.png)

If you've set it to remember your last inquiry, you can build on top of it like this: 

![](/assets/img/OpenAI/Setup/KQL2.png)

 > &#128161; _Pro-Tip: The effective cost per GB rate isn't $0.01 / GB for any commitment tier in the Central US region. This is an easy fix though, just look up your effective cost per GB based on your region and commitment tier [here](https://azure.microsoft.com/en-us/pricing/details/microsoft-sentinel/?ef_id=_k_87d6d4833d811f6a1c33b19d833b6887_k_&OCID=AIDcmm5edswduu_SEM__k_87d6d4833d811f6a1c33b19d833b6887_k_&msclkid=87d6d4833d811f6a1c33b19d833b6887) and plug it in. It should be noted that I didn't give it enough information to infer which commitment tier, so it gave me an example._ 

 <br/>

Maybe you completely forgot to read that book for book club, and don't have time to catch the movie adaptation, try asking your new assistant for key points:

![](/assets/img/OpenAI/Setup/KQL3.png)

Maybe you're new to the SOC and need to come up with a plan to protect your organization against that pesky _log4j_ some of us lost sleep over a while back... 

![](/assets/img/OpenAI/Setup/KQL4.png)

Maybe you caught an engineer wasting time on a logic app for a specific client request that could be solved more efficiently another way using existing tools... 

![](/assets/img/OpenAI/Setup/KQL5.png)

 &#128161; _Pro-Tip: Take whatever answers it gives you with some restraint. It's an LLM chat bot after all... it's not a person capable of simple fact/logic checking. It can just as easily provide a counter argument to an argument it just gave you, totally contradicting itself. It's given me some goofy answers to some pretty straight forward prompts sometimes too, so you can't rely on it **but you can use it to get a step ahead** of the game if used with caution._

<br/>

# Troubleshooting

&#128736; If you can get into Azure OpenAI Studio and open the chat interface, but your inquiries are refused, check your Public IP and update the settings in the Networking blade under your new OpenAI resource in the Azure portal 

![](/assets/img/OpenAI/Setup/11.png)
![](/assets/img/OpenAI/Setup/PublicIP.png)

&#128736; If you are unable to make any changes to your networking settings and receive the following type of error: 

```sql
Cannot modify resource with id '/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/OpenAI/providers/Microsoft.CognitiveServices/accounts/testai001' because the resource entity provisioning state is not terminal. Please wait for the provisioning state to become terminal and then retry the request.
```

...then your most effective, time-saving approach is to just nuke your deployment and start over (it really doesn't take that long). There are alternative methods available to reset the provisioning state listed here: [https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state](https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state) 

# In this post we:
- &#128073;Addressed **Pre-Requisites**
- &#128073;Deployed an LLM Model using **Azure OpenAI Studio**
- &#128073;Handled the **Basics**
- &#128073;Covered **Networking** 
- &#128073;Touched on **Tags**
- &#128073;Fine Tuned our Deployment's **Parameters** and **Deployment** Configuration
- &#128073;Generated Sample Code for **App Integration**
- &#128073;Had some **Fun** with our Deployment &#128526;	
- &#128073;Discussed **Common Issues/Troubleshooting**
<br/>
<br/>

# Thanks for Reading! 
If you found this guide to configuring a ChatBot with Azure OpenAI Studio valuable, there’s a lot more where that came from. My new book dives deeper — including full architectures, scripts, and hands-on scenarios.
A heartfelt thanks to everyone who’s already picked up a copy — if you’ve read it, a quick Amazon rating or review would be amazing 👉 [📘 Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/69vN3Om)

![Ultimate Microsoft XDR for Full Spectrum Cyber Defense](/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg)
<br/>
<br/>

# Resources: 
- [https://azure.microsoft.com/en-us/blog/start-building-with-azure-cognitive-services-for-free/](https://azure.microsoft.com/en-us/blog/start-building-with-azure-cognitive-services-for-free/) 

- [https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state](https://learn.microsoft.com/en-us/azure/networking/troubleshoot-failed-state) 

- [IP Chicken](www.ipchicken.com) &#128020;

- [learn more about Cognitive Services](https://azure.microsoft.com/en-us/services/cognitive-services/)

- [Azure free account](https://azure.microsoft.com/en-us/free/cognitive-services/)

<br/>

![](/assets/img/IoT%20Hub%202/footer.png)
