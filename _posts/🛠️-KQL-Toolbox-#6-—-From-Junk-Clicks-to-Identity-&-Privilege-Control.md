🔍 KQL Toolbox #6 — From Junk Clicks to Identity & Privilege Control

Last week in KQL Toolbox #5, we hunted phishing and malware like pros — sender domains, payloads, campaigns, and patterns.

But here’s the truth:

Even the best detections don’t matter if users still click…
and if identity controls aren’t watching what happens next.

So this week, we pivot from threat hunting to risk outcomes:

Who’s clicking junk mail links? (human-risk telemetry)

Who deleted an AD user? (identity tampering)

Who’s activating privileged roles via PIM? (privilege oversight)

Let’s break each query down line-by-line and show how to operationalize them like a real SOC.

1️⃣ Who’s Clicking on Junk Mail?
The Query
let JunkedEmails = EmailEvents
| where DeliveryLocation == "Junk folder"
| distinct NetworkMessageId;
UrlClickEvents
| where NetworkMessageId in(JunkedEmails)

Line-by-line breakdown (what each piece is doing)
let JunkedEmails = EmailEvents

Creates a named variable called JunkedEmails.

EmailEvents is the Microsoft Defender for Office / email telemetry table that tracks delivery and classification outcomes.

✅ Why this matters: Using let makes the query modular, readable, and reusable — you’re building a “set” of message IDs you’ll pivot on.

| where DeliveryLocation == "Junk folder"

Filters the email dataset down to only messages delivered into the Junk folder.

✅ Why this matters: This is the “your filters worked… BUT” moment.
These emails were already treated as suspicious/low-trust — yet people can still interact with them.

| distinct NetworkMessageId;

Extracts only unique message identifiers.

NetworkMessageId is the glue key that lets you correlate the same email across Defender tables (delivery, URL clicks, attachments, post-delivery actions, etc.).

✅ Why this matters: We’re building a clean list of “junk emails” we can match against user click activity.

UrlClickEvents

Switches to the table that records user clicks on URLs from messages.

This is where the rubber meets the road: user behavior.

| where NetworkMessageId in(JunkedEmails)

Filters click events down to only clicks that match the junk email message IDs you captured above.

✅ What you get out of this query:

“Which junked messages were clicked”

And (depending on your tenant’s schema) usually:

who clicked

what URL

when

from which device/IP/browser

This is your “risky click” leaderboard.

What it tells you (in plain English)

Users are clicking links from emails that already landed in Junk.
That’s a human-risk signal and a great leading indicator for phishing exposure.

Regulatory & Framework Mapping

NIST 800-53

AT-2 Awareness Training (target training based on actual risky actions)

SI-4 System Monitoring (monitor suspicious user interaction)

IR-4 Incident Handling (clicks can trigger investigation)

CMMC 2.0

AT.L2-3.2.1 / AT.L2-3.2.2 (security awareness + role-based training)

IR.L2-3.6.1 / IR.L2-3.6.2 (incident handling triggers)

AU.L2-3.3.1 (audit evidence)

CIS v8

Control 14 Security Awareness

Control 9 Email & Browser Protections

Control 8 Audit Log Management

Steps to Operationalize

Enrich it (add who/URL/time columns) and build a “Top Clickers” view.

Set thresholds: e.g., 2+ junk clicks in 7 days = investigation / targeted training.

Automate response:

user notification

password reset / token revoke if high-risk

block URL/domain if repeated

Measure improvement month-over-month (this is how you prove your awareness program works).

Escalate when clicks tie to known bad domains or credential-harvest paths.

2️⃣ Who Deleted an AD User?
The Query
SecurityEvent
| where TimeGenerated > ago (90d)
| where EventID == "4726"
| extend Actor_ = Account
| project-reorder TimeGenerated, Activity, Actor_, TargetAccount, Computer

Line-by-line breakdown
SecurityEvent

Queries Windows Security Event Logs forwarded to Sentinel / Log Analytics.

This is where classic AD audit logging lives (account changes, group membership, logons, etc.).

| where TimeGenerated > ago (90d)

Limits results to the last 90 days.

Keeps costs/performance reasonable and focuses on relevant incidents.

✅ Pro tip: for alerting, you’ll tighten this to 1h/24h. For audits, 30–180 days is common.

| where EventID == "4726"

Filters to Event ID 4726: “A user account was deleted.”

✅ Why this matters: Deleting users is identity destruction.
If attackers can’t keep persistence, sometimes they burn the house down on their way out.

| extend Actor_ = Account

Creates a new column Actor_ from the Account field (the actor who performed the deletion).

✅ Why this matters: explicit naming helps readability and makes it easier to join with other actor-based queries later.

| project-reorder TimeGenerated, Activity, Actor_, TargetAccount, Computer

Keeps only the most important columns and reorders them for analyst-friendly output.

✅ What you get:

When it happened

What happened (Activity)

Who did it (Actor_)

Who got deleted (TargetAccount)

Where it happened (Computer)

What it tells you

Which identities are being deleted, and who is doing it.

This supports:

change control validation

insider threat detection

compromise investigation

audit evidence

Regulatory & Framework Mapping

NIST 800-53

AC-2 Account management

AU-2 / AU-3 / AU-6 audit event definition, content, and review

CMMC 2.0

AC.L2-3.1.1 / AC.L2-3.1.2 access control enforcement

AU.L2-3.3.1 / AU.L2-3.3.3 audit log review

CIS v8

Control 5 Account Management

Control 8 Audit Log Management

Steps to Operationalize

Alert in near-real-time (last 1h/24h) for account deletions.

Escalate immediately if:

the deleted user was privileged

deletion occurred outside approved change window

actor is unusual/new

Correlate with:

group membership changes (4732/4728)

privilege activations (PIM)

suspicious logons (4624/4625 patterns)

Create an audit report for IAM: deletions vs ticket approvals.

Harden: ensure only tightly controlled accounts can delete users.

3️⃣ Who’s Activating Roles via PIM?
The Query
AuditLogs
| where Category == "RoleManagement"
| where ActivityDisplayName == "Add member to role completed (PIM activation)"
| extend Actor = tostring(parse_json(InitiatedBy).user.displayName)
| extend IP = tostring(parse_json(InitiatedBy).user.ipAddress)
| extend Role = tostring(parse_json(TargetResources)[0].displayName)
| extend ActivationTime = TimeGenerated
| project Actor, Role, ActivationTime, IP

Line-by-line breakdown
AuditLogs

Queries Entra ID (Azure AD) audit logs ingested to Sentinel / Log Analytics.

This is where identity governance actions show up: role changes, app consent, group changes, etc.

| where Category == "RoleManagement"

Narrows to role-related events.

✅ Why it matters: keeps your query clean and fast.

| where ActivityDisplayName == "Add member to role completed (PIM activation)"

Filters specifically to the audit event emitted when a user completes a PIM role activation.

✅ Translation: “Who elevated to admin… right now?”

| extend Actor = tostring(parse_json(InitiatedBy).user.displayName)

Parses the JSON blob inside InitiatedBy.

Extracts the initiating user’s display name.

✅ Why it matters: AuditLogs are nested JSON; parsing is how you get clean columns.

| extend IP = tostring(parse_json(InitiatedBy).user.ipAddress)

Pulls the initiator’s IP address.

✅ Why it matters:

verify corporate vs external IP

detect risky geo/IP anomalies

correlate with suspicious sign-ins

| extend Role = tostring(parse_json(TargetResources)[0].displayName)

Extracts the role that was activated (the “target resource”).

Uses index [0] because TargetResources is an array.

✅ Why it matters: Now you can build a “Top Activated Roles” and baseline your privileged access patterns.

| extend ActivationTime = TimeGenerated

Makes the event time explicit and readable.

| project Actor, Role, ActivationTime, IP

Outputs exactly what an auditor and a SOC analyst both care about.

✅ “Who, what, when, where.”

What it tells you

Who is elevating privileges via PIM, what role they activated, and where they came from.

This is your strongest “least privilege is real” evidence.

Regulatory & Framework Mapping

NIST 800-53

AC-2 Account management (privileged assignment activity)

AC-6 Least privilege (JIT elevation)

AU-2 / AU-6 audit and review

CMMC 2.0

AC.L2-3.1.5 least privilege

AC.L2-3.1.6 privileged account management

AU.L2-3.3.1 / AU.L2-3.3.3 auditing and review

CIS v8

Control 6 Access Control Management

Control 5 Account Management

Steps to Operationalize

Daily PIM activation digest to SOC + IAM.

Baseline: normal roles, normal people, normal hours, normal IP ranges.

Alert on anomalies:

rare roles (Global Admin / Privileged Role Admin)

activation outside business hours

unfamiliar IP / risky sign-in correlation

Correlate justification (ticket/approval) for audit defense.

Use it for access reviews: “Why is this role activated so often?”
