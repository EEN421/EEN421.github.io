# Introduction & Use Case:
During a regular security audit, you've discovered several jump boxes with network access to sensitive corporate resources (such as mission-critical production SQL databases) are exposed via RDP port 3389 to the internet and you need to lock them down. 

The Change Management Board has given some push back; they have approved, given the following requirements are satisfied as a part of the solution: 

- &#128268; Users are required to put in an access request that must be approved by a manager before they can connect to the jump box. 

- &#128221; Requests must be logged with justification. 

- &#9201; Network Access must only be provisioned while necessary.

You're no stranger to danger and know that the best way to do this is a combination of Privileged Identity Management (PIM) and Just-in-Time-Administration (JITA) because:
- &#128073; JIT is about controlling when and how a VM can be accessed

- &#128073; PIM is about managing who has access to resources and when they have that access. Both are important for maintaining a secure environment in Azure.

<br/>
<br/>

![](/assets/img/JITA_PIM/Default_Two_mysterious_ninjas_cloaked_in_dark_indigo_robes_eme_3.jpg)

<br/>
<br/>

# In this Post We Will: 

- &#x1F4BB; Define a "Jump Box" and when to use one. 
- &#128272; Define & Deploy Privileged Identity Management (PIM).
- &#x26A1; Define & Deploy Just-in-Time-Administration (JITA).
- &#128526; Define a Custom Role to Adhere to Principle of Least Privelege.
- &#128170; Secure Corporate Resources and Lock Down our Jump Box.
- &#x1f977; Defend your Cyber Dojo like a Ninja! 

![](/assets/img/JITA_PIM/PIM%20Castle.jpg)

<br/>
<br/>

# What's a Jump Box Again? 
A jump box is a network device that enables secure access to servers or other devices, acting as a gateway. It’s particularly useful when accessing sensitive resources like a mission-critical SQL database remotely without exposing it directly to the internet (you gotta hit the 'jump box' before you can access the resource). 

However, if not properly secured, it can pose a super-massive risk to your network’s security so it’s crucial that it’s well-protected.


<br/>

![](/assets/img/JITA_PIM/76a0a290-d56d-4c6e-bba6-c3922178fa6c.jpg)

<br/>
<br/>

# Define Privileged Identity Management (PIM)
Privileged Identity Management (PIM) is a service in Microsoft Entra ID that enables you to manage, control, and monitor access to important resources in your organization. You can find a [full list of PIM features here](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure) but for the purposes of this article, we're going to focus on the features that satisfy our use-case:

- Approval-Based Role Activation: Before activating privileged roles, users must seek approval. This ensures proper oversight and prevents misuse.

- Access Reviews: Regularly review user roles to ensure they still need access. This helps maintain security hygiene.

- Audit History: Download audit logs for internal or external audits.

![](/assets/img/JITA_PIM/PIM_Ninja.jpg)


<br/>
<br/>

# Define Just-in-Time-Administration (JITA)
Just-in-Time Administration (JIT) is a privileged access management practice that helps organizations control the duration of specific privileges granted to employees and close partners. It works alongside a precise definition of permissions known as Just Enough Admin (JEA). In short, a VM with JIT administration configured will have a Deny-All rule applied to it's network security group until a request is approved to add an Allow rule from the user's public IP address in real time. When the JIT access expires, the Allow rule does too and remote access is cut off. 

In the context of EntraID, JIT administration minimizes the attack vector associated with administrator accounts. By granting temporary access only when needed, it reduces the risk of unauthorized access and enhances control over privileged accounts. Additionally, JIT adds monitoring, visibility, and fine-grained controls, allowing organizations to track privileged administrators’ activities and usage patterns, which satisfies our use case. 

![](/assets/img/JITA_PIM/JITA_Ninja.jpg)


<br/>
<br/>

# Define a Custom Role to Adhere to Principle of Least Privelege
To satisfy the Change Management Board's requirements, we need access requests to be audited, accompanied by a justification, and then approved. When a user activates a role through PIM, they can be forced to provide a justification and the request will be logged with a time-stamp. PIM can also be configured to have a designated administrator approve the request before it is assigned.

This makes PIM a solid part of our overall solution. However, We will need to define a custom role that allows members to request access to the jumpbox VM as the pre-defined existing roles will allow members to do more than just request access. 

Here are the requirements for the custom role used to allow members to request access to a VM:

- Microsoft.Security/locations/jitNetworkAccessPolicies/initiate/action
- Microsoft.Security/locations/jitNetworkAccessPolicies/*/read
- Microsoft.Compute/virtualMachines/read
- Microsoft.Network/networkInterfaces/*/read
- Microsoft.Network/publicIPAddresses/read

![](/assets/img/JITA_PIM/JumpBox%20Custom%20Role.png)

<br/>
<br/>

# Step-by-Step Guide
1.) Navigate to the Azure portal and select Subscriptions:

![](/assets/img/JITA_PIM/CustomRole2.jpg)

<br/>
<br/>

2.) Select your subscription:

![](/assets/img/JITA_PIM/CustomRole3.jpg)

<br/>
<br/>

3.) Click on the IAM blade and select "Add Custom Role:"

![](/assets/img/JITA_PIM/customRole1.jpg)


<br/>
<br/>

4.) Add the required permissions and assign members:

![](/assets/img/JITA_PIM/JumpBox%20Custom%20Role.png)

<br/>
<br/>

5.) Now, when your users Navigate to the designated VM, they can select the "connect" blade and if they have the custom role applied, they will then be given the option to "request access," illustrated below:

![](/assets/img/JITA_PIM/CustomRole4.jpg)


<br/>
<br/>

# End Process & Results
In order to access a protected corporate resource, users now need to: 

PIM: 
- Request Activation of the Custom PIM Role.
- Provide Justification for Auditing.

JITA: 
- Request timed access to VM from their IP and only that IP.

![](/assets/img/JITA_PIM/approved.jpg)


<br/>
<br/>

# Thanks for Reading! 

If you've made it this far, thanks for reading! I hope this has been a helpful guide for locking down your jumpboxes and thus your critical corporate resources! 

f you found the PIM & JITA setup helpful, there’s a ton more where this came from. My new book dives deeper with full designs, configurations, and real-world use cases.
Huge thanks to everyone who’s already grabbed a copy — if you’ve read it, a quick review or rating on Amazon would mean a lot.
📘 https://a.co/d/69vN3Om




<br/>
<br/>

# In this Post We: 

- &#x1F4BB; Defined a "Jump Box" and when to use one. 
- &#128272; Defined & Deployed Privileged Identity Management (PIM).
- &#x26A1; Defined & Deployed Just-in-Time-Administration (JITA).
- &#128526; Defined a Custom Role to Adhere to Principle of Least Privelege.
- &#128170; Secured Corporate Resources and Lock Down our Jump Box.
- &#x1f977; Defended your Cyber Dojo like a Ninja! 

<br/>
<br/>

# 📚 Want to go deeper?

My **Toolbox** books turn real Microsoft security telemetry into defensible operations:

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/ifIo6eT" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/PowerShell-Cover.jpg"
      alt="PowerShell Toolbox: Hands-On Automation for Auditing and Defense"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🧰 <strong>PowerShell Toolbox</strong> Hands-On Automation for Auditing and Defense
  </p>
</div>

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/hZ1TVpO" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/KQL Toolbox Cover.jpg"
      alt="KQL Toolbox: Turning Logs into Decisions in Microsoft Sentinel"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🛠️ <strong>KQL Toolbox:</strong> Turning Logs into Decisions in Microsoft Sentinel
  </p>
</div>

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/4vveVCI" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg"
      alt="Ultimate Microsoft XDR for Full Spectrum Cyber Defense"
      style="max-width: 340px; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    📖 <strong>Ultimate Microsoft XDR for Full Spectrum Cyber Defense</strong><br/>
    Real-world detections, Sentinel, Defender XDR, and Entra ID — end to end.
  </p>
</div>

<br/>
<br/>

# Helpful Links & Resources:

- [https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure)

- [https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-resource-roles-custom-role-policy](https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-resource-roles-custom-role-policy)

- [https://learn.microsoft.com/en-us/azure/defender-for-cloud/just-in-time-access-usage#prerequisites](https://learn.microsoft.com/en-us/azure/defender-for-cloud/just-in-time-access-usage#prerequisites)

- [https://leonardo.ai/](https://leonardo.ai/)

<br/>
<br/>

![](/assets/img/JITA_PIM/JITA1.jpg)

The non-screenshot images featured in this article were generated from either [Microsoft Copilot](https://copilot.microsoft.com/) or [https://leonardo.ai/](https://leonardo.ai/). 

<br/>
<br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)