"""Reverse-image search via SerpApi Google Lens.

Follows the API pattern documented in the google-lens-scraper repo:
    GET https://serpapi.com/search.json?engine=google_lens&url=<IMG>&api_key=<KEY>

Implements a 3-tier result strategy so the pipeline never stalls:
    Tier 1 — social-media domain matches
    Tier 2 — any visual match
    Tier 3 — no matches (pipeline continues with self-hash mode)

Caching: every real API response is saved to ``output/.search_cache/``.
Subsequent runs with the same image reuse the cached response — zero
API calls burned during development/testing.  Pass ``force_fresh=True``
or use ``--fresh-search`` on the CLI to bypass the cache.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

from utils.config import get_config, get_output_dir
from utils.image_utils import upload_image

# ── social-media domain whitelist ──────────────────────────────────────
SOCIAL_DOMAINS: frozenset[str] = frozenset({
    "instagram.com",
    "x.com",
    "twitter.com",
    "facebook.com",
    "linkedin.com",
    "tiktok.com",
    "youtube.com",
    "pinterest.com",
})

_API_URL = "https://serpapi.com/search.json"
_TIMEOUT = 30


# ── cache helpers ──────────────────────────────────────────────────────

def _cache_dir() -> Path:
    d = get_output_dir() / ".search_cache"
    d.mkdir(exist_ok=True)
    return d


def _cache_key(image_path: str) -> str:
    """SHA-256 of the image bytes → deterministic cache filename."""
    h = hashlib.sha256(Path(image_path).read_bytes()).hexdigest()[:16]
    return h + ".json"


def _load_cache(image_path: str) -> Dict[str, Any] | None:
    f = _cache_dir() / _cache_key(image_path)
    if f.is_file():
        return json.loads(f.read_text(encoding="utf-8"))
    return None


def _save_cache(image_path: str, data: Dict[str, Any]) -> None:
    f = _cache_dir() / _cache_key(image_path)
    f.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ── public API ─────────────────────────────────────────────────────────

def search_face_online(
    image_path: str,
    *,
    force_fresh: bool = False,
) -> Dict[str, Any]:
    """Upload an image and run a Google Lens reverse-image search.

    Parameters
    ----------
    image_path:
        Local path to the face image.
    force_fresh:
        Bypass cache and make a real API call.

    Returns
    -------
    dict with keys
        ``social_media_matches`` – list filtered to social-media domains
        ``visual_matches``       – *all* visual matches from Google Lens
        ``search_tier``          – ``"social_media"`` | ``"visual_match"``
                                    | ``"no_match"``
        ``image_url``            – the public URL used for the search
        ``from_cache``           – True if cached result was used
    """
    # ── try cache first ────────────────────────────────────────────
    if not force_fresh:
        cached = _load_cache(image_path)
        if cached is not None:
            cached["from_cache"] = True
            return cached

    cfg = get_config()

    # 1. upload image to get a public URL
    image_url = upload_image(image_path)

    # 2. call SerpApi Google Lens
    params: Dict[str, str] = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": cfg["SERPAPI_API_KEY"],
        "no_cache": "true",
    }

    resp = requests.get(_API_URL, params=params, timeout=_TIMEOUT)
    resp.raise_for_status()
    data: Dict[str, Any] = resp.json()

    # 3. extract visual matches
    raw_matches: List[Dict] = data.get("visual_matches", [])
    visual: List[Dict[str, str]] = [
        _normalise_match(m) for m in raw_matches if m.get("link")
    ]

    # 4. filter for social-media
    social: List[Dict[str, str]] = [
        m for m in visual if _is_social(m["link"])
    ]

    # 5. determine tier
    if social:
        tier = "social_media"
    elif visual:
        tier = "visual_match"
    else:
        tier = "no_match"

    result = {
        "social_media_matches": social,
        "visual_matches": visual,
        "search_tier": tier,
        "image_url": image_url,
        "from_cache": False,
    }

    # ── persist to cache ───────────────────────────────────────────
    _save_cache(image_path, result)

    return result


# ── helpers ────────────────────────────────────────────────────────────

def _normalise_match(raw: Dict) -> Dict[str, str]:
    """Extract only the fields we need, with safe defaults."""
    return {
        "link": raw.get("link", ""),
        "title": raw.get("title", ""),
        "source": raw.get("source", ""),
        "thumbnail": raw.get("thumbnail", ""),
    }


def _is_social(url: str) -> bool:
    """Check whether *url* belongs to a known social-media domain."""
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return any(host == d or host.endswith("." + d) for d in SOCIAL_DOMAINS)
    except Exception:
        return False
