#!/usr/bin/env python3
"""Face Identification & Blockchain Verification — end-to-end CLI.

Usage:
    python main.py --image photo.jpg
    python main.py --image photo.jpg --threshold 0.5
    python main.py --image photo.jpg --no-blockchain
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# ── ensure project root is on sys.path ─────────────────────────────────
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


# ── pretty helpers (no external dep) ───────────────────────────────────

def _ts() -> str:
    return time.strftime("%H:%M:%S")

def _sec(t: float) -> str:
    return f"{t:.1f}s"

def _print_header():
    print("\n" + "=" * 58)
    print("  Face Identification & Blockchain Verification Pipeline")
    print("=" * 58 + "\n")

def _step(n: int, total: int, icon: str, title: str):
    print(f"\n[{n}/{total}] {icon} {title}")
    print("-" * 50)

def _ok(msg: str):
    print(f"  ✓ {msg}")

def _warn(msg: str):
    print(f"  ⚠ {msg}")

def _fail(msg: str):
    print(f"  ✗ {msg}", file=sys.stderr)


# ── CLI ────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Face ID + Blockchain Verification Pipeline",
    )
    p.add_argument(
        "--image", required=True,
        help="Path to input face image (jpg/png)",
    )
    p.add_argument(
        "--threshold", type=float, default=None,
        help="Cosine-similarity threshold (overrides .env)",
    )
    p.add_argument(
        "--no-blockchain", action="store_true",
        help="Skip blockchain upload (useful for search-only testing)",
    )
    p.add_argument(
        "--no-search", action="store_true",
        help="Skip web search (useful for face + blockchain testing)",
    )
    p.add_argument(
        "--fresh-search", action="store_true",
        help="Bypass search cache and make a real SerpApi call",
    )
    return p.parse_args()


# ── pipeline stages ────────────────────────────────────────────────────

def stage_face(image_path: str) -> dict:
    """Stage 1: detect face + extract embedding."""
    from face.face_scan import get_face_embedding, save_annotated_image
    from utils.config import get_output_dir

    emb, meta = get_face_embedding(image_path)
    _ok(f"Face detected — score {meta['det_score']:.2f}, "
        f"age {meta['age']}, gender {meta['gender']}")
    _ok(f"Embedding: {emb.shape[0]}-dim vector (L2-normalised)")
    _ok(f"Faces in image: {meta['num_faces']}")

    annotated = save_annotated_image(
        image_path, str(get_output_dir() / "face_detected.jpg")
    )
    _ok(f"Annotated image → {annotated}")

    return {"embedding": emb, "meta": meta}


def stage_search(image_path: str, *, force_fresh: bool = False) -> dict:
    """Stage 2: reverse-image search via Google Lens."""
    from search.web_search import search_face_online

    result = search_face_online(image_path, force_fresh=force_fresh)
    tier = result["search_tier"]

    social = result["social_media_matches"]
    visual = result["visual_matches"]
    _ok(f"Google Lens returned {len(visual)} visual match(es)")

    if social:
        _ok(f"Social-media matches: {len(social)}")
        for m in social[:3]:
            _ok(f"  → {m['source']}: {m['link'][:70]}")
    elif visual:
        _warn("No social-media matches — using best visual match")
    else:
        _warn("No matches found — pipeline will use self-hash mode")

    return result


def stage_verify(
    embedding, image_path: str, search_result: dict
) -> dict:
    """Stage 3: face-level candidate verification."""
    from search.verify_match import verify_candidates

    tier = search_result["search_tier"]
    if tier == "no_match":
        _warn("Skipping verification — no candidates to verify")
        return {"best_match": None, "all_scored": [], "skipped": [],
                "comparison_image": None}

    # prefer social-media, fall back to any visual
    candidates = (search_result["social_media_matches"]
                  or search_result["visual_matches"])

    result = verify_candidates(embedding, image_path, candidates)
    best = result["best_match"]

    if best and best["verified"]:
        _ok(f"MATCH — similarity {best['similarity']:.2f} "
            f"(threshold passed)")
        _ok(f"Source: {best.get('source', 'N/A')}")
        _ok(f"Link:   {best.get('link', 'N/A')[:80]}")
    elif best:
        _warn(f"Best candidate similarity {best['similarity']:.2f} "
              f"— below threshold")
    else:
        _warn("No candidate had a detectable face")

    if result["comparison_image"]:
        _ok(f"Comparison image → {result['comparison_image']}")

    scored_count = len(result["all_scored"])
    skip_count = len(result["skipped"])
    _ok(f"Scored {scored_count}, skipped {skip_count}")

    return result


def stage_blockchain(search_result: dict, verify_result: dict) -> dict:
    """Stage 4: hash upload + on-chain re-verification."""
    from blockchain.blockchain_upload import upload_proof
    from blockchain.blockchain_verify import verify_proof

    # build discovery payload
    best = verify_result.get("best_match")
    if best:
        discovery = {
            "link": best.get("link", ""),
            "title": best.get("title", ""),
            "source": best.get("source", ""),
            "similarity": best.get("similarity", ""),
        }
    else:
        # self-hash mode: hash the search metadata itself
        discovery = {
            "link": search_result.get("image_url", "self"),
            "title": "self-hash-mode",
            "source": "pipeline",
            "similarity": "N/A",
        }
        _warn("Using self-hash mode (no verified match)")

    # upload
    upload = upload_proof(discovery)
    _ok(f"Data hash : {upload['data_hash']}")
    _ok(f"TX hash   : {upload['tx_hash']}")
    _ok(f"Block #   : {upload['block_number']}")
    _ok(f"Record ID : {upload['record_id']}")
    _ok(f"Gas used  : {upload['gas_used']}")

    # re-verify
    verification = verify_proof(discovery, record_id=upload["record_id"])
    if verification["verified"]:
        _ok("On-chain re-verification: TRUE ✓")
    else:
        _fail("On-chain re-verification: FALSE ✗ — data may be tampered")

    return {"upload": upload, "verification": verification,
            "discovery_data": discovery}


# ── main ───────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    image_path = args.image

    if not Path(image_path).is_file():
        _fail(f"Image not found: {image_path}")
        sys.exit(1)

    # override threshold via CLI if provided
    if args.threshold is not None:
        os.environ["SIMILARITY_THRESHOLD"] = str(args.threshold)

    _print_header()
    pipeline_start = time.time()
    total_steps = 4 - int(args.no_search) - int(args.no_blockchain)
    step = 0

    # ── Stage 1: Face ──────────────────────────────────────────────
    step += 1
    _step(step, total_steps, "🔍", "Encoding Face...")
    t0 = time.time()
    face_result = stage_face(image_path)
    _ok(f"⏱  {_sec(time.time() - t0)}")

    search_result = {"search_tier": "no_match", "social_media_matches": [],
                     "visual_matches": [], "image_url": ""}
    verify_result = {"best_match": None, "all_scored": [], "skipped": [],
                     "comparison_image": None}

    # ── Stage 2: Search ────────────────────────────────────────────
    if not args.no_search:
        step += 1
        _step(step, total_steps, "🌐", "Searching Web for Matches...")
        t0 = time.time()
        try:
            search_result = stage_search(
                image_path, force_fresh=args.fresh_search
            )
            if search_result.get("from_cache"):
                _ok("(cached result — use --fresh-search for new API call)")
        except Exception as exc:
            _warn(f"Search failed: {exc}")
            _warn("Continuing in self-hash mode")
        _ok(f"⏱  {_sec(time.time() - t0)}")

        # ── Stage 3: Verify ────────────────────────────────────────
        step += 1
        _step(step, total_steps, "✅", "Verifying Face Match...")
        t0 = time.time()
        try:
            verify_result = stage_verify(
                face_result["embedding"], image_path, search_result
            )
        except Exception as exc:
            _warn(f"Verification failed: {exc}")
        _ok(f"⏱  {_sec(time.time() - t0)}")

    # ── Stage 4: Blockchain ────────────────────────────────────────
    blockchain_result = {}
    if not args.no_blockchain:
        step += 1
        _step(step, total_steps, "⛓️", "Blockchain Upload + Verification")
        t0 = time.time()
        try:
            blockchain_result = stage_blockchain(search_result, verify_result)
        except Exception as exc:
            _fail(f"Blockchain stage failed: {exc}")
            _warn("Ensure contract is deployed (python -m blockchain.deploy_contract)")
        _ok(f"⏱  {_sec(time.time() - t0)}")

    # ── summary ────────────────────────────────────────────────────
    total = time.time() - pipeline_start
    print("\n" + "=" * 58)
    print(f"  Pipeline complete — total time {_sec(total)}")

    # save full result to JSON
    from utils.config import get_output_dir
    out_json = get_output_dir() / "result.json"
    _save_result(out_json, face_result, search_result,
                 verify_result, blockchain_result)
    print(f"  Results saved → {out_json}")
    print("=" * 58 + "\n")


def _save_result(path: Path, face: dict, search: dict,
                 verify: dict, chain: dict) -> None:
    """Persist the full pipeline result as JSON (numpy → list)."""
    import numpy as np

    def _convert(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        if isinstance(obj, bytes):
            return obj.hex()
        raise TypeError(f"Not serialisable: {type(obj)}")

    data = {
        "face": {k: v for k, v in face.items() if k != "embedding"},
        "search": search,
        "verification": verify,
        "blockchain": chain,
    }
    path.write_text(json.dumps(data, indent=2, default=_convert),
                    encoding="utf-8")


if __name__ == "__main__":
    main()
