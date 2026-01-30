Sentinel Cost Optimization Challenge

So you read my [Sentinel Cost Optimization post](https://www.hanley.cloud/2023-04-24-Sentinel-Cost-Optimization/), _now what?_ Let’s test those fresh new skills you just picked up! See if you can [ninja](https://techcommunity.microsoft.com/t5/microsoft-sentinel-blog/become-a-microsoft-sentinel-ninja-the-complete-level-400/ba-p/1246310) your way through the following typically asked questions: 

> **_1.	What query should you run to graph the last 90 days of billable ingest volume?_**  <br/>
> **_2.	How do you find the commitment tier for Sentinel?_** <br/>
> **_3.	How do you find the commitment tier for your Log Analytics Workspace?_**<br/>
> **_4.	Are you on the right commitment tier?_**<br/>
> **_5.	Is your retention policy bleeding you dry?_**
 
<br/><br/>

# 1.  What query should you run to graph the last 90 days of billable ingest volume?
> **_Answer:_** 

```sql
Usage       	//<--tells us which table to apply this query to. In this case it’s the Usage log table.

| where TimeGenerated > ago(90d)	//<-- how far back the query will look in the Usage table.

| where IsBillable == true		//<-- filters out non-billable data (we’re only worried about data that incurs a cost).

| summarize TotalVolumeGB = sum(Quantity) / 1000 by bin(StartTime, 1d), Solution
 /* Convert to GB and return results by day, per ingest solution (LogManagement, Security, etc.)*/

| render columnchart		//<-- graph results to a column chart
``` 


# 2.	How do you find the commitment tier for Sentinel?
> **_Answer:_** <br/>
![](/assets/img/Optimization/Exercise/SentinelTier1.png)<br/>
![](/assets/img/Optimization/Exercise/SentinelTier2.png)<br/>

# 3.	How do you find the commitment tier for your Log Analytics Workspace? 
> **_Answer:_** <br/>
![](/assets/img/Optimization/Exercise/LAWTier1.png)<br/>
![](/assets/img/Optimization/Exercise/LAWTier2.png)<br/>

# 4.	Are you on the right commitment tier? 
> **_Answer:_** 
![](/assets/img/Optimization/Exercise/Right_Tier.png)


# 5.	Is your retention policy bleeding you dry?
> **_Answer:_**  
![](/assets/img/Optimization/Exercise/BadRetention.png)

In the above example, data retention beyond 30 days is accountable for half of total ingest volume cost. Lets bring it back down to 90 to save the day:

![](/assets/img/Optimization/Exercise/LAWTier1.png)<br/>
![](/assets/img/Optimization/Exercise/LAWTier2.png)<br/>
![](/assets/img/Optimization/Exercise/RetentionSetting.png)<br/>



# Summary: 
By now your Log Analytics Workspace and Sentinel Deployments should be humming along like a lean, mean, SIEM machine as you have mastered the basics of cost optimization. 

In this post, we answered the following typical deployment questions:

1.	What query should you run to graph the last 90 days of billable ingest volume? 
2.	How do you find the commitment tier for Sentinel?
3.	How do you find the commitment tier for your Log Analytics Workspace?  
4.	Are you on the right commitment tier? 
5.	Is your retention policy bleeding you dry? 

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


