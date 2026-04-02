"""
Villion GEO Audit API
FastAPI backend for analyzing webpages and generating JSON-LD recommendations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import AuditRequest, AuditResponse
from scraper import scrape_page
from schema_engine import recommend_schema

load_dotenv()  # loads OPENAI_API_KEY from .env

app = FastAPI(
    title="Villion GEO Audit API",
    description=(
        "Analyzes a public webpage for Generative Engine Optimization (GEO) readiness. "
        "Extracts page metadata, detects structured data opportunities, and generates "
        "JSON-LD schema recommendations to improve AI search engine citation likelihood."
    ),
    version="1.0.0",
)

# Allow the Next.js frontend (port 3000) to call this API during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Villion GEO Audit API is running."}


@app.post("/audit", response_model=AuditResponse, tags=["GEO Audit"])
def audit_url(request: AuditRequest):
    """
    **Audit a single webpage for GEO readiness.**

    Provide a public URL. The API will:
    1. Scrape the page (title, meta description, headings, images)
    2. Detect the most appropriate JSON-LD schema type
    3. Generate a recommended JSON-LD block (LLM-enriched if API key is set)
    4. Return actionable GEO improvement tips

    **Use case:** Helps brands improve their AI citation readiness on
    ChatGPT, Google AI Overviews, and Perplexity.
    """
    url_str = str(request.url)

    # Step 1: Scrape
    try:
        page_data, scrape_warning = scrape_page(url_str)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected scraping error: {str(e)}")

    # Step 2 & 3: Detect schema + generate JSON-LD
    try:
        schema_type, method, jsonld, geo_tips = recommend_schema(url_str, page_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema generation error: {str(e)}")

    return AuditResponse(
        url=url_str,
        page_data=page_data,
        detected_schema_type=schema_type,
        detection_method=method,
        recommended_jsonld=jsonld,
        geo_tips=geo_tips,
        warning=scrape_warning,
    )
