# Introduction and Use Case:

Continuing from a previous post, today we'll dissect even more simple but powerful KQL queries that are essential to keep in your threat hunting utility belt.

# Recap:

In my last post, we broke down some helpful, basic KQL queries and syntax:

- Defining **table** to query against
- Defining **time** periods manually and via GUI
- Filtering out **non-billable** query results
- Leveraged the **Summarize** function to manipulate results
- Graphing results to **chart**
- Querying specific **devices**
- Querying the **Usage table** for **anomalies**

<br/>

# How verbose is an EventID?
```sql
SecurityEvent // <--Define the table to query

| where EventID == "4663" // <--Query for specific EventID

| summarize count() by bin(TimeGenerated,1d) // <--Return count per day

| render columnchart // <--Graph a column chart
```

![4663](/assets/img/AOAQ2/4663_Graph.png)

<br/>

# Which Devices are Throwing a Specific EventID?

```sql
SecurityEvent // <--Define the table to query

| where EventID == "4663"   // <--Query for specific EventID

| summarize count() by Computer // <--Return count per computer
```
![4663 Count by Computer](/assets/img/AOAQ2/4663_byComputer.png)
<br/>
<br/>

# How often does a specific computer throw a specific EventID over a defined timespan?

```sql
SecurityEvent   // <--Define the table to query

| where EventID == "4663"   // <--Query for specific EventID

| where Computer == "This Guy" // <--Query a specific device

| summarize count() by bin(TimeGenerated,1d) // <--Return count per day

| render columnchart // <--Graph results to chart
```
![4663 on ThisGuy](/assets/img/AOAQ2/ThisGuy.png)

<br/>

# Summary:

In this post, we broke down some helpful, basic KQL queries and syntax:

- Defining **table** to query against
- Querying for specific **EventIDs**
- Querying specific **devices**
- Combining these to query for **specific EventIDs on specific devices**
- Leveraged the **Summarize** function to manipulate data (break totals up by day etc.)
- Graphing results to **chart**

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



Official Microsoft References:

- [https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/)
- [https://learn.microsoft.com/en-us/azure/data-explorer/kql-quick-reference](https://learn.microsoft.com/en-us/azure/data-explorer/kql-quick-reference)
- [https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/best-practices](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/best-practices)
- [https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/tutorials/use-aggregation-functions](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/tutorials/use-aggregation-functions)
