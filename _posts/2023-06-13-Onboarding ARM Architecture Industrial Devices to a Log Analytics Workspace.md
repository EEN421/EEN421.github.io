# Introduction and Use Case:
You're a industrial manufacturing plant manager, you need to prototype, deploy, secure, and remotely manage connected electronic devices at scale. You need to be practical and most importantly, cost-effective. Thankfully, you've made good decisions up to this point and have invested in a SIEM such as Azure Sentinel (good job!).

Most of your sensor and PLC equipment connects through an API or is compatible with the Azure Monitoring Agent. What do you do for your **unsupported** but **critical IoT architecture** (in my experience, typically some custom hardware running some flavour of Linux under the hood, think Raspberry Pi based microcontrollers that help automate the line for example)?

<br/>

# In this post we will: 
- Call out and solve for use-case pre-requisites
- Configure our 'unsupported' equipment accordingly (Ruby & FluentD Plugin for Log Analytics)
- Create a Log Analytics Workspace
- Retrieve WorkspaceID and Primary Key
- Program the config file for log aggregation (FluentD)
- Log auth and syslog tables to a Log Analytics Workspace
- Explore custom applications (soil moisture and temperature sensors for example)

<br/>

# Call out and solve for pre-requisites
Typically, the easiest way to send logs to Log Analytics workspace is to leverage the Microsoft OMS Agent. Microsoft supports Linux and has an OMS agent available for both x86 and x64 Linux OS editions but doesn’t support popular ARM platforms like a Raspberry Pi board. The existing OMS agent relies on Ruby, Fluentd, and OMI (this last is the unsupported component on ARM platform).

<br/>

# Configure our 'unsupported' equipment
1. Install Ruby
```bash
sudo aptitude install ruby-dev
```

<br/>

2. Check/Confirm Ruby Version:
```bash
ruby --ver
```

<br/>

3. Install FluentD Unified Log Aggregator & Plugin
```bash
sudo gem install fluentd -v "~> 0.12.0"
sudo fluent-gem install fluent-plugin-td
```

<br/>

4. Install FluentD Plugn for Azure Log Analytics
```bash
sudo fluent-gem install fluent-plugin-azure-loganalytics
```

<br/><br/>

# Create a Log Analytics Workspace
1. Navigate to Log Analytics Workspace in Azure Portal: <br/>
![](/assets/img/iot/LAW1.png)

<br/><br/>

2. Select '+Create' <br/>
![](/assets/img/iot/LAW2.png)

<br/><br/>

3. Select Subscription and Resource Group: <br/>
![](/assets/img/iot/LAW3.png)

<br/><br/>

4. Select Instance Name and Region: <br/>
![](/assets/img/iot/LAW4.png)

<br/><br/>

5. Commitment / Pricing Tier
Choose the appropriate commitment tier given your expected daily ingest volume. <br/><br/>

&#128161;
	&#128073;      **_I like to see roughly 15% more ingest than required for the next commitment / pricing tier to insulate against nights, weekends, and holidays which inherently drag down the daily ingest volume average._** 

<br/><br/>

6. Click Review & Create
 ...to Finish Setting up a New Log Analytics Workspace 

# Retrieve WorkspaceID and Primary Key
![](/assets/img/iot/WorkspaceIDandKey.png)

<br/><br/>

# Program the Configuration File for Log Aggregation (FluentD)
Swap out the WorkspaceID and Primary Key in this [fluent.conf](https://github.com/EEN421/EEN421.github.io/blob/master/assets/Code/iot/fluent.conf) file with the values we acquired in the previous step. 

<br/><br/>

# Query Auth and Syslog Tables
Navigate to your Log Analytics Workspace and you should see your custom logs:

![](/assets/img/iot/CustomLogs.png)

&#128161;Once FluentD is cooking without issue on your Pi,try logging in with an **incorrect password** to trigger an entry in the new custom log _'auth_cl'_ then query the table: 

![](/assets/img/iot/Auth_CL.png)

The syslog table (syslog_cl) is populating too: 
![](/assets/img/iot/syslog_cl.png)

<br/><br/>

# Explore Custom Use-Case Applications (Industrial Moisture and Temperature Sensors)
- TBD

<br/><br/>

# In this, post we: 
- Called out and solved for use-case pre-requisites
- Configured our ARM equipment accordingly (Ruby & Log Analytics Plugin for FluentD)
- Create a Log Analytics Workspace
- Retrieve WorkspaceID and Primary Key
- Program the config file for log aggregation (FluentD)
- Log auth and syslog tables to a Log Analytics Workspace
- Explore custom applications (soil moisture and temperature sensors for example)
<br/><br/>

# Resources:
- [FluentD Cloud Data Logging (Raspberry Pi)](https://docs.fluentd.org/v/0.12/articles/raspberrypi-cloud-data-logger)
- [FluentD configuration file syntax](https://docs.fluentd.org/v/0.12/configuration/config-file)
- [Create a Log Analytics Workspace - Official Microsoft Documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/quick-create-workspace?tabs=azure-portal) 