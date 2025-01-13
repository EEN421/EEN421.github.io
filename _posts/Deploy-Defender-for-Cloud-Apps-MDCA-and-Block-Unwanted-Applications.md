# Introduction & Use Case:
You're troubleshooting a mysterious bandwidth hog &#x1F416; in your network, only to discover that the culprit is the very same employee who asked you to look into it &#x1F601;&#x2757; It's March Madness, and that user is streaming the latest <font color="ligblue">KY Wildcat basketball game </font> on the ESPN app (<font color="ligblue">**Go Cats!** &#x1F63A;</font>)... What do you do in this situation?

To make it more fun, this organization is low budget, operating ad-hoc and so <font color="red">you cannot leverage **Intune**, **SCCM**, or **GPO**,</font> _but users are **E5** licensed._ 

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


<br/>

# Emoji List for this Article: 

&#x1F437; - Pig's Head <Br/>
&#x1F43D; - Pig's Snout <br/>
&#x1F416; - Side Pig <br/>
&#x1F417; - Wild Hog <br/>
&#x1F60E; - Shades <br/>
 
<br/>
<br/>


# In this Post We Will:
- &#x26A1; Deploy Defender for Cloud Apps.
- &#128295; Integrate with Defender for Endpoint.
- &#128268; Onboard a Device to Defender for Endpoint. 
- &#x2714; Confirm our Defender for Endpoint AV Configuration pre-requisites _without Intune, SCCM, or GPO_ (**spoiler alert:** it's powershell). 
- &#x1F6AB;	 Un-sanction an Unwanted Application.
- &#x1F6A7;	 Un-sanction an unwanted Application on your Firewall.
- &#128161; Ian's Insights.

<br/>
<br/>

# Deploy Defender for Cloud Apps

1.	Connect to the Defender for Cloud Apps Portal:

    - Ensure you have the necessary administrative permissions to configure and manage MDCA.

    - Access the MDCA portal through by navigating to the unified security portal at [www.security.microsoft.com](www.security.microsoft.com).

    - Navigate to settings blade towards the bottom of the left menu  and select Endpoint.

    ![]()

    - This integration allows for enhanced threat detection and response capabilities by correlating signals from endpoints and cloud apps.

    - If the Defender for Endpoint agent is deployed on devices within your organization, then MDCA can leverage the MDE agent to monitor network activities and traffic, including those related to cloud apps.

    - The Defender for Endpoint agent collects detailed information about cloud app usage directly from the endpoints. This includes data on which apps are being accessed, by whom, and from which devices.


<br/>
<br/>
<br/>
<br/>
<br/>

# Ian's Insights:

It’s refreshing to take a break from the norm and dive into something fun, like creating cool projects for Halloween. I'm already thinking about plans for next year, like adding a voice modulator to the mask, or a motion sensor to the Raspberry Pi maybe... Making time for side projects like this helps keep me sharp when it’s time to get back to work. Just remember to gather your supplies early and make time to screw around.

<br/>
<br/>
<br/>
<br/>

# In this Post We:

**Part 1:**
- &#128190; Performed a Headless Raspberry Pi Setup (BullseyeOS).
- &#128268; Connected Hardware & Deployed Software Eyes.
- &#128064; Customized Eye Shapes, Colours, Iris, Sclera, etc. 
- &#127875; Lit up a Pumpkin! 

**Part 2:**
- &#128297; Customized our Monster M4SK.  
- &#128295; Extended the Distance Between Displays.
- &#128123; Spooked the Neighbour's Kids! 

<br/>
<br/>
<br/>
<br/>

# Thanks for Reading!
 I hope this was a much fun reading as it was writing. Happy Halloween!  

<br/>

![](/assets/img/Halloween24/Banner2.jpg)

<br/>
<br/>

# Helpful Links & Resources: 

- [Animated Eyes Bonnet for Raspberry Pi](https://www.adafruit.com/product/3356)
- [PiSugar S Plus Portable 5000 mAh UPS Lithium Battery Power Module](https://a.co/d/72oBlGg)
- [Raspberry Pi 4 Model B ](https://www.adafruit.com/product/4292)
- [Animated Snake Eyes Bonnet for Raspberry Pi](https://learn.adafruit.com/animated-snake-eyes-bonnet-for-raspberry-pi/software-installation)
- [Lithium Ion Cylindrical Battery - 3.7v 2200mAh](https://www.adafruit.com/product/1781)
- [JST SH 9-Pin Cable - 100mm long x 2](https://www.adafruit.com/product/4350)
- [Adafruit MONSTER M4SK - DIY Electronic Eyes Mask](https://www.adafruit.com/product/4343)
- [Separate the MONSTER M4SK](https://learn.adafruit.com/wide-set-monster-m4sk-creature-eyes/separate-the-monster-m4sk)
- [Spruce Up a Costume with MONSTER M4SK Eyes and Voice](https://learn.adafruit.com/spruce-up-a-costume-with-monster-m4sk-eyes-and-voice)


<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
