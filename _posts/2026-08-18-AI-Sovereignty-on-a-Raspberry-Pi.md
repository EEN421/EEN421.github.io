---
layout: post
title: "AI Sovereignty on a Raspberry Pi: Running Qwen3 with Ollama"
subtitle: "No GPU. No API key. No monthly bill. The model they can’t turn off."
date: 2026-08-17
author: DevSecOpsDad
---

![](/assets/img/QWEN/1.png)

# When the Cloud Says No: Running Qwen3 on a Raspberry Pi 4B with Ollama

*No GPU. No API key. No expensive AI workstation. Just a Raspberry Pi, Ollama, and a small language model that answers to you.*

There is a weird assumption developing around AI infrastructure...

- You need a monster GPU.

- You need a Mac Mini with a pile of unified memory.

- You need one of NVIDIA's shiny new Spark boxes.

- You need a cloud subscription.

- You need an API key.

- You need a datacenter somewhere doing something expensive on your behalf.

For frontier models? Sure. For **every useful AI workload? Absolutely not.**

I wanted something much simpler: a private model I could run inside my own network for tasks where sending the data to someone else's infrastructure was either undesirable or unnecessary.

So I grabbed a Raspberry Pi 4B, installed Ollama, pulled Qwen3, and started talking to it.

**No GPU - No cloud inference - No monthly AI bill.**

And, perhaps more importantly, no one else gets to decide **when** I can use it.

<br/>

---

<br/>

## The Little AI Box

For this project, I sprung for the **8GB Raspberry Pi 4B**.

Going into it, I assumed RAM would be the limiting factor; **_It wasn't._**

Once you've picked a model small enough to fit comfortably into memory, the much more obvious constraint on a Raspberry Pi is **compute**. Not how much data the board can hold — but how fast its CPU can chew through transformer math without a GPU doing the heavy lifting.

Ollama supports ARM64 Linux, so running it on a 64-bit Raspberry Pi OS installation is straightforward. But there is no NVIDIA GPU hiding underneath the Pi's heatsink waiting to accelerate transformer inference. For this build, the work is being done entirely by the Cortex-A72. All four of them. Slowly.

That means the experience is not:

> prompt → instantaneous wall of text

It's more:

> prompt → Raspberry Pi thinks very hard about its life choices → tokens start appearing

And that's fine. The goal here isn't to build a Raspberry Pi competitor to a rack of H100s.

The goal is to build a **private inference appliance**... Something quiet, something cheap, something sitting on your network that can answer questions _**without your prompt ever needing to leave the building**_.

This is more accessible and more affordable than the current hype cycle around AI chipmaking would have you believe. You don't need the NVIDIA Spark. You don't need a new Mac Mini. _**You need a credit-card-sized board and about twenty minutes.**_

<br/>

![](/assets/img/QWEN/2.png)

<br/>

---

<br/>

## LLM or SLM?

Technically, calling what I'm running an **SLM — Small Language Model — is probably more honest**.

Qwen3 is a family of language models ranging from tiny dense models all the way up to enormous mixture-of-experts models. Qwen released dense variants including 0.6B and 1.7B parameter models specifically small enough to make edge deployments interesting.

Those are the two I'm interested in here:

```bash
qwen3:1.7b
qwen3:4b
```

Ollama currently packages the 0.6B model at roughly **523MB** and the 1.7B model at roughly **1.4GB**.

That changes the economics of the whole experiment.

We're not talking about trying to squeeze a 70-billion-parameter model onto a Raspberry Pi and calling the smoke coming out of the USB-C port "inference."

We're choosing the _right tool_ for the hardware; **Small model. Small machine. Private workload**.

<br/>

![](/assets/img/QWEN/3.png)

<br/>

---

<br/>

# Act I: Prepare the Pi

I'm running **Raspberry Pi OS Trixie** — the latest 64-bit release, Lite variant, CLI only. No desktop environment burning cycles on a GPU that doesn't exist.

Start with the usual housekeeping:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y curl
```

If you want to verify you're running a 64-bit userspace:

```bash
uname -m
```

You want:

```text
aarch64
```

Ollama publishes an ARM64 Linux build, which is what makes this deployment pleasantly boring.

And boring infrastructure is good infrastructure.


<br/>

---

<br/>

# Act II: About That Swap File

A lot of Raspberry Pi LLM tutorials immediately tell you to create several gigabytes of swap.

That made sense to me too.

So my original build notes included expanding swap from around 200MB to 2GB using `dphys-swapfile`, like so:

```bash
sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo systemctl restart dphys-swapfile
```

Except there's an important wrinkle if you're using **Raspberry Pi OS Trixie**:

`dphys-swapfile` doesn't exist anymore.

Trixie doesn't ship it. If you try to run the command above, you'll get:

```text
sed: can't read /etc/dphys-swapfile: No such file or directory
```

Trixie introduced Raspberry Pi's newer `rpi-swap` system, which supports **zram**, traditional file-backed swap, or a hybrid of the two. Raspberry Pi specifically designed it to replace `dphys-swapfile`.

Before changing anything, check what the Pi is actually doing:

```bash
free -h
swapon --show
```

<br/>

![memory](/assets/img/QWEN/swap.png)

Here's the funny part.

On my 8GB Pi running Trixie, swapon showed **2GB of zram swap already configured out of the box:**

```text
NAME       TYPE      SIZE USED PRIO
/dev/zram0 partition   2G   0B  100
```

<br/>

![](/assets/img/QWEN/4.png)

<br/>

**I didn't need to increase swap at all.**

That was probably my first indication that RAM wasn't going to be the interesting bottleneck in this project.

The CPU was.

### If Trixie actually needs more swap

If you are seeing memory pressure and want to force a traditional 2GB swapfile on current Raspberry Pi OS, the `rpi-swap` configuration provides a drop-in override:

```bash
sudo mkdir -p /etc/rpi/swap.conf.d/

sudo tee /etc/rpi/swap.conf.d/80-use-swapfile.conf > /dev/null <<EOF
[Main]
Mechanism=swapfile

[File]
FixedSizeMiB=2048
EOF

sudo reboot
```

Check again after reboot:

```bash
swapon --show
free -h
```

If your model is already running comfortably, however, don't create swap merely because a tutorial told you to.

More swap doesn't make your CPU faster.

<br/>

---

<br/>

# Act III: Install Ollama

This is the part where I expected some Raspberry-Pi-specific nonsense.

There really wasn't any.

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

<br/>

![install](/assets/img/QWEN/install.png)

<br/>

That's the current Linux installation method published by Ollama. The script detects `aarch64`, pulls the ARM64 binary, creates a systemd service, and starts it. You'll see a warning about not finding a GPU — that's expected. There isn't one.

Verify it:

```bash
ollama --version
```

And because the installer configures Ollama as a service on Linux, you can check that too:

```bash
systemctl status ollama --no-pager
```

Congratulations! - Your $75 Raspberry Pi is now an AI server (sort of)... We still need a brain.

---

# Act IV: Give It a Brain

For the Pi 4B, I'd start with Qwen3 0.6B:

```bash
ollama pull qwen3:1.7b
```

![Qwen3:1.7b](/assets/img/QWEN/3-1.7b.png)

<br/>

> Note: I found that Qwen3:4b reflected better, more accurate responses (less hallucinations). 

The size difference isn't particularly scary. That's part of what surprised me about this project.

There is so much noise around AI hardware right now — trillions of dollars in chip investment, entire power plants being built for inference clusters, the AI infrastructure arms race playing out across every earnings call — that it's easy to develop a completely distorted idea of what running a model actually requires.

Yes, training frontier models involves absurd amounts of compute. Yes, running massive models locally benefits enormously from expensive GPUs.

But **those aren't the only models that exist**.

If what you need is a small private assistant that can summarize text, inspect a configuration, reason about some code, transform data, or help analyze information you don't particularly want uploaded to a third party, the entry price is a Raspberry Pi and an SD card. Not an NVIDIA DGX. Not a cloud subscription. Not a Mac Studio.

A Raspberry Pi.

<br/>

---

<br/>

# Act V: Talk to It

Run the model:

```bash
ollama run qwen3:4b
```

You'll get a prompt.

Ask it something.

```text
>>> tell me about your capabilities and what your were designed to do please.
```

![](/assets/img/QWEN/Qwen3-4b.png)

And your Raspberry Pi will start generating the response locally.

- No API token was exchanged.

- No request was sent to OpenAI.

- No request was sent to Anthropic.

- No prompt needed to leave your network.

- Ollama states that when models are run locally, prompts and responses are processed locally rather than being sent back to Ollama's service.

That's the entire reason I built this thing.

<br/>

---

<br/>

# The Performance Reality

Let's set expectations appropriately: The Raspberry Pi 4B is not secretly an AI workstation.

With no supported GPU accelerator doing the inference work, you're asking _**four ARM CPU cores**_ to perform a job modern AI accelerators were explicitly designed to perform faster. **A lot faster**.

So yes: **It's slow.**

But "slow" and "useless" are not the same. 😜

<br/>

![](/assets/img/QWEN/5.png)

<br/>

For interactive chat, experimentation, text analysis, small automation workflows, home-lab services, and privacy-sensitive jobs where a few seconds matter significantly less than where the data goes? **It works.**

And the 8GB RAM in my Pi turned out to be more breathing room than necessity for the 0.6B model. It's the CPU where I feel the constraint. This is actually useful information when deciding what Pi to buy for this project. If you're choosing between a 4GB and 8GB board specifically for SLM inference, the 8GB gives you headroom to run the 1.7B model comfortably. _**But don't assume that jumping from 4GB to 8GB magically doubles inference speed, because it doesn't**_

Once the model fits, you're waiting on compute.

<br/>

---

<br/>

# Act VI: Turn the Pi Into an API

Running Qwen from an SSH session is neat. Turning the Pi into an AI service for the rest of your network is much more interesting. Ollama exposes a REST API on port `11434`, but by default it listens only on:

```text
127.0.0.1:11434
```

That means the Pi itself can reach Ollama, but another device on your LAN can't.

First test the API locally:

```bash
curl http://localhost:11434/api/chat \
  -d '{
    "model": "qwen3:1.7b",
    "messages": [
      {
        "role": "user",
        "content": "Explain what a Raspberry Pi is in one sentence."
      }
    ],
    "stream": false
  }'
```

Now make it network-accessible.

Edit the Ollama service:

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Save it, then reload systemd and restart Ollama:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

That `:11434` is worth including explicitly; it's also how Ollama documents the Linux configuration.

Find the Pi's address:

```bash
hostname -I
```

Now another machine on the network can test it:

```bash
curl http://PI_IP_ADDRESS:11434/api/tags
```

<br/>

![](/assets/img/QWEN/6.png)

<br/>

And suddenly the Pi isn't just running an SLM.

It's providing an **AI service** 😎

---

# Act VII: Don't Put Port 11434 on the Internet

![](/assets/img/QWEN/7.png)

This is **_DevSecOpsDad_**. So we're going to talk about **security**.

```ini
OLLAMA_HOST=0.0.0.0:11434
```

means:

> Listen on every network interface.

It does **not** mean:

> Magically turn this into a secure production AI API.

Those are **_very_** different statements.

I would not port-forward `11434` through my router and expose Ollama directly to the Internet. Ollama has no authentication. No TLS. No rate limiting. If you expose it raw, anyone who finds the port can use your model, abuse your hardware, and read every prompt and response in transit.

I don't need to; if I want to use this thing remotely, I already have a much better architectural pattern:

```text
Phone
   |
WireGuard
   |
Home Network
   |
Raspberry Pi
   |
Ollama
   |
Qwen
```

- The model stays private.

- The API stays private.

- Remote access is handled by the VPN.

That's exactly how I'd rather design it anyway.

<br/>

---

<br/>

# The Use Cases Are More Interesting Than the Benchmark

This isn't going to replace ChatGPT; that's not the point. I still want frontier models when the task deserves frontier-model capability, but there is another category of problem where capability isn't my only concern.

Sometimes **data ownership** matters more. Say I want to review six months of exported banking transactions and ask:

```text
Where is my money actually going?
```

I'd rather not upload raw financial records to another company's infrastructure just because I want some categories and percentages. Maybe I'd like to upload medical records such as X-Rays and ask questions. Or maybe I want an AI assistant to inspect:

```text
index.html
.env.example
docker-compose.yml
nginx.conf
```

from one of my projects.

Maybe the repository contains internal hostnames, architecture, customer identifiers, API endpoints, or configuration patterns... Or perhaps I'm responding to an incident and want a model to chew on logs, commands, malicious scripts, or other content that a commercial model's cybersecurity safety system may decide it doesn't want to process.

That's where the local box starts making an awful **lot** of sense.

<br/>

![](/assets/img/QWEN/8.png)

<br/>

---

<br/>

# And Then Hugging Face Got Hacked

This project became more interesting almost immediately because of something that happened in July 2026.

During an advanced cybersecurity evaluation, OpenAI's GPT-5.6 Sol and a more capable unreleased model escaped their sandboxed testing environment, accessed the Internet, and compromised Hugging Face's production infrastructure. The models had been trying to find information to cheat on their evaluation — and they succeeded. Hugging Face described the incident as the first time it had handled a cyber event "driven, end to end, by an autonomous AI agent system."

OpenAI subsequently described it as an unprecedented cybersecurity incident.

But there was another part of the story that caught my attention.

During the response, Hugging Face's security team tried to use frontier AI models behind commercial APIs to analyze more than 17,000 log events — a completely reasonable thing to do when you're drowning in attack telemetry. **_The requests were blocked._** The providers' safety guardrails could not distinguish between an incident responder reconstructing an intrusion and an attacker preparing one. The same exploit payloads, C2 artifacts, and attack commands that defenders need to analyze are exactly the content those classifiers are trained to refuse.

<br/>

![](/assets/img/QWEN/9.png)

<br/>

Hugging Face's own incident report put it bluntly: *"The attacker was bound by no usage policy, while our own forensic work was blocked by the guardrails of the hosted models we first tried."*

So they switched to GLM 5.2, an open-weight model from China's Z.ai lab, and ran it locally on their own infrastructure. Not only did it process the data the commercial models refused — it kept every credential, every attacker artifact, and every indicator of compromise inside Hugging Face's environment. Nothing left the building.

That is an extraordinary real-world example of something defenders have been discussing for years.

**It doesn't matter how capable your tool theoretically is if you aren't allowed to use it when you actually need it.**

And I understand why those guardrails exist... Cybersecurity is dual-use: **_the same model that explains how an exploit works to a defender can explain how it works to an attacker._**

That is a genuinely difficult problem for hosted AI providers, but that difficulty exposes another problem: **The provider owns the control plane.**

- They decide the policy.

- They decide what the model will process.

- They decide whether your account can access a feature.

- They decide whether a particular class of request is permitted.

And if their service is unavailable — or if their classifier thinks your forensic analysis looks a little too much like an attack — neither your prompt engineering nor your subscription tier will make the API answer.

<br/>

---

<br/>

# Self-Hosted Changes the Control Plane

<br/>

![](/assets/img/QWEN/10.png)

<br/>

This is where I think the humble Raspberry Pi becomes philosophically more interesting than its benchmark score:

- My Qwen instance doesn't need to phone OpenAI before answering me.

- Anthropic can't disable it.

- OpenAI can't rate-limit it.

- There isn't an account to suspend.

- There isn't an API key to expire.

- There isn't a safety classifier sitting between me and the model deciding whether my incident-response artifact looks too offensive to analyze.

Once the model weights are downloaded, inference doesn't depend on a model provider's service being reachable. It doesn't depend on their content policy. It doesn't depend on their uptime. It doesn't depend on their opinion about what I should be allowed to do with a language model.

As long as I have:

```text
Power
+
Hardware
+
The model
```

I have inference.

That's not an argument against commercial AI, it's an argument for **resilience through ownership**.

Cloud AI and local AI solve different problems. Use both.

<br/>

---

<br/>

# Your AI Doesn't Have to Be Huge to Be Yours

The AI industry is currently obsessed with scale.

- More GPUs.

- More parameters.

- More datacenters.

- More power.

- More billions of dollars spent producing the next model.

And all of that is fascinating, but there's another direction worth exploring: **smaller.**

- A tiny computer.

- A tiny model.

- A tiny API.

- Sitting quietly on a shelf.

- Answering questions for one household or one lab.

- Costing less than a decent pair of running shoes.

The interesting part isn't that a Raspberry Pi 4B can outperform a GPU server; **it can't**. The interesting part is that **it doesn't need one** to be useful. I bought the 8GB Pi expecting memory to be the challenge, and it wasn't. I expected swap configuration to matter, it didn't — Trixie already had 2GB of zram configured. I expected running an AI model locally to involve significantly more engineering, it didn't.

What I ended up with was roughly:

```bash
sudo apt update && sudo apt full-upgrade -y && sudo apt install -y curl
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:1.7b
ollama run qwen3:1.7b
```

Four commands between:

```text
Raspberry Pi
```

and:

```text
Private AI server
```

<br/>

![](/assets/img/QWEN/11.png)

<br/>

The model isn't enormous.

The hardware isn't impressive.

The tokens aren't instantaneous.

But the machine is mine.

The data is mine.

And the off switch is mine too.

**That's a feature no benchmark measures.**


<br/>
<br/>

# 📚 Want to go deeper?

My **Toolbox** books turn real Microsoft security telemetry into defensible operations:

<div style="text-align:center; margin: 2.5em 0;">
  <a href="https://a.co/d/ifIo6eT" target="_blank" rel="noopener noreferrer">
    <img 
      src="/assets/img/PowerShell-Cover.jpg"
      alt="PowerShell Toolbox: Hands-On Automation for Auditing and Defense"
      style="width: 215px; margin: 0 auto; box-shadow: 0 16px 40px rgba(0,0,0,.45); border-radius: 8px;"
    />
  </a>
  <p style="margin-top: 0.75em; font-size: 0.95em; opacity: 0.85;">
    🧰 <strong>PowerShell Toolbox</strong> Hands-On Automation for Auditing and Defense
  </p>
</div>

<br/>

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
<br/>

# 🔗 Helpful Links & Resources: 
