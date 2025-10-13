# Introduction and Use Case:
You have recently deployed Microsoft Defender for Endpoint. Before this, your workstations were reporting directly to Sentinel. Now that your workstations have 30 days of retention in the Defender for Endpoint product, why duplicate those workstation logs into your Sentienl ingest volume and pay twice? From a Defense in Depth perspective, that's nice to have the added layer, however that's not always practical. For added complexity, your Sentinel and Log Analytics Workspace commitment tiers are different/don't match up.

_What should you do?_

> **_1.	Identify deployment region for both Sentinel and Log Analytics Workspace (LAW)_**  <br/>
> **_2.	Identify the Sentinel and Log Analytics Workspace **Commitment Tiers**_** <br/>
> **_3.	Calculate Effective per GB rates_** <br/>
> **_4. Leverage KQL to query for workstations logging directly to Sentinel_**
> **_5.	**Join** results to another query against a different table_** <br/>
> **_5.	Plug Rates into KQL Query to Calculate Cost_** <br/>

 
<br/><br/>

# 1. Identify Deployment Region for Workspace
![](/assets/img/Optimization2/Sentinel.png)
<br/><br/>
![](/assets/img/Optimization2/Region.png)

>***_Take note of the location, we'll need it later_***

# 2. Identify Commitment Tiers
To determine your Sentinel commitment tier, **search "Sentinel" in the top navbar** then **select your workspace** and click on the **Settings** blade, illustrated in the following screenshots:<br/>
![](/assets/img/Optimization2/Sentinel.png)<br/>
![](/assets/img/Optimization2/workspace.png)<br/>
![](/assets/img/Optimization2/Sentinel_Settings_Blade.png)<br/>

> ***_Note:_*** Shortcut to LAW from Settings blade in Sentinel:
 To skip searching for LAW in the navbar and several subsequent clicks to get to the same place. While in Sentinel, you can quickly swith to LAW using this shortcut in the **Settings** blade:

![](/assets/img/Optimization2/LAWTierShortcut.png)

Then you can go directly to the **Usage and estimated costs** blade:

 
![](/assets/img/Optimization2/LAW%20Cost%20Blade.png)

# 3. Calculate Effective Per GB Rates
In this example where Sentinel is set to **Pay-as-you-go** and LAW is set to **100GB / day**, the **effective per GB rate is \$3.96**

**Log Analytics Workspace:**<br/>
<!--$$ {\$196/day \over 100GB/day} = {\$196 \over 100GB}=\$1.96 /GB $$-->
($196/~~day~~) % (100GB/~~day~~) = ($196 % 100GB) = **$1.96 / GB**

All we have to do next is **combine** this with the **Sentinel** cost per GB for a total **Effective Per GB Price:**<br/>
<!--$$ Sentinel (\$2.00/GB) + LAW (\$1.96) = Effective Per GB Price (\$3.96) $$-->
Sentinel ($2.00/GB) + LAW ($1.96) = Effective Per GB Price (**$3.96**)


# 4. Query for Workstations
```sql
Heartbeat                                                                       //<-- Query the Heartbeat table
| where OSName contains "Windows 10" or OSName contains "Windows 11"            //<-- Query for Win10 and 11 Workstations
| where TimeGenerated >ago(30d)                                                 //<-- Query the last 30 days
| summarize arg_max(TimeGenerated, OSName) by Computer                          //<-- Summarize by computer
```

# 5. Join Results to SecurityEvent Query
```sql
Heartbeat                                                                       
| where OSName contains "Windows 10" or OSName contains "Windows 11"
| where TimeGenerated >ago(30d)
| summarize arg_max(TimeGenerated, OSName) by Computer
| join (SecurityEvent                                                           //<-- Join results with the following query against the SecurityEvent table
| where TimeGenerated >ago(30d)) on Computer                                    //<-- Query the last 30 days
| summarize GB=sum(_BilledSize)/1000/1000/1000                                  //<-- Summarize by total _Billed Size and convert to GB
```

# 6. Plug in Effective Per GB Rate
```sql
let rate=3.96;                                                                  //<-- Plug in Effective per GB Rate Here)
Heartbeat
| where OSName contains "Windows 10" or OSName contains "Windows 11"
| where TimeGenerated >ago(30d)
| summarize arg_max(TimeGenerated, OSName) by Computer
| join (SecurityEvent
| where TimeGenerated >ago(30d)) on Computer
| summarize GB=sum(_BilledSize)/1000/1000/1000
| extend cost = GB*rate                                                         //<-- Multiply total GB by the effective per GB rate
``` 
![](/assets/img/Optimization2/Workstation_Cost.png)

<br/>
<br/>

# Summary:
In this exercise, we identified the **region** and **commitment tiers** for our environment in order to calculate the **effective per GB price** and plug it into a **KQL query** to see exactly how much duplicate cost these workstations logging to Defender and Sentinel were running up.


<br/>
<br/>

# Thanks for Reading!
 &#128161; Want to go deeper into these techniques, get full end-to-end blueprints, scripts, and best practices? Everything you’ve seen here — and much more — is in my new book. Grab your copy now 👉 [Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ).  I hope this was a much fun reading as it was writing! <br/> <br/> - Ian D. 
Hanley • DevSecOps Dad


![](/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg)
<br/>
# Resources:
- [https://github.com/EEN421/KQL-Queries](https://github.com/EEN421/KQL-Queries)
- [https://github.com/rod-trent/MustLearnKQL](https://github.com/rod-trent/MustLearnKQL)
- [https://learn.microsoft.com/en-us/sharepoint/dev/general-development/keyword-query-language-kql-syntax-reference](https://learn.microsoft.com/en-us/sharepoint/dev/general-development/keyword-query-language-kql-syntax-reference)
- [https://techcommunity.microsoft.com/t5/microsoft-sentinel-blog/become-a-microsoft-sentinel-ninja-the-complete-level-400/ba-p/1246310](https://techcommunity.microsoft.com/t5/microsoft-sentinel-blog/become-a-microsoft-sentinel-ninja-the-complete-level-400/ba-p/1246310)
