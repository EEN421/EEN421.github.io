
*One Azure bill. Three audiences. A reporting pipeline that had to do more than add up the numbers.*

Every month, the same Azure bill lands in front of three different teams.

Finance wants to know whether the numbers reconcile, which P&L line they belong to, and whether we're over budget.

Operations wants to know what grew, what spiked, and what we can turn off.

Internal IT wants to know who owns the spend, what's missing tags, and whether the commitments we've already paid for are actually being used.

Same data. Three different sets of questions.

Azure Cost Management is pretty good at telling you what you spent. But "what did we spend?" isn't necessarily the interesting question.

**Who spent it? Was the increase real? Is that resource actually getting more expensive? And does the recommendation to save money survive even a basic sanity check?**

Those questions take more work.

So I built a monthly reporting pipeline that pulls Azure cost data once, processes it offline, and produces three outputs:

- A self-contained HTML report with interactive views and charts.
- An Excel workbook with the numbers and formulas behind the findings.
- A short email that gives Finance, Operations, and IT the parts they actually care about.

Simple enough.

Except the interesting problems weren't broken API calls, bad arithmetic, or missing data.

They were **correct numbers telling the wrong story.**

And if you've spent any time writing KQL detections, you'll probably recognise that particular failure mode.

## Why Build This When Azure Already Has Cost Management?

Fair question.

Azure Cost Management already has dashboards, budgets, anomaly detection, exports, and cost allocation. And [azure-cost-cli](https://github.com/mivano/azure-cost-cli) makes much of that information available from the command line, including cost comparisons, resource-level breakdowns, and anomaly detection.

Both are useful. I use the CLI in this very pipeline.

But neither, out of the box, answers all the questions my three audiences are asking.

Finance doesn't just want subscription totals. It wants costs mapped to P&L categories, commitment payments reconciled against allocated consumption, and assumptions clearly identified.

Operations doesn't just want a list of cost anomalies. It needs to know whether an increase represents actual growth, an extra calendar day, a billing reversal, or a sustained step change that a rolling baseline has stopped flagging.

IT doesn't just want an untagged percentage. It needs ownership resolved through resource-group fallbacks, AKS-managed resource groups, and inconsistent naming conventions, with genuinely unresolvable costs separated from attribution problems we can fix.

And nobody should be handed a savings figure that double-counts mutually exclusive Advisor recommendations.

That's the gap this pipeline fills.

**Azure provides the cost data and analysis tools. `azure-cost-cli` makes that data accessible and automatable. My pipeline applies our organization's rules, reconciles the competing interpretations, and validates the conclusions before anyone acts on them.**

The result isn't another cost dashboard.

It's one reproducible set of evidence, translated into three different operational decisions, without asking Finance, Operations, and IT to independently figure out what the numbers mean.

### This Isn't My First Attempt at Making Azure Costs Useful

Back in July 2023, I built an [IoT Azure Cost Monitor](https://www.hanley.cloud/2023-07-06-IoT-Azure-Cost-Monitor/) using the Azure Cost Management API, CircuitPython, and an ESP32-powered e-ink display.

The idea was straightforward: get Azure spending information out of the portal and onto a little wireless display I could stick to the fridge.

Three years later, I'm still working with the same underlying cost data, but the problem has changed.

Back then, I wanted to make the numbers visible.

Now I want to make sure the conclusions drawn from those numbers are actually defensible.

It turns out displaying a cost is considerably easier than explaining one.

## Act I: Two Correct Numbers, Two Different Stories

Azure gives you two perfectly legitimate ways of looking at cost.

**Actual cost** tells you when the money was charged. Buy a reservation or savings plan, and the payment appears against the subscription that paid for it.

**Amortized cost** distributes the commitment cost over its term and attributes the benefit to the resources consuming it.

Both are correct.

They just answer different questions.

Imagine a shared-services subscription paying $10,000 per month for a compute savings plan. Most of that discount is actually being consumed by workloads running in two other subscriptions.

Look at actual cost alone and three things happen:

1. Shared services looks $10,000 more expensive.
2. That $10,000 appears to have no resource owner, because a commitment payment isn't a tagged resource.
3. Your growth chart suddenly shows shared services getting $10,000 more expensive every month after the plan begins, compared with the pre-purchase baseline.

Nothing is necessarily wrong with the invoice.

But if someone asks which workloads are consuming the money, the invoice view doesn't give them the answer.

**The invoice tells you when money moved. Allocation tells you where it was used.**

That's why I kept both cost bases.

Actual cost drives invoice reconciliation and budget comparisons. In my environment, the budgets' own spend-to-date figures matched actual cost to the cent.

Amortized cost drives the allocation views: subscription, customer, resource group, owner, and P&L.

And because commitment timing means those two views can differ significantly in any given month, the workbook includes both and explicitly reconciles the difference.

The mistake would have been choosing one number and pretending it answered every question.

Sound familiar?

It's the same problem as treating one telemetry source as the complete story of an attack.

## Act II: Build the Boring Pipeline

The architecture isn't particularly exciting.

That's intentional.

The pipeline collects cost information, saves the raw exports, performs its calculations locally, and generates the finished reports.

The tooling:

- [azure-cost-cli](https://github.com/mivano/azure-cost-cli) for Cost Management queries.
- Azure CLI for Advisor recommendations, resource-group tags, and budgets.
- Python for processing, attribution, reconciliation, and analysis.
- `openpyxl` for the Excel workbook.
- Self-contained HTML with embedded data and inline SVG for the report.

No complicated platform. No reporting service that needs to be kept running.

And critically, **the calculation stage never calls Azure.**

Every raw export is saved before processing begins.

That means I can change an attribution rule, fix a chart, or investigate a suspicious number and regenerate the entire report using exactly the same underlying data.

No drifting values between runs. No API timing differences changing the evidence halfway through an investigation.

### What I collect

For each subscription, I pull:

| Dataset | Purpose |
|---|---|
| Daily amortized cost by resource group | Trends, growth, anomalies |
| Daily cost by pricing model, actual and amortized | Invoice reconciliation and commitment analysis |
| Monthly amortized cost by resource, including tags | Attribution and service breakdowns |
| Advisor cost recommendations | Optimization opportunities |
| Resource-group tags | Attribution fallback |
| Azure budgets | Budget comparisons |

One of the more useful discoveries was the pricing-model dimension.

On actual cost, the `SavingsPlan` bucket represents the commitment payment.

On amortized cost, that bucket represents usage receiving savings plan pricing, attributed across subscriptions.

That's useful because I can identify where the discounted usage is occurring without requiring billing-account-level access.

I initially tried grouping by charge type. The API rejected that grouping for these subscriptions.

Pricing model turned out to be a better fit anyway.

Sometimes the workaround is actually the better design.

## Act III: Every Dollar Needs an Owner

This is where the reporting becomes useful.

And where it becomes very easy to produce misleading numbers.

If a resource doesn't have an owner tag, does that mean its cost is genuinely unattributed?

Not necessarily.

It might inherit ownership from its resource group.

It might be an AKS node resource group automatically created by Azure.

Or the resource group might have been deleted before the report ran.

If you treat all three as "untagged," your report is technically reflecting missing metadata, but it's hiding important context.

So I use a consistent attribution chain:

1. Read the tag directly from the resource.
2. If it's missing, check the resource group.
3. If it's an AKS node resource group, resolve the parent cluster's resource group and check there.

That third step matters.

AKS creates managed node resource groups following a pattern such as:

`MC_<group>_<cluster>_<region>`

Those groups don't necessarily carry the ownership tags present on the cluster's original resource group.

In my data, a substantial proportion of the month's spending sat in AKS node groups.

Without that fallback, the dashboard would have reported a much bigger ownership problem than actually existed.

The numbers would still have added up.

The interpretation would have been wrong.

### Tags aren't as clean as diagrams suggest

There were a few other things worth handling.

**Multiple customer identifiers.** Some teams use `customer`; others use a billing code. I use configurable tag preferences instead of assuming everyone follows the same convention.

**Aliases.** `devops`, `DevOps`, and `dev-ops team` probably refer to the same owner. That's a normalization rule, not three distinct departments.

**Typos.** A tag such as `example.securtity` might be an accidental variation of a legitimate owner. I flag near matches without automatically deciding which value is correct.

**Deleted resource groups.** Historical cost can reference a resource group that no longer exists. The tag lookup fails, but that doesn't prove the resource was untagged when the charge occurred.

**Spend without a conventional resource group.** Azure DevOps and GitHub-related charges can appear without the normal resource-group metadata. That's not a problem you fix by telling engineers to tag their VMs.

These distinctions matter.

**Untagged spend isn't just a percentage. It's a collection of different problems that happen to share a label.**

Once attribution is in place, the report can also estimate customer cost to serve.

That means combining the customer's directly attributed cost-of-revenue spending with a proportional share of shared or unattributed costs.

But it's an estimate, and the report says so.

If a third of the allocation pool is untagged, that uncertainty belongs alongside the cost-to-serve figure.

Not buried in documentation nobody reads.

## Act IV: The Growth That Wasn't Growth

This was probably the most interesting part of the build.

I started looking at month-over-month growth and unusual spending patterns.

The numbers looked reasonable.

Some of the conclusions weren't.

### A refund masquerading as two anomalies

Imagine a large charge appearing against a resource group in one month.

A few months later, an equal credit appears against the same group.

That's one billing reversal.

But an ordinary trend chart sees two unrelated events: a spike in the first month and a dramatic cost reduction in the second.

Now every growth comparison around those months is distorted.

I added logic to pair exact reversals and exclude both sides from like-for-like trend analysis.

The report still shows the actual billed numbers, of course. Finance needs those.

But it also shows the adjusted trend so Operations isn't investigating an increase that never represented a sustained change in consumption.

Partial refunds remain visible and annotated rather than being silently normalized away.

On the first run, the raw month-over-month increase looked significant.

After adjusting for reversals, the increase was only a few percent.

Problem solved?

Not quite.

### A 31-day month is longer than a 30-day month

Some of that remaining increase came from the calendar.

Compare two otherwise identical workloads running for 30 and 31 days.

One month will cost more.

That isn't evidence of expanding infrastructure.

It's evidence that time passed.

So the report shows the per-day change alongside the month-over-month total.

For much of the spending I was examining, most of the apparent growth disappeared once I normalized by day.

Again, the original numbers were correct.

The comparison was misleading.

### The baseline that learned to ignore the problem

For unusual daily spending, my initial rule was straightforward.

Compare a day's cost against the median of the previous 28 days. If it exceeds twice that median and clears a minimum dollar threshold, flag it.

That works for short-lived spikes.

Then I hit a database whose daily cost had roughly quadrupled and stayed there.

My detection found three spikes.

Three.

Not a sustained fourfold increase.

Why?

Because the rolling median eventually caught up with the new spending level.

Once the higher costs entered the baseline, the higher costs became normal.

**A rolling baseline will eventually normalize anything. Including the problem you're supposed to detect.**

That should sound familiar to anyone building behavioral detections.

A legitimate anomaly can disappear from view simply because the detector adapts to it.

The fix was to distinguish temporary spikes from sustained step changes.

If spending remains elevated at month end, the pipeline walks backward to identify where the sustained increase began and reports the change along with its monthly financial impact.

It also compares longer-term growth using the average of the final three months against the first three months of the year, alongside the most recent month-over-month movement.

That last part matters.

A resource group can be one of the year's fastest-growing expenses while already trending downward.

Both facts belong in the report.

## Act V: The Budget That Wasn't a Budget

Azure budgets seemed straightforward.

Read the budgets, compare them with actual cost, report the variance.

Except some subscriptions had multiple active budgets.

And not every object called a budget was actually being used as a budget.

I encountered three cases.

**Multiple active budgets.** One subscription had more than one. Choosing the wrong one made the subscription appear several times over budget when it wasn't.

The pipeline now selects the primary budget through configuration and shows additional budgets separately.

**Budgets used as alerting mechanisms.** Some had thresholds set at several hundred percent of their stated amounts.

Those weren't meaningful financial plans. They were essentially spend-alert mechanisms.

I excluded budgets whose alert thresholds only began at 200% or higher from the primary budget comparison.

**Commitment payments distorting subscription budgets.** The subscription purchasing the savings plan appeared significantly over budget on actual cost.

So I show both the actual budget percentage and what that percentage would look like without the commitment payment.

That doesn't mean changing the accounting.

It means explaining the variance.

I also pull the current month's budget spend-to-date into the summary email.

Because knowing that a subscription is already over budget before the month is halfway through is a lot more actionable than discovering the problem in next month's report.

## Act VI: Azure Advisor Isn't a Savings Forecast

Azure Advisor offers useful optimization recommendations.

But there's a fairly important distinction between a list of potential actions and a defensible estimate of realized savings.

I discovered that the hard way.

### Double-counting savings

Advisor might recommend a compute savings plan and VM reservations against overlapping usage.

Or a database savings plan and Cosmos DB reservations.

Individually, those recommendations may be legitimate alternatives.

But you cannot simply add every projected saving together.

That would be like counting two mutually exclusive cost reductions as if you could receive both.

In my data, summing all the recommendations inflated the potential savings headline by more than a third.

For each subscription, I take the larger projected saving from each overlapping commitment pair, then add recommendations that don't overlap.

It's still an estimate.

But at least it isn't built on obvious double-counting.

### Savings greater than the current cost

Another interesting case: a recommendation projecting $3,000 in annual savings for a resource costing roughly $1,500 a year at the previous month's run rate.

Those are illustrative numbers, but the underlying problem was real.

The recommendation might reflect changing utilization, pricing assumptions, or a different measurement period.

It isn't automatically impossible.

It also isn't something I'd put into a CFO-facing headline without qualification.

So I calculate each resource's annualized current cost and show it alongside the recommendation.

I also produce a capped savings total in addition to Advisor's original projection.

### Recommendations for resources that no longer exist

Some Advisor recommendations pointed to disks in resource groups that had already been deleted.

Technically valid recommendation records.

Operationally useless actions.

The pipeline checks that the resource group still exists before counting the projected savings.

It also classifies recommendations by the actual action rather than loosely grouping different optimization types together.

**Advisor produces recommendations. It doesn't guarantee outcomes.**

Or, put another way: a potential saving isn't a saving until the action is feasible, non-overlapping, and actually implemented.

## Act VII: Three Outputs, One Set of Evidence

Once the calculations are done, the data needs to be useful to people who don't want to dig through Azure exports.

That's why I separated the outputs.

### The HTML report

It's one self-contained HTML file with embedded data and inline SVG charts.

No external data requests are required to render it; fonts are the only external dependency.

You can attach it to an email, place it on a file share, or open it locally.

Every chart also has a table view, because eventually someone in Finance is going to want to copy the numbers into Excel.

### The Excel workbook

The workbook contains the underlying figures and formulas.

There's an easily missed problem with generating Excel files using `openpyxl`: the library writes formulas but doesn't calculate their results.

That means a workbook can contain perfectly valid formulas while showing empty totals in Outlook or mobile previews.

I added a scripted Excel open-and-save step to populate the cached values.

Small detail.

Massive difference when someone forwards the workbook to an executive who only sees a preview.

### The email

The email is deliberately short.

Three lines of summary, followed by spending, budget position, P&L allocation, optimization opportunities, and open questions.

Everything else stays in the attached report.

I also built a copy-friendly HTML version for Outlook. The subject and instructions are displayed in a non-selectable area, so selecting and copying the content picks up just the email body.

And where something requires Finance's judgment, I don't pretend the pipeline has decided it.

If a subscription's P&L classification hasn't been agreed upon, it goes into a **To confirm with Finance** section.

A reporting pipeline can calculate allocation based on configured rules.

It shouldn't quietly invent accounting policy.

## Act VIII: The Report Passed Every Check. So I Attacked the Claims.

This was the part that changed how I looked at the whole exercise.

After the report was working, I built an independent validation process.

Not another function calling the same calculation routines.

A separate recomputation that reads the original raw exports and shares no calculation code with the report builder.

It independently calculates daily costs, monthly totals, resource-group spending, ownership allocation, customers, services, budgets, and anomalies.

Thousands of checks.

Everything matched.

I even checked the charts themselves, comparing rendered bar lengths with their corresponding values.

The arithmetic was correct.

But that wasn't enough.

I asked a reviewer with no involvement in the build to challenge the report's claims against the raw evidence.

Then a second reviewer independently examined it without seeing the first reviewer's findings.

They uncovered the important problems.

Not arithmetic errors.

**Interpretation errors.**

- A subscription was compared against the wrong active budget.
- Customer spending was misattributed because an alternative tag wasn't being considered.
- Overlapping commitment recommendations were counted together.
- A sustained spending increase was described as a handful of isolated spikes.
- A month-over-month increase largely reflected the number of days in the month.
- Stale Advisor recommendations were counted toward potential savings.
- A billing reversal was handled differently in the report and workbook, creating disagreement between the two outputs.

Every one of those findings could have survived a calculation-only validation.

Because the numbers being calculated weren't necessarily wrong.

**The claims attached to those numbers were wrong.**

This is exactly the problem I keep coming back to in detection engineering.

A KQL query can execute successfully, return the expected columns, and produce perfectly valid results while still failing to identify the behavior it was designed to detect.

A cost report can reconcile to the cent and still incorrectly tell someone that a subscription is over budget, that an application is growing, or that a particular team owns a charge.

In both cases, the failure isn't necessarily in the computation.

It's in the assumptions connecting the evidence to the conclusion.

And validating the computation doesn't validate those assumptions.

## What I'd Do Again

If I were building another one of these tomorrow, I'd keep a few rules from the outset.

**1. Preserve both cost bases.** Actual and amortized cost answer different questions. Don't silently substitute one for the other.

**2. Keep the raw evidence.** Pull once, save everything, and make the entire reporting process repeatable without another Azure query.

**3. Treat attribution as an engineering problem.** Resource tags, resource-group fallbacks, AKS node groups, aliases, and deleted resources all need explicit handling.

**4. Challenge every comparison.** Account for reversals, calendar differences, and sustained step changes before describing something as growth or an anomaly.

**5. Don't confuse configured budgets with financial intent.** Multiple budgets and alert-only configurations need to be identified rather than silently accepted.

**6. Don't add mutually exclusive savings recommendations.** Advisor is an input to optimization, not a guaranteed savings forecast.

**7. Make uncertainty visible.** Unattributed spend, estimated customer allocation, and unresolved P&L classifications should be clearly identified.

**8. Validate the interpretation independently.** Recalculate everything, then ask someone to attack the conclusions using the original evidence.

None of this required an expensive FinOps platform.

Python, Azure CLI, some straightforward reporting code, and the willingness to question your own output went a long way.

The hardest part wasn't getting the numbers out of Azure.

It was making sure those numbers supported the story we were telling.

## The Query Ran Successfully. The Numbers Reconciled. So What?

That's the lesson I took away from building this.

For detection engineers, a successful query isn't proof of a successful detection.

For cloud engineers, a reconciled report isn't proof of an accurate explanation.

For Finance, a correct invoice isn't necessarily an accurate picture of where the costs belong.

All three disciplines run into the same fundamental problem:

**Correct evidence doesn't automatically produce a correct conclusion.**

You have to validate the assumptions in between.

And that's where the interesting engineering starts.

---

*I write about cybersecurity, detection engineering, KQL, cloud infrastructure, and the occasional problem that turns out to be more interesting than it looked. You can find more at [DevSecOpsDad.com](https://devsecopsdad.com) and [DevSecOpsDadAttack.com](https://devsecopsdadattack.com).*
