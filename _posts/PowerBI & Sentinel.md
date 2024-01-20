#Run and export our KQL to a PowerBI M Query#

1.	Fire up your favourite browser, navigate to https://portal.azure.com and load your Log Analytics Workspace or choice.
2.	Paste the 90 Day Billable Ingest Volume.kql query into the query window and run it.
3.	Once the query has finished running, the --> Export button will become available. Click on it and select PowerBI (as an M query), illustrated below.

![](/assets/img/PowerBI%20Reports/1.png)



4.	A PowerBIQuery.txt file will populate in your Downloads folder. Hang onto this.
  
![](/assets/img/PowerBI%20Reports/2.png)


#Import our M Query into PowerBI#

1.	Spin up the PowerBI Desktop App (PowerBI WebApp does NOT support importing M Queries) and go to Home > Get data > Blank Query (displayed in screenshot on right).

![](/assets/img/PowerBI%20Reports/3.png)



3.	A new window will pop up. Select Advanced Editor (shown below).

![](/assets/img/PowerBI%20Reports/4.png)
 

5.	Paste the contents of the PowerBIQuery.txt from earlier into the Advanced Editor and click on Done

![](/assets/img/PowerBI%20Reports/5.png)
 

7.	A preview of your data will populate in a table for verification.

![](/assets/img/PowerBI%20Reports/6.png)
 


10.	Rename your Query in the Advanced Editor, then select Close & Apply

![](/assets/img/PowerBI%20Reports/7.png)



#Manipulate Data Sets and Render Visuals#

1.	Now that we’ve imported our dataset, lets do something with it! Select the Visuals tab on the right and choose Clustered Column Chart

![](/assets/img/PowerBI%20Reports/8.png)




3.	Select All of the data sources from the Data tab on the right under our 90 Day billable Ingest Trend dataset.

![](/assets/img/PowerBI%20Reports/9.png)




5.	The bar chart renders with data from the selected dataset.

![](/assets/img/PowerBI%20Reports/10.png)
 

7.	Rename the page and create additional pages as illustrated below:

![](/assets/img/PowerBI%20Reports/11.png)
 

Real Talk:
Right about now you’re probably asking yourself “So I have to edit line 2 in the original query and re-run it, export the M query, then import each data set into PowerBI? What a DRAG!” …and you’d be right… so lets streamline this!

You can re-use the original PowerBIQuery.txt for the rest, here’s how to adjust the time frame on the fly:

5.	Open a new page, rename it to 60 Day Billable Ingest and select Get Data just like we did earlier and import your original PowerBIQuery.txt file, only this time before clicking on Close & Apply, look in the query window for “P90D” and swap it out for “P60D” to change the timeframe that this M query will apply to, illustrated below:
  
![](/assets/img/PowerBI%20Reports/12.png)

 

8.	Select Close & Apply, then create your preferred visual the same way we rendered a bar graph in previous steps. 

9.	Create a new page and rename it to 30 Day Billable Ingest, and repeat previous steps for 30 days, then 7, or even as far as you’d like; up to the last 30 minutes or as far back as your retention allows.

10.	Select File > Export to print to PDF.


In my experience, 90, 60, and 30 day trends tend to lend themselves pretty well to Quarterly Business Reviews and deliver added value. What sort of reports will YOU automate? 
