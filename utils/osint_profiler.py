"""Automated OSINT Social Profiler with Indian Database Dorking.

After the LLM Intelligence Brief extracts a person's name (or any clue),
this module automatically hunts for their social media profiles using
Google Dork queries via SerpApi.

Includes India-specific dorking for matrimonial sites, job portals,
and LinkedIn India.
"""

from __future__ import annotations

import json
import sys
import re
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests
from groq import Groq


_SERPAPI_URL = "https://serpapi.com/search.json"
_TIMEOUT = 15


# ── Entity Extraction via LLM ────────────────────────────────────────

def _extract_entities(llm_text: str, groq_api_key: str) -> Dict[str, str]:
    """Use Groq LLaMA to extract structured entities from LLM intel text.
    
    Returns: {"name": str, "location": str, "org": str, "keywords": str}
    """
    if not groq_api_key or not llm_text or llm_text in ("N/A", "PENDING..."):
        return {"name": "", "location": "", "org": "", "keywords": ""}
    
    try:
        client = Groq(api_key=groq_api_key)
        
        prompt = f"""Extract the following entities from this intelligence text. Return ONLY a valid JSON object, nothing else.

Text:
{llm_text[:3000]}

Return this exact JSON structure:
{{"name": "full name of the person or empty string", "location": "city/state/country or empty string", "org": "organization/company/college or empty string", "keywords": "any other identifying keywords separated by commas, or empty string"}}

Rules:
- If a field is not found, use empty string ""
- Do NOT invent or guess information
- Return ONLY the JSON, no markdown, no explanation"""

        chat = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You extract structured entities from text. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-8b-8192",
            temperature=0.0,
            max_tokens=200,
        )
        
        raw = chat.choices[0].message.content.strip()
        # Clean up markdown code fences if present
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        
        parsed = json.loads(raw)
        return {
            "name": str(parsed.get("name", "")),
            "location": str(parsed.get("location", "")),
            "org": str(parsed.get("org", "")),
            "keywords": str(parsed.get("keywords", "")),
        }
    except Exception as e:
        print(f"  [OSINT] Entity extraction failed: {e}", file=sys.stderr)
        return {"name": "", "location": "", "org": "", "keywords": ""}


# ── Google Dorking via SerpApi ────────────────────────────────────────

def _run_dork(query: str, serpapi_key: str, num: int = 5) -> List[Dict[str, str]]:
    """Run a single Google Dork query via SerpApi and return results."""
    try:
        params = {
            "engine": "google",
            "q": query,
            "api_key": serpapi_key,
            "num": str(num),
            "no_cache": "true",
        }
        
        resp = requests.get(_SERPAPI_URL, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        
        results = []
        for item in data.get("organic_results", []):
            link = item.get("link", "")
            if not link:
                continue
            
            # Determine platform from URL
            try:
                domain = urlparse(link).netloc.lower().replace("www.", "")
            except:
                domain = ""
            
            platform = _domain_to_platform(domain)
            
            results.append({
                "platform": platform,
                "url": link,
                "title": item.get("title", "")[:200],
                "snippet": item.get("snippet", "")[:300],
            })
        
        return results
    except Exception as e:
        print(f"  [OSINT] Dork query failed: {query[:50]}... -> {e}", file=sys.stderr)
        return []


def _domain_to_platform(domain: str) -> str:
    """Map a domain to a human-readable platform name."""
    mapping = {
        "instagram.com": "Instagram",
        "x.com": "X (Twitter)",
        "twitter.com": "X (Twitter)",
        "facebook.com": "Facebook",
        "linkedin.com": "LinkedIn",
        "pinterest.com": "Pinterest",
        "youtube.com": "YouTube",
        "tiktok.com": "TikTok",
        "shaadi.com": "Shaadi.com",
        "jeevansathi.com": "JeevanSathi",
        "bharatmatrimony.com": "BharatMatrimony",
        "naukri.com": "Naukri.com",
        "apna.co": "Apna Jobs",
    }
    for key, val in mapping.items():
        if key in domain:
            return val
    return domain


# ── Main OSINT Profiler ───────────────────────────────────────────────

def run_osint_profiling(
    llm_text: str,
    groq_api_key: str,
    serpapi_key: str,
) -> Dict[str, Any]:
    """Run full OSINT social profiling pipeline.
    
    1. Extract entities (name, location, org) from LLM text via Groq
    2. Run Google Dork queries across social media + Indian platforms
    3. Return structured profile results
    
    Returns:
    {
        "extracted": {"name": str, "location": str, "org": str},
        "profiles": [
            {"platform": str, "url": str, "title": str, "snippet": str},
            ...
        ]
    }
    """
    # Step 1: Extract entities
    print("  [OSINT] Extracting entities from intelligence brief...")
    entities = _extract_entities(llm_text, groq_api_key)
    
    name = entities.get("name", "").strip()
    location = entities.get("location", "").strip()
    org = entities.get("org", "").strip()
    
    if not name:
        print("  [OSINT] No name extracted. Skipping social profiling.")
        return {
            "extracted": entities,
            "profiles": [],
        }
    
    print(f"  [OSINT] Target identified: {name} | Location: {location or 'Unknown'} | Org: {org or 'Unknown'}")
    
    # Step 2: Build dork queries
    dork_queries = []
    
    # --- Global Social Media Dorks ---
    location_suffix = f" {location}" if location else ""
    org_suffix = f" {org}" if org else ""
    
    # Instagram
    dork_queries.append(f'site:instagram.com "{name}"{location_suffix}')
    
    # X (Twitter)
    dork_queries.append(f'site:x.com OR site:twitter.com "{name}"{location_suffix}')
    
    # LinkedIn
    dork_queries.append(f'site:linkedin.com/in/ "{name}"{org_suffix}')
    
    # Facebook
    dork_queries.append(f'site:facebook.com "{name}"{location_suffix}')
    
    # --- India-Specific Dorks ---
    # Matrimonial sites (huge photo databases of Indian people)
    dork_queries.append(f'site:shaadi.com OR site:jeevansathi.com "{name}"')
    
    # BharatMatrimony (South India heavy)
    dork_queries.append(f'site:bharatmatrimony.com "{name}"')
    
    # Job portals
    dork_queries.append(f'site:naukri.com OR site:apna.co "{name}"{org_suffix}')
    
    # General web profile search (catches blogs, college sites, etc.)
    dork_queries.append(f'"{name}"{location_suffix}{org_suffix} profile OR about')
    
    # Step 3: Execute dorks in parallel (max 4 concurrent to avoid SerpApi rate limits)
    print(f"  [OSINT] Running {len(dork_queries)} dork queries in parallel...")
    all_profiles: List[Dict[str, str]] = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_run_dork, query, serpapi_key, 3): query
            for query in dork_queries
        }
        
        for future in as_completed(futures):
            query = futures[future]
            try:
                results = future.result()
                if results:
                    print(f"  [OSINT] Dork hit: {len(results)} results for: {query[:60]}...")
                    all_profiles.extend(results)
            except Exception as e:
                print(f"  [OSINT] Dork failed: {e}")
    
    # Step 4: Deduplicate by URL
    seen_urls = set()
    unique_profiles = []
    for p in all_profiles:
        url = p.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_profiles.append(p)
    
    # Sort: social media first, then Indian platforms, then general
    platform_priority = {
        "Instagram": 1, "X (Twitter)": 2, "LinkedIn": 3, "Facebook": 4,
        "Shaadi.com": 5, "JeevanSathi": 6, "BharatMatrimony": 7,
        "Naukri.com": 8, "Apna Jobs": 9,
    }
    unique_profiles.sort(key=lambda x: platform_priority.get(x.get("platform", ""), 99))
    
    print(f"  [OSINT] Social profiling complete: {len(unique_profiles)} unique profiles found")
    
    return {
        "extracted": entities,
        "profiles": unique_profiles[:20],  # Cap at 20 results
    }
