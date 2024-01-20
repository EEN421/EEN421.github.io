# Introduction and Use Case: 
Microsoft Sentinel is a powerful tool that enables security teams to detect, investigate, and respond to threats across their entire organization. However, when it comes to presenting this data to clients, it can be challenging to make sense of the raw data. 

This is where PowerBI comes in - a business analytics service that provides interactive visualizations and business intelligence capabilities with an interface simple enough for end users to create their own reports and dashboards. In this post, we will explore how to automate Sentinel report generation using PowerBI, allowing you to save time and streamline your reporting process.

In this Post We Will:
- &#128073;Define our report and the underlying KQL
- &#128073;Run and export our KQL to a PowerBI M Query
- &#128073;Import our M Query into PowerBI
- &#128073;Manipulate Data Sets and Render Visuals
- &#128073;Save and Export our Report to PDF
- &#128073;Re-run our report with 1-click!
- &#128073;Achieve Awesome-ness 😎


# Pre-Requisites:

- [PowerBI Desktop License (included with E5)](https://powerbi.microsoft.com/en-us/pricing/)
-	[Log Analytics Workspace](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/quick-create-workspace?tabs=azure-portal)
-	[Security Reader Role](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)

# Define our Report and the Underlying KQL:
Lets keep it simple and report on our Ingest tends for this exercise and query the Usage table. In my experience, usage and cost trends are almost always brought up during quarterly business reviews. You could manually query your workspace with KQL every quarter and paste the results into a PowerPoint deck or whatever, but that’s a drag on your time… Let’s automate this!

 > &#128161; Pro Tip:
Everybody’s got a Usage table right? Depending on what you’ve got in your environment, maybe you could involve firewall logs via the commonsecuritylog or syslog tables for quarterly security meetings etc. You’re only limited to what’s in your workspace.


For this report, lets include ingest trends from the Usage table for the past 90, 60, 30, and 7 days. You can copy and paste the KQL from my GitHub repo here: KQL-Queries/90 Day Billable Ingest Volume.kql at Main · EEN421/KQL-Queries (github.com)


 > &#128161; Pro Tip:
  Check out my full catalogue of useful KQL queries ready to copy and paste here: EEN421/KQL-Queries: Ian Hanley's deceptively simple KQL queries. (github.com)
 
 


# Run and export our KQL to a PowerBI M Query

1.	Fire up your favourite browser, navigate to the [Azure portal](https://portal.azure.com) and load your Log Analytics Workspace or choice.
2.	Paste the *90 Day Billable Ingest Volume.kql* query into the query window and run it.
3.	Once the query has finished running, the **--> Export** button will become available. Click on it and select **PowerBI (as an M query)**, illustrated below.

![](/assets/img/PowerBI%20Reports/1.png)



4.	A **PowerBIQuery.txt file** will populate in your Downloads folder.
  
![](/assets/img/PowerBI%20Reports/2.png)

5. *Hang onto this*&#10071;

# Import our M Query into PowerBI:

1.	Spin up the PowerBI Desktop App (*PowerBI WebApp does NOT support importing M Queries*) and make sure you're signed into PowerBI with an account that has the Security Reader RBAC role and go to **Home > Get data > Blank Query**.

![](/assets/img/PowerBI%20Reports/3.png)



3.	A new window will pop up. Select **Advanced Editor** (shown below).

![](/assets/img/PowerBI%20Reports/4.png)
 

5.	Paste the contents of the **PowerBIQuery.txt** from earlier into the **Advanced Editor** and click on **Done**

![](/assets/img/PowerBI%20Reports/5.png)
 

7.	A preview of your data will populate in a table for verification.

![](/assets/img/PowerBI%20Reports/6.png)
 


10.	Rename your Query in the **Advanced Editor**, then select **Close & Apply**

![](/assets/img/PowerBI%20Reports/7.png)



# Manipulate Data Sets and Render Visuals:

1.	Now that we’ve imported our dataset, lets do something with it! Select the Visuals tab on the right and choose **Clustered Column Chart**

![](/assets/img/PowerBI%20Reports/9.png)




3.	Select All of the data sources from the **Data** tab on the right under our 90 Day billable Ingest Trend dataset.

![](/assets/img/PowerBI%20Reports/10.png)




5.	The bar chart renders with data from the selected dataset.

![](/assets/img/PowerBI%20Reports/11.png)
 

7.	Rename the page and create additional pages as illustrated below:

![](/assets/img/PowerBI%20Reports/12.png)
 

 > &#128161; Real Talk:
Right about now you’re probably asking yourself *“So I have to edit line 2 in the original query and re-run it, export the M query, then import each data set into PowerBI? What a DRAG!”* …and you’d be right… **so lets streamline this!**

&#x26A1; You can re-use the original **PowerBIQuery.txt** for the rest, here’s how to adjust the time frame on the fly:

5.	Open a new page, rename it to **60 Day Billable Ingest** and select **Get Data** just like we did earlier and import your original **PowerBIQuery.txt** file, only this time *before clicking on **Close & Apply***, look in the query window for **“P90D”** and swap it out for **“P60D”** to change the timeframe that this M query will apply to without having to regenerate the whole **M query**, illustrated below:
  
![](/assets/img/PowerBI%20Reports/12.png)

 

8.	Select **Close & Apply**, then create your preferred visual the same way we rendered a bar graph in previous steps. 

9.	Create a new page and rename it to **30 Day Billable Ingest**, and repeat previous steps for 30 days, then 7, or even as far as you’d like; up to the last 30 minutes or as far back as your retention allows.


# Save and Export our Report to PDF:
-	**File > Export > Export to PDF**


# Re-run our report with 1-click!
-	Save your PowerBI report to easily generate again next quarter.

# Achieve Awesome-ness
In my experience, 90, 60, and 30 day trends tend to lend themselves pretty well to Quarterly Business Reviews and deliver added value. What sort of reports will YOU automate? 

# In this Post We:
- &#128073;Defined our report and the underlying KQL
- &#128073;Ran and exported our KQL to a PowerBI M Query
- &#128073;Imported our M Query into PowerBI
- &#128073;Manipulated Data Sets and Rendered Visuals
- &#128073;Saved and Exported our Report to PDF
- &#128073;Re-ran our report with 1-click!
- &#128073;Achieved a State of Awesome-ness 😎
    
# References & Resources:
- [Role Based Access Control (RBAC) Roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
- [PowerBI Licensing/Pricing](https://powerbi.microsoft.com/en-us/pricing/)
-	[Create a Log Analytics Workspace](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/quick-create-workspace?tabs=azure-portal)
-	[90 Day Billable Ingest Volume.kql](https://github.com/EEN421/KQL-Queries/blob/Main/90%20Day%20Billable%20Ingest%20Volume.kql)
-	[Ian Hanley's deceptively simple KQL queries](https://github.com/EEN421/KQL-Queries/tree/Main)
-	[Azure Portal](https://portal.azure.com/)



