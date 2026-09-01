"""Face-level verification of search candidates.

For each candidate thumbnail returned by Google Lens, this module:
  1. downloads the thumbnail image
  2. runs InsightFace to extract an embedding
  3. computes cosine similarity against the original face
  4. ranks all candidates and picks the best confirmed match

Because ``normed_embedding`` is already L2-normalised, cosine similarity
reduces to a single ``np.dot`` — O(512) per comparison.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from face.face_scan import get_face_embedding
from utils.config import get_config, get_output_dir
from utils.image_utils import create_comparison_image, download_image


# ── public API ─────────────────────────────────────────────────────────

def verify_candidates(
    original_embedding: np.ndarray,
    original_image_path: str,
    candidates: List[Dict[str, str]],
) -> Dict[str, Any]:
    """Score every candidate against the original face embedding.

    Parameters
    ----------
    original_embedding:
        512-d L2-normalised vector of the query face.
    original_image_path:
        Path to the original input image (for comparison visual).
    candidates:
        List of dicts, each with at least ``thumbnail`` and ``link``.

    Returns
    -------
    dict with keys
        ``best_match``  – highest-similarity candidate (or ``None``)
        ``all_scored``  – every candidate that could be scored
        ``skipped``     – candidates where face detection failed
        ``comparison_image`` – path to side-by-side image (or ``None``)
    """
    threshold = float(get_config(skip_validation=True).get(
        "SIMILARITY_THRESHOLD", "0.4"
    ))

    scored: List[Dict[str, Any]] = []
    skipped: List[Dict[str, str]] = []

    for cand in candidates:
        thumb_url = cand.get("thumbnail", "")
        if not thumb_url:
            skipped.append(cand)
            continue

        try:
            thumb_img = download_image(thumb_url)
            cand_emb, _ = get_face_embedding(thumb_img)
        except (ValueError, Exception):
            # no face in thumbnail or download failed — skip silently
            skipped.append(cand)
            continue

        sim = float(np.dot(original_embedding, cand_emb))
        scored.append({
            **cand,
            "similarity": round(sim, 4),
            "verified": sim >= threshold,
            "_thumb_img": thumb_img,   # kept in-memory for comparison image
        })

    # rank by similarity descending
    scored.sort(key=lambda x: x["similarity"], reverse=True)

    # build result
    best: Optional[Dict[str, Any]] = None
    comparison_path: Optional[str] = None

    if scored:
        best = {k: v for k, v in scored[0].items() if k != "_thumb_img"}
        # generate comparison image for the top candidate
        try:
            orig_img = cv2.imread(original_image_path)
            if orig_img is not None:
                out = str(get_output_dir() / "comparison.jpg")
                create_comparison_image(
                    orig_img,
                    scored[0]["_thumb_img"],
                    scored[0]["similarity"],
                    out,
                )
                comparison_path = out
        except Exception:
            pass  # non-critical; skip silently

    # strip internal ndarray before returning
    all_clean = [
        {k: v for k, v in s.items() if k != "_thumb_img"} for s in scored
    ]

    return {
        "best_match": best,
        "all_scored": all_clean,
        "skipped": skipped,
        "comparison_image": comparison_path,
    }
