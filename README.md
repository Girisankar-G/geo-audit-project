# Villion GEO Audit — Mini Platform Prototype

A full-stack prototype that audits any public webpage for **Generative Engine Optimization (GEO)** readiness — analyzing structured data opportunities and generating JSON-LD schema recommendations to improve AI citation likelihood on ChatGPT, Perplexity, and Google AI Overviews.

---

## Quick Start

### 1. Clone the repo
```bash
git clone <your-repo-url>
cd villion-geo-audit
```

### 2. Backend setup (Python / FastAPI)
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

Create your `.env` file:
```bash
copy .env.example .env      # Windows
# cp .env.example .env      # Mac/Linux
```
Edit `.env` and paste your OpenAI API key.

Start the API:
```bash
uvicorn main:app --reload
```
API runs at: **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

### 3. Frontend setup (Next.js)
```bash
cd ../frontend
npx create-next-app@latest . --yes
# Replace app/page.js with the page.js file from this repo
npm run dev
```
Frontend runs at: **http://localhost:3000**

---

## API Reference

### `POST /audit`

**Request body:**
```json
{ "url": "https://example.com/about" }
```

**Response:**
```json
{
  "url": "https://example.com/about",
  "page_data": {
    "title": "About Us | Acme Corp",
    "meta_description": "We build...",
    "headings": ["H1: About Acme", "H2: Our Mission"],
    "image_urls": ["https://..."],
    "page_text_snippet": "Acme Corp is a..."
  },
  "detected_schema_type": "Organization",
  "detection_method": "llm",
  "recommended_jsonld": { "@context": "https://schema.org", ... },
  "geo_tips": ["Add a longer meta description...", "..."],
  "warning": null
}
```

---

## Architecture Overview

```
Frontend (Next.js)
      │
      │  POST /audit  { url }
      ▼
Backend (FastAPI)
      │
      ├─► scraper.py         httpx + BeautifulSoup
      │     Extract: title, meta, headings, images, text snippet
      │
      ├─► schema_engine.py
      │     ├─ Rule-based keyword scorer → detect schema TYPE
      │     ├─ Template builder         → base JSON-LD block
      │     └─ LLM enrichment (GPT-4o-mini) → fill in missing fields
      │
      └─► AuditResponse (Pydantic) → JSON to frontend
```

---

## Design Decision Log

### Problem Breakdown
The core challenge: given an arbitrary URL, produce a *useful* structured data recommendation — not just a generic template. I broke this into three subproblems:
1. **Extraction** — reliably get page content despite varied HTML structures
2. **Classification** — decide which schema type fits best
3. **Generation** — produce a schema block with real values, not just placeholders

---

### Decision 1: httpx over requests for scraping
**Considered:** `requests`, `httpx`, `Playwright`  
**Chose:** `httpx` with sync client  
**Why:** httpx is nearly identical to requests for sync use, but supports async natively. This matters for the scale-up scenario (50+ pages in parallel) — I can switch to `AsyncClient` with minimal refactoring. Playwright was overkill for the prototype since most informational pages don't require JavaScript rendering.  
**Trade-off:** JavaScript-heavy SPAs (React/Next.js sites) won't scrape well with httpx. A production system would need Playwright as a fallback layer.

---

### Decision 2: Rule-based schema TYPE detection, LLM for VALUE filling
**Considered:** (a) pure rules, (b) pure LLM, (c) hybrid  
**Chose:** Hybrid — rules for *type*, LLM for *content*  
**Why this split matters:**  
- Schema type detection is essentially a classification problem with ~5 categories. A keyword scorer is fast, free, fully deterministic, and easy to audit. Sending every URL to GPT just to answer "is this an Article or Product page?" wastes tokens and adds latency.  
- Schema *value* filling (author name, publisher, datePublished) requires reading and understanding page content — exactly what LLMs are good at. A rule-based system can't infer "this article was written by Jane Smith" from a body text snippet.  
- If the LLM call fails (timeout, rate limit, no API key), the system gracefully falls back to rule-based output. Resilience matters in a production audit tool.

---

### Decision 3: FastAPI over Flask/Django
**Chose:** FastAPI  
**Why:** Automatic OpenAPI docs at `/docs`, native Pydantic integration, async-ready. For a small prototype with clean API contracts, FastAPI is the fastest path to a production-quality interface. Django would be overkill; Flask lacks type safety.

---

### Decision 4: What I deliberately did NOT use LLMs for
- **Schema type detection** — too expensive and slow for what a keyword scorer handles well  
- **HTML parsing** — deterministic, structured problem; LLMs would hallucinate tags  
- **GEO tips generation** — rule-based tips are more consistent and auditable  
This is intentional. LLM calls should be reserved for tasks where unstructured language understanding adds real value over deterministic logic.

---

## Scale-Up Architecture (50+ Pages)

If this needed to audit an entire website:

```
Coordinator Agent
    │
    ├─► URL Discovery Worker  (sitemap.xml parser or crawl BFS)
    │
    ├─► Scrape Workers (async pool, N=10 concurrent)
    │       └─ httpx AsyncClient + retry logic + rate limiting
    │
    ├─► Schema Classification Workers (rule-based, no LLM bottleneck)
    │
    ├─► LLM Enrichment Workers (batched, rate-limited, cached by URL hash)
    │       └─ Use OpenAI Batch API for 50% cost reduction
    │
    ├─► Results Aggregator → PostgreSQL or Redis
    │
    └─► Report Generator → PDF / dashboard
```

**Key design choices for scale:**
- **Multi-agent pattern:** Separate workers for scraping vs. schema generation so slow scrapers don't block fast classifiers
- **LLM batching:** Use OpenAI's Batch API — async, 24hr window, half the cost
- **Failure handling:** Each worker retries with exponential backoff; dead-letter queue for persistently failing URLs
- **Caching:** Hash-based cache (URL → result) avoids re-auditing unchanged pages
- **Deterministic first:** Run rule-based classification for all 50 pages instantly; only invoke LLM for pages where confidence is low or schema requires content understanding

---

## Known Limitations & What I'd Improve

1. **JavaScript-rendered pages** — httpx can't execute JS. Playwright integration with a fallback trigger would fix 80% of edge cases.
2. **LLM hallucination on schema values** — the LLM prompt tells it not to invent prices/addresses, but edge cases exist. A post-processing validator that checks schema fields against extracted page text would catch this.
3. **Single URL only** — the scale-up design above addresses this.
4. **Schema validation** — currently no Google Rich Results test integration. Plugging in the Schema.org validator API would confirm correctness automatically.
5. **Caching** — every audit re-fetches the page. A Redis layer with TTL would make the tool much faster for repeated audits.

---

## How This Supports Villion's GEO Vision

AI search engines (ChatGPT Plugins, Perplexity, Google AI Overviews) increasingly rely on structured data to identify citable, authoritative content. By ensuring every client page has:
- Correct JSON-LD schema type (signals content category to AI crawlers)
- Populated author, publisher, datePublished fields (signals authority and freshness)
- Descriptive meta descriptions (used as citation snippets)

...brands meaningfully increase their surface area for AI citation. This audit tool is the diagnostic layer of that process — it tells you *what's missing* before the optimization work begins.
