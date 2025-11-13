# Introduction & Use Case: Audit Readiness Without the Burnout

Let’s be honest — nobody looks forward to audit season.
Between spreadsheets, evidence collection, screenshots of portal settings, and the dreaded “please export that to CSV,” most security teams burn entire weekends chasing compliance data that PowerShell could have gathered in minutes.

That’s where this PowerShell Toolbox comes in.
I built and refined these four scripts to automate the grunt work behind CIS Benchmarks, NIST 800-53, CMMC 2.0, and other security assessments. They surface exactly what auditors ask for — privileged roles, network exposure, GPO compliance, and end-of-life assets — in repeatable, exportable formats.

So grab your coffee, crack open VS Code, and let’s make audit prep something you actually look forward to (or at least don’t dread).


# 🧠 What `Write-Progress` Does

`Write-Progress` displays a progress bar in the PowerShell console to give the user visual feedback on long-running tasks.

It’s **purely informational** — it doesn’t affect the logic of the script; it just shows the *status*, *percentage complete*, and *activity description*.

<br/>
<br/>
<br/>
<br/>

## ⚙️ Syntax Overview

```powershell
Write-Progress
    [-Activity] <string>
    [[-Status] <string>]
    [[-PercentComplete] <int>]
    [-CurrentOperation <string>]
    [-Id <int>]
    [-ParentId <int>]
    [<CommonParameters>]
```

### Key Parameters Explained:

| Parameter               | Description                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------- |
| **`-Activity`**         | The main label describing what’s happening (e.g. “Processing files”).              |
| **`-Status`**           | A short message describing the current step (e.g. “Copying file 3 of 10”).         |
| **`-PercentComplete`**  | Integer (0–100) indicating progress percentage.                                    |
| **`-CurrentOperation`** | More detail about what’s currently happening within the task.                      |
| **`-Id`**               | Identifies the progress bar instance (useful when running multiple progress bars). |
| **`-ParentId`**         | Groups child progress bars under a parent (for nested tasks).                      |

<br/>
<br/>
<br/>
<br/>

## 🧩 Example Script — Simulated File Processing

Here’s a **fully commented PowerShell script** that demonstrates `Write-Progress` in action:

```powershell
# ----------------------------------------------------------------------
# Example: Demonstrate Write-Progress in PowerShell
# Description: Simulates processing 10 files with progress updates.
# ----------------------------------------------------------------------

# Define how many files to simulate
$totalFiles = 10

# Start the main loop
for ($i = 1; $i -le $totalFiles; $i++) {

    # Calculate percentage completion
    $percentComplete = [math]::Round(($i / $totalFiles) * 100, 0)

    # Simulate "processing" by waiting a short time
    Start-Sleep -Milliseconds 500

    # Display the progress bar
    Write-Progress `
        -Activity "Processing files..." `               # Main task name
        -Status "Processing file $i of $totalFiles" `   # Current status line
        -PercentComplete $percentComplete `             # Percent progress
        -CurrentOperation "Working on file_$i.txt"      # More detailed info
}

# Once the loop completes, clear the progress bar
Write-Progress -Activity "Processing files..." -Completed

# Optional: Confirm completion
Write-Host "✅ All $totalFiles files have been processed successfully!"
```

<br/>
<br/>
<br/>
<br/>

## 🪄 Output Behavior

When run in a PowerShell console:

* You’ll see a **progress bar** update in place (it doesn’t scroll the screen).
* The **Activity** line shows the main task (“Processing files...”).
* The **Status** line updates with each file.
* The **progress percentage** automatically updates.
* When finished, `-Completed` removes the progress bar.

---

## 💡 Bonus Tip — Nested Progress Bars

You can track sub-tasks with **`-ParentId`**:

```powershell
for ($i = 1; $i -le 3; $i++) {
    Write-Progress -Activity "Main Task" -Status "Phase $i" -PercentComplete (($i/3)*100) -Id 1

    for ($j = 1; $j -le 5; $j++) {
        Write-Progress -Activity "Sub-Task $i" -Status "Item $j of 5" -PercentComplete (($j/5)*100) -Id 2 -ParentId 1
        Start-Sleep -Milliseconds 300
    }
}
Write-Progress -Activity "Main Task" -Completed
```

This creates **a main progress bar with sub-progress bars** underneath — great for loops within loops (e.g., scanning folders and then files).

<br/>
<br/>
<br/>
<br/>

# 📚 Bonus: Want to Go Deeper?

If this kind of automation gets your gears turning, check out my book:
🎯 Ultimate Microsoft XDR for Full Spectrum Cyber Defense
 — published by Orange Education, available on Kindle and print. 👉 Get your copy here: [📘Ultimate Microsoft XDR for Full Spectrum Cyber Defense](https://a.co/d/0HNQ4qJ)

⚡ It dives into Defender XDR, Sentinel, Entra ID, and Microsoft Graph automations just like this one — with real-world MSSP use cases and ready-to-run KQL + PowerShell examples.

&#128591; Huge thanks to everyone who’s already picked up a copy — and if you’ve read it, a quick review on Amazon goes a long way!

![Ultimate Microsoft XDR for Full Spectrum Cyber Defense](/assets/img/Ultimate%20XDR%20for%20Full%20Spectrum%20Cyber%20Defense/cover11.jpg)


<br/>
<br/>
<br/>
<br/>

<a href="https://hanleycloudsolutions.com">
    <img src="/assets/img/footer.png">
</a>

![www.hanley.cloud](/assets/img/IoT%20Hub%202/footer.png)