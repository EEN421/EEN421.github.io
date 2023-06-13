# Introduction and Use Case:
You're a industrial manufacturing plant manager, you need to _prototype, deploy, secure,_ and _remotely manage_ connected electronic devices at _scale._ You need to be practical and most importantly, cost-effective. Thankfully, you've made good decisions up to this point and have invested in a SIEM such as **Azure Sentinel** (_good job!_).

&#128073; Most of your sensor and PLC equipment connects through an API or is compatible with the Azure Monitoring Agent. **What do you do** for your **unsupported** but **critical IoT architecture**?

 
>  &#128161;  **_In my experience, typically some custom hardware running some flavour of Linux under the hood, think Raspberry Pi based microcontrollers that help automate the line for example._**

<br/>

# In this post we will: 
- Call out and solve for use-case pre-requisites
- Configure our 'unsupported' equipment accordingly (Ruby & FluentD)
- Create a Log Analytics Workspace
- Retrieve WorkspaceID and Primary Key
- Program the config file for log aggregation (FluentD)
- Log auth and syslog tables to a Log Analytics Workspace


<br/>

# Call out and solve for pre-requisites
Typically, the easiest way to send logs to Log Analytics workspace is to leverage the Microsoft OMS Agent. Microsoft supports Linux and has an OMS agent available _but doesn’t support popular ARM platforms like a Raspberry Pi build._ Our setup will rely on **Ruby** and **FluentD** to talk to the **Log Analytics Workspace** 

<br/>

# Configure our 'unsupported' equipment

- Install Ruby
```bash
sudo aptitude install ruby-dev
```

<br/>

- Check/Confirm Ruby Version:
```bash
ruby -ver
```

<br/>

- Install FluentD Unified Log Aggregator & Plugin
```bash
sudo gem install fluentd -v "~> 0.12.0"
sudo fluent-gem install fluent-plugin-td
```

<br/>

- Install FluentD Plugn for Azure Log Analytics
```bash
sudo fluent-gem install fluent-plugin-azure-loganalytics
```

<br/><br/>

# Create a Log Analytics Workspace
- Navigate to Log Analytics Workspace in Azure Portal: <br/>
![](/assets/img/iot/LAW1.png)

<br/><br/>

- Select ** +Create **  <br/>
![](/assets/img/iot/LAW2.png)

<br/><br/>

- Select **Subscription** and **Resource Group:** <br/>
![](/assets/img/iot/LAW3.png)

<br/><br/>

- Select Instance **Name** and **Region:** <br/>
![](/assets/img/iot/LAW4.png)

<br/><br/>

- Pricing Tier:
Choose the appropriate commitment tier given your expected daily ingest volume. <br/><br/>

&#128161;
	&#128073;      **_I like to see roughly 15% more ingest than required for the next pricing tier to insulate against nights, weekends, and holidays which inherently drag down the daily ingest volume average._** 

<br/>

- Click **Review & Create** to finish setting up a new Log Analytics Workspace 

<br/><br/>

# Retrieve WorkspaceID and Primary Key
![](/assets/img/iot/WorkspaceIDandKey.png)

<br/><br/>

# Build a Configuration File for FluentD
- Swap out the WorkspaceID and Primary Key in this [fluent.conf](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iot/fluent.conf) file with the values we acquired in the previous step.

- Run the following command to start logging to your Log Analytics Workspace:

```python
sudo fluentd -c /etc/fluent.conf --log /var/log/td-agent/fluent.log
```

<br/>

Lets break down the above command, there's a lot going on here:

```python
sudo fluentd #<-- starts fluentd with super user privileges

-c /etc/fluent.conf #<-- the '-c' switch tells us where to look for the config file (I keep mine in /etc/)

--log /var/log/td-agent/fluent.log #<-- the '--log' switch enables verbose logging and specifies where to drop the resulting log output
```

<br/><br/>

>  &#128161;  **_Pro-Tip: save the command to start logging to your workspace as a .bash command so you don't have to re-enter the lengthy paramters every time. Run the following commands to do this:_**
> ```bash
> sudo nano start.bash #<-- opens nano text editor and creates file 'start.bash'
>```
> Paste the entire start command and parameters and press:
>```bash
> CTRL+X followed by 'Y' then Enter to save
>```
> Now to run the start command, all you have to do is: 
>```bash
>sudo start.bash
>```

<br/><br/>

>  &#128161;  **_Another Pro-Tip: &#128073; Create a CRON job to start logging on startup_**


<br/><br/>

# Query Auth and Syslog Tables
Navigate to your Log Analytics Workspace and you should see your custom logs (logs ingested this way show up under 'Custom Logs' and have '_CL' appended to their name when they hit the workspace, illusgtrated below):

![](/assets/img/iot/CustomLogs.png)

<br/><br/>

&#128161; Once FluentD is cooking without issue on your Pi, try logging in with an **incorrect password** to trigger an entry in the new custom log _'auth_cl'_ then query the table &#128071;

![](/assets/img/iot/Auth_CL.png)

<br/>

The syslog table (syslog_cl) is populating too: 
![](/assets/img/iot/syslog_cl.png)

<br/><br/>


# In this, post we: 
- &#10003; Called out and solved for use-case pre-requisites
- &#10003; Configured our ARM equipment accordingly (Ruby & FluentD)
- &#10003; Create a Log Analytics Workspace
- &#10003; Retrieve WorkspaceID and Primary Key
- &#10003; Program the config file for log aggregation (FluentD)
- &#10003; Log auth and syslog tables to a Log Analytics Workspace

<br/><br/>

# Resources:
- [FluentD Cloud Data Logging (Raspberry Pi)](https://docs.fluentd.org/v/0.12/articles/raspberrypi-cloud-data-logger)
- [FluentD configuration file syntax](https://docs.fluentd.org/v/0.12/configuration/config-file)
- [Create a Log Analytics Workspace - Official Microsoft Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/quick-create-workspace?tabs=azure-portal) 
