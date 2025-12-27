# Introduction and Use Case:
You’ve just deployed Microsoft Sentinel to your Log Analytics Workspace… now what? How do you know this is an efficient setup? Let’s take a walk on the LEAN side. 

# In this post we will: 

- Determine long term ingest trend
- Determine short term ingest trend
- Confirm Sentinel commitment tier
- Confirm Log Analytics Workspace (LAW) commitment tier
- Confirm Retention policy

# Where to start? 

The eventual outcome will differ depending on your priorities.  What we can do right now, is check for the “low hanging fruit” or “easy wins.” You’re going to need a couple weeks’ worth of billable ingest before this will be effective too (we’ll sort out what’s billable and filter out the rest). Let’s look at the ingest pattern over the past quarter and see what’s going on. 

# Determine Long Term Ingest Trend

Navigate to Sentinel:

 ![](/assets/img/Optimization/Sentinel.png)

Go to “Logs” and run the following query:

```sql
Usage
| where TimeGenerated > ago(90d)
| where IsBillable == true          // <-- filters out non-billable data (we're only worried about data that incurs a cost)
| summarize TotalVolumeGB = sum(Quantity) / 1000 by bin(StartTime, 1d), Solution
| render columnchart
```

![](/assets/img/Optimization/usage.png)

		
Take note of any unusual spikes or valleys in billable ingest from the above graph. Also note that the second “where” statement (3rd line) in this query filters out non-billable ingest volume. Nothing crazy going on here in this example. It’s normal to see a slight decline in volume over the weekends and holidays etc. 

If your results are different, check out my [KQL Detective series](https://www.hanley.cloud/2023-04-19-KQL-Detective-Part-1/) at [hanley.cloud](https://www.hanley.cloud) in which we track down the root cause of cost anomalies in billable ingest (like a suddenly noisy firewall or a device going offline for example). For a more detailed, line-by-line breakdown of a KQL query, please visit my [Anatomy of a KQL Query series](https://www.hanley.cloud/2023-04-06-Anatomy-of-a-KQL-Query-Part-1/).

# Determine Short Term Ingest Trend

Next we’ll take a look at the short term ingest trend. You can run the same query as above and change out the value in line two from 90 to 30, OR you can navigate to the “Settings” blade in Sentinel (towards the bottom of the list of blades). This will tell you which tier you’re currently subscribed to as well as graph out the last 31 days of billable ingest volume: 

 ![](/assets/img/Optimization/Sentinel.png)

 ![](/assets/img/Optimization/Sentinel_Settings_Blade.png)

 ![](/assets/img/Optimization/Short%20Term%20Ingest.png)


Based off the average billable ingest volume displayed in the above short term and long term graphs, we should be able to make an educated decision about which commitment tier to move to.
> **_&#128161;_**   Commitment Tiers are tricky, as they come with different discounts for Sentinel and your Log Analytics workspace separately. For example, it's cost effective to move to the 100GB/Day commitment tier from Pay-As-You-Go when you get to 50GB+/Day because of the 50% Sentinel discount, but the Analytics workspace discount is 15%, so it's not cost effective until roughly 85-90GB/Day or more (I like to a little more to insulate from nights and weekends).

# Confirm Sentinel Commitment Tier

![](/assets/img/Optimization/Sentinel.png)

![](/assets/img/Optimization/Sentinel_Settings_Blade.png)
 
 ![](/assets/img/Optimization/Sentinel%20Tier.png)

# Confirm Log Analytics Workspace (LAW) Commitment Tier

Next we need to determine the Log Analytics Workspace commitment tier, as it's separately from Sentinel. Both the LAW and Sentinel commitment tiers should generally be the same, unless you’ve got a very complex setup with different ingest volumes, but that’s not typical in my experience. 

To determine your LAW commitment tier, navigate to your workspace and select the Usage and estimated costs blade:
 
![](/assets/img/Optimization/LAW.png)
 
 ![](/assets/img/Optimization/LAW%20Cost%20Blade.png)

This shows you the same 31 days of billable ingest graphed on the right and your current commitment tier in the middle. 


![](/assets/img/Optimization/LAW%20Tier.png)

 

Notice how this time the commitment tier drop-down displays the estimated cost (this is harder to calculate for sentinel, there may be credits based on a Defender for cloud subscription etc.). Again, it’s typically a good idea for both Sentinel and LAW commitment tiers to match up unless there’s a specific use case in play. 

# Confirm Retention Policy 

Lastly, lets check out our retention settings. ***Anything more than 90 days will incur a cost.*** Navigate to the LAW Usage and estimated costs blade, then select “Data Retention” to see what the current policy is set to: 
 
 
![](/assets/img/Optimization/LAW.png)

![](/assets/img/Optimization/LAW%20Cost%20Blade.png)

![](/assets/img/Optimization/Retention.png)

![](/assets/img/Optimization/Retnetion%202.png)
 
> **_&#128161;_**   In my experience, it’s best practice to configure retention for 90 days with a valid Sentinel subscription because it’s included.

# Conclusion:
The easiest ways to optimize your overall billable ingest cost are to ask yourself the following questions first: 
- What’s normal for my environment?
- What anomalies are affecting my cost such as suddenly verbose firewalls or systems that stopped reporting in?
- Are your Log Analytics Workspace and Sentinel commitment tiers configured appropriately?
- Is your Retention Policy costing you money? 

# Summary: 
In this post, we optimized our LAW and Sentinel billable ingest volume by:
- Determining long term ingest trend
- Determining short term ingest trend
- Confirming Sentinel commitment tier
- Confirming Log Analytics Workspace (LAW) commitment tier
- Confirming Retention policy
<br/>
<br/>

# Thanks for Reading!
 &#128161; Want to go deeper into these techniques, get full end-to-end blueprints, scripts, and best practices? Everything you’ve seen here — and much more — is in my new book. Grab your copy now 👉 [Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ).  I hope this was a much fun reading as it was writing! <br/> <br/> - Ian D. 
Hanley • DevSecOps Dad


<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/4vveVCI" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg"
      alt="Ultimate Microsoft XDR for Full Spectrum Cyber Defense"
      style="max-width: 340px; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    📘 <strong>Ultimate Microsoft XDR for Full Spectrum Cyber Defense</strong><br/>
    Real-world detections, Sentinel, Defender XDR, and Entra ID — end to end.
  </p>
</div>
<br/>

