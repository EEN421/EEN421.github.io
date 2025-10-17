# Introduction & Use Case: 
In the modern SOC, more data isn’t always better data. When you connect a Fortinet firewall to Microsoft Sentinel for full-spectrum visibility👀, the first thing you notice is… the noise 🔊. Specifically: connection teardown events — hundreds of thousands of them 💥.

At first glance, they look harmless — just logs marking the end of a session. But once you start scaling Sentinel ingestion, those teardown logs quietly turn into the digital equivalent of background static: expensive 💸, repetitive 🔁, and rarely helpful from a security perspective 🕵️‍♂️.

Every log you ingest should earn its place by delivering detection value 🛡️ or investigation value 🔍 — and Fortinet **teardown traffic** fails that test ❌.

This post breaks down what I've learned about Data Collection Rules (DCRs), Fortinet logs, and how to tune them to keep the signal 📡 — _without paying for the noise.🤑_

<br/>
<br/>

# In this Post We Will:
- 🔍 Identify The Problem: Too Much Teardown, Too Little Value
- 💡 Explore the “Detection vs. Investigation Value” framework — and why teardown logs don’t make the cut
- ⚡ Build out our DCR Logic for Fortinet
- 🔧 Convert our query logic into a Data Collection Rule (DCR) transformation that stops them before ingestion
- 🧪 Build our DCR in JSON
- 👌 Leverage the DCR Toolkit Workbook to Manage DCRs
- 🚀 Deploy the DCR Template via Azure CLI
- ⚠️ Avoid the gotchas that cause DCRs to silently fail
- 🧠 Ian's Insights & Key Takeaways for Security Teams
- 🔗 Helpful Links & References

<br/>
<br/>

# 🔍 The Problem: Too Much Teardown, Too Little Value

In Fortinet network traffic logs, every connection generates *two* major events:

1. **Connection standup** — when a new session is created (`traffic:forward start`)

2. **Connection teardown** — when the session closes (`traffic:forward close`, `client-fin`, `server-fin`, etc.)

Multiply that by thousands of clients and microservices, and teardown events quickly dominate your ingestion stream.

<br/>
<br/>

# 💡 Detection versus Investigation Value Breakdown - Why Network Teardown Log Traffic Doesn't Make the Cut

Before diving into KQL and JSON, it’s worth defining what “value” means in a logging context; I like to break down logs into 2 categories that either provide Detection Value or Investigation value:

- **Detection Value** helps us detect and mitigate malicious behaviour in it's tracks. Example: A DeviceFileEvents record showing an unsigned executable dropped into a startup folder. _That’s actionable — it can trigger a rule, block an action, or enrich an alert._ Another example: When malware calls home, the **standup log** shows the destination C2 domain — *that’s actionable*.
  
- **Investigation Value** may not help us detect and stop a malicious act, but it's the first thing the DFIR team asks for during a post-breach investigation and helps reconstruct what happened after a compromise. Example: VPN session duration or DNS lookup history. _It doesn’t detect the attack, but it helps the DFIR team trace lateral movement and data exfiltration._ Additional examples: When a lateral movement connection is opened, the **standup log** shows source → target — _that’s valuable for threat hunting._ But when the connection closes? _The teardown event just repeats the tuple and says “we’re done here.”_

- By the time teardown traffic is written, the attacker’s action already happened.
In short/TLDR: teardown = bookkeeping, not detection.

<br/>

With that framing, Fortinet **teardown traffic** sits firmly in the “no value” zone:

- It offers no detection value — by the time a connection teardown happens, the event is already over.

- It offers minimal investigation value, because a teardown only confirms what a “session start” already implied: that a connection eventually closed.

- The network standup (session start) logs already include source, destination, port, protocol, duration, and bytes — all you need for forensic reconstruction.

<br/>

What it does add:

- **Noise and cost** — these logs inflate ingestion with no added visibility.

<br/>

> ⚠️ Unless you’re in a niche scenario like analyzing abnormal session terminations (e.g., repeated client-RSTs indicating a DDoS condition or proxy instability), teardown logs add noise, not insight.

That’s when I stepped back and asked: *do teardown logs really help us detect or respond to threats faster?* The answer was a resounding "No" the more I thought about it. 

<br/>
<br/>

# ⚡ Build out our DCR Logic for Fortinet to Filter the Noise, not the Signal

I refine my Sentinel ingestion rules using **KQL-based filters** that exclude teardown-only messages while retaining high-value network telemetry.

Here’s the core Fortinet logic in KQL for the DCR rule. DCRs are pushed via **JSON format** so you _can't just copy and paste_ the below KQL (even though it works in the Log blade) into the Transformation Editor; only simplified KQL works here because as a DCR it gets applied prior to ingestion. Many of the advanced functions leveraged below, such as Coalesce() simply will not work in the TransformKQL window. You can, however, copy this KQL into the **Log** blade in Sentinel to test and confirm that the logic works though:

```bash
CommonSecurityLog
| where DeviceVendor == "Fortinet" or DeviceProduct startswith "Fortigate"
| extend _msg = tostring(coalesce(Message, Activity))
// CURRENT FILTERS - Only connection teardown/close events:
| where _msg !~ @"traffic:forward close"       // Connection close events
| where _msg !~ @"traffic:forward client-rst"  // Client reset packets  
| where _msg !~ @"traffic:forward server-rst"  // Server reset packets
| where _msg !~ @"traffic:forward timeout"     // Connection timeouts
| where _msg !~ @"traffic:forward cancel"      // Cancelled connections
| where _msg !~ @"traffic:forward client-fin"  // Client FIN packets
| where _msg !~ @"traffic:forward server-fin"  // Server FIN packets
| where _msg !~ @"traffic:local close"         // Local (intra-device) connection close events
| where _msg !~ @"traffic:local client-rst"    // Local (intra-device) client reset packets
| where _msg !~ @"traffic:local timeout"       // Local (intra-device) connection timeouts
| where _msg !~ @"traffic:local server-rst"    // Local (intra-device) server reset packets
// STILL INCLUDED (high volume, potentially low security value):
// - "traffic:forward accept" etc.
// - Normal application traffic, web browsing, etc.
// - ICMP/ping traffic  
// - DNS queries
// - Routine administrative traffic
| extend RespCode_ = toint(extract(@"ResponseCode=([0-9]+)", 1, AdditionalExtensions)),
         URL_      = extract(@"RequestURL=([^;]+)", 1, AdditionalExtensions),
         App_      = extract(@"ApplicationProtocol=([^;]+)", 1, AdditionalExtensions),
         Threat_   = extract(@"ThreatName=([^;]+)", 1, AdditionalExtensions),
         IPS_      = extract(@"IPSAction=([^;]+)", 1, AdditionalExtensions),
         Policy_   = extract(@"PolicyID=([^;]+)", 1, AdditionalExtensions),
         BytesIn_  = tolong(extract(@"ReceivedBytes=([0-9]+)", 1, AdditionalExtensions)),
         BytesOut_ = tolong(extract(@"SentBytes=([0-9]+)", 1, AdditionalExtensions))
| project
    TimeGenerated,
    Computer = coalesce(Computer, DeviceName),
    Message = _msg,
    EventID = coalesce(DeviceEventClassID, ExtID),
    SourceIP, DestinationIP, SourcePort, DestinationPort, Protocol,
    Action = coalesce(DeviceAction, SimplifiedDeviceAction),
    RuleName = coalesce(DeviceCustomString1, DeviceCustomString2),
    RuleID   = coalesce(DeviceCustomNumber1, DeviceCustomNumber2),
    SubjectUserName = coalesce(SourceUserName, DeviceCustomString3),
    TargetUserName  = coalesce(DestinationUserName, DeviceCustomString4),
    ProcessName = coalesce(ProcessName, DeviceCustomString6),
    Method = RequestMethod,
    URLPath = coalesce(RequestURL, URL_),
    URLDomain = coalesce(DestinationHostName, extract(@"://([^/]+)", 1, coalesce(RequestURL, URL_))),
    ResponseCode = coalesce(DeviceCustomNumber3, RespCode_),
    App = App_, 
    ThreatName = Threat_, 
    IPSAction = IPS_, 
    PolicyID = Policy_,
    BytesIn = BytesIn_, 
    BytesOut = BytesOut_,
    LogSeverity, 
    DeviceVendor, 
    DeviceProduct, 
    _ResourceId
```

Each line intentionally excludes teardown variants across both *forward* and *local* traffic types — while preserving **start**, **allow**, and **deny** events that matter for detection and compliance.

<br/>
<br/>

# 🔧 Convert that query logic into a Data Collection Rule (DCR) transformation that stops them before ingestion.

> ⚠️ Not every KQL function that works in Logs is allowed in DCR transformations.

**Transform queries run per record and only support a documented subset of operators and functions.** Microsoft’s “[Supported KQL features in Azure Monitor transformations](https://learn.microsoft.com/en-us/azure/azure-monitor/data-collection/data-collection-transformations-kql)” explicitly says that only the listed operators/functions are supported—and coalesce() isn’t on that list. In practice, that means queries relying on coalesce() (and a few other conveniences) will error or silently fail when placed into the transformKql window.


Two key takeaways from the doc that matter here:

- Per-record constraint: Transformations process one event at a time; anything that aggregates or isn’t in the “supported” set won’t run. 
Microsoft Learn

- Allowed functions are explicit: If it’s not in the list, assume it’s unsupported in DCRs—even if it works fine in Log Analytics queries. (You will see iif, case, isnull, isnotnull, isnotempty, etc., but not coalesce.) 
Microsoft Learn

> 👉 Another common snag when porting queries is using dynamic literals like ```dynamic({})```. In DCR transforms, prefer ```parse_json("{}")``` instead.

Here's an adjusted, simplified iteration of the previous KQL query listed above, but this one is below is compatible and can be pasted directly into the TransformKQL window:

```bash
source   // Start from your chosen source table (e.g., CommonSecurityLog, Syslog, etc.).
| where DeviceVendor == "Fortinet" or DeviceProduct startswith "Fortigate"  // Keep only Fortinet events; match explicit vendor name or products that start with “Fortigate”.
| extend tmpMsg = tostring(columnifexists("Message",""))    // Create a temp column from Message if it exists; otherwise default to empty string. columnifexists() prevents runtime errors when a column is missing.
| extend tmpAct = tostring(columnifexists("Activity",""))  // Same idea for the Activity field (some connectors use Activity instead of Message).
| extend tmpCombined = iff(isnotempty(tmpMsg), tmpMsg, tmpAct)  // Combine the two: prefer Message when it’s non-empty; otherwise fall back to Activity. iff() is KQL’s inline if; isnotempty() checks for null/blank.
// ------- Network teardown / close signals to EXCLUDE at ingest -------
| where tmpCombined !has "traffic:forward close"  // Exclude “forward” path closes (generic close). `has` is token-based, case-insensitive; good for structured text with clear word boundaries.
| where tmpCombined !has "traffic:forward client-rst"  // Exclude client-initiated resets on forward traffic.
| where tmpCombined !has "traffic:forward server-rst"  // Exclude server-initiated resets on forward traffic.
| where tmpCombined !has "traffic:forward timeout"  // Exclude idle/timeout closes on forward traffic.
| where tmpCombined !has "traffic:forward cancel"  // Exclude user/admin or system cancellations on forward traffic.
| where tmpCombined !has "traffic:forward client-fin"  // Exclude FIN-based client closes on forward traffic.
| where tmpCombined !has "traffic:forward server-fin"  // Exclude FIN-based server closes on forward traffic.
| where tmpCombined !has "traffic:local close"  // Exclude “local” (device-originated) generic close events.
| where tmpCombined !has "traffic:local client-rst"  // Exclude client resets on local traffic.
| where tmpCombined !has "traffic:local timeout"  // Exclude timeouts on local traffic.
| where tmpCombined !has "traffic:local server-rst"  // Exclude server resets on local traffic.
| project-away tmpMsg, tmpAct, tmpCombined  // Drop the temp helper columns so they don’t flow downstream or get stored.
```

<br/>
<br/>

# 🧪 Build our DCR in JSON
Now that we have our DCR-ready KQL filter ready to rock, it still needs a few adjustments in order to fit into a DCR JSON template. Here are things we need to fix:

- Remove all KQL comments: DCR transformations don’t allow // ... comments. Strip every inline/explanatory comment.

- Keep to DCR-safe operators: Your query only uses source, where, extend, iff, isnotempty, tostring, columnifexists, and project-away — all OK for DCR transforms. (Avoid let, coalesce, join, union, etc. when preparing other rules.)

- Don’t create persisted custom columns (unless you add _CF): You only create temporary tmp* helpers and drop them with project-away, so you’re fine. In DCRs, any persisted new column must end with _CF.

- Encode the KQL as a JSON string: In the template, the KQL must be a single JSON string:
    - escape double quotes ```"``` → ```\"```
    - keep line breaks as ```\n``` (or make it one long line)

- Target the right stream/table: Attach the transform to Microsoft-CommonSecurityLog (this query references fields like DeviceVendor, DeviceProduct, Message, Activity that exist there). If you associate this with another stream/table, expect field mismatches even though you used columnifexists.

After taking into account all of the above, here's what your 1-line JSON-ready transform KQL statement should look like: 

```json
"transformKql": "source\n| where DeviceVendor == \"Fortinet\" or DeviceProduct startswith \"Fortigate\"\n| extend tmpMsg = tostring(columnifexists(\"Message\",\"\"))\n| extend tmpAct = tostring(columnifexists(\"Activity\",\"\"))\n| extend tmpCombined = iff(isnotempty(tmpMsg), tmpMsg, tmpAct)\n| where tmpCombined !has \"traffic:forward close\"\n| where tmpCombined !has \"traffic:forward client-rst\"\n| where tmpCombined !has \"traffic:forward server-rst\"\n| where tmpCombined !has \"traffic:forward timeout\"\n| where tmpCombined !has \"traffic:forward cancel\"\n| where tmpCombined !has \"traffic:forward client-fin\"\n| where tmpCombined !has \"traffic:forward server-fin\"\n| where tmpCombined !has \"traffic:local close\"\n| where tmpCombined !has \"traffic:local client-rst\"\n| where tmpCombined !has \"traffic:local timeout\"\n| where tmpCombined !has \"traffic:local server-rst\"\n| project-away tmpMsg, tmpAct, tmpCombined"
```

&#x261D; Let's plug this into our DCR JSON template! 

Take the above line and paste it into the following JSON DCR template for Fortinet via AMA as illustrated below, about 2/3 of the way down, where it says ```"transformKql":```:

```json
// Author: Ian D. Hanley | LinkedIn: /in/ianhanley/ | Twitter: @IanDHanley | Github: https://github.com/EEN421 | Blog: Hanley.cloud / DevSecOpsDad.com
// This KQL filter targets Fortinet/Fortigate logs and removes connection teardown or session-close events (like FINs, resets, and timeouts) at ingestion, ensuring only active or meaningful network traffic is retained for analysis.

{
  // === ROOT LEVEL ===
  // A Data Collection Rule (DCR) defines how data is collected, transformed, and sent to destinations.
  "properties": {

    // A unique immutable identifier automatically generated when the DCR was first created.
    // Not required when creating a new rule — only present for reference or export.
    "immutableId": "dcr-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",

    // === DATA SOURCES SECTION ===
    // Defines the origin of the incoming data that this DCR will process.
    "dataSources": {
      "syslog": [  // This DCR listens for Syslog data (typical for CEF or firewall connectors).
        {
          // Identifies which data stream the syslog input is mapped to.
          // Microsoft-CommonSecurityLog is used by the CEF connector (e.g., Fortinet, Cisco ASA).
          "streams": [
            "Microsoft-CommonSecurityLog"
          ],

          // The syslog facilities that this rule will accept messages from.
          // These correspond to facility codes in RFC 5424 (e.g., auth, daemon, local0, etc.).
          "facilityNames": [
            "alert", "audit", "auth", "authpriv", "cron", "daemon", "clock", "ftp",
            "kern", "local0", "local1", "local2", "local3", "local4", "local5",
            "local6", "local7", "lpr", "mail", "news", "ntp", "syslog", "user", "uucp"
          ],

          // Syslog severity levels this rule will process.
          "logLevels": [
            "Info", "Notice", "Warning", "Error", "Critical", "Alert", "Emergency"
          ],

          // A friendly name used by Azure Monitor to identify this syslog source.
          "name": "sysLogsDataSource-xxxxxxxxxx"
        },
        {
          // Additional syslog configuration (optional secondary source).
          // In this example, it captures a narrow facility/severity combination (e.g., emergency messages).
          "streams": [
            "Microsoft-CommonSecurityLog"
          ],
          "facilityNames": [
            "nopri"
          ],
          "logLevels": [
            "Emergency"
          ],
          "name": "sysLogsDataSource-xxxxxxxxxx"
        }
      ]
    },

    // === DESTINATIONS SECTION ===
    // Defines where the processed data will be sent (in this case, a Log Analytics workspace).
    "destinations": {
      "logAnalytics": [
        {
          // The full Azure Resource ID of the Log Analytics workspace to receive data.
          "workspaceResourceId": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/your-resource-group/providers/Microsoft.OperationalInsights/workspaces/your-workspace-name",
          // The unique workspace ID (GUID).
            "workspaceId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",

          // Logical name used within this DCR to reference the destination.
          "name": "DataCollectionEvent"
        }
      ]
    },

    // === DATA FLOWS SECTION ===
    // This defines how data moves from the source (stream) through an optional transformation
    // to its destination (Log Analytics workspace).
    "dataFlows": [
      {
        // Input stream — the type of data being ingested.
        "streams": [
          "Microsoft-CommonSecurityLog"
        ],

        // The transformKql field applies a KQL query at ingest time.
        // This runs before the data is written to Log Analytics.
        // In this case, it filters out Fortinet connection teardown events
        // to reduce noise and ingestion cost.
       👉 "transformKql": "transformKql": "source\n| where DeviceVendor == \"Fortinet\" or DeviceProduct startswith \"Fortigate\"\n| extend tmpMsg = tostring(columnifexists(\"Message\",\"\"))\n| extend tmpAct = tostring(columnifexists(\"Activity\",\"\"))\n| extend tmpCombined = iff(isnotempty(tmpMsg), tmpMsg, tmpAct)\n| where tmpCombined !has \"traffic:forward close\"\n| where tmpCombined !has \"traffic:forward client-rst\"\n| where tmpCombined !has \"traffic:forward server-rst\"\n| where tmpCombined !has \"traffic:forward timeout\"\n| where tmpCombined !has \"traffic:forward cancel\"\n| where tmpCombined !has \"traffic:forward client-fin\"\n| where tmpCombined !has \"traffic:forward server-fin\"\n| where tmpCombined !has \"traffic:local close\"\n| where tmpCombined !has \"traffic:local client-rst\"\n| where tmpCombined !has \"traffic:local timeout\"\n| where tmpCombined !has \"traffic:local server-rst\"\n| project-away tmpMsg, tmpAct, tmpCombined",

        // Destination reference — must match the logical name under "destinations".
        "destinations": [
          "DataCollectionEvent"
        ]
      }
    ],

    // Provisioning status of the DCR (auto-populated by Azure).
    // Can be omitted when creating or updating.
    "provisioningState": "Succeeded"
  },

  // === METADATA ===
  // Resource ID — present when exported; omit during creation.
  "id": "/subscriptions/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/resourceGroups/your-resource-group/providers/Microsoft.Insights/dataCollectionRules/your-dcr-name",


  // The DCR kind (Linux/Windows) defines agent compatibility.
  "kind": "Linux",

  // The Azure region where the DCR resource is stored.
  "location": "YourTenantLocale",

  // Tags are metadata for organizational or automation purposes.
  "tags": {
    "createdBy": "Sentinel"
  }
}
```

> ⚠️ Remember, JSON doesn't natively support comments, the above snippet is for learning purposes only. [The proper JSON formatted template is available for use here on my Github.](https://github.com/EEN421/Sentinel_Cost_Optimization/blob/Main/Fortinet/Fortinet-DCR-Template.json)

<br/>
<br/>

# 👌 Leverage the DCR Toolkit Workbook to Manage DCRs
First, we need to navigate to the **Sentinel > Content Management > Content Hub** and search for **Data Collection Toolkit**:

![](/assets/img//Fortinet%20DCR/ContentHub_DCRToolkit.png)

<br/>

Once you find and select it, a fly-out will pop from the right hand side with an **Install** button:

![](/assets/img/Fortinet%20DCR/DCRToolkit_Install.png)

<br/>

Now that you've installed it from the Content Hub, you can open it by navigating to **Threat Management > Workbooks > Templates** and searching for **Data Collection Toolkit**. Select the workbook, then click on **View saved workbook**:

![](/assets/img/Fortinet%20DCR/DCRToolkit_Open%20Workbook.png)

<br/>

If you're starting from scratch, you can pretty much copy/paste the template described earlier, preformatted with the network traffic teardown exclusions built-in from [here on my Github](https://github.com/EEN421/Sentinel_Cost_Optimization/blob/Main/Fortinet/Fortinet-DCR-Template.json) to get you started. 

Chances are, though.. if you're reading this far it's because you've already got a DCR in place to collect your Fortinet logs and are concerned about the cost so lets look at how to **Review/Modify** an existing DCR with our transformationKQL for disregarding network teardown traffic for Fortinet firewalls next. 

Select your **Subscription** and **Workspace** from the dropdowns, then select **Review/Modify DCR Rules**:

![](/assets/img/Fortinet%20DCR/DCRToolkit_ModifyDCR.png)

<br/>

This will show you a list of existing DCR rules in play:

![](/assets/img/Fortinet%20DCR/DCRToolkit_ModifyDCRRuleList.png)

<br/>

Select the DCR rule responsible for collecting Fortinet logs, then click on **Modify**:

![](/assets/img/Fortinet%20DCR/ModifyDCR.png)

<br/>

Find the right spot under **dataFlows** to insert your **"transformKql"** JSON statement as described in the commented out JSON example earlier and paste it in, illustrated below:

![](/assets/img/Fortinet%20DCR/DCRToolkit_transformKql%20Statement%20for%20DCR_JSON.png)

> ⚠️ If you are **modifying** and existing DCR that _already has a **transformKql** statement_, you should copy it into chatGPT along with our Fortinet transformKql statement and **merge** them, then paste the result back here as a single **transformKql** statement. Make sure to backup the original **transformKql** statement so you can revert back and **always check with the Detection Engineer that built the DCR if you're unsure!** Lastly, definitely make sure they are at least notified if you make any changes. Your SOC will thank you later &#x1F600;	

<br/>

Next we need to **PUT** the new DCR template to production with the **Deploy Update** button:

![](/assets/img/Fortinet%20DCR/DCRToolkit_Deploy.png)

<br/>

![](/assets/img/Fortinet%20DCR/DCRToolkit_PUT%20succeeded.png)

<br/>

Confirm your deployment:

![](/assets/img/Fortinet%20DCR/DCRToolkit_UpdateDCR_Confirmation.png)

<br/>

And that's it! Now we just wait a few minutes and then query for any of the network teardown traffic we just tuned out and see if our DCR rule did the trick. 

The following KQL query will show you if any of our tuned out traffic has made it to Sentinel in the last 5 minutes:

```bash
CommonSecurityLog
| where TimeGenerated > ago(5m)
| where DeviceVendor == "Fortinet" or DeviceProduct startswith "Fortigate"  
| where Activity contains "close"
```

![](/assets/img/Fortinet%20DCR/Success.png)

<br/>

# 🚀 Deploy the DCR Template via Azure CLI [Optional]

Step 1 - login to Azure CLI and set Subscription: 

```powershell
# Sign in and select your sub
az login
az account set --subscription "<SUBSCRIPTION_NAME_OR_ID>"

# Create or select a resource group (use the SAME region as your LAW!)
az group create -n rg-xdr -l eastus
```

Grab your Log Analytics Workspace and Subscription IDs, and your Sentinel region (Your DCR **must** reside in the same region or destination binding will fail later).

Download the template [here from my Github](https://github.com/EEN421/Sentinel_Cost_Optimization/blob/Main/Fortinet/Fortinet-DCR-Template.json) and upload it to your Azure CLI session.

Run the following command (after you've adjusted the template with your IDs and Region etc.)
```powershell
az deployment group create \
  --resource-group rg-xdr \
  --template-file Fortinet-DCR-Template.json \
  ```

If you're using **AMA on a VM/Arc Forwarder** to collect the logs and send them to Sentinel, you'll also need to **associate the DCR**

```powershell
az monitor data-collection rule association create \
  --name dcr-assoc-fortinet \
  --rule-id "$DCR_ID" \
  --resource "$VM_ID"
```

> ⚠️ Note: The **Association** command is part of the **monitor-control-service extension**; the CLI installs it automatically the first time you call it.

Verify and make sure the DCR and LAW are in the same region [(This is the #1 cause of “destination missing” or silent failures).](https://learn.microsoft.com/en-us/azure/azure-monitor/vm/data-collection?utm_source=chatgpt.com)

After a few minutes, run a quick sanity-check query:

```bash
CommonSecurityLog
| where TimeGenerated > ago(5m)
| where DeviceVendor == "Fortinet" or DeviceProduct startswith "Fortigate"  
| where Activity contains "close"
```

![](/assets/img/Fortinet%20DCR/Success.png)

<br/>
<br/>

# 🧠 Ian's Insights & Key Takeaways for Other Security Teams

Noise reduction isn’t just about saving money — it’s about sharpening focus.
By filtering teardown traffic, we transformed our firewalls from noisy log generators into **high-value security signal providers**.
* **Don’t ingest everything.** More logs ≠ more visibility. Focus on what helps you detect and respond.
* **Teardown ≠ telemetry.** Those events tell you a connection *ended*, not that it was *malicious*.
* **Validate before excluding.** Always test filters with a quick `summarize count()` to ensure no legitimate security logs disappear.
* **Reinvest the savings.** Use your reduced ingestion costs to onboard richer data sources — endpoint, identity, or cloud app telemetry.

That’s the difference between drowning in data and acting on intelligence.

<br/>
<br/>

# 📖 Thanks for Reading!
 &#128161; Want to go deeper into these techniques, get full end-to-end blueprints, scripts, and best practices? Everything you’ve seen here — and much more — is in my new book. Grab your copy now 👉 [Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ).  I hope this was a much fun reading as it was writing! <br/> <br/> - Ian D. 
Hanley • DevSecOps Dad


![](/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg)

<br/>
<br/>

# 🔗 Helpful Links & Refences

- [Supported KQL features in Azure Monitor transformations — the canonical list (note coalesce() is absent; use iif/case/isnotempty instead).](https://learn.microsoft.com/en-us/azure/azure-monitor/data-collection/data-collection-transformations-kql)

- [Create a transformation in Azure Monitor — reiterates that only certain KQL is supported.](https://learn.microsoft.com/en-us/azure/azure-monitor/data-collection/data-collection-transformations-create?utm_source=chatgpt.com&tabs=portal)

- [coalesce() function (Kusto) — valid in general KQL, but not in DCR transforms per the supported list; this is why your Log query worked but the transform didn’t.](https://learn.microsoft.com/en-us/kusto/query/coalesce-function?view=microsoft-fabric)

- [Data collection in Azure Monitor — overview of the data collection process, including DCRs, agents, and pipeline architecture.](https://learn.microsoft.com/en-us/azure/azure-monitor/vm/data-collection)

<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)
