from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional


class AuditRequest(BaseModel):
    url: HttpUrl

    @field_validator("url")
    @classmethod
    def url_must_be_http(cls, v):
        if not str(v).startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class PageData(BaseModel):
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: list[str] = []
    image_urls: list[str] = []
    page_text_snippet: Optional[str] = None  # first ~500 chars for LLM context


class AuditResponse(BaseModel):
    url: str
    page_data: PageData
    detected_schema_type: str          # e.g. "Article", "Organization", "Product"
    detection_method: str              # "rule-based" or "llm"
    recommended_jsonld: dict           # the actual JSON-LD block
    geo_tips: list[str]                # human-readable GEO improvement tips
    warning: Optional[str] = None      # scraping issues, fallback notices
