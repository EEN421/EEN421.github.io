# 🧰 PowerShell Toolbox: Linting Your Scripts with `Invoke-ScriptAnalyzer`
*Because even your PowerShell scripts deserve a code review ☕🔍*

If there’s one universal truth in DevSecOps, it’s this:  
**the code you wrote at 1 AM absolutely *does* contain a bug — you just haven’t found it yet.**

We lint Python.  
We lint JavaScript.  
We lint YAML because *of course* we forgot a space after a colon somewhere.

PowerShell? Yep — it has a linter too. And a sneaky good one.

Let me introduce you to your new best friend:  
**`Invoke-ScriptAnalyzer`** — the PowerShell code reviewer that never sleeps, never sugarcoats, and definitely never lets you ship a half-asleep `Write-Host` to production.

---

# 🧔☕ DevSecOpsDad-Style Intro

Before we jump into the example, let’s talk about why this little cmdlet deserves a permanent spot in your PowerShell toolbox. If you’re anything like me, half your scripts are written during coffee-fueled “just-let-me-automate-one-more-thing-before-bed” sessions 🧉💻 — and while they *work*, they’re often held together by duct tape, good intentions, and the faint smell of burnt espresso.

That’s where **`Invoke-ScriptAnalyzer`** swoops in. It’s like having a PowerShell code reviewer living inside your terminal — one that doesn’t judge you (too harshly), but still calls you out when you forget indentation, misuse cmdlets, or resurrect `Write-Host` like it’s 2012. Whether you’re pushing scripts to production, running tools in a client’s tenant, or polishing code for your next blog post, ScriptAnalyzer keeps you honest, clean, and safe.

---

# 🧠 What `Invoke-ScriptAnalyzer` Does

`Invoke-ScriptAnalyzer` comes from the **PSScriptAnalyzer** module — a static analysis engine that scans your PowerShell scripts for:

- Errors  
- Warnings  
- Style violations  
- Deprecated patterns  
- Security risks  
- Performance issues  
- Cross-platform compatibility problems  

Think of it as **`lint` for PowerShell**, tuned to the official PowerShell Best Practices.

---

# 🛡️ Why ScriptAnalyzer Matters for Security People

This is where things get fun — because ScriptAnalyzer isn’t just about pretty code.  
It’s a **security tool** hiding in plain sight.

Security folks aren’t just worried about whether a script runs — we’re worried about what it might *break*, *expose*, or *accidentally reveal* along the way. Even seemingly small scripts interact with:

- Graph API  
- Azure resources  
- Entra ID  
- Sentinel/Defender data  
- Privileged permissions  
- Customer tenants (for MSSPs)

That makes secure coding a **defensive discipline**, not just a dev task.

Here’s why ScriptAnalyzer is essential for security pros:

### 🔐 1. Prevents accidental security weaknesses  
It flags things like:

- Hard-coded secrets  
- Plain-text credentials  
- Deprecated risky cmdlets (`Invoke-Expression`)  
- Unsafe string handling  
- Injection-prone patterns  
- Debug logging you forgot to remove  

It catches the stuff attackers love — before attackers ever see it.

---

### 🧯 2. Reduces human error in automated SOC/IR workflows  
A broken script in an automated playbook isn’t just inconvenient — it’s dangerous.

Bad scripts can:

- Mangle Defender ATP data  
- Break Logic Apps  
- Mis-tag cloud resources  
- Corrupt audit logs  
- Apply policies incorrectly  
- Modify RBAC roles the wrong way  

ScriptAnalyzer provides a static safety net so simple mistakes don’t turn into big outages.

---

### 🪪 3. Critical for MSSPs and consultants  
If you work in multiple tenants, consistency and safety aren’t “nice-to-have” — they’re required.

ScriptAnalyzer helps you avoid:

- Shipping broken automation  
- Running deprecated modules  
- Violating internal coding standards  
- Creating regressions across clients  

Cleaner scripts = fewer escalations = happier clients = fewer 11 PM emergencies.

---

### 🧬 4. Creates consistent, auditable, repeatable code  
Security teams live on repeatability.

ScriptAnalyzer enforces:

- Naming consistency  
- Param block consistency  
- Function structure consistency  
- Safe coding defaults  

This makes your scripts easier to review, easier to hand off, and easier to integrate into future tooling.

---

### 🧠 5. Teaches secure PowerShell habits  
Every warning is a tiny lesson:

- *“Here's a safer verb…”*  
- *“This alias makes things ambiguous…”*  
- *“This cmdlet casing breaks style guidelines…”*  

It's like pair-programming with the PowerShell team.

---

# 📚 ScriptAnalyzer Rule Categories (Explained DevSecOpsDad Style)

## 🧹 **1. Formatting Rules**
*"Because misaligned braces hurt feelings and readability."*

Checks for consistent indentation, whitespace, casing, and layout.

## 🎛️ **2. Style Rules**
*"Do you really need three aliases in a row? No. You do not."*

Flags aliases, positional parameters, incorrect naming, quoting issues, etc.

## 🔐 **3. Security Rules**
*"Because the threat actors don’t need you helping them out."*

Catches unsafe cmdlets, hard-coded secrets, injection patterns, and more.

## 🧪 **4. Performance Rules**
*"You could run that… or you could run it *faster*."*

Identifies slow patterns, unnecessary loops, and deprecated commands.

## 🚫 **5. Compatibility Rules**
*"Your script may work on PowerShell 7… but what about that old VM in the corner?"*

Ensures scripts work across platforms and PowerShell versions.

## 🧩 **6. Maintainability Rules**
*"Future you will want to hug present you for using these."*

Encourages clean function structures, comments, and reusable logic.

## 🚦 **7. Semantic Rules**
*"Not just how it looks — but what it *means*."*

Flags unused variables, unreachable code, and suspicious conditionals.

---

# 🧪 Hands-On Example: Analyzing a Script with ScriptAnalyzer

Let’s walk through a full example that:

1. Installs PSScriptAnalyzer  
2. Creates a sample “bad” script  
3. Analyzes it  
4. Outputs the results  

```powershell
<#
.SYNOPSIS
    Demonstration of Invoke-ScriptAnalyzer
.DESCRIPTION
    This example creates a sample PowerShell script filled with
    intentional "teachable moments" 😅 and then analyzes it using
    Script Analyzer.
#>

# Step 0 — Make sure PSScriptAnalyzer is available
if (-not (Get-Module -ListAvailable -Name PSScriptAnalyzer)) {
    Write-Host "☕ Installing PSScriptAnalyzer..." -ForegroundColor Cyan
    Install-Module -Name PSScriptAnalyzer -Force -Scope CurrentUser
}

# Step 1 — Create a bad example script
$ScriptPath = "$env:TEMP\TestScript.ps1"

@"
# This script intentionally contains several PowerShell sins 🙈

param(\$inputParam)

Write-Host "Hello world"
if(\$inputParam -eq "test")
{
write-output "Running test..."
}
else
{
write-output "Done"
}
"@ | Set-Content -Path $ScriptPath

Write-Host "📝 Created test script at $ScriptPath" -ForegroundColor Green

# Step 2 — Run the analyzer
Write-Host "`n🔍 Running Invoke-ScriptAnalyzer..." -ForegroundColor Yellow
$results = Invoke-ScriptAnalyzer -Path $ScriptPath

# Step 3 — Display results
if ($results) {
    Write-Host "`n⚠️ Issues found:" -ForegroundColor Red
    $results | Format-Table RuleName, Severity, Line, Message -AutoSize
}
else {
    Write-Host "🎉 No issues found — you're a PowerShell wizard." -ForegroundColor Green
}
🚀 Pro Tip: Add ScriptAnalyzer to Your CI/CD Pipeline
Want to enforce PowerShell best practices automatically?

Add this to GitHub Actions or Azure DevOps:

powershell
Copy code
$failures = Invoke-ScriptAnalyzer -Path .\Scripts -Recurse -Severity Error
if ($failures) {
    Write-Error "❌ ScriptAnalyzer found issues. Fix before merging."
    exit 1
}
Now your repo enforces its own quality gate — like a tiny automated SOC analyst.

🎯 Final Thoughts
Invoke-ScriptAnalyzer isn’t glamorous. It doesn’t spin up VMs, query Sentinel, or summon KQL magic. But it does help you write cleaner, safer, more maintainable PowerShell — and that’s the foundation of every mature DevSecOps practice.

It’s one of those tools that quietly saves you from:

Future bugs

Future rework

Future “who wrote this?” moments

Future weekend firefights

Add it to your toolbox now.
Your future self — and your clients — will thank you. ☕🛡️💻
