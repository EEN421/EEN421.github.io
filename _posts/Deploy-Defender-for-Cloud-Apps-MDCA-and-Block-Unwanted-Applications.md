# Introduction & Use Case:
You're troubleshooting a mysterious bandwidth hog &#x1F416; in your network, only to discover that the culprit is the very same employee who asked you to look into it &#x1F601;&#x2757; It's March Madness, and that user is streaming the latest <font color="ligblue">KY Wildcat basketball game </font> on the ESPN app (<font color="ligblue">**Go Cats!** &#x1F63A;</font>) and you need to preserve bandwidth and compliance at the same time... What do you do in this situation?

To make it more fun, this organization is low budget and operating ad-hoc, so <font color="red">you cannot leverage **Intune**, **SCCM**, or **GPO**,</font> _but users are **E5** licensed._ 

In my experience, my favorite is the 'scream test' and it goes one of two ways if implemented correctly:<br/>

-    If they know they're not supposed to have access, they're not going to complain when it gets cut off &#x1F609;	. <br/>

-    You'll see who screams and quickly learn how important the application you just disabled is to productivity &#x1F4B2; &#x1F4B2; &#x1F4B2;.
>&#128161; Pro-Tip:Make sure to document that somewhere safe and accessible for the new kids on the block . <br/>

This blog post will guide you through deploying Defender for Cloud Apps from the ground up and integrating it seamlessly with Microsoft Defender for Endpoint to effectively block or unsanction unwanted applications that don't meet your requirements (SOC2, GDPR, PIPEDA, CMMC, NIST, just to name a few). This ensures your cloud infrastructure remains secure, compliant, effective, and cost-efficient (even if you're just trying to conserve bandwidth during the sweet 16 &#x1F3C0;).

Whether you're an IT/SecOps professional or a Security & Compliance enthusiast, this comprehensive guide will provide you with the Defender for Cloud Apps knowledge and insights you need to identify and keep those bandwidth hogs at bay&#x1F43D;, lock down your environment&#x1F512;, and knock those compliance scores out of the park &#x2705;

<br/>

![](/assets/img/Defender%20for%20Cloud%20Apps/Microsoft-Defender-for-Cloud-Apps.jpg)


<br/>
<br/>


# In this Post We Will:
- &#x26A1; Deploy Defender for Cloud Apps.
- &#128295; Integrate with Defender for Endpoint.
- &#128268; Onboard a Device to Defender for Endpoint. 
- &#x2714; Confirm our Defender for Endpoint AV Configuration pre-requisites _without Intune, SCCM, or GPO_ (**spoiler alert:** it's powershell). 
- &#x1F6AB;	 Un-sanction an Unwanted Application.
- &#x1F6A7;	 Un-sanction an unwanted Application on your Firewall (for devices that don't support the MDE agent).
- &#128161; Ian's Insights.

<br/>
<br/>

# Deploy Defender for Cloud Apps

 - Ensure you have the necessary administrative permissions to configure and manage MDCA.

 - Access the unified security portal at [www.security.microsoft.com](www.security.microsoft.com).

 - Navigate to **settings** blade towards the bottom of the left menu and select **Cloud Apps**.

    ![](/assets/img/Defender%20for%20Cloud%20Apps/MDE%20Integration%2000.png)

 - Scroll down to **Microsoft Defender for Endpoint** and check the **Microsoft Defender for Endpoint Integration** box.

    ![](/assets/img/Defender%20for%20Cloud%20Apps/MDE%20Integration%2001.png)

 - This integration allows for enhanced threat detection and response capabilities by correlating signals from endpoints and cloud apps.

 - If the Defender for Endpoint agent is deployed on devices within your organization, then MDCA can leverage the MDE agent to monitor network activities and traffic, including those related to cloud apps.

 - The Defender for Endpoint agent collects detailed information about cloud app usage directly from the endpoints. This includes data on which apps are being accessed, by whom, and from which devices and IP addresses etc.

<br/>
<br/>

# Integrate with Defender for Endpoint 

 - Access the unified security portal at [www.security.microsoft.com](www.security.microsoft.com).

<br/>

- Navigate to **settings** blade towards the bottom of the left menu  and select **Endpoints**.

![](/assets/img/Defender%20for%20Cloud%20Apps/MDCA%20Integration%2000.png)

<br/>

Click on **Advanced Features** under **General** and toggle the **Microsoft Defender for Cloud Apps** Toggle switch to **On** as illustrated below: 

![](/assets/img/Defender%20for%20Cloud%20Apps/MDCA%20Integration%2001.png)

<br/>

- Enabling this feature sends telemetry collected by Defender for Endpoint over to Defender for Cloud Apps. You can confirm by going back to **the unified security portal >> Settings >> Cloud Apps >> Automatic Log Upload** and verifying the following entry populates (it can take up to 30 minutes): 

![](/assets/img/Defender%20for%20Cloud%20Apps/Automatic%20Log%20Upload.png)

<br/>

>&#128161; While you're in here, you'll need to toggle **Custom Network Indicators** to the **On** position: 

![](/assets/img/Defender%20for%20Cloud%20Apps/custom_network_indicators.png)

<br/>
<br/>

# Onboard a Device to Defender for Endpoint

So perhaps you don't have all of your devices onboarded to Defender for Endpoint, but you have a fair idea of who might be consuming all the bandwidth and want to start there. Follow the steps below to onboard their devices to Defender for Endpoint and get Cloud App Telemetry: 

- Logon to your device

- Navigate to the unified security portal at www.security.microsoft.com from your device

- Select the **Settings** blade from the left menu, then choose **Endpoints**

![](/assets/img/Defender%20for%20Cloud%20Apps/MDCA%20Integration%2000.png)

- Scroll down to **Onboarding** and fill out the appropriate settings, then download the onboarding package

![](/assets/img/Defender%20for%20Cloud%20Apps/onboard.png)

- Run it with administrative privilges on the device you wish to onboard.

![](/assets/img/Defender%20for%20Cloud%20Apps/MDE_onboarding_script_DL.png)

![](/assets/img/Defender%20for%20Cloud%20Apps/MDE%20Onboarding%20Completed.png)

- Give it a few minutes and the device will show up in the unified security portal, illustrated below: 

![](/assets/img/Defender%20for%20Cloud%20Apps/onboarded.png)

<br/>
<br/>

# Confirm Defender for Endpoint AV Configuration Pre-Requisites via Powershell

- Logon to your device

- Launch Powershell as an administrator

- Run the following command:

```powershell
Get-MpComputerStatus
```

- Confirm the following pre-requisites are met: 

![](/assets/img/Defender%20for%20Cloud%20Apps/Powershell_Config.png)

If either of these are **False** then use the following command to set them:

```powershell
Set-MpComputerStatus
```

Here's a [list of available commands for reference]( https://learn.microsoft.com/en-us/powershell/module/defender/?view=windowsserver2025-ps#defender)

>&#128161; Alternatively, you'd have to use Intune, Group Policy, SCCM, or a combination thereof to onboard and configure your fleet. 

<br/>
<br/>

# Un-sanction an Unwanted Application

Now that we've got our devices onboarded and our MDE and MDCA platforms integrated, we can enforce MDCA polcies like blocking un-sanctioned applications using the MDE agent directly. 

- From the unified security portal, navigate to the **Cloud Discovery** Blade, located under **Cloud Apps**

- Swing over from the **Dashboard** tab to the next one to the right, called **Discovered Apps** to list all of the applications reported from Defender for Endpoint that have run on that device since the **Automatic Log upload** has been deployed from MDE to MDCA earlier. 

- You can Un-sanction any application found in your environment from here. 

>&#128161; Why wait until an application is already active in your environment to block it? The **Cloud App Catalogue** blade (directly underneath the **Cloud Discovery** blade) lists all of the applications that Microsoft has evaluated, and there's thousands of them! 

- In this example, we'll block applications we know we don't want to see in our network. From the **Cloud App Catalogue** search for your unwanted applications and select the **Unsanction** button to the right for each application you want to block:

![](/assets/img/Defender%20for%20Cloud%20Apps/UnSanctioned.png)

<br/>

Give it a few minutes and try to navigate to one of those applications in a browser or through their designated local applications on a device that you've onboarded to MDE to see them fail (gloriously): 

![](/assets/img/Defender%20for%20Cloud%20Apps/Steam_Games_block.png)

<br/>

![](/assets/img/Defender%20for%20Cloud%20Apps/Netflix_Block.png)

<br/>
<br/>

# Un-sanction an unwanted Application on your Firewall (for devices that don't support the MDE agent).
So what about those weird Linux distros that don't support MDE (yet)... they need protection too right? If they're behind a firewall appliance, check out this awesome MDCA feature out that becomes available once you've un-sanctioned a few unwanted applications...

- From the **Cloud Discovery Dashboard** go to the **Actions** drop down, located in the top-right hand cornder of the screen, and click on **Generate Block Script...**:

![](/assets/img/Defender%20for%20Cloud%20Apps/Block_script_00.png)

- Select your Firewall vendor:

![](/assets/img/Defender%20for%20Cloud%20Apps/Block_script_01.png)

- Copy and paste the output from a privileged exec state in your fireall to block the unwanted applications at the DNS level

- Here's an example output for a Palo Alto firewall that blocks Netflix, Steam Games, Epic Games, etc: 

```bash
set application $serviceName1 category $pancategory subcategory $pansubcategory technology browser-based risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern epicgames.com
Set rulebase security rule rule$serviceName1 application $serviceName1 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern epicgames.com
Set rulebase security rule rule$serviceName1 application $serviceName1 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern api.epicgames.dev
Set rulebase security rule rule$serviceName1 application $serviceName1 from any to any action deny

set application $serviceName2 category $pancategory subcategory $pansubcategory technology browser-based risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflix.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflix.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern nflxvideo.net
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern nflxext.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern nflximg.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest2.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest3.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest4.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest5.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest6.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest7.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest8.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest9.com
Set rulebase security rule rule$serviceName1 application $serviceName2 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern netflixdnstest10.com
Set rulebase security rule rule$serviceName2 application $serviceName2 from any to any action deny

set application $serviceName3 category $pancategory subcategory $pansubcategory technology browser-based risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern store.steampowered.com
Set rulebase security rule rule$serviceName1 application $serviceName3 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern store.steampowered.com
Set rulebase security rule rule$serviceName1 application $serviceName3 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern api.steampowered.com
Set rulebase security rule rule$serviceName1 application $serviceName3 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern test.steampowered.com
Set rulebase security rule rule$serviceName1 application $serviceName3 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern crash.steampowered.com
Set rulebase security rule rule$serviceName3 application $serviceName3 from any to any action deny

set application $serviceName4 category $pancategory subcategory $pansubcategory technology browser-based risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern steamcommunity.com
Set rulebase security rule rule$serviceName1 application $serviceName4 from any to any action deny set application $serviceName category $pancategory subcategory $pansubcategory technology browser-baes risk $panrisk signature s1 and-condition a1 or-condition o1 operator pattern-match context http-req-host-header pattern steamcommunity.com
Set rulebase security rule rule$serviceName4 application $serviceName4 from any to any action deny
```



<br/>
<br/>


# Ian's Insights:

Ever use a DNS Sink Hole like a Pi-Hole (raspberry Pi powered)? This functioned pretty much the same way by refusing to resolve addresses known to host the application we are blocking. A Pi-Hole will actually resolve the addresses but send the results to an IP that doesn't exist (hence "sinkhole"). Web pages load faster when they don't have to resolve all the "junk" ads etc. 

Lastly, consider going to the **unified security portal >> settings >> cloud apps >> Exclude Entities** and adding an exclusion so you can watch the finals &#x1F61C;

<br/>
<br/>
<br/>
<br/>

# In this Post We:
- ⚡ Deployed Defender for Cloud Apps.
- 🔧 Integrated with Defender for Endpoint.
- 🔌 Onboarded a Device to Defender for Endpoint.
- ✔ Confirmed our Defender for Endpoint AV Configuration.pre-requisites without Intune, SCCM, or GPO (spoiler alert: it was powershell).
- 🚫 Un-sanctioned an Unwanted Application.
- 🚧 Un-sanctioned an unwanted Application on your Firewall (for devices that don't support the MDE agent).

<br/>
<br/>

# Thanks for Reading!
 I hope this was a much fun reading as it was writing. What will you block from your environment first? 

<br/>

![](/assets/img/Defender%20for%20Cloud%20Apps/MDCA_Logo_Square.jpg)

<br/>
<br/>

# Helpful Links & Resources: 




<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
