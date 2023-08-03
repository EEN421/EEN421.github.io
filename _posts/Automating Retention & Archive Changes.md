# Introduction and Use Case:
Retention policies define when to remove or archive data in a Log Analytics workspace. Archiving lets you keep older, less used data in your workspace at a reduced cost. You're a Sentinel Ninja and your organization needs to adjust their interactive and archive retention settings across the board to remain in compliance with the latest industry regulations. 

<br/>

# In this post we will:
- Explore manually adjusting interactive and archive retention settings
- Leverage an automation script in Azure CLI
- Create a custom .json file to hold your secrets/unique information
- Adjust both interactive and archive retention across multiple tables 
- Save yourself time and stress 


# Manual Process:
Each workspace has a default retention policy that's applied to all tables. You can set a different retention policy on individual tables, one at a time in the portal's GUI.
- Navigate to the **Tables** blade under **Settings** in your Log Analytics Workspace.
![](Blade.png)

- Select a table and click on the **"..."**
- Select **"Manage Table"** to see the current retention settings

- Interactive Retention can be set to a range of values from 30 days to 2 years.
- Archive Retention can be set to a much wider ranger of values from 30 days to 7 years.
- Archive Retention cannot be less than the Interactive Retention period.
- Archiving can be effectively turned off by setting it equivalent to the Interactive Retention:


```json
{
  "TenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "SubscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "LogAnalyticsResourceGroup": "rg-hanley-demonstration",
  "LogAnalyticsWorkspaceName":  "test-workspace",
  "TablePlan": "Analytics",
  "SetEntireLogAnalyticsWorkspace": "YES",  
  "WorkspaceRetentionInDays": 90,
  "ArchiveRetentionInDays": 270,
  "TotalRetentionInDays": 365,
}
```

# Create Azure Web App & Assign RBAC Role

- Login to the [Azure Portal](www.portal.azure.com)

- Select the CloudShell button illustrated below: <br/>

![](/assets/img/IoT%20Azure%20Cost%20Monitor/CLI.png)
