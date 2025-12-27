# Introduction and Use Case:

So you're a new kid on the SOC and Accounting is freaking out about a massive unexpected increase in their Sentinel ingest cost (or a sudden decrease, both are covered in detail) - and demanding an explanation. This is a step-by-step guide to leveraging KQL for investigating unexplained dips and spikes in ingest volume and uncovering the when/what/why. Put on your detective hat.
<br/>
<br/>
# Where to start?

As mentioned, all you know is that there are significant discrepancies in cost over the past quarter (90 days). Let's look at the ingest pattern over the past quarter and graph billable volume via the usage table with the following query for a birds-eye view of what's going on in the environment:

```sql
Usage
| where TimeGenerated > ago(90d)
| where IsBillable == true
| summarize TotalVolumeGB = sum(Quantity) / 1000 by bin(StartTime, 1d), Solution
| render columnchart
```

![](/assets/img/Detective1/Usage.png)

Hover over the colour coded lines to see what they represent. In this case, purple represents LogManagement and the darker colour represents Security log tables, illustrated here:

![](/assets/img/Detective1/Usage1-Purple.png)![](/assets/img/Detective1/Usage2-Dark.png)

Take note of any unusual spikes or valleys in ingest. The first thing you should notice is the drop off for ingest volume in January. Next is the sudden increase in ingest volume towards the end of March. In the below screenshot, ingest volume from the LogManagement tables almost completely disappeared in January, and the Security tables grew significantly in March.

![](/assets/img/Detective1/Delta.png)
<br/>
<br/>
<br/>
# What happened to LogManagement ingest volume in January?

The LogManagement tables can be viewed in the UI from the Sentinel workspace, simply expand the LogManagement drop-down to see them, shown below:

![](/assets/img/Detective1/Tables.png)

Something in one or more of these tables within the LogManagement solution has changed and is responsible for the drop in ingest volume.

To find out, we can graph the usage for each solution across the specified time frame. Set the custom time frame as illustrated in the below screenshot that corresponds with the sudden change:

![](/assets/img/Detective1/Date_GUI.png)

To determine which of these tables dropped off during that time, we can run the following queries which will hit each table from the LogManagment solution and graph their ingest volume.
<br/>
<br/>

```sql
AzureDiagnostics
| summarize count() by bin(TimeGenerated,1d)
| render columnchart
```
<br/>
<br/>&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;...<br/>
<br/>

```sql
AzureActivity
| summarize count() by bin(TimeGenerated,1d)
| render columnchart
```

<br/>
<br/>&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;...<br/>
<br/>

```sql
AuditLogs
| summarize count() by bin(TimeGenerated,1d)
| render columnchart
```

<br/>
<br/>&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;… … … … …
<br/>
<br/>
<br/>


None of the above correlate or explain what happened. However, the next one, syslog, yielded results:

```sql
Syslog
| summarize count() by bin(TimeGenerated,1d)
| render columnchart
```

![](/assets/img/Detective1/syslog_Graph.png)

Here we can see that the syslog table is responsible for the LogManagment drop off noted earlier on. The next question you should be asking yourself is "where are these coming from/what computers are contributing to syslog volume?" Lets further define the "What" part of this equation.

This next query will return which computers are generating syslog data:


```sql
Syslog
| summarize count() by Computer
```

![](/assets/img/Detective1/Syslog_Count_by_Computer.png)

Note the 3 most verbose machines listed. Running the following query against each machine will tell us if this drop off in ingestion can be wholly or partially attributed to them.

In this next step we plugin the top 3 machines from the previous query to confirm:

```sql
Syslog
| where TimeGenerated > ago(90d)
| where Computer == "5604-Barsoom-main"
| summarize count() by bin(TimeGenerated,1d)
```

![](/assets/img/Detective1/syslog_barsoom.png)

This confirms which machines were responsible for the drop off. Take note of these devices and check with the team(s) responsible for their management and maintenance, they'll want to know.
<br/>
<br/>
In my next post, we will explore the sudden increase in billable ingest volume coming from the Security source/solution.
<br/>
<br/>
<br/>
# Summary:

In this post, we:

- Graphed the last 90 days of billable ingest cost
- Identified a sudden drop off of billable ingest volume
- Identified the Logging Solution (LogManagement)
- Identified the specific Table
- Tracked down the specific device

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

