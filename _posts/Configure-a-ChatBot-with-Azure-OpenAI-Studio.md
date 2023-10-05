# Introduction and Use Case:
Have you ever wondered how to take your LLM (Language Model) to the next level? Look no further, because we have got you covered. In this blog post, we will **guide you through the process of configuring an LLM with Azure OpenAI Studio,** taking your natural language processing capabilities to new heights. With the power of Azure OpenAI Studio, you can easily build and deploy an LLM that can understand the nuances of language like never before. So, fasten your seatbelts, and get ready to explore!

Spinning up your own Chat Bot/LLM is _**way easier**_ than you might think. Would you believe that the preceding paragraph above was written by one? The possibilities are nigh endless; I've even used mine to help come up with some complicated KQL queries. Check out my below guide to getting your own up and running _quick!_

<br/>

# In this post we will:
- Configure an LLM with Azure OpenAI Studio
- Take your natural language processing capabilities to new heights
- Easily build and deploy an LLM that can understand the nuances of language like never before
- Leverage your LLM to write better KQL queries!


# Step-by-Step:
Log into your [Azure Portal](https://www.portal.azure.com) and search for **Azure Open AI** as illustrated below:

![](/assets/img/OpenAI/Setup/1_search.png)

<br/>

Select **+Create**

![](/assets/img/OpenAI/Setup/2.png)

<br/>

# Basics
This next window has several fields we need to populate, shown below: 

1. Select which **Subscription** you'd like to build this under
2. Select an appropriate **Resource Group** 
3. Select your **Region** (I like to keep this the same as your Sub for simplicity)
4. **Name** your Azure OpenAI GPT-3 model
5. Select your **Pricing Tier** 

![](/assets/img/OpenAI/Setup/3.png)

<br/>

# Networking
This next part is very important from a **security perspective:**
- Select _All networks, **including the internet,** can access this resource_ **at your own risk.**
- It's _more secure_ to lock this resource down and create an exception on the firewall for your public IP address. 
- Create or Select a **virtual network** and **subnet**
- Define your public IP address 

Note: Unless you have a persistent public IP address through your ISP, your public IP will change from time to time. When this happens, you will not be able to access your chatbot in Azure OpenAI Studio. You can go to [IP Chicken](www.ipchicken.com) to quickly find your public IP address



![](/assets/img/OpenAI/Setup/4.png)

<br/>

![](/assets/img/OpenAI/Setup/5.png)

<br/>

![](/assets/img/OpenAI/Setup/6.png)

<br/>

![](/assets/img/OpenAI/Setup/7.png)

<br/>

![](/assets/img/OpenAI/Setup/8.png)

<br/>

![](/assets/img/OpenAI/Setup/10.png)

<br/>

![](/assets/img/OpenAI/Setup/11.png)

<br/>

![](/assets/img/OpenAI/Setup/12.png)

<br/>

![](/assets/img/OpenAI/Setup/13.png)

<br/>

![](/assets/img/OpenAI/Setup/14.png)

<br/>

![](/assets/img/OpenAI/Setup/15.png)

<br/>

![](/assets/img/OpenAI/Setup/16.png)

<br/>

![](/assets/img/OpenAI/Setup/17_models.png)

<br/>

![](/assets/img/OpenAI/Setup/19.png)

<br/>

![](/assets/img/OpenAI/Setup/20.png)

<br/>

![](/assets/img/OpenAI/Setup/21.png)

<br/>

![](/assets/img/OpenAI/Setup/23_config.png)

<br/>

![](/assets/img/OpenAI/Setup/24_parameters.png)

<br/>

![](/assets/img/OpenAI/Setup/25.png)

<br/>

![](/assets/img/OpenAI/Setup/26_api.png)

<br/>

![](/assets/img/OpenAI/Setup/27_introduction%20paragraph.png)

<br/>

![](/assets/img/OpenAI/Setup/22.png)

<br/>



