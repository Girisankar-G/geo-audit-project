"""
Schema Engine: Recommends JSON-LD structured data blocks for GEO optimization.

Design decision:
  - Rule-based logic first: fast, free, deterministic, works offline
  - LLM as an upgrade layer: adds nuance when API key is available
  - Why not LLM-only? Cost, latency, and fragility for a high-volume audit tool
"""

import os
import json
import re
from models import PageData

# Optional LLM support — gracefully skips if key not set
try:
    from openai import OpenAI
    _openai_available = True
except ImportError:
    _openai_available = False


# ---------------------------------------------------------------------------
# Rule-based schema type detector
# ---------------------------------------------------------------------------

SCHEMA_KEYWORDS = {
    "Product": [
        "buy", "price", "cart", "shop", "product", "order", "checkout",
        "add to bag", "sku", "in stock", "shipping", "$", "€", "£",
        "pricing", "plan", "hobby", "pro", "enterprise", "per month",
        "per year", "free tier", "upgrade", "subscribe", "billing"
    ],
    "Article": [
        "blog", "post", "article", "published", "author", "written by",
        "read more", "min read", "news", "press", "insights", "guide",
        "research", "report", "study", "analysis", "whitepaper"
    ],
    "FAQPage": [
        "faq", "frequently asked", "how do i", "what is", "questions",
        "help center", "support", "q&a"
    ],
    "LocalBusiness": [
        "hours", "location", "directions", "address", "open", "closed",
        "visit us", "our store", "near me", "map"
    ],
    "Organization": [],  # default fallback — every company page qualifies
}


def detect_schema_type(page_data: PageData) -> str:
    """
    Score each schema type based on keyword matches in title, meta, headings, snippet.
    Returns the highest-scoring type; falls back to Organization.
    """
    combined_text = " ".join(filter(None, [
        page_data.title or "",
        page_data.meta_description or "",
        " ".join(page_data.headings),
        page_data.page_text_snippet or "",
    ])).lower()

    scores = {schema: 0 for schema in SCHEMA_KEYWORDS}
    for schema, keywords in SCHEMA_KEYWORDS.items():
        for kw in keywords:
            if kw in combined_text:
                scores[schema] += 1

    # Remove Organization from scoring (it's the fallback)
    scores.pop("Organization")
    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return "Organization"
    return best


# ---------------------------------------------------------------------------
# JSON-LD template builders (rule-based)
# ---------------------------------------------------------------------------

def _base_url_from(url: str) -> str:
    from urllib.parse import urlparse
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def build_organization_jsonld(url: str, page_data: PageData) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": page_data.title or "Unknown Organization",
        "url": _base_url_from(url),
        "description": page_data.meta_description or "",
        "logo": page_data.image_urls[0] if page_data.image_urls else "",
    }


def build_article_jsonld(url: str, page_data: PageData) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": page_data.title or "",
        "description": page_data.meta_description or "",
        "url": url,
        "image": page_data.image_urls[0] if page_data.image_urls else "",
        "author": {"@type": "Organization", "name": "Unknown"},
        "publisher": {
            "@type": "Organization",
            "name": _base_url_from(url),
            "logo": {"@type": "ImageObject", "url": ""},
        },
    }


def build_product_jsonld(url: str, page_data: PageData) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": page_data.title or "",
        "description": page_data.meta_description or "",
        "url": url,
        "image": page_data.image_urls[0] if page_data.image_urls else "",
        "offers": {
            "@type": "Offer",
            "priceCurrency": "USD",
            "price": "0.00",
            "availability": "https://schema.org/InStock",
        },
    }


def build_faq_jsonld(url: str, page_data: PageData) -> dict:
    # Extract heading-style questions as FAQ items
    faq_items = []
    for h in page_data.headings:
        text = re.sub(r"^H[12]:\s*", "", h)
        if "?" in text or text.lower().startswith(("what", "how", "why", "when", "who")):
            faq_items.append({
                "@type": "Question",
                "name": text,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "See the full answer at the URL above."
                }
            })
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "url": url,
        "mainEntity": faq_items or [
            {
                "@type": "Question",
                "name": "What does this page cover?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": page_data.meta_description or "Visit the page for details."
                }
            }
        ]
    }


def build_local_business_jsonld(url: str, page_data: PageData) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": page_data.title or "",
        "description": page_data.meta_description or "",
        "url": url,
        "image": page_data.image_urls[0] if page_data.image_urls else "",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "",
            "addressLocality": "",
            "addressRegion": "",
            "postalCode": "",
            "addressCountry": "US"
        },
    }


BUILDERS = {
    "Organization": build_organization_jsonld,
    "Article": build_article_jsonld,
    "Product": build_product_jsonld,
    "FAQPage": build_faq_jsonld,
    "LocalBusiness": build_local_business_jsonld,
}


# ---------------------------------------------------------------------------
# GEO tips generator
# ---------------------------------------------------------------------------

def generate_geo_tips(page_data: PageData, schema_type: str) -> list[str]:
    tips = []

    if not page_data.meta_description:
        tips.append("Add a meta description — AI engines like Perplexity use it as a citation snippet.")
    elif len(page_data.meta_description) < 100:
        tips.append("Meta description is short (<100 chars). Expand it to 150–160 chars with your brand's key value prop.")

    if not any("H1:" in h for h in page_data.headings):
        tips.append("No H1 detected. A clear H1 helps AI engines identify the page topic for citations.")

    if not page_data.image_urls:
        tips.append("No images detected. Adding images with descriptive alt text improves AI multimodal indexing.")

    if schema_type == "Article":
        tips.append("Add 'author' and 'datePublished' fields to your Article schema for Google AI trust signals.")

    if schema_type == "FAQPage":
        tips.append("FAQ schema is highly cited by ChatGPT and Perplexity — ensure answers are 40–60 words each.")

    if not tips:
        tips.append("Page structure looks solid. Focus on adding more factual, citable content blocks.")

    return tips


# ---------------------------------------------------------------------------
# LLM-powered enrichment (optional)
# ---------------------------------------------------------------------------

def enrich_with_llm(url: str, page_data: PageData, base_jsonld: dict, schema_type: str) -> tuple[dict, str]:
    """
    Uses GPT to fill in missing fields and improve schema quality.
    Returns (enriched_jsonld, detection_method).

    Why LLM here specifically?
    - Rule-based can't infer author names, org names from page text
    - LLM reads the snippet and makes intelligent guesses
    - We still use rule-based for schema TYPE detection (cheaper, faster)
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or not _openai_available:
        return base_jsonld, "rule-based"

    client = OpenAI(api_key=api_key)

    prompt = f"""You are a structured data expert for GEO (Generative Engine Optimization).
Given this webpage context, improve the JSON-LD schema block below.
Fill in missing fields like author, name, description, datePublished where you can infer them.
Do NOT invent prices or addresses. Return ONLY valid JSON, no markdown.

URL: {url}
Page Title: {page_data.title}
Meta Description: {page_data.meta_description}
Headings: {', '.join(page_data.headings[:5])}
Page Snippet: {page_data.page_text_snippet}
Schema Type: {schema_type}

Current JSON-LD:
{json.dumps(base_jsonld, indent=2)}

Return improved JSON-LD:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # cheap + fast; gpt-4o for higher quality
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,       # low temp = more deterministic, less hallucination
            max_tokens=800,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if model added them
        raw = re.sub(r"^```json\s*|^```\s*|```$", "", raw, flags=re.MULTILINE).strip()
        enriched = json.loads(raw)
        return enriched, "llm"
    except Exception as e:
        # LLM failure is non-fatal — fall back to rule-based output
        print(f"[LLM WARNING] Enrichment failed: {e}")
        return base_jsonld, "rule-based (llm failed)"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def recommend_schema(url: str, page_data: PageData) -> tuple[str, str, dict, list[str]]:
    """
    Returns: (schema_type, detection_method, jsonld_dict, geo_tips)
    """
    schema_type = detect_schema_type(page_data)
    builder = BUILDERS.get(schema_type, build_organization_jsonld)
    base_jsonld = builder(url, page_data)

    enriched_jsonld, method = enrich_with_llm(url, page_data, base_jsonld, schema_type)
    tips = generate_geo_tips(page_data, schema_type)

    return schema_type, method, enriched_jsonld, tips
