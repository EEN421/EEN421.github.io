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

<br/>

# Continuous Improvement:
The most blatant offense here, is that I’m burning resources crawling through **everything** using **_“search *”_** in **line 1** instead of specifying a table. This means that this query can take forever and even time-out in larger environments (after about 10 minutes). In the next iteration of this query, we query the **Usage** table instead to achieve the same results in less time. Try it out yourself in the [free demonstration workspace](https://portal.azure.com/#view/Microsoft_OperationsManagementSuite_Workspace/LogsDemo.ReactView) and see the difference:  

```sql
1.	Usage   //<-- Query the USAGE table (instead of "search *" to query everything)

2.	| where TimeGenerated > (30d)          //<-- Check the past 30 days

3.	| where IsBillable == true            //<-- Only include billable ingest volume

4.	| summarize GB= sum(Quantity)/1000 by bin(TimeGenerated,1d) //<-- Summarize in GBs by Day
   
5.	| summarize AvgGBPerDay=avg(GB)       //<-- Take the average 
```
![](/assets/img/Potato/plainGB.png)

<br/>

# Continuous Improvement – Now What? Calculate Cost, of Course!
Now we have an efficient query to return the daily average ingest, but **why stop there?** The next question I’m _almost always_ immediately asked next is “but what does that **_cost?_**” &#129297;

&#128161;This next iteration includes an attempt to calculate average cost, and does so by introducing a rate variable (this variable holds your _effective cost per GB_ based on your commitment tier. To find your effective cost per GB, check out [my previous cost optimization blog post where this is covered in greater detail](https://www.hanley.cloud/2023-05-15-Sentinel-Cost-Optimization-Part-2/)) and leveraging the [percentiles](https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/percentiles-aggfunction) function.

```sql
1.	let rate = 4.30;         //<-- Effective $ per GB rate for East US
   
2.	Usage	//<-- Query the USAGE table (instead of "search *" to query everything)
  
3.	| where TimeGenerated > ago(30d)          //<-- Check the past 30 days

4.	|where IsBillable == true 		//<-- Only include billable ingest volume
  
5.	|summarize GB= sum(Quantity)/1000 by bin(TimeGenerated,1d) //<-- Summarize GB/Day 
  
6.	|extend Cost=GB*rate	//<-- calculate average cost
  
7.  | summarize AvgCostPerDay=percentiles(Cost,50),AvgGBPerDay=percentiles(GB,50) //<-- Return the 50th percentile for Cost/Day and GB/Day
```
![](/assets/img/Potato/Ugly.png)

<br/>

# Continuous Improvement - Underlying Query Logic and Presentation...
My grievances against the above query are as follows: Leveraging the percentiles function to take **the 50th percentile is not technically the true average,** but the closest actual cost to the median. Depending on the size of your environment, this can amount to a significant deviation from the true average. Last but not least, the output is just **ugly** too. **_Let’s fix that_** in our next query! &#128071;

```sql
1.	let rate = 4.30;         //<-- Effective $ per GB rate for East US

2.	Usage   //<-- Query the USAGE table (instead of "search *" to query everything)

3.	| where TimeGenerated > ago(30d)     //<-- Check the past 30 days

4.	| where IsBillable == true           //<-- Only include billable ingest volume

5.	| summarize GB= sum(Quantity)/1000 by bin(TimeGenerated,1d)     //<-- break it up into GB/Day

6.	| summarize AvgGBPerDay=avg(GB)      //<-- take the Average

7.	| extend Cost=AvgGBPerDay * rate     //<-- calculate average cost

8.	| project AvgGBPerDay=strcat(round(AvgGBPerDay,2), ' GB/Day'), AvgCostPerDay=strcat('$', round(Cost,2), ' /Day')    //<-- This line is tricky. I convert everything to string in order to prepend '$' and append ' /Day' to make the results more presentable
```
![](/assets/img/Potato/Formatted.png)
>_Much Better_&#128070;

<br/>
<br/>

# In this post, we accomplished the following:
- &#10003; Craft basic a basic, quick n’ dirty query that gets the job done
- &#10003; Improve the efficiency and thus the time it takes to return results
- &#10003; Improve upon the underlying query logic for more meaningful results
- &#10003; Improve the end result presentation
- &#10003; Understand the different layers of complexity for future query improvements
- &#10003; Build something **_awesome_** &#128526;

<br/>

![](/assets/img/IoT%20Hub%202/footer.png)


