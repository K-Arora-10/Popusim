import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import logging
from urllib.parse import urlparse, urljoin

logger = logging.getLogger("popusim.ingestion")

async def ingest_website(url: str) -> dict:
    """
    Ingests a target website URL using Playwright.
    Falls back to httpx + BeautifulSoup if Playwright fails.
    Extracts structure, metadata, and interactive elements.
    """
    logger.info(f"Ingesting website: {url}")
    result = {
        "url": url,
        "title": "",
        "meta_description": "",
        "headings": [],
        "text_content": "",
        "links": [],
        "buttons": [],
        "inputs": [],
        "error": None
    }
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Set timeout to 15 seconds to avoid hanging
            await page.goto(url, wait_until="networkidle", timeout=15000)
            
            result["title"] = await page.title()
            
            # Extract meta description
            meta_desc = await page.locator("meta[name='description']").get_attribute("content")
            if meta_desc:
                result["meta_description"] = meta_desc
                
            # Get DOM elements
            html = await page.content()
            await browser.close()
            
            # Parse HTML for structural text
            soup = BeautifulSoup(html, "html.parser")
            
            # Title if not caught by playwright
            if not result["title"]:
                result["title"] = soup.title.string if soup.title else ""
                
            # Headings
            for h in soup.find_all(["h1", "h2", "h3"]):
                text = h.get_text().strip()
                if text:
                    result["headings"].append(text)
                    
            # Text content (first 2000 chars for LLM context)
            # Remove scripts and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            result["text_content"] = soup.get_text(separator=" ").strip()[:2000]
            
            # Parse links
            parsed_origin = urlparse(url)
            for a in soup.find_all("a"):
                href = a.get("href")
                text = a.get_text().strip()
                if href and text:
                    # Clean/resolve absolute url
                    absolute_url = urljoin(url, href)
                    # Filter for internal links (same domain)
                    parsed_link = urlparse(absolute_url)
                    is_internal = parsed_link.netloc == parsed_origin.netloc or not parsed_link.netloc
                    
                    result["links"].append({
                        "text": text,
                        "href": href,
                        "absolute_url": absolute_url,
                        "is_internal": is_internal
                    })
                    
            # Parse buttons
            for b in soup.find_all(["button", "input"]):
                if b.name == "input" and b.get("type") not in ["submit", "button"]:
                    # Form input fields
                    result["inputs"].append({
                        "type": b.get("type", "text"),
                        "name": b.get("name", ""),
                        "placeholder": b.get("placeholder", ""),
                        "id": b.get("id", "")
                    })
                else:
                    # Button element
                    text = b.get_text().strip() or b.get("value", "").strip() or b.get("placeholder", "").strip()
                    if text or b.get("id") or b.get("class"):
                        result["buttons"].append({
                            "text": text,
                            "id": b.get("id", ""),
                            "class": " ".join(b.get("class", []))
                        })
                        
    except Exception as e:
        logger.warning(f"Playwright ingestion failed: {e}. Falling back to HTTPX/BeautifulSoup.")
        result["error"] = str(e)
        
        # Fallback using httpx
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                response = await client.get(url, headers=headers)
                
                soup = BeautifulSoup(response.text, "html.parser")
                result["title"] = soup.title.string if soup.title else ""
                
                # Meta description
                meta = soup.find("meta", attrs={"name": "description"})
                if meta:
                    result["meta_description"] = meta.get("content", "")
                    
                # Headings
                for h in soup.find_all(["h1", "h2", "h3"]):
                    text = h.get_text().strip()
                    if text:
                        result["headings"].append(text)
                
                # Text content
                for script in soup(["script", "style"]):
                    script.decompose()
                result["text_content"] = soup.get_text(separator=" ").strip()[:2000]
                
                # Links
                parsed_origin = urlparse(url)
                for a in soup.find_all("a"):
                    href = a.get("href")
                    text = a.get_text().strip()
                    if href and text:
                        absolute_url = urljoin(url, href)
                        parsed_link = urlparse(absolute_url)
                        is_internal = parsed_link.netloc == parsed_origin.netloc or not parsed_link.netloc
                        result["links"].append({
                            "text": text,
                            "href": href,
                            "absolute_url": absolute_url,
                            "is_internal": is_internal
                        })
                
                # Buttons/inputs
                for b in soup.find_all(["button", "input"]):
                    if b.name == "input" and b.get("type") not in ["submit", "button"]:
                        result["inputs"].append({
                            "type": b.get("type", "text"),
                            "name": b.get("name", ""),
                            "placeholder": b.get("placeholder", ""),
                            "id": b.get("id", "")
                        })
                    else:
                        text = b.get_text().strip() or b.get("value", "").strip() or b.get("placeholder", "").strip()
                        result["buttons"].append({
                            "text": text,
                            "id": b.get("id", ""),
                            "class": " ".join(b.get("class", [])) if b.get("class") else ""
                        })
        except Exception as e_inner:
            logger.error(f"Fallback ingestion also failed: {e_inner}")
            result["error"] = f"Ingestion failed: {e} | Fallback failed: {e_inner}"
            result["title"] = urlparse(url).netloc or "Target Website"
            
    return result
