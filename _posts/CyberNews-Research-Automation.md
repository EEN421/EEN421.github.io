

## What this automation does

This is a manually-run cyber briefing pipeline.

It does five jobs:

1. Pulls recent articles from trusted security RSS feeds.
2. Normalizes each feed into the same schema.
3. Merges, deduplicates, and keeps the newest/top 10 articles.
4. Sends those articles to Gemini with a CISO-briefing prompt.
5. Splits the AI output into Discord-safe chunks and posts them in order.

The big idea: **RSS feeds are noisy. This workflow turns them into a decision-grade briefing.**

---

## Node-by-node breakdown

### Manual Trigger

This is the front door.

Nothing runs on a schedule yet. You click **Execute Workflow**, and it kicks off all six RSS branches at once.

DevSecOpsDad read: this is safer while testing because you control when API calls, Gemini usage, and Discord posting happen.

---

### RSS Read nodes

You have six RSS collection nodes:

* `RSS Read - Krebs`
* `RSS Read - Hacker News`
* `RSS Read - Schneier`
* `RSS Read - DarkReading`
* `RSS Read - SecurityWeek`
* `RSS Read - BleepingComputer`

Each one fetches articles from a specific cyber/security news feed.

These nodes do not make decisions. They just ingest raw feed items. Different RSS feeds use different fields like `content`, `summary`, `description`, `pubDate`, or `isoDate`, so the output is inconsistent at this stage.

---

### Set / normalization nodes

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

DevSecOpsDad read: this is where the workflow stops trusting the feeds and starts shaping the data. Good automation needs contracts. This node creates one.

---

### Merge

The `Merge` node combines the six normalized feed streams into one article stream.

At this point, you could have up to 30 articles:

```text
6 feeds × 5 articles each = 30 candidate stories
```

This is still raw volume, not intelligence.

---

### Dedupe

The `Dedupe` Code node removes repeated stories.

It creates a key from:

```js
(j.link || j.title || '').toLowerCase().trim()
```

Then it skips anything already seen.

That means exact duplicate URLs or titles get removed.

DevSecOpsDad read: this is good enough for operational hygiene, but not true semantic dedupe. If three outlets cover the same breach with different URLs and different headlines, Gemini still has to collapse that later.

---

### Filter - Top N(10)

This node sorts all remaining articles newest-first using `published`, then keeps the first 10.

```js
return items
  .sort((a, b) => new Date(b.json.published) - new Date(a.json.published))
  .slice(0, 10);
```

This is your cost and signal-control gate.

Instead of feeding Gemini 30 stories, you feed it 10. That lowers token use, reduces prompt noise, and keeps the final Discord post readable.

---

### Prompt

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

---

### Gemini Offload

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

---

### Parse AI Results

This Code node extracts Gemini’s response from the nested JSON:

```js
$json.candidates?.[0]?.content?.parts?.[0]?.text
```

Then it returns a simple object:

```js
{ summary: text }
```

This is another schema-control point. Gemini’s response shape is ugly; this node turns it into something the rest of the workflow can use.

---

### Split/Chunk

Discord has message size limits, so this node splits the briefing into chunks of about 1,800 characters.

It prefers splitting on:

1. Newlines
2. Spaces
3. Hard character limit if needed

That avoids ugly mid-sentence cuts when possible.

DevSecOpsDad read: this is delivery engineering. The best briefing in the world still fails if it arrives as a broken wall of text.

---

### Loop Over Items

This node loops over each chunk one at a time.

Its job is sequencing.

Without this, Discord posts may arrive out of order or too quickly. With the loop, each chunk gets passed to Discord, then the workflow loops back for the next one.

---

### Post to Discord

This HTTP Request node posts each chunk to Discord via webhook:

```json
{
  "content": $json.content
}
```

This is the final delivery point.

Important: your exported workflow contains the Discord webhook URL. Rotate it too. A Discord webhook is effectively a write credential.

---

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

## The one thing I would fix first

Fix the field mismatch in the `Prompt` node:

```js
Published: ${a.published}
Snippet: ${a.summary}
```

Right now the prompt asks for `pubDate` and `snippet`, but your upstream normalization nodes create `published` and `summary`.

That is the kind of bug that makes an automation “work” while quietly degrading the output.
