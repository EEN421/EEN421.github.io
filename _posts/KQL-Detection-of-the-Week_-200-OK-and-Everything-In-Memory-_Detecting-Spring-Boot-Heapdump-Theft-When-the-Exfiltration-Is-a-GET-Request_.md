---
layout: post
title: "KQL Detection of the Week: 200 OK, and Everything In Memory — Detecting Spring Boot Heapdump Theft When the Exfiltration Is a GET Request"
subtitle: "Threat intelligence translated into detection engineering action."
date: 2026-08-03
author: DevSecOpsDad
tags:
  - detection-engineering
  - kql
  - Spring Boot
  - actuator
  - heapdump
  - Java
  - ASIM
  - CommonSecurityLog
  - T1190
  - T1552
---

![DevSecOpsDadAttack!](/assets/img/HeapOfTrouble/NinjaCat.png)

There is an HTTP endpoint somewhere in your estate that will hand a stranger every string your application has ever touched. Database passwords. JWT signing keys. Session tokens. The API key for the payment processor. It returns them in a single response, over TLS, with a `200`, in about four seconds.

It is not a vulnerability. It is a **feature**, it is documented, Spring ships it, and your platform team probably turned it on during an incident in 2023 and never turned it back off.

Last week the attacker's trick was that they brought no infrastructure — the C2 was a calendar, the encryptor was `manage-bde.exe`, every artifact belonged to you. This week they went one step further and brought no *technique*. There is no exploit here. There is no payload, no shellcode, no injection, no bypass. There is a GET request, and the response is the crown jewels. The adversary didn't break in. **They asked, and the application said yes.**

That thread ran through nearly all seven of this week's briefs and their **28 KQL candidates** — 5 production, 10 hunting-only, 13 needing environment mapping — a Check Point SmartConsole auth bypass (CVE-2026-16232) carried over from last week and running Monday into Wednesday, AutoIT process injection into remote process memory, a TeamCity RCE (CVE-2026-63077) whose *second* detection was about credential files on disk, a vCenter directory-service authentication bypass (CVE-2026-59309) and its syslog directory traversal sibling (CVE-2026-59310), an SSH bot doing hardware reconnaissance before deploying a miner, OctLurk/SilkLurk running network scans while touching LSASS, the Rails Active Storage arbitrary file read the researchers called KindaRails2Shell (CVE-2026-66066), XCSSET writing into Xcode projects, and Midnight Blizzard signing in with credentials it already had.

Count the ones where the adversary's core move was **reading something they were technically permitted to read**: the heapdump, the TeamCity credential files, the Rails file read, LSASS, the Xcode projects, the vCenter directory, the Midnight Blizzard sign-in. That's most of the week.

But the one worth four thousand words is the Spring Boot heapdump, because it is the purest form of the problem and because **all four of the briefs' heapdump detections would have missed the traffic the source report actually documented.** Not through bad engineering — through one string.

So this week's KQL of the Week is heapdump exfiltration, in three queries and five corrections. Act I hunts the **request**, from the web tier, and the fight there is over a number that most connectors don't populate. Act II hunts the **host**, and turns out to be the stronger query, because Spring leaves a file behind whose name tells you an HTTP request happened even when your web logs don't. The honorable mention stops hunting the attacker altogether and hunts **your own exposure**, which is the only finite population in this whole article.

<br/>

---

<br/>

## 🥇 Act I: The Response Is the Payload

![Act I](/assets/img/HeapOfTrouble/ACT_I.png)

Here's the problem the winning query solves.

On July 27, [SANS ISC published a diary on active scanning for Spring Boot heapdump endpoints](https://isc.sans.edu/diary/33188). The mechanic is about as simple as intrusion gets. Spring Boot Actuator exposes a management endpoint that, when called, triggers a full JVM heap dump and streams it back as the HTTP response body. On HotSpot that's an HPROF file; on OpenJ9 it's PHD. Either way it is a byte-for-byte image of everything live in the process: every object, every field, every `String` — which in a real application means the contents of your `HikariConfig`, your OAuth client secrets, your signing keys, and every session token currently in flight.

The briefs picked it up Monday and Tuesday and produced four detection candidates from it: endpoint access from any source, successful retrieval by an external IP, external scanning, and heapdump file creation on the application host. Two of those are good ideas. All four have the same defect.

**Every one of them hardcodes the literal path `/actuator/heapdump`.**

Read the ISC diary again. The requests Johannes Ullrich actually captured were not to `/actuator/heapdump`. They were to **`/admin-api/actuator/heapdump`**, and the diary explains why: the management base path is configuration, set with `management.endpoints.web.base-path`, and moving it off the default is a normal — arguably *recommended* — thing to do. The attacker in that capture also sent `Authorization: Basic YWRtaW46YWRtaW4=`, which is `admin:admin`, because they assumed the endpoint would be behind authentication and just bet on the password.

So the detections derived from that report would not have fired on the traffic in that report. The source article contains the counterexample to the queries built from it, three paragraphs above where the queries got their idea. That is not a subtle failure and it is not a tuning problem — it is a **string that was mistaken for a protocol**.

Here is the distinction that fixes it, and it's the whole detection. In Spring Boot, the **base path is configurable and the endpoint ID is not.** `heapdump`, `env`, `configprops`, `beans`, `threaddump`, `mappings`, `loggers` — those are the endpoint identifiers, and they appear as the final path segment regardless of where the management surface is mounted. `management.endpoints.web.path-mapping.*` can rename an individual endpoint, but almost nobody does, and the ones who do are not the ones with an exposed heapdump.

Match the endpoint. Never match the path.

<br/>

### The KQL

```kql
let lookback = 7d;
// Endpoint IDs are fixed by Spring. The BASE PATH is not -- the ISC capture shows
// /admin-api/actuator/heapdump, and management.endpoints.web.base-path can move it
// anywhere. Anything that hardcodes "/actuator/heapdump" is matching a default,
// not a protocol.
let ActuatorEndpoints = dynamic([
    "heapdump","env","configprops","beans","threaddump","mappings",
    "loggers","httpexchanges","httptrace","auditevents","jolokia","dump","trace"
]);
// Endpoints that leak secrets directly rather than structure. Used for RANKING,
// not for filtering -- a 200 on /beans is still an exposed management surface.
let SecretBearing   = dynamic(["heapdump","env","configprops","jolokia","dump"]);
// Prefilter terms MUST be the endpoint list itself, not a trimmed "cheap" subset.
// Trimming this narrows the detection silently. See the encoding caveat below.
let PrefilterTerms  = dynamic([
    "actuator","heapdump","env","configprops","beans","threaddump","mappings",
    "loggers","httpexchanges","httptrace","auditevents","jolokia"
]);
// A ranking hint, NOT a gate. Nothing is discarded for being under it.
let ServedFloorBytes = 1048576;
_Im_WebSession(starttime=ago(lookback), url_has_any=PrefilterTerms)
// --- Path normalization. Decode FIRST: an encoded slash is a slash to the server
// and is not a slash to split(). Then strip scheme+authority (HTTPSession events
// carry them, WebServerSession events don't), then query, fragment, matrix params.
| extend UrlLower = tolower(url_decode(tostring(Url)))
| extend PathOnly = trim_start(@"[a-z][a-z0-9+.\-]*://[^/]*", UrlLower)
| extend PathOnly = tostring(split(PathOnly, "?")[0])
| extend PathOnly = tostring(split(PathOnly, "#")[0])
| extend PathOnly = tostring(split(PathOnly, ";")[0])
// Collapse //, then drop trailing slashes, so /actuator//heapdump/ and
// /actuator/heapdump are the same request -- because to Spring, they are.
| extend NormPath = trim_end(@"/+", replace_regex(PathOnly, @"/{2,}", "/"))
| extend Segments = split(NormPath, "/")
| extend Endpoint = tostring(Segments[array_length(Segments) - 1])
// THE authoritative test: exact equality against a parsed path SEGMENT.
// Not `Url has "heapdump"` -- that is a question about a term appearing somewhere,
// which is a different question and answers yes to /docs/heapdump-howto.html.
| where Endpoint in (ActuatorEndpoints)
// --- Result. EventResultDetails is the HTTP status code; HttpStatusCode is an alias.
// toint() returns null when a parser wrote a word instead of a number, so EventResult
// (Success == status < 400) is the documented fallback, not a guess.
| extend StatusCode = toint(EventResultDetails)
| extend Answered = (StatusCode == 200)
             or (isnull(StatusCode) and tostring(EventResult) =~ "Success")
// --- Size. DstBytes is defined as bytes from the destination to the source, so on a
// web session it is the RESPONSE. HttpResponseBodyBytes is more precise and arrived in
// schema 0.2.7, so it may not exist in your parser at all -- column_ifexists, not
// coalesce, because coalesce on an absent column is a semantic error, not a null.
| extend RespBytes = coalesce(
             column_ifexists("HttpResponseBodyBytes", long(null)),
             column_ifexists("DstBytes", long(null)))
// Three states, not two. "No byte count" is NOT "small response" -- see the bonus.
| extend SizeVerdict = case(
      isnull(RespBytes),                "Unknown",
      RespBytes == 0,                   "Unknown",     // most parsers write 0 for absent
      RespBytes >= ServedFloorBytes,    "LargeBody",
                                        "SmallBody")
// Resolve optional columns ONCE, up here. column_ifexists() inside a summarize
// aggregate is asking a schema question in a place that should only see values.
| extend
    Client      = tostring(SrcIpAddr),
    ForwardedFor= tostring(column_ifexists("HttpRequestXff", "")),
    UserAgent   = tostring(column_ifexists("HttpUserAgent", "")),
    Service     = coalesce(tostring(column_ifexists("HttpHost","")),
                           tostring(column_ifexists("DstFQDN","")),
                           tostring(DstIpAddr)),
    Secretive   = Endpoint in (SecretBearing)
// Entity = the CLIENT. The service is an attribute here; it becomes the entity in the
// honorable mention, because "who took it" and "what of mine answers" are two questions.
| summarize
    Requests        = count(),
    AnsweredHits    = countif(Answered),
    SecretHits      = countif(Answered and Secretive),
    LargeBodyHits   = countif(Answered and SizeVerdict == "LargeBody"),
    UnknownSizeHits = countif(Answered and SizeVerdict == "Unknown"),
    MaxRespBytes    = max(RespBytes),
    Endpoints       = make_set(Endpoint, 15),
    Services        = make_set(Service, 10),
    Paths           = make_set(NormPath, 10),
    Statuses        = make_set(EventResultDetails, 10),
    UserAgents      = make_set(UserAgent, 5),
    Methods         = make_set(HttpRequestMethod, 5),
    Xff             = make_set_if(ForwardedFor, isnotempty(ForwardedFor), 5),
    Sources         = make_set(EventProduct, 5),
    ActiveDays      = dcount(bin(TimeGenerated, 1d)),
    FirstSeen       = min(TimeGenerated),
    LastSeen        = max(TimeGenerated)
    by Client
| extend
    DistinctEndpoints = array_length(Endpoints),
    Enumerating       = array_length(Endpoints) > 2,
    ProbablyInternal  = ipv4_is_private(Client),
    MaxRespReadable   = format_bytes(coalesce(MaxRespBytes, long(0)))
// Ranking, in order of what actually changes your afternoon:
//   1. a secret-bearing endpoint answered at all
//   2. it answered with a body big enough to be a real dump
//   3. it answered and we CANNOT TELL how big -- an unknown outranks a small body
//   4. breadth of enumeration
// Raw request volume is deliberately last. One successful GET is the whole incident;
// ten thousand 404s are Tuesday.
| order by SecretHits desc, LargeBodyHits desc, UnknownSizeHits desc,
           DistinctEndpoints desc, AnsweredHits desc
```

<br/>

### The line that does the work

```kql
| where Endpoint in (ActuatorEndpoints)
```

Four words, and they're the difference between a detection and a decoration.

Note what this **isn't**. It isn't `Url has "/actuator/heapdump"`, which is what all four brief candidates do in one spelling or another. That predicate asserts a full path, and a full path is a *default value* — the one thing about this endpoint that the operator of the application controls freely and that the attacker doesn't need to touch. It also isn't `Url has "heapdump"`, which looks like the safe broadening but quietly changes the question: `has` tests whether a **term** appears anywhere in the value, so it returns true for `/docs/heapdump-analysis.html`, for a referrer, for a query string parameter named `heapdump`, and for a WAF rule name that got logged into the URL field. Presence is not position, and a detection that can't tell the difference between "the client requested the heapdump endpoint" and "the string heapdump occurred in this record" will be tuned into silence within a week by an analyst who is, correctly, sick of it.

What the query does instead is parse the URL into segments and compare a **segment** for exact equality. That's the same discipline as splitting a hostname into DNS labels rather than pattern-matching the dots: if your data is structured, compare it as structured data. `/admin-api/actuator/heapdump` has a final segment of `heapdump`. So does `/actuator/heapdump`, `/mgmt/heapdump`, `/internal/ops/actuator/heapdump`, and whatever your platform team invented in 2023. All four match. `/docs/heapdump-analysis.html` doesn't, because its final segment is `heapdump-analysis.html`, and equality knows that and `has` doesn't.

The normalization above it is doing real work too, and each line is there because a real evasion exists for it:

- `url_decode()` **first**, because `%2factuator%2fheapdump` is a legitimate request to the server and an unparseable string to `split()`. Decode, then split — never the reverse. The cost of decoding first is that a legitimately encoded slash inside a segment gets over-split, which broadens the match. This is a positive selector, so breadth is free here; it would not be free in a suppression filter.
- Collapsing `/{2,}` and trimming trailing slashes, because `//actuator//heapdump/` reaches the same handler and is a different string.
- Cutting at `;`, because `/actuator/heapdump;.js` is a path-parameter trick that survives a lot of naive WAF rules and reaches Spring intact.

And the second half of the section, which is the part I'd put on a wall.

<br/>

### Three states, because "I don't know" is not "no"

Tuesday's Detection 3 is the best idea in the briefs this week. It is trying to separate a **scan** from a **breach** by asking whether the response was large enough to have been a real heap dump. That is exactly right — the request tells you nothing, since the internet requests this path continuously and always will; the *answer* is the incident. Here is the query it shipped:

```kql
| where EventOutcome startswith "200"
| where isnotempty(BytesReceived)
| where tolong(BytesReceived) > 1048576
```

Three lines, four problems, and they fail in three different directions.

**`BytesReceived` is not a column in `CommonSecurityLog`.** The columns are `ReceivedBytes` and `SentBytes`, mapped from the CEF `in` and `out` keys respectively. The brief's own caveat says that if the connector doesn't populate the field, `tolong(BytesReceived)` evaluates to null and the filter silently drops all rows. That's the wrong failure mode for the right field: a reference to a column that doesn't exist in the schema isn't a null, it's a **semantic error**, and the query doesn't return zero rows — it doesn't run. Which is, honestly, the *lucky* outcome. A query that won't compile gets fixed on the day someone tries it. Everything else in this list gets discovered a quarter later.

**Even spelled correctly, the direction is a coin flip.** Microsoft documents `in` → `ReceivedBytes` as "number of bytes transferred inbound" and `out` → `SentBytes` as "number of bytes transferred outbound". Inbound and outbound *relative to what* is not specified, because it can't be — it depends on whether the reporting device considers the client or the server to be the source, which varies by vendor and sometimes by log type within one vendor. For a GET request the two numbers are wildly asymmetric: the request is a few hundred bytes and the response is a few hundred megabytes. Pick the wrong one and your "was it served" gate is reading the size of the request, which is small for a successful theft and small for a blocked scan and therefore tells you nothing at all. There is no way to resolve this from the schema. You resolve it by downloading something large through the device and reading which column moved.

**`EventOutcome` is documented as `success` or `failure`**, not as an HTTP status code. Some CEF sources do put the status code there; plenty write a word, and some write `200 OK`. `startswith "200"` handles the last case and fails the first, and also matches `2000` and `200000` if a source ever writes a byte count into an outcome field, which is the kind of thing that happens exactly once and takes a day to find.

**And `isnotempty()` deletes the finding.** This is the one that matters, and it survives every other fix in this list.

Walk the logic. `isnotempty(BytesReceived)` discards every record where the connector didn't emit a byte count. In an environment where the connector emits byte counts, that clause does nothing. In an environment where it doesn't, that clause discards **the entire population**, and the query returns clean. So the filter is a no-op in the environments that don't need it and a total blackout in the environments that do. It cannot help. It can only hide.

And the reasoning behind it is the interesting part, because it's the reasoning everybody uses. The engineer wrote `isnotempty()` to be *careful* — to avoid comparing against a null. But look at what the guard actually encodes. A missing byte count means **we do not know whether the heap dump was served**. And on this endpoint, "we don't know whether the crown jewels left the building" is not a low-signal event to be filtered away. It is the second-highest-priority row in the result set, behind only a confirmed large response, and ahead of every confirmed *small* one.

Two states — matched, not matched — cannot express that. So the query above uses three:

```kql
| extend SizeVerdict = case(
      isnull(RespBytes),             "Unknown",
      RespBytes == 0,                "Unknown",
      RespBytes >= ServedFloorBytes, "LargeBody",
                                     "SmallBody")
```

and then ranks `LargeBodyHits`, then `UnknownSizeHits`, then everything else. Nothing is discarded for being unmeasurable. The unmeasurable rows are *promoted*, and the analyst is told which ones they are, which means the first time this rule fires in an environment with no byte counts, someone finds out that the environment has no byte counts. That is a better outcome than a clean dashboard.

The `RespBytes == 0` line is a judgement call and I want it visible rather than buried. My reading is that most parsers write `0` rather than null when the source didn't report a size, which makes treating a literal zero as "unknown" the safer default — but that is a generalization about parser behaviour, not something the schema promises, and it is the single assumption in this query I'd most want you to check rather than inherit. There's a validation query for it in *Keeping it honest* below. The cost of being wrong in my direction is that you can't detect a genuinely empty response body, which nobody needs. The cost of being wrong in the other direction is that every unmeasured response gets filed as `SmallBody` and ranks last, which is the whole failure this section exists to argue against.

The floor itself — 1 MiB — is fine, and it's fine for a reason worth naming, because thresholds in this article are otherwise treated as suspect. It is not separating "big" from "small" traffic in some baselined sense. It's separating **a heap dump from an error page**. A JVM heap for a real Spring application starts in the tens of megabytes and routinely runs into the hundreds; a `404`, a WAF block page, a JSON error body, and a redirect are all under 100 KB. There is roughly three orders of magnitude of empty space between those two populations, and a threshold placed in the middle of a three-order-of-magnitude gap is not a tuning parameter, it's a type check. The threshold you should be suspicious of is the one placed inside a distribution, not the one placed in a hole.

<br/>

### A KQL note: `column_ifexists()` and the difference between absent and empty

Act I references three columns that may not exist in your workspace at all — `HttpResponseBodyBytes` (added in Web Session schema 0.2.7 and Optional even there), `HttpRequestXff`, and `HttpUserAgent`. That is a different problem from a column that exists and is null, and it needs a different tool.

```kql
// Wrong: if the column is absent, this is a semantic error and the query won't run.
| extend RespBytes = coalesce(HttpResponseBodyBytes, DstBytes)

// Right: resolve the column reference at query time, with a typed default.
| extend RespBytes = coalesce(
             column_ifexists("HttpResponseBodyBytes", long(null)),
             column_ifexists("DstBytes", long(null)))
```

`coalesce()` handles *values*. `column_ifexists()` handles *schemas*. They are not interchangeable and the failure modes are opposite: a value problem gives you a wrong answer, a schema problem gives you no answer. Note the typed default — `long(null)` and not `0`, and not `""`. A default of `0` would turn "this schema has no byte counts" into "every response was zero bytes long", which is the `isnotempty()` mistake wearing a different hat: an unknown laundered into a measurement. Type it to match the column you're substituting for, and let it stay null so that the `case` above can see it.

This matters beyond ASIM. Any query that has to run across multiple workspaces, or across a connector migration, or against a table Microsoft is still adding columns to, is a query that should be reaching for `column_ifexists()` rather than assuming.

<br/>

### Keeping it honest

The briefs filed all three web-tier candidates as **requires environment mapping**, and that's the correct call — for a reason none of them names, which is that the mapping isn't optional, it's the detection.

- **`_Im_WebSession` returns nothing at all if you have no Web Session parsers deployed, and it returns it silently.** The unifying ASIM parsers are a union over the source-specific parsers you've actually enabled. Zero enabled parsers is a valid, empty union. Run this before anything else: `_Im_WebSession(starttime=ago(1d)) | summarize Events = count() by EventVendor, EventProduct, EventType | order by Events desc`. If that comes back empty, you have a parser deployment task, not a detection task — and finding that out in ninety seconds is worth more than the rest of this section.
- **`EventType` changes what the other fields mean.** `HTTPSession` events come from a proxy or web gateway that terminated the client connection: they carry full URLs with scheme and host, and they usually carry byte counts. `WebServerSession` and `ApiRequest` events come from the server or application itself: the docs are explicit that these "typically have less network related information", the URL is path-and-parameters only, and `DstBytes` is frequently absent. So the *same detection* has different reliability depending on which side of the connection logged it, and a workspace fed only by app servers will run entirely in the `Unknown` size lane. That's not a bug, and it's exactly why the size verdict has three states.
- **Whether your parsers write `0` or null for an absent byte count is an assumption I've made and you should test.** The Act I `case` treats a literal `0` as `Unknown` rather than as a measurement, and that choice is load-bearing: get it backwards and every unmeasured response is silently classified `SmallBody`, which is the one verdict that ranks *below* everything else — the `isnotempty()` failure re-created inside the fix for it. ASIM's schema says what `DstBytes` *means*; it does not say what a parser does when the source didn't report it, and different parsers genuinely differ. Settle it before you deploy:

```kql
_Im_WebSession(starttime=ago(7d))
| extend RespBytes = coalesce(
             column_ifexists("HttpResponseBodyBytes", long(null)),
             column_ifexists("DstBytes", long(null)))
| summarize
    Rows      = count(),
    NullBytes = countif(isnull(RespBytes)),
    ZeroBytes = countif(RespBytes == 0),
    Populated = countif(RespBytes > 0),
    MedianPop = percentile(RespBytes, 50),
    P99Pop    = percentile(RespBytes, 99)
    by EventVendor, EventProduct, EventType, HttpRequestMethod
| extend ZeroShare = round(todouble(ZeroBytes) / todouble(Rows), 3)
| order by Rows desc
```

  Read it per parser, not in aggregate. A source with a high `ZeroShare` on `GET` traffic is using zero as its null and the `RespBytes == 0` line is correct for it. A source with real nulls and almost no zeros is scrupulous, and for that source the line costs you nothing but buys you nothing either. A source where `Populated` is near zero across the board is telling you it has no byte counts at all, which means every finding from it will land in `Unknown` — good to know on the day you deploy rather than on the day it matters.
- **If you don't have ASIM, the `CommonSecurityLog` version is fine — with the right column names.** Here it is, with the direction problem left visible rather than guessed at:

```kql
let lookback = 7d;
let ActuatorEndpoints = dynamic(["heapdump","env","configprops","beans","threaddump",
                                 "mappings","loggers","httpexchanges","jolokia"]);
CommonSecurityLog
| where TimeGenerated > ago(lookback)
| where isnotempty(RequestURL)
| where RequestURL has_any ("actuator","heapdump","jolokia","configprops","threaddump")
| extend UrlLower = tolower(url_decode(RequestURL))
| extend PathOnly = trim_start(@"[a-z][a-z0-9+.\-]*://[^/]*", UrlLower)
| extend PathOnly = tostring(split(tostring(split(tostring(split(PathOnly,"?")[0]),"#")[0]),";")[0])
| extend NormPath = trim_end(@"/+", replace_regex(PathOnly, @"/{2,}", "/"))
| extend Segments = split(NormPath, "/")
| extend Endpoint = tostring(Segments[array_length(Segments) - 1])
| where Endpoint in (ActuatorEndpoints)
// BOTH directions are carried, because CEF does not tell you which one is the
// response. Run the validation query below, then delete the column you don't need.
| extend
    BytesIn  = tolong(column_ifexists("ReceivedBytes", long(null))),
    BytesOut = tolong(column_ifexists("SentBytes",     long(null)))
| extend BiggestSide = max_of(coalesce(BytesIn, long(0)), coalesce(BytesOut, long(0)))
// EventOutcome is documented as success/failure. Some sources write a status code,
// some write a word, some write "200 OK". Read it; don't gate on it.
| summarize
    Requests     = count(),
    Outcomes     = make_set(EventOutcome, 10),
    Endpoints    = make_set(Endpoint, 15),
    Paths        = make_set(NormPath, 10),
    Devices      = make_set(DeviceName, 5),
    Vendors      = make_set(strcat(DeviceVendor, "/", DeviceProduct), 5),
    Agents       = make_set(RequestClientApplication, 5),
    MaxBytesIn   = max(BytesIn),
    MaxBytesOut  = max(BytesOut),
    MaxEitherSide= max(BiggestSide),
    ActiveDays   = dcount(bin(TimeGenerated, 1d)),
    FirstSeen    = min(TimeGenerated),
    LastSeen     = max(TimeGenerated)
    by SourceIP
| extend
    NoByteCounts = isnull(MaxBytesIn) and isnull(MaxBytesOut),
    Readable     = format_bytes(coalesce(MaxEitherSide, long(0))),
    Enumerating  = array_length(Endpoints) > 2
| order by MaxEitherSide desc, NoByteCounts desc, Enumerating desc, Requests desc
```

- **Settle the byte direction empirically, once, and write the answer down.** Download something large and known through the device, then look:

```kql
CommonSecurityLog
| where TimeGenerated > ago(1d)
| where isnotempty(RequestURL)
| summarize
    Records      = count(),
    WithIn       = countif(isnotnull(ReceivedBytes) and ReceivedBytes > 0),
    WithOut      = countif(isnotnull(SentBytes)     and SentBytes > 0),
    MedianIn     = percentile(ReceivedBytes, 50),
    MedianOut    = percentile(SentBytes, 50),
    P99In        = percentile(ReceivedBytes, 99),
    P99Out       = percentile(SentBytes, 99)
    by DeviceVendor, DeviceProduct, RequestMethod
| order by Records desc
```

  On `GET` traffic the response side is one to three orders of magnitude larger than the request side, so the column with the big P99 on `GET` is your response column. That's a five-second answer to a question you would otherwise argue about in a channel for a day. Do the same for `EventOutcome`: `CommonSecurityLog | where isnotempty(RequestURL) | summarize count() by EventOutcome, DeviceProduct | order by count_ desc` tells you in one screen whether you're getting `200`, `success`, `200 OK`, or nothing.

- **`not(ipv4_is_private(SourceIP))` is the wrong filter, in the wrong place, for the wrong reason.** Tuesday's Detections 2 and 3 both scope to external sources only. The framing came from the source report, which is about internet scanning — but the detection you deploy is not the report. The two cases it deletes are the two you'd most want: a **compromised internal host** enumerating actuator endpoints across the estate, which is a post-exploitation credential harvest and the single most dangerous version of this activity; and the far more mundane case where `SourceIP` is your own load balancer or ingress controller, in which case *every* request is private, the filter is a total blackout, and the true client is sitting in `HttpRequestXff` being ignored. The query above carries `ProbablyInternal` as a triage column and ranks on evidence instead. If you must reduce volume, reduce it on the *service* side — scope to hosts that actually answer — not on the client side.
- **`ipv4_is_private()` on an IPv6 address does not do what you want**, and the briefs flag this correctly. In a dual-stack estate, use `ipv4_is_private()` and `ipv6_is_match()` against the ULA and link-local ranges, or normalize first. Better: don't make routability a filter at all, per the previous bullet.
- **The prefilter can under-match on encoded paths, and that's a real hole rather than a theoretical one.** `url_has_any=PrefilterTerms` runs against the *raw* URL, before my `url_decode()`. A request written as `/actuator/%68eapdump` contains neither the term `heapdump` nor anything else in the list, so the parser-level filter drops it and the authoritative test never sees it. There are exactly two honest options and no clever third one: keep the prefilter and accept that percent-encoded evasion is out of scope for the scheduled version, or drop the `url_has_any` argument entirely for a targeted hunt and pay for the full scan. I keep it for the scheduled rule and drop it for hunts, and I'd rather say that plainly than pretend the prefilter is free. Note the shape of this failure, because it generalizes: last week's prefilter trap was about *tokenization*, this one is about *encoding*, and both have the same structure — a cheap filter sitting upstream of an authoritative test, where every row it wrongly drops is invisible.

  **And I want to be explicit about the standard of evidence here, because it's lower than the rest of this article.** Microsoft documents what `url_has_any` *filters on* — the `Url` field — and does not document whether individual parsers normalize or decode that value before the comparison, or whether the operator underneath is a term test or a substring test. Both of those are implementation details of each source-specific parser, and there is no reason to assume they're uniform across the Palo Alto parser, the Squid parser, and whatever you wrote yourself. So the paragraph above is reasoning from the documented behaviour of the *field*, not from an observed result — which is exactly the kind of claim last week's article got wrong about `has_any` adjacency and had to correct in public. Don't inherit my answer. Measure it, in your workspace, in about a minute:

```kql
// Does the parser-level prefilter see the same rows as an unfiltered scan?
// If Filtered < Unfiltered, the prefilter is dropping rows the authoritative
// test would have kept -- and those rows are invisible in the scheduled rule.
let Terms = dynamic(["actuator","heapdump"]);
let Unfiltered = _Im_WebSession(starttime=ago(7d))
| where tolower(url_decode(tostring(Url))) has_any ("actuator","heapdump","%68eapdump","%61ctuator");
let Filtered = _Im_WebSession(starttime=ago(7d), url_has_any=Terms);
union
    (Unfiltered | summarize Rows = count() | extend Population = "Decoded match, no prefilter"),
    (Filtered   | summarize Rows = count() | extend Population = "Parser prefilter applied")
```

  If the two numbers match, your parsers decode before filtering and you can keep the prefilter with a clear conscience. If they don't, the gap is the size of the hole, and you now know whether it's worth paying for the full scan. Either way, write the answer in a comment next to the query, because the next person to read it will make the same assumption I did.
- **`HttpRequestXff` is attacker-controlled and it is still worth having.** X-Forwarded-For is a request header; a client can send whatever it likes in it, and your edge may append rather than replace. So it is not an identity and must never be the entity key. It is a *lead*: if your edge appends, the rightmost value your edge added is trustworthy and the rest isn't, and if you don't know which your edge does, find out before you use the field for anything. It's in the aggregation as `Xff`, not in the `by` clause, for exactly the reasons last week's article gave for keeping actors out of the grouping.
- **`python-requests/2.34.2` is a gift and it will not last.** The ISC capture shows a default library user agent and `admin:admin` basic auth. Both are free corroborators and both cost the operator one line to change. Use them to rank, never to select. The same goes for a `401` immediately followed by a `200` on the same endpoint from the same source, which is the credential-guessing shape from that capture and is genuinely high-signal for as long as the attacker keeps guessing.
- **This is a lead, not a verdict, and the confirmation is not in the SIEM.** A large `200` on `/…/heapdump` means the application generated and streamed a heap dump. What was *in* that heap dump is a question for the application owner, and it's the only question that determines the blast radius. The first triage call is to whoever owns the service, and the question is: what secrets does this process hold in memory. Everything else — blocking the source, disabling the endpoint — is cleanup that doesn't change what already left.

Act I hunts the request. Which assumes you can see the request. That assumption is doing more work than it looks like.

<br/>

---

<br/>

## 🥈 Act II: Spring Writes the Evidence For You

![Act II](/assets/img/HeapOfTrouble/ACT_II.png)

Everything in Act I depends on the web tier logging the URL path. Consider how often that's actually true.

`RequestURL` in `CommonSecurityLog` is only populated when the CEF source is a proxy, WAF, or application delivery controller that emits HTTP request detail — the briefs say so, and it's right. A generic firewall doesn't. A network IDS mostly doesn't. TLS-terminating load balancers vary. And an enormous number of Spring Boot applications in the real world are reachable on a container port through an ingress that logs to stdout and into a platform your SIEM has never heard of. The path `/admin-api/actuator/heapdump` reached the JVM; whether it reached your workspace is a completely separate question, and in a lot of estates the answer is no.

Monday's Detection 4 went looking for the answer on the host, which is the right instinct. It searched `DeviceFileEvents` for `.hprof` files created by a Java process. And then its caveats said this:

> Spring Boot's heapdump endpoint in many configurations streams the heap dump directly to the HTTP response without writing a persistent file to disk; in such configurations, this detection will produce no results even when the endpoint is successfully accessed.

That is not how the endpoint works, and the correction turns Monday's weakest candidate into the best detection in this article.

Read `HeapDumpWebEndpoint` in the Spring Boot source. It does this, in order:

1. `File.createTempFile("heapdump" + yyyy-MM-dd-HH-mm + (live ? "-live" : ""), ".hprof")` — creating an empty placeholder in the JVM's temp directory.
2. `file.delete()` — immediately, because `HotSpotDiagnosticMXBean.dumpHeap()` refuses to write to a path that already exists.
3. `heapDumper.dumpHeap(file, live)` — the JVM writes the entire heap to that path.
4. It returns a `TemporaryFileSystemResource` wrapping the file, which streams it to the response and **deletes it once the response is written.**

So the file is not skipped. The file is written, in full, to disk, every single time — and then removed. What Monday's caveat described as "streaming without writing" is actually "writing, streaming, and cleaning up," and the difference is the entire detection, because MDE records the create and the delete as events regardless of whether the file survives.

And the filename is not incidental. Look at what Spring encodes into it:

| Component | Value | What it tells you |
|---|---|---|
| Prefix | `heapdump` | This came from the **web endpoint**, not from an operator |
| Date | `yyyy-MM-dd-HH-mm` | The minute the HTTP request arrived, in the **JVM's local time** |
| Optional | `-live` | The caller passed `?live=true` — a deliberate parameter, not a stray click |
| Suffix | random digits + `.hprof` | `createTempFile` uniqueness |

That naming pattern belongs to the actuator endpoint and to nothing else. A JVM dumping on out-of-memory writes `java_pid<pid>.hprof`. An operator running `jmap` or `jcmd` writes wherever they said to write. Nothing else in the Java ecosystem produces `heapdump2026-08-03-14-49<digits>.hprof` in a temp directory.

Which means: **the filename is proof that an HTTP request hit the heapdump endpoint.** Not evidence that a heap dump happened — evidence that *someone called the web endpoint*. On a host where you have no web logs at all, `DeviceFileEvents` will tell you the request occurred, and the embedded timestamp will tell you the minute it arrived, to the minute, which is a join key back into whatever request logs you *do* have.

That's an unusual thing for endpoint telemetry to be able to say about a network event, and it exists purely because the developers needed a unique temp filename and reached for a timestamp.

<br/>

### The KQL

```kql
let lookback = 30d;
// Spring's HeapDumpWebEndpoint: createTempFile("heapdump" + yyyy-MM-dd-HH-mm
// + optional "-live", ".hprof"). The trailing digits are createTempFile's uniqueness.
let ActuatorDumpRegex = @"^heapdump\d{4}-\d{2}-\d{2}-\d{2}-\d{2}(-live)?\d+\.hprof$";
// -XX:+HeapDumpOnOutOfMemoryError writes java_pid<pid>.hprof to the working directory.
let OomDumpRegex      = @"^java_pid\d+\.hprof$";
let DumpTools         = dynamic(["jmap","jcmd","jattach","jhsdb","java"]);
let DumpEvents = DeviceFileEvents
| where Timestamp > ago(lookback)
// endswith on the extension is the only safe prefilter. `FileName has "heapdump"`
// does NOT match heapdump2026-08-03-14-49123.hprof -- see the note below.
| where FileName endswith ".hprof" or FileName endswith ".phd"
| extend NameLower = tolower(FileName)
| extend DumpOrigin = case(
      NameLower matches regex ActuatorDumpRegex, "ActuatorWebEndpoint",
      NameLower matches regex OomDumpRegex,      "JvmOutOfMemory",
                                                 "OperatorOrUnknown")
// The minute in the filename is the request arrival time in the JVM's LOCAL zone.
// Extracted as a string on purpose: comparing it to TimeGenerated tells you the
// host's UTC offset, which you need before you join it to anything.
| extend FilenameStamp = extract(@"^heapdump(\d{4}-\d{2}-\d{2}-\d{2}-\d{2})", 1, NameLower)
| extend LiveOnly = NameLower matches regex @"^heapdump[\d\-]+-live\d+\.hprof$"
| project
    Timestamp, DeviceId, DeviceName, ActionType, FileName, FolderPath,
    FileSize = column_ifexists("FileSize", long(null)),
    DumpOrigin, FilenameStamp, LiveOnly,
    Process     = InitiatingProcessFileName,
    ProcessPath = InitiatingProcessFolderPath,
    ProcessId   = InitiatingProcessId,
    Account     = InitiatingProcessAccountName,
    CommandLine = InitiatingProcessCommandLine;
// Lane 2 -- the BENIGN corroborator. Not an exclusion. An operator-run jcmd on the
// same host in the same window makes a dump explainable; its ABSENCE makes one
// unexplained. Excluding these outright would delete the evidence that a dump was fine.
let DiagnosticRuns = DeviceProcessEvents
| where Timestamp > ago(lookback)
| where FileName in~ (DumpTools) or ProcessCommandLine has_any ("GC.heap_dump","dumpHeap","-dump:")
| where ProcessCommandLine has_any ("heap_dump","heapdump","dumpHeap","-dump:","hprof")
| summarize
    DiagRuns     = count(),
    DiagCommands = make_set(ProcessCommandLine, 5),
    DiagAccounts = make_set(AccountName, 5),
    DiagFirst    = min(Timestamp),
    DiagLast     = max(Timestamp)
    by DeviceId;
DumpEvents
// Entity = (device, file). One file produces multiple rows: createTempFile creates it,
// Spring deletes the placeholder, the JVM writes it, the response streams, Spring
// deletes it again. Four to five events, one artifact, one finding.
| summarize
    Actions       = make_set(ActionType),
    EventCount    = count(),
    FirstEvent    = min(Timestamp),
    LastEvent     = max(Timestamp),
    MaxFileSize   = max(FileSize),
    Folders       = make_set(FolderPath, 3),
    Processes     = make_set(Process, 5),
    ProcessPaths  = make_set(ProcessPath, 5),
    Accounts      = make_set(Account, 5),
    CommandLines  = make_set(CommandLine, 3),
    DeviceNames   = make_set(DeviceName, 3),
    Origins       = make_set(DumpOrigin, 3),
    Stamps        = make_set_if(FilenameStamp, isnotempty(FilenameStamp), 3),
    LiveRequested = countif(LiveOnly) > 0
    by DeviceId, FileName
| extend
    Created      = set_has_element(Actions, "FileCreated"),
    Deleted      = set_has_element(Actions, "FileDeleted"),
    // DumpOrigin is a pure function of FileName and FileName is in the by clause,
    // so this set is always a singleton. Indexing it is safe here and nowhere else.
    Origin       = tostring(Origins[0]),
    LifetimeSec  = tolong(datetime_diff('second', LastEvent, FirstEvent)),
    SizeReadable = format_bytes(coalesce(MaxFileSize, long(0)))
// Create AND delete, with the actuator naming, is the complete protocol signature.
| extend WebEndpointConfirmed = Origin == "ActuatorWebEndpoint" and Created and Deleted
| join kind=leftouter DiagnosticRuns on DeviceId
| project-away DeviceId1
| extend
    DiagnosticNearby = isnotnull(DiagRuns)
        and DiagLast between ((FirstEvent - 15m) .. (LastEvent + 15m)),
    RenamedInWindow  = array_length(DeviceNames) > 1
// An actuator-named dump with NO operator diagnostic activity anywhere near it is the
// finding. With one, it's probably a human being doing their job -- still worth a look,
// because "an operator ran jcmd" and "an attacker called the endpoint while an operator
// happened to be working" look identical from here.
| extend Verdict = case(
      WebEndpointConfirmed and not(DiagnosticNearby), "WebEndpoint-Unexplained",
      WebEndpointConfirmed,                           "WebEndpoint-OperatorNearby",
      Origin == "JvmOutOfMemory",                     "OutOfMemory",
                                                      "Operator-Or-Unknown")
| order by WebEndpointConfirmed desc, DiagnosticNearby asc, LiveRequested desc,
           MaxFileSize desc, LastEvent desc
```

<br/>

### The line that does the work

```kql
| where FileName endswith ".hprof" or FileName endswith ".phd"
```

That's the prefilter, and it's the only safe one available — which is the correction, because the obvious alternative is in Monday's query and it does not work.

Monday filtered with `where FileName endswith ".hprof" or FileName has "heapdump"`. The first half is fine. **The second half can never match a real Spring heapdump filename**, and the reason is the same term-matching behaviour that keeps showing up in these articles from different angles.

`has` tests for a whole indexed **term**. KQL breaks values into terms on non-alphanumeric characters, so `heapdump2026-08-03-14-49123456.hprof` decomposes into the terms `heapdump2026`, `08`, `03`, `14`, `49123456`, and `hprof`. The term `heapdump` is not among them — `heapdump2026` is a *different term*, because the digits are alphanumeric and nothing separates them from the letters. `has "heapdump"` asks whether a term exactly equal to `heapdump` is present. It isn't. The clause returns false on every actuator-generated dump in your estate.

It doesn't error, it doesn't return anything strange, and it doesn't cost anything — because the `endswith ".hprof"` on the other side of the `or` is quietly carrying the whole query. Which is precisely why this survives review. The predicate is dead, the query works, and the day somebody "optimizes" by dropping the extension check in favour of the more specific-looking name check, the detection goes to zero and looks healthy. If you want to match the prefix, `startswith "heapdump"` or a regex are the operators that ask that question; `has` is not, and no amount of adjacent-token reasoning makes it one.

The authoritative test is the regex:

```kql
| extend NameLower = tolower(FileName)
| extend DumpOrigin = case(
      NameLower matches regex ActuatorDumpRegex, "ActuatorWebEndpoint",
      NameLower matches regex OomDumpRegex,      "JvmOutOfMemory",
                                                 "OperatorOrUnknown")
```

and note that it doesn't just *detect*, it **classifies**. This is the part I'd take to production tomorrow. Three origins produce `.hprof` files and they mean three completely different things:

- `heapdump<date>[-live]<digits>.hprof` → somebody called the HTTP endpoint. **This is a network event you're reading off the disk.**
- `java_pid<pid>.hprof` → the JVM hit `OutOfMemoryError` with `-XX:+HeapDumpOnOutOfMemoryError` set. That's a stability event — and occasionally an attacker-induced one, since a reliable OOM is a denial of service with a credential file as a souvenir.
- Anything else → an operator with `jmap`, `jcmd`, or a profiler, writing to a path they chose.

A detection that returns all three as "heap dump created" hands the analyst a triage problem. A detection that separates them hands the analyst an answer. The cost of the classification is one `case` statement and two regexes, and it converts the noisiest lane in this table — APM agents and CI runners and out-of-memory crashes, all of which really do generate `.hprof` files constantly — from false positives into *labelled* rows.

And the `-live` flag deserves its own sentence. `?live=true` restricts the dump to reachable objects. It is a smaller, faster, cleaner dump, and it is a parameter you pass on purpose. A monitoring integration might. A browser click won't. It's not evidence by itself, but it's in the ranking because the population of callers who know that parameter exists is small and interesting.

<br/>

### The lane that isn't an exclusion

`DiagnosticRuns` is the design choice in Act II I'd most want copied, and it's the inverse of what the tuning instinct says to do.

Every triage runbook in the briefs, correctly, lists "an operator generated a heap dump during troubleshooting" as the leading benign explanation. The natural next step is to write that into the query as an exclusion — drop hosts where `jmap` or `jcmd` ran, drop dumps by the APM agent's account, drop the CI runners. Don't. **Every one of those exclusions is a place to hide**, and more importantly, they throw away the fact that would have made the finding actionable.

So `DiagnosticRuns` is joined `leftouter` and lands in a boolean. A dump with operator diagnostic activity fifteen minutes either side is *probably* a person doing their job — and it ranks below one with none, rather than being deleted. The `Verdict` column says which it is, in words, and the analyst reads that instead of trusting an exclusion list they didn't write.

There's a second reason, and it's the honest one: `DiagnosticNearby` being true does not mean the dump was benign. It means an operator was working on that host in that window, which is also an excellent time for something else to happen unnoticed. The flag lowers the rank and it does not close the case. An exclusion would have closed the case, silently, forever, without anybody deciding to.

Note the join key too: `DeviceId` alone, and the grouping key is `DeviceId, FileName`. `DeviceName` is in the aggregation as `DeviceNames` with a `RenamedInWindow` flag, for the same reason as always — a label that changes on rename and collides across a fleet is not an identity, and a rename inside a thirty-day window would split one compromised host into two half-findings, each below the bar.

<br/>

### Keeping it honest

`ActuatorWebEndpoint` with `Created and Deleted and not(DiagnosticNearby)` is a scheduled rule I'd deploy this week. The rest of it is a hunt. The gap between those two states:

- **The whole detection rests on a temp file that exists for seconds.** MDE's `DeviceFileEvents` is an event stream, not a filesystem scan, so the transience doesn't matter to the query — but it matters enormously to the *response*. By the time anyone reads the alert, the file is gone, and there is no way to recover what was in it. You cannot answer "what did they get" from the artifact. You answer it from the application owner, who knows what that process holds in memory. Plan the runbook around that or the first real one will be an hour of people trying to find a deleted file.
- **Container workloads are the coverage question, and most Spring Boot is containerized.** If the JVM runs in a container and the MDE agent runs on the host, the temp file lands in the container's writable layer and shows up under an overlay path — often visible, sometimes not, depending on your runtime and MDE version. If the agent isn't on the node at all, none of this exists. Check before you rely on it: `DeviceFileEvents | where TimeGenerated > ago(7d) | where InitiatingProcessFileName has_any ("java","javaw") | summarize Files = count(), Devices = dcount(DeviceId) by tostring(split(FolderPath, "/")[1]) | order by Files desc` will show you whether you're seeing `/tmp`, `/var/lib/docker/overlay2/...`, both, or nothing.
- **`java.io.tmpdir` is not always `/tmp`, and that's a feature here.** `createTempFile` writes to whatever `java.io.tmpdir` points at — which containers, systemd units, and app servers all commonly override. The query deliberately does **not** scope by `FolderPath`, for the same reason last week's `logAzure.txt` hunt didn't: the location is unpredictable and the location is *evidence*. Where the file landed tells you which unit the JVM runs under.
- **The regex is a version contract, and I've stated it as one.** The `yyyy-MM-dd-HH-mm` format and the `heapdump` prefix are what current Spring Boot writes. Spring has changed this file's naming before and can change it again, and an OpenJ9 JVM produces `.phd` rather than HPROF. The extension prefilter covers both formats; the *classification* regex covers current Spring on HotSpot. If it stops matching, you'll see it as a population shift into `OperatorOrUnknown` rather than as silence — which is the right direction for that failure to fall, and is why the prefilter is deliberately broader than the classifier rather than equal to it.
- **`InitiatingProcessName` is not a column and `FileRead` is not an ActionType.** Neither error is in Monday's query, but both are in Saturday's Detection 1, which hunts the Rails file read with `where InitiatingProcessName has_any (railsProcesses)` and `where ActionType in ("FileRead", "FileAccessed")`. The column is `InitiatingProcessFileName`; `InitiatingProcessName` doesn't resolve, so the query is a semantic error. And `DeviceFileEvents` `ActionType` values are `FileCreated`, `FileModified`, `FileRenamed`, and `FileDeleted` — MDE does not emit generic file *reads* to that table, which is exactly the blind spot Thursday's and Saturday's briefs both flag in their own callouts. Two independent problems, and the second one is the interesting one, because it means **arbitrary-file-read vulnerabilities are structurally invisible to `DeviceFileEvents`**. You detect them by their consequences — a child process, an outbound connection, an authentication with a stolen secret — not by the read. Which is the same lesson as Act I from the other end: you cannot detect a read, only its effects.
- **`.hprof` volume is not zero, and that's the point of the classifier.** APM agents, CI runners executing tests that OOM, and genuine production incidents all generate these. Run `DeviceFileEvents | where TimeGenerated > ago(30d) | where FileName endswith ".hprof" | summarize Files = dcount(FileName), Devices = dcount(DeviceId) by InitiatingProcessFileName, InitiatingProcessAccountName | order by Files desc` before you schedule anything, and expect the `OperatorOrUnknown` bucket to be the big one. If `ActuatorWebEndpoint` is non-zero in that baseline and nobody can explain it, you have your answer before you deploy the rule.
- **This is the detection you keep when the web tier goes dark, and the one you correlate with when it doesn't.** `FilenameStamp` is a local-time minute; `Timestamp` is UTC. Compare them once per host to learn the offset, then use the stamp as a join key back into Act I. When both fire on the same minute, you have the request, the source IP, the response size, and the file — which is a complete incident narrative assembled from two telemetry domains that share no common field.

Act I hunts the request. Act II hunts the artifact. The last query stops hunting the attacker entirely.

<br/>

---

<br/>

## 🎖 Honorable Mention: Stop Detecting the Scan. Detect the Answer.

![Honorable Mention](/assets/img/HeapOfTrouble/Honorable_Mention.png)

All four of the briefs' web-tier heapdump detections group by `SourceIP`. Every one of them ranks by request count. Every one of them is asking: *who is scanning us?*

That question has no useful answer. Actuator scanning is background radiation. It runs continuously, from thousands of hosts, forever, and it will keep running after you block every address in the result set. A detection that ranks scanners by volume produces a list that is always populated, never actionable, and identical next week. It is a weather report.

Flip the entity and the question becomes finite: **which of my services answer?**

That population is small. It is enumerable. It is *fixable* — every row is a configuration change with an owner, and when you fix it the row disappears and does not come back. It is also, crucially, the only version of this that catches the exposure **before** somebody finds it, because your own monitoring, health checks, and internal traffic will trip an exposed actuator endpoint long before an external scanner does.

The discriminator is the status code, and it's beautifully clean. A `404` means the endpoint isn't mounted — that's a healthy application telling you so. A `401` or `403` means it's mounted and protected, which is a finding of a different severity. A `200` on `/…/env` or `/…/heapdump` means the application will hand its secrets to whoever asks, and it means that regardless of who asked.

```kql
let lookback = 30d;
let ActuatorEndpoints = dynamic([
    "heapdump","env","configprops","beans","threaddump","mappings",
    "loggers","httpexchanges","httptrace","auditevents","jolokia","dump","trace",
    "health","info","metrics","shutdown","restart","refresh"
]);
let SecretBearing = dynamic(["heapdump","env","configprops","jolokia","dump"]);
let StateChanging = dynamic(["shutdown","restart","refresh","loggers"]);
let PrefilterTerms = dynamic([
    "actuator","heapdump","env","configprops","beans","threaddump","mappings",
    "loggers","httpexchanges","httptrace","auditevents","jolokia","shutdown"
]);
_Im_WebSession(starttime=ago(lookback), url_has_any=PrefilterTerms)
| extend UrlLower = tolower(url_decode(tostring(Url)))
| extend PathOnly = trim_start(@"[a-z][a-z0-9+.\-]*://[^/]*", UrlLower)
| extend PathOnly = tostring(split(tostring(split(tostring(split(PathOnly,"?")[0]),"#")[0]),";")[0])
| extend NormPath = trim_end(@"/+", replace_regex(PathOnly, @"/{2,}", "/"))
| extend Segments = split(NormPath, "/")
| extend Endpoint = tostring(Segments[array_length(Segments) - 1])
| where Endpoint in (ActuatorEndpoints)
// The management BASE PATH, recovered from the data rather than assumed. This is the
// output that goes to the platform team: it tells them where their surface actually is.
| extend BasePath = trim_end(@"/+", substring(NormPath, 0, strlen(NormPath) - strlen(Endpoint)))
| extend StatusCode = toint(EventResultDetails)
| extend Answered   = (StatusCode == 200)
                   or (isnull(StatusCode) and tostring(EventResult) =~ "Success")
| extend RespBytes = coalesce(
             column_ifexists("HttpResponseBodyBytes", long(null)),
             column_ifexists("DstBytes", long(null)))
| extend
    Service   = coalesce(tostring(column_ifexists("HttpHost","")),
                         tostring(column_ifexists("DstFQDN","")),
                         tostring(DstIpAddr)),
    UserAgent = tostring(column_ifexists("HttpUserAgent", ""))
| where isnotempty(Service)
// ipv4_is_private() returns null for a v6 literal, and not(null) is null, so a v6
// client would count as neither internal nor external. Default it to external --
// the safer direction for a surface report.
| extend ExternalClient = coalesce(not(ipv4_is_private(tostring(SrcIpAddr))), true)
// Entity = the SERVICE and the ENDPOINT. One row per thing you might have to fix.
| summarize
    Requests        = count(),
    AnsweredHits    = countif(Answered),
    NotFoundHits    = countif(StatusCode == 404),
    AuthWallHits    = countif(StatusCode in (401, 403)),
    DistinctClients = dcount(SrcIpAddr),
    ExternalClients = dcountif(SrcIpAddr, ExternalClient),
    MaxRespBytes    = max(RespBytes),
    BasePaths       = make_set(BasePath, 5),
    SampleClients   = make_set(SrcIpAddr, 10),
    Statuses        = make_set(EventResultDetails, 10),
    Agents          = make_set(UserAgent, 5),
    ActiveDays      = dcount(bin(TimeGenerated, 1d)),
    FirstSeen       = min(TimeGenerated),
    LastSeen        = max(TimeGenerated)
    by Service, Endpoint
// Exposed == it answered at least once. Not "answered a lot". Once.
| extend
    Exposed        = AnsweredHits > 0,
    Protected      = AnsweredHits == 0 and AuthWallHits > 0,
    NotPresent     = AnsweredHits == 0 and AuthWallHits == 0 and NotFoundHits > 0,
    LeaksSecrets   = Endpoint in (SecretBearing),
    ChangesState   = Endpoint in (StateChanging),
    FoundExternally= ExternalClients > 0,
    MaxReadable    = format_bytes(coalesce(MaxRespBytes, long(0)))
| extend Priority = case(
      Exposed and LeaksSecrets and FoundExternally, "P1 - secrets, externally reachable",
      Exposed and ChangesState and FoundExternally, "P1 - state change, externally reachable",
      Exposed and LeaksSecrets,                     "P2 - secrets, internal callers only",
      Exposed and ChangesState,                     "P2 - state change, internal callers only",
      Exposed,                                      "P3 - management surface exposed",
      Protected,                                    "P4 - mounted, authenticated",
                                                    "OK - not mounted")
| where not(Priority startswith "OK")
| order by Priority asc, MaxRespBytes desc, ExternalClients desc, AnsweredHits desc
```

<br/>

### The line that does the work

```kql
| extend Exposed = AnsweredHits > 0
```

One. Not a threshold, not a rate, not a baseline — **one successful response, ever, in thirty days.**

This is the opposite of everything else in this article, and it's worth being explicit about why the same author is arguing both sides. Elsewhere I've spent paragraphs objecting to volume gates, and the objection stands: you cannot separate a beacon from a business integration by counting, and `CalendarOps > 20` or `RequestCount > 1` are thresholds placed inside a distribution where the two populations overlap.

But this query isn't measuring behaviour. It's measuring **configuration**, and configuration is binary. An endpoint either serves or it doesn't. A service that returned `200` on `/…/env` once is exactly as misconfigured as one that returned it ten thousand times — the difference between those two numbers is how many people have looked, not how exposed you are. Counting would rank a heavily-scanned staging box above a quiet production service holding live payment credentials, and the quiet one is the emergency.

The `BasePath` extraction is the other line worth stealing, and it is the deliverable. The query recovers where your management surface is actually mounted, from your own traffic, rather than assuming `/actuator`. That's the answer to a question the platform team probably cannot answer from memory across a hundred services — and it's also the input to every other query in this article, because once you know your real base paths you can tighten the prefilters honestly instead of hopefully.

Note the negative-result lane too. `NotPresent` — endpoints that only ever returned `404` — is filtered out of the output, and it is the row you want to see in a *validation* run. If your entire result set is `NotPresent`, either you're clean or your parser isn't populating status codes, and you should find out which before you file this as good news.

<br/>

### Keeping it honest

This one is a **hunt and a report**, not an alert, and it doesn't belong in the SOC queue at all. It belongs in a ticket to whoever owns each service:

- **It only sees services your web telemetry covers**, which is the same coverage limit as Act I and it bites harder here, because absence reads as safety. A service with no proxy logging produces no rows and looks compliant. Pair this with an actual asset inventory, or with an authenticated internal scan, and treat the query output as a floor.
- **It only sees endpoints somebody requested.** This is inherently a *passive* discovery method: an exposed `/…/heapdump` that nobody has ever asked for will not appear. That's fine for `heapdump`, `env`, and `configprops`, which the internet probes constantly, and it's a real gap for anything unusual. The thirty-day window exists to give background scanning time to do your reconnaissance for you.
- **`Service` is whatever your telemetry calls the destination**, and `HttpHost`, `DstFQDN`, and `DstIpAddr` are three different granularities. A shared ingress will collapse many applications into one row; a load-balanced service will fan one application into several. Prefer `HttpHost` where it's populated — it's the virtual host the client asked for, which is closest to "the application" as an owner would understand it — and check what you've actually got before you send anyone a list: `_Im_WebSession(starttime=ago(1d)) | summarize count() by HasHost = isnotempty(column_ifexists("HttpHost","")), HasFqdn = isnotempty(column_ifexists("DstFQDN",""))`.
- **`health` and `info` are on the endpoint list on purpose and they are not findings.** They're the two actuator endpoints that are exposed by default and are supposed to be. They're included so that the base-path recovery works on services where the only thing anyone ever hits is the health check — which is most of them — and they land in P3 at worst. If a P3 list of every health endpoint in the estate is noise for you, filter them at the end, not at the start, or you lose the base paths.
- **A `200` is not always a served endpoint.** Some WAFs and ingress controllers return `200` with a block page. That's why `MaxRespBytes` is in the output and in the sort: an "exposed" heapdump endpoint whose largest response was 4 KB is a block page, and the size column tells you so without your having to trust the status code alone. When the size is `Unknown`, it stays in the list — same discipline as Act I.
- **Fixing this is not a detection engineering task and you should hand it over.** `management.endpoints.web.exposure.include` is the property that decides what's mounted; the default is `health` on Spring Boot 3.x and `health,info` on much of 2.x. Anything else on that list got there deliberately, usually during an incident, usually years ago. The detection's job is to produce the list. Somebody else's job is to shorten it.

<br/>

---

<br/>

## ✨ Bonus: Three-Valued Logic, or Why `where not(X)` Isn't the Opposite of `where X`

![Bonus](/assets/img/HeapOfTrouble/Bonus.png)

Act I turned on a number that might not be there. Last week's bonus was about **order** (`prev()` and serialization); the week before was about **membership** (`leftanti`). This week's is about the thing underneath both of them: **what KQL does when it doesn't know.**

<br/>

### `where` keeps `true`, and null is not `false`

KQL comparisons are three-valued. `RespBytes > 1048576` evaluates to `true`, `false`, or **`null`** — and `where` keeps only the rows where the predicate is `true`. Null rows are discarded, exactly like false rows, and nothing in the output distinguishes them.

Which produces the result that surprises people:

```kql
// These two do NOT partition the table.
| where RespBytes > 1048576         // keeps the big ones
| where not(RespBytes > 1048576)    // keeps the small ones -- and NOT the unknown ones
```

`not(null)` is `null`, not `true`. So a row with no byte count fails both filters. Run them separately, add up the counts, and you will get fewer rows than you started with — and if you've never checked, you have no idea by how much.

This is the mechanism behind Tuesday's `isnotempty(BytesReceived)` gate. That clause wasn't creating the problem; the comparison on the next line would have dropped the same rows anyway. What the explicit guard did was make the deletion look *intentional*, which is worse, because it reads as care.

<br/>

### The reconciliation that proves it

Before you trust any numeric filter on a field you didn't populate yourself, make the four populations add up:

```kql
let Base = _Im_WebSession(starttime=ago(7d), url_has_any=dynamic(["actuator","heapdump"]))
| extend RespBytes = coalesce(
             column_ifexists("HttpResponseBodyBytes", long(null)),
             column_ifexists("DstBytes", long(null)));
union
    (Base | summarize Rows = count() | extend Population = "All rows"),
    (Base | where RespBytes > 1048576
          | summarize Rows = count() | extend Population = "Above threshold"),
    (Base | where RespBytes <= 1048576
          | summarize Rows = count() | extend Population = "At or below threshold"),
    (Base | where isnull(RespBytes)
          | summarize Rows = count() | extend Population = "NULL - invisible to both"),
    (Base | where RespBytes == 0
          | summarize Rows = count() | extend Population = "Zero - probably also unknown")
| order by Rows desc
```

Three things to read off it. First, rows one through four must reconcile — `All rows` equals the sum of the other three. If they don't, you have a fifth state you haven't thought about. Second, if `NULL` is most of the table, your detection isn't conservative, it's **absent**, and the threshold is decoration. Third, look hard at the ratio of `Zero` to `NULL`: a parser that never writes null and frequently writes zero is telling you that zero *is* its null, and any `> 0` filter you write is a null filter in disguise.

This is the same habit as last week's partition-guard check and the week before's key-cardinality check. Different operator, identical discipline: **before you trust a filter, prove it's discarding what you think it's discarding.**

<br/>

### The four ways a value goes missing, and they need four different tools

| Situation | What you get | Test with | Don't use |
|---|---|---|---|
| The column doesn't exist in the schema | Semantic error — query won't run | `column_ifexists("Name", long(null))` | `coalesce()`, `isnull()` |
| Numeric column, no value | Real `null` | `isnull()` | `isempty()` |
| String column, no value | **Empty string** — KQL has no string null | `isempty()` | `isnull()` — always false |
| Value present but unparseable | `tolong()` returns `null` | `isnull()` after conversion | trusting the conversion |

The string row is the one that reads as a technicality and isn't. `isnull()` on a string column returns `false` unconditionally, because KQL represents string nulls as empty strings. A clause written `where isnull(PrevSubject)` doesn't error and doesn't warn — it just never fires, and it sits in the query looking exactly like a guard. If you've written `isnull()` against a string anywhere, it isn't doing anything.

And the conversion row is where the byte-count case actually lands most often. `tolong("")` is null. `tolong("1,048,576")` is null, because of the separators. `tolong("12 KB")` is null. Each of those is a value that a real CEF source has emitted into a numeric-looking field, and each one arrives at your comparison as an unknown wearing a plausible disguise. If the field is a string in your workspace, convert it and *then* check:

```kql
| extend RawBytes = tostring(SentBytes)
| extend Bytes    = tolong(RawBytes)
| extend BytesState = case(
      isempty(RawBytes),  "Absent",
      isnull(Bytes),      "Unparseable",   // and RawBytes tells you what it actually said
                          "Parsed")
| summarize count() by BytesState
```

Three lines, and the day someone's connector starts writing `"1.2M"` you find out from a population shift instead of from a quarter of missed detections.

<br/>

### Aggregations lie in the other direction

`summarize` treats nulls differently from `where`, and the difference will bite you at the reporting stage after you've handled it correctly at the filtering stage:

- `count()` counts **rows**, including rows whose values are null.
- `countif(predicate)` counts only rows where the predicate is `true` — so nulls silently don't count, same as `where`.
- `max()`, `min()`, `avg()`, `sum()` **skip** nulls. `avg()` of a column that's 90% null is the average of the other 10%, reported without comment. `sum()` of an all-null column is null.
- `dcount()` doesn't count null as a distinct value.

Which is why the Act I summarize carries `UnknownSizeHits = countif(Answered and SizeVerdict == "Unknown")` as a first-class column rather than inferring it from `MaxRespBytes` being null. The count of what you couldn't measure is data. Derive it explicitly, put it in the grid, and let the ranking use it.

<br/>

### Classify, then rank — don't filter

The general form, and the one thing to take from this section:

```kql
// Don't do this. It has two states and the data has three.
| where isnotempty(Bytes) and tolong(Bytes) > 1048576

// Do this. Every row survives; the query says what it knows about each one.
| extend Bytes = tolong(column_ifexists("SentBytes", long(null)))
| extend Confidence = case(
      isnull(Bytes),           "Unknown",
      Bytes >= 1048576,        "Confirmed",
                               "Unlikely")
| order by Confidence asc     // Confirmed, then Unknown, then Unlikely
```

A filter converts *uncertainty* into *absence*, and absence is indistinguishable from safety. A classification keeps the uncertainty on screen where somebody has to look at it. The extra cost is one column. The saving is that the first time the field goes missing, you find out from the alert rather than from the incident.

One last note, and it's a callback: `format_bytes()` is in these queries for readability and it returns a **string**. Keep the raw number as its own column. A field you buried in a display string is a field you deleted, with extra steps — you can't sort it, threshold it, or put it in an `order by`, and the analyst reads it out of prose instead of a grid.

<br/>

---

<br/>

## The Bigger Lesson

![](/assets/img/HeapOfTrouble/Authorized_Read.png)

Seven briefs, twenty-eight candidates, and a thread through most of them: **nothing was exploited.**

- **The credential store was an HTTP endpoint.** No payload, no injection, no bypass — a documented diagnostics feature that returns the process's memory as a response body, reachable at a path the operator chose (Act I). When the theft *is* a legitimate request, the detection has nowhere to look except the size of the answer, the artifact the application left behind, and the fact that the service answered at all.
- **The best evidence was the application's own housekeeping.** Not the request, not the response — a temp file that Spring creates because it needs somewhere to put the heap before it streams it, named with a timestamp because the developers needed uniqueness (Act II). That file exists for seconds, tells you an HTTP request happened, and tells you the minute it arrived. Look for the artifact the software created for its own convenience. It's a habit that keeps paying: last week it was `logAzure.txt`, written because the malware authors wanted config persistence.
- **The rest of the week was the same move at different layers.** TeamCity credential files read by an unexpected process. The Rails Active Storage arbitrary file read, where the exploit is an image upload and the payload is `config/master.key`. LSASS access alongside a network scan. XCSSET writing into Xcode projects that a developer will compile and sign for it. vCenter's directory service issuing an authentication it shouldn't have. Midnight Blizzard signing in. In every one of those, the adversary's core action was a **read that the system was configured to permit**.
- **And the honest structural finding: you cannot detect a read.** `DeviceFileEvents` doesn't emit file-read events, which both Thursday's and Saturday's briefs flag in their own blind-spot callouts. Neither does a proxy log tell you what was inside a 400 MB response. Reads are the least instrumented operation in the entire stack, and this week's adversaries lived in that gap — not because they planned to, but because reading is what you do when the system has already decided to let you.

Last week's grammar was borrowed *infrastructure*: the C2 is your calendar, the encryptor is your `manage-bde.exe`. This week's is borrowed **permission**: the request is well-formed, the response is correct, the application behaved exactly as configured. There is no anomaly in the transaction. The anomaly is in the *configuration*, and configuration is not something a SIEM watches.

Which is why the honorable mention is the query I'd actually run first, even though it's the least clever one in the article. Acts I and II detect an event that has already happened to a service you may not have known was exposed. The exposure query enumerates the services and hands you a list you can finish. One of those is security operations and the other is just operations, and the week's evidence is that the second one would have prevented more of this than the first would have caught.

**The corrections, collected**, because five of them landed in one article and four are worth checking in your own content:

1. **All four heapdump candidates hardcode `/actuator/heapdump`**, and the ISC diary they came from documents scans against `/admin-api/actuator/heapdump`. The base path is configuration; the endpoint ID is the protocol.
2. **`BytesReceived` is not a `CommonSecurityLog` column** — it's `ReceivedBytes` and `SentBytes` — and the brief's caveat describes the wrong failure mode for it. An absent column is a semantic error, not a null.
3. **`isnotempty()` on the byte count deletes the finding** in exactly the environments that need the detection, and the direction of `in`/`out` is undefined relative to the client anyway. Three states, ranked, not two states, filtered.
4. **`FileName has "heapdump"` cannot match a Spring heapdump filename**, because `heapdump2026-08-03-14-49123456.hprof` tokenizes to `heapdump2026` and `has` is a whole-term test. The clause is dead and the `endswith` beside it hides that.
5. **The endpoint does write a file**, contrary to Monday's caveat. `HeapDumpWebEndpoint` creates it, the JVM fills it, `TemporaryFileSystemResource` deletes it after the response. That correction is what makes Act II possible at all.

And one that isn't a query bug but is worth naming for anyone running a content pipeline: **the same behaviour got two different ATT&CK techniques on two consecutive days.** Monday mapped the heapdump work to **T1005 Data from Local System**. Tuesday mapped it to **T1190 Exploit Public-Facing Application**. Same endpoint, same source report, same threat, two techniques — which means a coverage map fed by both days has one behaviour reporting coverage in two cells and no way to notice. Neither mapping is unreasonable in isolation. That's the problem: a plausible mapping and a correct mapping look identical, and nothing downstream ever contradicts either one.

Every one of these came straight out of this week's daily briefs — each detection shipped with ATT&CK mappings, telemetry requirements, deployment gates, triage runbooks, false-positive notes, and an honest readiness call. Twenty-eight of them this week, and once again the ones I disagreed with were the ones worth writing about.

This kind of detection content is published _daily_ — fresh threat intel translated straight into deployable detections, so you spend your time tuning and shipping instead of reading and re-deriving — that's the whole point of the **[Daily Detection Engineering Brief at DevSecOpsDadAttack.com](https://devsecopsdadattack.com/detectionengineering/)**.

<br/>

---

<br/>

## Helpful Links and References:

This Week's Detection Engineering Briefs:
- [Monday, 27th July](https://devsecopsdadattack.com/2026-07-27-detection-engineering-brief-monday-july-27-2026/)
- [Tuesday, 28th July](https://devsecopsdadattack.com/2026-07-28-detection-engineering-brief-tuesday-july-28-2026/)
- [Wednesday, 29th July](https://devsecopsdadattack.com/2026-07-29-detection-engineering-brief-wednesday-july-29-2026/)
- [Thursday, 30th July](https://devsecopsdadattack.com/2026-07-30-detection-engineering-brief-thursday-july-30-2026/)
- [Friday, 31st July](https://devsecopsdadattack.com/2026-07-31-detection-engineering-brief-friday-july-31-2026/)
- [Saturday, 1st August](https://devsecopsdadattack.com/2026-08-01-detection-engineering-brief-saturday-august-1-2026/)
- [Sunday, 2nd August](https://devsecopsdadattack.com/2026-08-02-detection-engineering-brief-sunday-august-2-2026/)

DevSecOpsDadAttack Tags:
- [detection-engineering](https://devsecopsdadattack.com/tags/#detection-engineering)
- [kql](https://devsecopsdadattack.com/tags/#kql)
- [Spring Boot](https://devsecopsdadattack.com/tags/#Spring-Boot)
- [Actuator](https://devsecopsdadattack.com/tags/#Actuator)
- [heapdump](https://devsecopsdadattack.com/tags/#heapdump)
- [Java](https://devsecopsdadattack.com/tags/#Java)
- [JVM](https://devsecopsdadattack.com/tags/#JVM)
- [ASIM](https://devsecopsdadattack.com/tags/#ASIM)
- [Web Session](https://devsecopsdadattack.com/tags/#Web-Session)
- [CommonSecurityLog](https://devsecopsdadattack.com/tags/#CommonSecurityLog)
- [CEF](https://devsecopsdadattack.com/tags/#CEF)
- [DeviceFileEvents](https://devsecopsdadattack.com/tags/#DeviceFileEvents)
- [column_ifexists](https://devsecopsdadattack.com/tags/#column-ifexists)
- [Three-Valued Logic](https://devsecopsdadattack.com/tags/#Three-Valued-Logic)
- [Null Handling](https://devsecopsdadattack.com/tags/#Null-Handling)
- [Attack Surface](https://devsecopsdadattack.com/tags/#Attack-Surface)
- [CVE-2026-66066](https://devsecopsdadattack.com/tags/#CVE-2026-66066)
- [CVE-2026-63077](https://devsecopsdadattack.com/tags/#CVE-2026-63077)
- [CVE-2026-59309](https://devsecopsdadattack.com/tags/#CVE-2026-59309)
- [CVE-2026-16232](https://devsecopsdadattack.com/tags/#CVE-2026-16232)
- [T1190](https://devsecopsdadattack.com/tags/#T1190)
- [T1552](https://devsecopsdadattack.com/tags/#T1552)
- [T1005](https://devsecopsdadattack.com/tags/#T1005)
- [Microsoft Sentinel](https://devsecopsdadattack.com/tags/#Microsoft-Sentinel)
- [Defender XDR](https://devsecopsdadattack.com/tags/#Defender-XDR)

ATT&CK Coverage in This Article:

**Detected by the queries above:**
- **T1190** — Exploit Public-Facing Application (Act I: a request to an exposed management endpoint that returns process memory. The technique covers abuse of internet-facing software weaknesses including misconfiguration, which is what an exposed actuator surface is.)

**Present in the activity, not cleanly mappable:**
- **T1552** — Unsecured Credentials, at the **parent** level only. The heap contains plaintext database passwords, API keys, tokens, and signing material, and the adversary obtains them without touching an identity system. But read the sub-techniques: `.001 Credentials In Files` describes credentials at rest on a filesystem the adversary can already reach; `.004 Private Keys` is about key material specifically; `.007 Container API` is a different plane entirely. None of them describes *credentials resident in process memory, served to an unauthenticated caller by the application itself*. T1003 OS Credential Dumping is the nearest structural analogue and it is explicitly about operating-system credential material, not application secrets. I'm mapping the parent and declining to force a sub-technique, because forcing one would report coverage of a behaviour the query doesn't test.

**Deliberately unmapped:**
- **Act II carries no technique.** The `.hprof` file is written by Spring, not by the adversary. There is no ATT&CK cell for "the application created a temp file while serving a request," and the nearby candidates are all wrong in the same way: they assert an adversary action that didn't occur. It is an artifact, not a behaviour — the same call last week's article made for `logAzure.txt` and `AzureCommunication.dll`, for the same reason.
- **The honorable mention carries no technique either, and it's the more interesting case.** The tempting mappings are `T1595 Active Scanning` or `T1592 Gather Victim Host Information`, and both are wrong, because the query is not detecting the scanner. It's inventorying **your configuration**. The adversary is incidental to it — the same rows appear if the only caller was your own uptime monitor. A configuration finding is not adversary behaviour and does not belong on a coverage map. If yours has nowhere to put "we are exposed," that's a gap in the map.

**Discussed as a correction, not covered by any query here:**
- **T1005 vs T1190 on the same behaviour.** Monday filed the heapdump work under T1005 Data from Local System; Tuesday filed it under T1190. T1005 is the weaker of the two here — it describes an adversary searching a system they have access to, and in this campaign the adversary has no system access at all, only an HTTP client. Pick one, and prefer T1190 for the access with T1552 alongside for what was taken.

External Sources:
- Johannes B. Ullrich / SANS Internet Storm Center. *Java Spring Boot "heapdump" scans.* 27 July 2026. <https://isc.sans.edu/diary/33188>
- Spring Boot Actuator API documentation. *Heap Dump (heapdump).* <https://docs.spring.io/spring-boot/api/rest/actuator/heapdump.html>
- Spring Boot API documentation. *HeapDumpWebEndpoint.* <https://docs.spring.io/spring-boot/api/java/org/springframework/boot/actuate/management/HeapDumpWebEndpoint.html>
- Microsoft Learn. *CEF and CommonSecurityLog field mapping.* <https://learn.microsoft.com/en-us/azure/sentinel/cef-name-mapping>
- Microsoft Learn. *The Advanced Security Information Model (ASIM) Web Session normalization schema reference.* <https://learn.microsoft.com/en-us/azure/sentinel/normalization-schema-web>
- Rapid7. *KindaRails2Shell: CVE-2026-66066, Critical Arbitrary File Read and Possible Remote Code Execution in Ruby on Rails.* <https://www.rapid7.com/blog/post/etr-kindarails2shell-cve-2026-66066-critical-arbitrary-file-read-and-possible-remote-code-execution-in-ruby-on-rails>


<br/>

---

<br/>

# Stay Ahead of Emerging Threats

_Looking for actionable threat intelligence and detection engineering insights?_

DevSecOpsDadAttack publishes daily:

📈 Threat Intelligence Briefs focused on active campaigns, exploitation trends, and operational risk <br/><br/>
🛠️ Detection Engineering Briefs with ATT&CK mappings, telemetry requirements, KQL detections, tuning guidance, and triage workflows <br/><br/>
🔍 Practical analysis designed for SOC teams, threat hunters, detection engineers, and security leaders <br/><br/>

Visit [DevSecOpsDadAttack.com](https://devsecopsdadattack.com) for the latest intelligence and detection content.

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://devsecopsdadattack.com" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Attack1.png"
      style="width: auto; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
</div>

<br/><br/>

# 📚 Want to go deeper?

Anyone can aggregate threat intel.
Very few teams can prove why they acted—or why they didn’t.

The below books are about closing that gap; turning curated signal into defensible decisions across KQL, PowerShell, and the Microsoft security stack.

<br/><br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/hZ1TVpO" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/KQL Toolbox Cover.jpg"
      alt="KQL Toolbox: Turning Logs into Decisions in Microsoft Sentinel"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🛠️ <strong>KQL Toolbox:</strong> Turning Logs into Decisions in Microsoft Sentinel
  </p>
</div>

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/ifIo6eT" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/PowerShell-Cover.jpg"
      alt="PowerShell Toolbox: Hands-On Automation for Auditing and Defense"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🧰 <strong>PowerShell Toolbox:</strong> Hands-On Automation for Auditing and Defense
  </p>
</div>

<br/>

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/4vveVCI" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg"
      alt="Ultimate Microsoft XDR for Full Spectrum Cyber Defense"
      style="max-width: 340px; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    📖 <strong>Ultimate Microsoft XDR for Full Spectrum Cyber Defense</strong><br/>
    Real-world detections, Sentinel, Defender XDR, and Entra ID — end to end.
  </p>
</div>

<br/>
