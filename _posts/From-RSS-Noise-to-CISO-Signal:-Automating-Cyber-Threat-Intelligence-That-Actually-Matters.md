![Title Image(.png)](/assets/img/SecurityNews/intro.png)

What does your daily “stay current” routine actually look like? If you’re honest, it’s probably a blur—tabs open, feeds scrolling, headlines competing for attention. Cybersecurity moves fast enough that even well-run teams struggle to keep pace. So here’s a better question: what if the signal came to you, already filtered, already prioritized, already useful?

Every morning, security leaders face the same flood:

- dozens of RSS feeds
- overlapping headlines
- vendor-biased narratives
- just enough technical detail to sound important, but not enough to act on

<br/>

Buried somewhere in that noise are the answers that actually matter:

- What’s being exploited right now?
- Who’s truly at risk?
- What needs to be patched, monitored, or escalated today?

Most teams never quite get there. They skim, bookmark, forward a link or two—and then move on to whatever is on fire next. *This is where automation proves its value. Not by collecting more data, but by forcing clarity out of chaos.*

<br/>

![Coffee Cat(.png)](/assets/img/SecurityNews/coffeecat.png)

<br/>

In this post, we’ll walk through a practical, opinionated n8n workflow that does exactly that. It aggregates high-signal cybersecurity RSS feeds, normalizes and deduplicates overlapping stories, prioritizes what matters, and translates raw reporting into a concise, CISO-ready briefing using Google Gemini—delivered straight into Discord in a format people will actually read.

This isn’t a novelty project or a demo bot. It’s a repeatable system designed to answer a single uncomfortable question every day: *If this is the only security update leadership reads today… is it enough?*

<br/><br/>

## What this automation does

This is a manually-run cyber briefing pipeline.

It does five jobs:

1. Pulls recent articles from trusted security RSS feeds.
2. Normalizes each feed into the same schema.
3. Merges, deduplicates, and keeps the newest/top 10 articles.
4. Sends those articles to Gemini with a CISO-briefing prompt.
5. Splits the AI output into Discord-safe chunks and posts them in order.

The big idea: **RSS feeds are noisy. This workflow turns them into a decision-grade briefing.**

<br/>

![N8N Diagram(.png)](/assets/img/SecurityNews/n8n_diag.png)

<br/><br/>

## Prerequisites

On the Pi 4B, you will want:

- Raspberry Pi OS Lite
- Docker and Docker Compose
- n8n in Docker Compose
- A Gemini API key from Google AI Studio
- One delivery target:
- Discord webhook, or
  - SMTP/Gmail account, or
  - Teams webhook / Power Automate flow

<br/><br/>

## Grab your Gemini API Key

Go to Google AI Studio and create an API key for the Gemini API. New accounts begin on the Free Tier, and Google’s docs note that free tier access applies to certain models, including Flash-class options rather than every premium model.

For our use case, we'll use a Flash model, not a Pro preview model. A safe target to start with is: **gemini-3-flash-preview...** That matches Google’s current free-tier guidance for Gemini API use.

###  Go to Google AI Studio

Open: 👉 https://aistudio.google.com

Sign in with your Google account.

### Create (or select) a project

When you first land in AI Studio:

If prompted → click **“Create Project,”** otherwise it will auto-create one behind the scenes. You don’t need to overthink this—this is just a container for your API usage.

### Navigate to API Keys

In the left sidebar:

- Click “Get API key”
OR
- Click your profile icon (top right) → “API keys”

You’ll land on the API key management page.

### Create a new API key

Click: **“Create API key”**

Then select your project (or default one) and click **Create.**

You’ll immediately get something like:

```
AIzaSyD...your-long-key...
```

>⚠️ IMPORTANT! <br/><br/>
>Treat this like a password... 👇
>- ❌ Don’t commit it to GitHub
>- ❌ Don’t paste it in screenshots
>- ✅ Store it in .env 

### Save that Key ☝️

<br/>

### Know your limits (free tier reality)

Google’s Gemini API:

- ✅ Has a free tier
- ⚠️ Limited to certain models (use Flash, not Pro)
- ⚠️ Has request + token limits

<br/><br/>

## Prep the Pi 4B

### Update the box:

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

<br/>

![Update && Upgrade -y(.png)](/assets/img/SecurityNews/update.png)

<br/>

### Install Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

<br/>

![Install Docker(.png)](/assets/img/SecurityNews/docker.png)

<br/>

### Confirm it works:
```bash
docker --version
docker compose version
```
<br/>

![Docker Version(.png)](/assets/img/SecurityNews/dockerBuild.png)

<br/>

### Create an n8n working folder
```bash
mkdir -p ~/n8n-stack
cd ~/n8n-stack
mkdir -p n8n_data
```

<br/>

Generate a strong encryption key for n8n credentials:

```bash
openssl rand -hex 32
```

> 🔒 n8n uses an encryption key to protect saved credentials, and the docs recommend setting your own persistent key instead of relying on an auto-generated one.

<br/>

### Create your .env file

Create ~/n8n-stack/.env:

```bash
nano .env
```

<br/>

Paste this, replacing values:

```bash
N8N_HOST=pi4b.local
N8N_PORT=5678
N8N_PROTOCOL=http
GENERIC_TIMEZONE=America/New_York
```

<br/>

### Use the value you generated with openssl
```bash
N8N_ENCRYPTION_KEY=REPLACE_WITH_LONG_RANDOM_HEX
```

<br/>

### Optional but recommended
```bash
N8N_SECURE_COOKIE=false
```

<br/>

### Gemini
```bash
GEMINI_API_KEY=REPLACE_WITH_YOUR_GEMINI_KEY
```

>👉 **GENERIC_TIMEZONE** matters here because n8n scheduling uses the instance timezone.

<br/>

## Create docker-compose.yml

Create ~/n8n-stack/docker-compose.yml:

```bash
services:
  n8n:
    image: docker.n8n.io/n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    env_file:
      - .env
    environment:
      - TZ=America/New_York
    volumes:
      - ./n8n_data:/home/node/.n8n
```

> ✔️ This follows the official Docker/Docker Compose self-hosting pattern for n8n.

Start it:

```bash
docker compose up -d
docker compose logs -f
```

Then open:
```
http://<your-pi4-ip>:5678
```

Create your n8n owner account in the browser and get started on your first workflow.

<br/><br/>

## Node-by-node breakdown

### Manual Trigger

This is the front door. Nothing runs on a schedule yet. You click **Execute Workflow**, and it kicks off all six RSS branches at once.

> 🔑 Note: this is safer while testing because you control when API calls, Gemini usage, and Discord posting happen.

You'll want to automate this later such that it runs every morning right around the time you've sat down at your desk with that first cup of hot coffee (or tea). 

<br/><br/>

### RSS Read nodes

<br/>

![RSS Node(.png)](/assets/img/SecurityNews/RSS.png)

<br/>

I use six RSS collection nodes:

* `RSS Read - Krebs`
* `RSS Read - Hacker News`
* `RSS Read - Schneier`
* `RSS Read - DarkReading`
* `RSS Read - SecurityWeek`
* `RSS Read - BleepingComputer`

Each one fetches articles from a specific cyber/security news feed.

These nodes do not make decisions. They just ingest raw feed items. Different RSS feeds use different fields like `content`, `summary`, `description`, `pubDate`, or `isoDate`, so the output is inconsistent at this stage.

<br/>

Here's the full list of RSS URLs used in this example: 

- [https://www.bleepingcomputer.com/feed/](https://www.bleepingcomputer.com/feed/)
- [https://feeds.feedburner.com/securityweek](https://feeds.feedburner.com/securityweek)
- [https://www.darkreading.com/rss.xml](https://www.darkreading.com/rss.xml)
- [https://www.schneier.com/feed/](https://www.schneier.com/feed/)
- [https://feeds.feedburner.com/TheHackersNews](https://feeds.feedburner.com/TheHackersNews)
- [https://krebsonsecurity.com/feed/](https://krebsonsecurity.com/feed/)

<br/><br/>

### Set / normalization nodes

<br/>

![Set Node(.png)](/assets/img/SecurityNews/set.png)

<br/>

Each RSS feed flows into a matching Code node:

* `Set - Krebs`
* `Set - Hacker News`
* `Set - Scheier`
* `Set - DarkReading`
* `Set - SecurityWeek`
* `Set - BleepingComputer`

Each one does roughly the same thing:

* Keeps only the first 5 articles from that source.
* Adds a clean `source` name.
* Sets `category: news`.
* Extracts `title`, `link`, `published`, and `summary`.
* Strips HTML.
* Normalizes whitespace.
* Truncates summaries to 300 characters.

This is the schema enforcement layer.

> 💡 **Ian's Insights:** this is where the workflow stops trusting the feeds and starts shaping the data. Good automation needs contracts; these 'Set' nodes creates them.

<br/><br/>

### Merge

<br/>

![Merge Node(.png)](/assets/img/SecurityNews/merge.png)

<br/>

The `Merge` node combines the six normalized feed streams into one article stream.

At this point, you could have up to 30 articles:

```text
6 feeds × 5 articles each = 30 candidate stories
```

This is still raw volume, not intelligence.

<br/><br/>

### Dedupe

<br/>

![Deduplication Node(.png)](/assets/img/SecurityNews/dedupe.png)

<br/>


The `Dedupe` Code node removes repeated stories.

It creates a key from:

```js
(j.link || j.title || '').toLowerCase().trim()
```

Then it skips anything already seen.

That means exact duplicate URLs or titles get removed.

DevSecOpsDad read: this is good enough for operational hygiene, but not true semantic dedupe. If three outlets cover the same breach with different URLs and different headlines, Gemini still has to collapse that later.

<br/><br/>

### Filter - Top N(10)

<br/>

![Filter Node (TopN)(.png)](/assets/img/SecurityNews/Filter.png)

<br/>

This node sorts all remaining articles newest-first using `published`, then keeps the first 10.

```js
return items
  .sort((a, b) => new Date(b.json.published) - new Date(a.json.published))
  .slice(0, 10);
```

This is your cost and signal-control gate.

Instead of feeding Gemini 30 stories, you feed it 10. That lowers token use, reduces prompt noise, and keeps the final Discord post readable.

<br/><br/>

### Prompt

<br/>

![Prompt Node(.png)](/assets/img/SecurityNews/prompt.png)

<br/>

This node builds the Gemini prompt.

It takes the filtered articles and creates a briefing instruction set:

* Use only supplied articles.
* Deduplicate overlapping stories.
* Prioritize breaches, exploitation, ransomware, cloud abuse, identity abuse, major vulnerabilities, and vendor issues.
* Explain business impact.
* Identify likely affected groups.
* Classify threat type.
* Determine opportunistic vs. targeted.
* Recommend what a CISO should consider next.
* Output markdown.

This is the most important node in the workflow.

DevSecOpsDad read: this is where “news” becomes “executive decision support.”

One issue: your prompt code references:

```js
a.pubDate
a.snippet
```

But your normalization nodes output:

```js
published
summary
```

So the prompt may produce blank/undefined values for published date and snippet. You probably want:

```js
Published: ${a.published}
Snippet: ${a.summary}
```

<br/><br/>

### Gemini Offload

<br/>

![AI Offload Node(.png)](/assets/img/SecurityNews/AI%20Offload.png)

<br/>

This HTTP Request node sends the prompt to Gemini:

```text
gemini-2.5-flash-lite:generateContent
```

It sends a JSON body with:

```json
contents → parts → text
```

That is the handoff from deterministic workflow logic to generative summarization.

Important: your exported workflow contains what looks like a Gemini API key. Rotate it.

<br/><br/>

### Parse AI Results

<br/>

![Parse AI Response Node(.png)](/assets/img/SecurityNews/parse.png)

<br/>

This Code node extracts Gemini’s response from the nested JSON:

```js
$json.candidates?.[0]?.content?.parts?.[0]?.text
```

Then it returns a simple object:

```js
{ summary: text }
```

This is another schema-control point. Gemini’s response shape is ugly; this node turns it into something the rest of the workflow can use.

<br/><br/>

### Split/Chunk

![Split/Chunk Node(.png)](/assets/img/SecurityNews/chunk.png)

Discord has message size limits, so this node splits the briefing into chunks of about 1,800 characters.

It prefers splitting on:

1. Newlines
2. Spaces
3. Hard character limit if needed

That avoids ugly mid-sentence cuts when possible.

DevSecOpsDad read: this is delivery engineering. The best briefing in the world still fails if it arrives as a broken wall of text.

<br/><br/>

### Loop Over Items

<br/>

![Loop Node(.png)](/assets/img/SecurityNews/loop.png)

<br/>

This node loops over each chunk one at a time.

Its job is sequencing.

Without this, Discord posts may arrive out of order or too quickly. With the loop, each chunk gets passed to Discord, then the workflow loops back for the next one.

<br/><br/>

### Post to Discord

<br/>

![Post to Discord Node(.png)](/assets/img/SecurityNews/Discord.png)

<br/>

This HTTP Request node posts each chunk to Discord via webhook:

```json
{
  "content": $json.content
}
```

This is the final delivery point.

Important: your exported workflow contains the Discord webhook URL. Rotate it too. A Discord webhook is effectively a write credential.

<br/><br/>

## The workflow in plain English

```text
Manual Run
  → Pull 6 RSS feeds
  → Normalize each feed
  → Merge all articles
  → Remove exact duplicates
  → Sort newest first
  → Keep top 10
  → Build CISO briefing prompt
  → Send to Gemini
  → Extract Gemini response
  → Split response into Discord-sized chunks
  → Loop chunks one-by-one
  → Post to Discord
```

<br/><br/>

## Final Thoughts
At the end of the day, this isn’t about RSS feeds, n8n, or even AI—it’s about whether your security program **decides before it reacts.** The teams that win aren’t the ones reading more—**they’re the ones structuring signal faster than attackers can generate noise.** Automation isn’t replacing analysts; it’s removing the excuse that “we didn’t see it in time.” If your threat intelligence still depends on someone having a free 30 minutes and a cup of coffee, you don’t have a pipeline—you have a hope. Build the system that tells you what matters before the alerts fire, or accept that you’ll always be triaging someone else’s timeline.

<br/><br/>

![CoffeeKat(.png)](/assets/img/SecurityNews/CoffeeKat.png)

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

<br/><br/>

![DevSecOpsDad.com](/assets/img/NewFooter_DevSecOpsDad.png)
