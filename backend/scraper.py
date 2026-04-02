import httpx
from bs4 import BeautifulSoup
from models import PageData


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def scrape_page(url: str) -> tuple[PageData, str | None]:
    """
    Fetches a public URL and extracts key on-page elements.
    Returns (PageData, warning_message_or_None).

    Why httpx over requests?
    - httpx supports async natively, which matters when we scale to 50+ pages
    - For now we use sync client to keep complexity low
    """
    warning = None

    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise ValueError(f"Request timed out for URL: {url}")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP {e.response.status_code} error fetching URL: {url}")
    except Exception as e:
        raise ValueError(f"Failed to fetch URL: {str(e)}")

    soup = BeautifulSoup(response.text, "html.parser")

    # --- Title ---
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None

    # --- Meta Description ---
    meta_desc = None
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"].strip()
    else:
        # Try OpenGraph as fallback — many modern sites use og:description
        og_tag = soup.find("meta", property="og:description")
        if og_tag and og_tag.get("content"):
            meta_desc = og_tag["content"].strip()
            warning = "Meta description missing; used og:description as fallback."

    # --- Headings (h1 + h2 only, max 10 to keep response clean) ---
    headings = []
    for tag in soup.find_all(["h1", "h2"])[:10]:
        text = tag.get_text(strip=True)
        if text:
            headings.append(f"{tag.name.upper()}: {text}")

    # --- Images (src or data-src for lazy-loaded images, max 5) ---
    image_urls = []
    for img in soup.find_all("img")[:20]:
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if src:
            # Make relative URLs absolute
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                src = f"{parsed.scheme}://{parsed.netloc}{src}"
            if src.startswith("http"):
                image_urls.append(src)
        if len(image_urls) >= 5:
            break

    # --- Page text snippet for LLM context ---
    # Strip scripts/styles, get visible text, truncate to 500 chars
    for script_or_style in soup(["script", "style", "nav", "footer"]):
        script_or_style.decompose()
    body_text = soup.get_text(separator=" ", strip=True)
    body_text = " ".join(body_text.split())  # normalize whitespace
    snippet = body_text[:500] if body_text else None

    page_data = PageData(
        title=title,
        meta_description=meta_desc,
        headings=headings,
        image_urls=image_urls,
        page_text_snippet=snippet,
    )

    return page_data, warning
