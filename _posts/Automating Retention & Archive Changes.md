# Introduction and Use Case:
The sheer versatility of KQL as a query language is staggering. The fact that there are so many query variations that ultimately deliver to the same results, leads me to think how one query could be more beneficial than another in a given circumstance. Today we'll explore a crude KQL example that works, but then improve it in more ways than one (think not only compute requirements and time spent crunching, but how the output could be improved upon as well). 

<br/>

# In this post we will:
- Craft basic a basic, quick n’ dirty query that gets the job done 
- Improve the efficiency and thus the time it takes to return results 
- Improve upon the underlying query logic for more meaningful results 
- Improve the end result presentation 
- Understand the different layers of complexity for future query improvements


&#128073; Let’s break down the first iteration of this query and then discuss _how we can clean it up and make it **more efficient.**_ This started out as a quick and dirty way to grab your daily average ingest, but as we’re about to learn, **_there’s more than one way to peel this KQL potato!_**

```sql
1.	search *                     //<-- Query Everything

2.	| where TimeGenerated > (30d)          //<-- Check the past 30 days

3.	| where _IsBillable == true  //<-- Only include billable ingest volume

4.	| summarize TotalGB = round(sum(_BilledSize/1000/1000/1000)) by bin(TimeGenerated, 1d)       //<-- Summarize billable volume in GB using the _BilledSize table column

5.	| summarize avg(TotalGB)     //<-- Summarize and return the daily average
```
![](/assets/img/Potato/Original3.png)
