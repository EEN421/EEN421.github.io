# Recap:

In my last post, we leveraged the awesome power of KQL to investigate the drop in billable LogManagement ingest volume illustrated below (left side). During this investigation, we noticed a sudden increase in Security ingest volume toward the end of March. In this post, we're going to track down the root cause of this sudden increase.

![](/assets/img/Detective2/Delta.png)

KQL query to generate the chart referenced above:

```sql
Usage
| where TimeGenerated > ago(90d)
| where IsBillable == true
| summarize TotalVolumeGB = sum(Quantity) / 1000 by bin(StartTime, 1d), Solution
| render columnchart
```

<br/><br/>


# Where did additional Security ingest volume come from in March?

The security tables can be viewed in the UI from the Sentinel workspace (expand the Microsoft Sentinel drop-down to see them, shown below. Something in one or more of these Security tables has changed and is responsible for the sudden increase in ingest volume in March.

![](/assets/img/Detective2/Security_Event_Table.png)

After checking the **SecurityAlert, SecurityEvent,** and **SecurityIncident** tables, the SecurityEvent table returned a matching pattern in ingestion volume, illustrated below.

```sql
SecurityEvent
| where TimeGenerated > ago(30d)
| summarize count() by bin(TimeGenerated,1d)
| render columnchart
```

![](/assets/img/Detective2/Security_Event_Count_Graph.png)

The next step is to see which EventIDs have started to fire more frequently and why.

This query summarizes the results by EventID and their count (number of times they've fired):

```sql
SecurityEvent
| where TimeGenerated > ago(30d)
| summarize count() by EventID
 ```

![](/assets/img/Detective2/Events_by_EventID.png)

Sort the results by the "count\_" column to see the most frequently occurring events (pictured above).

The outlier here is EventID 4663, lets run a query to see the volume over time for this event:

```sql
SecurityEvent
| where EventID == "4663"
| summarize count() by bin(TimeGenerated,1d)
| render columnchart
```

![](/assets/img/Detective2/4663_Count_Graph.png)

The results above look like the security volume pattern we noticed in the Usage table earlier.

This next query shows which machines are throwing EventID 4663 so we can try to identify where the source of increased ingest volume is coming from:


```sql
SecurityEvent
| where EventID == "4663"
| summarize count() by Computer
```

![](/assets/img/Detective2/4663_by_Computer.png)


If we graph this by clicking on the "Chart" button in the UI (shown below) we can see 2 **_major_ outliers:**

![](/assets/img/Detective2/These_Guys.png)

Plugging these outliers into the next query will graph how many times each machine has triggered this event ID:

```sql
SecurityEvent
| where EventID == "4663"
| where Computer == "This Guy"
| summarize count() by bin(TimeGenerated,1d)
| render columnchart
```

![](/assets/img/Detective2/4663_on_ThisGuy.png)

Plugging in the other outlier's FQDN returned the same trend. **_These two machines are responsible for a significant increase in ingest volume because they have started triggering EventID 4663 more frequently since March 21st._** At this time, we need to notify the administrator and inquire about any changes involving these two machines from this time period. My best guess is that they were spun up on March 20th and configured differently when compared to other machines in the environment, something they will want to know about.

# Summary

In this post, we:

- Graphed the last 90 days of billable ingest cost
- Identified a sudden increase in billable ingest volume
- Identified the Logging Solution (Security)
- Identified the specific Table
- Identified the EventID
- Identified the Device(s)
- Identified the exact time frame

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

