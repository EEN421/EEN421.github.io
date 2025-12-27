# Introduction and Use Case:
Workspace Transformation Rules are a very effective way to fine tune your ingest volume. Perhaps you need data from the SecurityEvent table but not ALL of the EventIDs that go with it? Let’s take out the trash!
<br/><br/>

# In this post we will:
- Identify the most voluminous table
- Identify the most frequently thrown EventID in that table
- Determine which machines are throwing this EventID and how often
- Build a DCR Transformation rule to filter out a verbose EventID that does not contribute any detection or investigation value.
<br/><br/>

# Find the Most Voluminous Table:
Lets craft a KQL query to return EventIDs from the SecurityEvent table and their respective count (number of times they’ve fired over a given period) to figure out which EventIDs are the loudest, and more importantly, how much it’s costing you. 
```sql
SecurityEvent				//<-- Query the SecurityEvent table
| where TimeGenerated > ago(30d)	//<-- Query the last 30 days
| summarize count() by EventID	        //<-- Summarize EventIDs by number of times they fire
```
![](/assets/img/Transform/Picture1.png)
<br/>
<br/>

We now know that the most frequently thrown EventID in the SecurityEvents table is EventID 8002. This is potentially the “trash” we need to take out. Let’s see how much of it has gathered in our environment in terms of GB in our next query:
```sql
SecurityEvent						//<-- Query the SecurityEvent table
| where TimeGenerated > ago(1h)			        //<-- Query the last hour
| where EventID == 8002					//<-- Query for EventID 8002
| summarize GB=sum(_BilledSize)/1000/1000/1000	        //<-- Summarize billable volume in GB
```
![](/assets/img/Transform/Picture2.png)
<br/>
<br/>

18GB / hour is pretty steep. From my experience, EventID 8002 offers little to no detection (ability to detect malicious activity) or investigation value (post-breach). Let’s filter 18GB of 8002 / hour from our billable ingest volume and save the day! 


**Notes:**
- You can change the last line in the above query to the following if you’re a stickler for Gibibytes (GB) versus Gigabytes(GiB): 
```sql
| summarize GB=sum(_BilledSize)/1024/1024/1024	//<-- Summarize billable volume in GiB
```
<br/>

-	The _BilledSize table column is a standard column in Azure Monitor Logs, but not explicitly listed to the left of the query GUI for you to choose from. You can find out more about _BilledSize and other [Standard columns](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/log-standard-columns#_billedsize).

- Before implementing a Workspace Transformation Rule, it may be worth [figuring out which devices are throwing this EventID](https://github.com/EEN421/KQL-Queries/blob/Main/Which%20Devices%20are%20Throwing%20this%20EventID%3F.kql). If this is a single problem device, then it may make more sense to troubleshoot locally before tuning out this event. In this scenario however, this EventID provides no value regardless, and so can be safely dropped from this environment in this specific example. 

- Please confirm with your administrator or supervisor prior to implementing a Workspace Transformation Rule, as they can result in catastrophic results if implemented incorrectly. 
<br/>
<br/>

# Implementing a Workspace Transformation Rule:
1.	First, go to your **Log Analytics Workspace**: <br/>
![](/assets/img/Transform/Picture3.png)
 <br/>
 <br/>

2.	Select the **Tables** blade: <br/>
![](/assets/img/Transform/Picture4.png)
 <br/>
 <br/>

3.	Search for the **SecurityEvent** table: <br/>
![](/assets/img/Transform/Picture5.png)
 <br/>
 <br/> 

4.	Click on the **“…”** for that table and then on **Create transformation.** <br/>
![](/assets/img/Transform/Picture6.png)
 <br/>
 <br/>

5.	Name the transformation rule: <br/>
![](/assets/img/Transform/Picture7.png)
 <br/>
 <br/>

6.	Click on **</> Transformation editor** <br/>
![](/assets/img/Transform/Picture8.png)
 <br/>
 <br/>

7.	Use KQL to define _‘everything except 8002’_ for collection as illustrated below: <br/>
![](/assets/img/Transform/Picture9.png)
 <br/>
 <br/>

8.	Review and **confirm**: <br/>
![](/assets/img/Transform/Picture10.png)
 <br/>
 <br/>
 
9.	To test, we can query the SecurityEvent table for EventID 8002 after the workspace transformation rule was deployed (just over 5 minutes ago): <br/>
 
![](/assets/img/Transform/Picture11.png)
 
 <br/>
 <br/>

EventID 8002 has effectively been excluded from ingest volume, saving 18GB / hour and therefore lots of $$$ over the course of a month or quarter. Make sure you check in with accounting whenever you successfully knock one of these out and forever secure your legacy as THE KQL ninja in your network. 

<br/>

**_WARNING:_**   While transformations themselves don't incur direct costs, the following scenarios [can result in additional charges](https://learn.microsoft.com/en-us/azure/azure-monitor/essentials/data-collection-transformations#cost-for-transformations):
- If a transformation increases the size of the incoming data, such as by adding a calculated column, you'll be charged the standard ingestion rate for the extra data.

- If a transformation reduces the incoming data by more than 50% and Sentinel is **NOT** deployed, _you will be charged for the amount of filtered data above 50%._

<br/>

# Summary: 
In this post, we learned how to:

- Identify the most verbose table
- Identify the most frequently thrown EventID in that table
- Determine which machines are throwing this EventID and how often
- Build a DCR Transformation rule to filter out a verbose EventID that does not contribute any detection or investigation value.

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

<br/>

# References: 
- [https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/)  
- [https://learn.microsoft.com/en-us/azure/data-explorer/kql-quick-reference](https://learn.microsoft.com/en-us/azure/data-explorer/kql-quick-reference)
- [https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/best-practices](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/best-practices)
- [https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-workspace-transformations-portal](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/tutorial-workspace-transformations-portal)

