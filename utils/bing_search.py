"""Free Bing Visual Search scraper — no API key required.

Submits an image URL to Bing's Visual Search endpoint and parses
the HTML response for matching pages and similar images.

This is a "best-effort" engine: if Bing blocks the request or
returns no results, it silently returns an empty list. The pipeline
continues with Google + Yandex results. Never crashes.
"""

from __future__ import annotations

import re
import json
import sys
from typing import Dict, List
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup


_TIMEOUT = 20

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.bing.com/",
    "DNT": "1",
}


def search_bing_visual(image_url: str) -> List[Dict[str, str]]:
    """Search Bing Visual Search with an image URL.
    
    Returns a list of candidate dicts in the same format as Google Lens:
        [{"link", "title", "source", "thumbnail", "original_url"}, ...]
    
    Returns [] on any error — never raises.
    """
    results: List[Dict[str, str]] = []
    
    try:
        # Method 1: Bing's SBI (Search By Image) URL paste endpoint
        encoded_url = quote_plus(image_url)
        search_url = f"https://www.bing.com/images/search?view=detailv2&iss=sbi&form=SBIHMP&sbisrc=UrlPaste&q=imgurl:{encoded_url}"
        
        session = requests.Session()
        session.headers.update(_HEADERS)
        
        resp = session.get(search_url, timeout=_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        
        html = resp.text
        
        # Strategy 1: Parse structured JSON-LD or data attributes from Bing's response
        soup = BeautifulSoup(html, "html.parser")
        
        # Look for "Pages with this image" section
        # Bing embeds these as anchor tags with specific classes
        for tag in soup.find_all("a", href=True):
            href = tag.get("href", "")
            # Skip internal Bing links, javascript, and empty hrefs
            if not href or href.startswith("#") or href.startswith("/") or "bing.com" in href or "microsoft.com" in href:
                continue
            if not href.startswith("http"):
                continue
                
            # Extract title from various possible locations
            title = ""
            title_tag = tag.find(["h2", "h3", "span", "div"])
            if title_tag:
                title = title_tag.get_text(strip=True)
            if not title:
                title = tag.get("title", "") or tag.get_text(strip=True)[:100]
            
            # Extract thumbnail if there's an img inside the anchor
            thumbnail = ""
            img_tag = tag.find("img")
            if img_tag:
                thumbnail = img_tag.get("src", "") or img_tag.get("data-src", "")
            
            # Parse the source domain
            try:
                source = urlparse(href).netloc.replace("www.", "")
            except Exception:
                source = ""
            
            if source and title:
                results.append({
                    "link": href,
                    "title": title[:200],
                    "source": source,
                    "thumbnail": thumbnail,
                    "original_url": href,
                })
        
        # Strategy 2: Look for embedded JSON data blobs that Bing sometimes includes
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if "pageData" in script_text or "knowledge" in script_text:
                # Try to extract JSON objects from script content
                json_matches = re.findall(r'\{[^{}]*"url"\s*:\s*"https?://[^"]+?"[^{}]*\}', script_text)
                for jm in json_matches[:20]:
                    try:
                        obj = json.loads(jm)
                        url = obj.get("url", "") or obj.get("hostPageUrl", "")
                        if url and "bing.com" not in url and "microsoft.com" not in url:
                            try:
                                src = urlparse(url).netloc.replace("www.", "")
                            except:
                                src = ""
                            results.append({
                                "link": url,
                                "title": obj.get("name", "") or obj.get("title", ""),
                                "source": src,
                                "thumbnail": obj.get("thumbnailUrl", "") or obj.get("contentUrl", ""),
                                "original_url": obj.get("contentUrl", url),
                            })
                    except (json.JSONDecodeError, KeyError):
                        continue
        
        # Deduplicate by link
        seen = set()
        unique = []
        for r in results:
            if r["link"] not in seen:
                seen.add(r["link"])
                unique.append(r)
        
        print(f"  [BING] Found {len(unique)} candidates via Bing Visual Search")
        return unique[:40]  # Cap at 40 results
        
    except Exception as e:
        print(f"  [BING] Bing Visual Search failed (non-fatal): {e}", file=sys.stderr)
        return []
