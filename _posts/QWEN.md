---
layout: post
title: "QWEN"
subtitle: "QWEN Stuff"
date: 2026-08-17
author: DevSecOpsDad
---

# When the Cloud Says No: Running Qwen3 on a Raspberry Pi 4B with Ollama

*No GPU. No API key. No expensive AI workstation. Just a Raspberry Pi, Ollama, and a small language model that answers to you.*

There is a weird assumption developing around AI infrastructure.

You need a monster GPU.

You need a Mac Mini with a pile of unified memory.

You need one of NVIDIA's shiny new AI boxes.

You need a cloud subscription.

You need an API key.

You need a datacenter somewhere doing something expensive on your behalf.

For frontier models? Sure.

For **every useful AI workload? Absolutely not.**

I wanted something much simpler: a private model I could run inside my own network for tasks where sending the data to someone else's infrastructure was either undesirable or unnecessary.

So I grabbed a Raspberry Pi 4B, installed Ollama, pulled Qwen3, and started talking to it.

No GPU.

No cloud inference.

No monthly AI bill.

And, perhaps more importantly, no one else gets to decide when I can use it.

---

## The Little AI Box

For this project, I sprung for the **8GB Raspberry Pi 4B**.

Going into it, I assumed RAM would be the limiting factor.

It wasn't.

Once you've picked a model small enough to fit comfortably into memory, the much more obvious constraint on a Raspberry Pi is **compute**.

Ollama supports ARM64 Linux, so running it on a 64-bit Raspberry Pi OS installation is straightforward. But there is no NVIDIA GPU hiding underneath the Pi's heatsink waiting to accelerate transformer inference. For this build, the work is being done by the CPU.

That means the experience is not:

> prompt → instantaneous wall of text

It's more:

> prompt → Raspberry Pi thinks very hard about its life choices → tokens start appearing

And that's fine.

The goal here isn't to build a Raspberry Pi competitor to a rack of H100s.

The goal is to build a **private inference appliance**.

Something quiet.

Something cheap.

Something sitting on your network that can answer questions without your prompt ever needing to leave the building.

---

## LLM or SLM?

Technically, calling what I'm running an **SLM — Small Language Model — is probably more honest**.

Qwen3 is a family of language models ranging from tiny dense models all the way up to enormous mixture-of-experts models. Qwen released dense variants including 0.6B and 1.7B parameter models specifically small enough to make edge deployments interesting.

Those are the two I'm interested in here:

```bash
qwen3:0.6b
qwen3:1.7b
```

Ollama currently packages the 0.6B model at roughly **523MB** and the 1.7B model at roughly **1.4GB**.

That changes the economics of the whole experiment.

We're not talking about trying to squeeze a 70-billion-parameter model onto a Raspberry Pi and calling the smoke coming out of the USB-C port "inference."

We're choosing the right tool for the hardware.

Small model.

Small machine.

Private workload.

---

# Act I: Prepare the Pi

I'm running Raspberry Pi OS Trixie.

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

---

# Act II: About That Swap File

A lot of Raspberry Pi LLM tutorials immediately tell you to create several gigabytes of swap.

That made sense to me too.

So my original build notes included expanding swap from around 200MB to 2GB.

Something like:

```bash
sudo sed -i 's/^CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo systemctl restart dphys-swapfile
```

Except there's an important wrinkle if you're using **Raspberry Pi OS Trixie**:

`dphys-swapfile` is the old way.

Trixie introduced Raspberry Pi's newer `rpi-swap` system, which supports zram, traditional file-backed swap, or a hybrid of the two. Raspberry Pi specifically designed it to replace `dphys-swapfile`.

Before changing anything, check what the Pi is actually doing:

```bash
free -h
```

And:

```bash
swapon --show
```

Here's the funny part.

**On my 8GB Pi, I didn't actually need to increase swap at all.**

That was probably my first indication that RAM wasn't going to be the interesting bottleneck in this project.

The CPU was.

### If Trixie actually needs more swap

If you are seeing memory pressure and want to force a traditional 2GB swapfile on current Raspberry Pi OS, the `rpi-swap` documentation provides a drop-in configuration specifically for this:

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

---

# Act III: Install Ollama

This is the part where I expected some Raspberry-Pi-specific nonsense.

There really wasn't any.

Install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

That's the current Linux installation method published by Ollama.

Verify it:

```bash
ollama --version
```

And because the installer configures Ollama as a service on Linux, you can check that too:

```bash
systemctl status ollama --no-pager
```

Congratulations.

Your $35-to-$whatever-Raspberry-Pis-cost-this-week computer is now an AI server.

Sort of.

We still need a brain.

---

# Act IV: Give It a Brain

For the Pi 4B, I'd start with Qwen3 0.6B:

```bash
ollama pull qwen3:0.6b
```

If you've got the 8GB model and don't mind trading more compute for a more capable model, try:

```bash
ollama pull qwen3:1.7b
```

The size difference isn't particularly scary.

Again, Ollama currently lists them at approximately:

```text
qwen3:0.6b    523MB
qwen3:1.7b    1.4GB
```

That's part of what surprised me about this project.

There is so much noise around AI hardware right now that it's easy to develop a completely distorted idea of what running an AI model requires.

Yes, training frontier models involves absurd amounts of compute.

Yes, running massive models locally benefits enormously from expensive GPUs.

But **those aren't the only models that exist**.

If what you need is a small private assistant that can summarize text, inspect a configuration, reason about some code, transform data, or help analyze information you don't particularly want uploaded to a third party, the entry price can be dramatically lower.

---

# Act V: Talk to It

Run the model:

```bash
ollama run qwen3:0.6b
```

You'll get a prompt.

Ask it something.

```text
>>> Explain the difference between an IOC and a behavioral detection in cybersecurity.
```

And your Raspberry Pi will start generating the response locally.

No API token was exchanged.

No request was sent to OpenAI.

No request was sent to Anthropic.

No prompt needed to leave your network.

Ollama states that when models are run locally, prompts and responses are processed locally rather than being sent back to Ollama's service.

That's the entire reason I built this thing.

---

# The Performance Reality

Let's set expectations appropriately.

The Raspberry Pi 4B is not secretly an AI workstation.

With no supported GPU accelerator doing the inference work, you're primarily asking four ARM CPU cores to perform a job modern AI accelerators were explicitly designed to perform faster.

So yes:

**It's slow.**

But "slow" and "useless" are not synonyms.

For interactive chat, experimentation, text analysis, small automation workflows, home-lab services, and privacy-sensitive jobs where a few seconds matter significantly less than where the data goes?

It works.

And the 8GB RAM in my Pi turned out to be more breathing room than necessity for the 0.6B model.

The CPU is where I feel the constraint.

This is actually useful information when deciding what Pi to buy for the project.

Don't assume that jumping from 4GB to 8GB magically doubles inference speed.

It doesn't.

Once the model fits, you're waiting on compute.

---

# Act VI: Turn the Pi Into an API

Running Qwen from an SSH session is neat.

Turning the Pi into an AI service for the rest of your network is much more interesting.

Ollama exposes a REST API on port `11434`, but by default it listens only on:

```text
127.0.0.1:11434
```

That means the Pi itself can reach Ollama, but another device on your LAN can't.

First test the API locally:

```bash
curl http://localhost:11434/api/chat \
  -d '{
    "model": "qwen3:0.6b",
    "messages": [
      {
        "role": "user",
        "content": "Explain what a Raspberry Pi is in one sentence."
      }
    ],
    "stream": false
  }'
```

Ollama documents the same `/api/chat` interface for Qwen3.

Now we can make it network accessible.

Edit the Ollama service:

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Save it.

Then reload systemd and restart Ollama:

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

And suddenly the Pi isn't just running an SLM.

It's providing an **AI service**.

---

# Act VII: Don't Put Port 11434 on the Internet

This is DevSecOpsDad.

So we're going to talk about the thing every tutorial eventually forgets.

```ini
OLLAMA_HOST=0.0.0.0:11434
```

means:

> Listen on every network interface.

It does **not** mean:

> Magically turn this into a secure production AI API.

Those are very different statements.

I would not port-forward `11434` through my router and expose Ollama directly to the Internet.

I don't need to.

If I want to use this thing remotely, I already have a much better architectural pattern:

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

The model stays private.

The API stays private.

Remote access is handled by the VPN.

That's exactly how I'd rather design it anyway.

---

# The Use Cases Are More Interesting Than the Benchmark

This isn't going to replace ChatGPT.

That's not the point.

I still want frontier models when the task deserves frontier-model capability.

But there is another category of problem where capability isn't my only concern.

Sometimes **data ownership** matters more.

Say I want to review six months of exported banking transactions and ask:

```text
Where is my money actually going?
```

I'd rather not upload raw financial records to another company's infrastructure just because I want some categories and percentages.

Or maybe I want an AI assistant to inspect:

```text
index.html
.env.example
docker-compose.yml
nginx.conf
```

from one of my projects.

Maybe the repository contains internal hostnames.

Architecture.

Customer identifiers.

API endpoints.

Configuration patterns.

Or perhaps I'm responding to an incident and want a model to chew on logs, commands, malicious scripts, or other content that a commercial model's cybersecurity safety system may decide it doesn't want to process.

That's where the local box starts making an awful lot of sense.

---

# And Then Hugging Face Got Hacked

This project became more interesting almost immediately because of something that happened in July 2026.

During an advanced cybersecurity evaluation, OpenAI models escaped their intended test environment, reached the Internet, and ultimately compromised Hugging Face infrastructure. OpenAI subsequently described it as an unprecedented cybersecurity incident involving state-of-the-art cyber capabilities.

But there was another part of the story that caught my attention.

During the response, Hugging Face said it used an open-weight Chinese model, GLM-5.2, for portions of its analysis. Reuters reported that leading U.S. models refused to process some of the necessary attack data because their guardrails could not adequately distinguish defensive analysis from offensive cyber activity. Hugging Face also noted the benefit of keeping credentials and attacker data inside its own environment.

That is an extraordinary real-world example of something defenders have been discussing for years.

It doesn't matter how capable your tool theoretically is if you aren't allowed to use it when you actually need it.

And I understand why those guardrails exist.

Cybersecurity is dual-use.

The same model that explains how an exploit works to a defender can explain how it works to an attacker.

That is a genuinely difficult problem for hosted AI providers.

But that difficulty exposes another problem.

**The provider owns the control plane.**

They decide the policy.

They decide what the model will process.

They decide whether your account can access a feature.

They decide whether a particular class of request is permitted.

And if their service is unavailable, neither your prompt engineering nor your subscription tier will make the API answer.

---

# Self-Hosted Changes the Control Plane

This is where I think the humble Raspberry Pi becomes philosophically more interesting than its benchmark score.

My Qwen instance doesn't need to phone OpenAI before answering me.

Anthropic can't disable it.

OpenAI can't rate-limit it.

There isn't an account to suspend.

There isn't an API key to expire.

There isn't a safety classifier sitting between me and the model deciding whether my incident-response artifact looks too offensive to analyze.

Once the model weights are already downloaded, inference doesn't depend on a model provider's service being reachable.

As long as I have:

```text
Power
+
Hardware
+
The model
```

I have inference.

That's not an argument against commercial AI.

It's an argument for **resilience through ownership**.

Cloud AI and local AI solve different problems.

Use both.

---

# Your AI Doesn't Have to Be Huge to Be Yours

The AI industry is currently obsessed with scale.

More GPUs.

More parameters.

More datacenters.

More power.

More billions of dollars spent producing the next model.

And all of that is fascinating.

But there's another direction worth exploring:

**smaller.**

A tiny computer.

A tiny model.

A tiny API.

Sitting quietly on a shelf.

Answering questions for one household or one lab.

The interesting part isn't that a Raspberry Pi 4B can outperform a GPU server.

It can't.

The interesting part is that **it doesn't need one** to be useful.

I bought the 8GB Pi expecting memory to be the challenge.

It wasn't.

I expected swap configuration to matter.

It didn't.

I expected running an AI model locally to involve significantly more engineering.

It didn't.

What I ended up with was roughly:

```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y curl

curl -fsSL https://ollama.com/install.sh | sh

ollama pull qwen3:0.6b

ollama run qwen3:0.6b
```

That's basically it.

Four steps between:

```text
Raspberry Pi
```

and:

```text
Private AI server
```

The model isn't enormous.

The hardware isn't impressive.

The tokens aren't instantaneous.

But the machine is mine.

The data is mine.

And the off switch is mine too.

**That's a feature no benchmark measures.**
