import os
import shutil
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env before importing main modules to ensure config reads it
load_dotenv()

# Import pipeline stages from main.py
from main import stage_face, stage_search, stage_verify, stage_blockchain
from utils.config import get_config, get_output_dir

app = FastAPI(title="Talaash Face ID API")

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://person-finder-ten.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/scan")
async def scan_face(file: UploadFile = File(...), serpapi_key: str = Form(None)):
    suffix = Path(file.filename).suffix if file.filename else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    if serpapi_key:
        get_config()["SERPAPI_API_KEY"] = serpapi_key
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Missing SerpApi key. Please provide it in the UI.")

    try:
        # Stage 1: Face
        face_result = stage_face(tmp_path)
        face_meta = face_result["meta"]
        
        # Stage 2: Web Search (Dual Search)
        search_result = stage_search(tmp_path, face_result["cropped_path"], force_fresh=False)
        
        # Stage 3: Verification
        verify_result = stage_verify(face_result["embedding"], tmp_path, search_result)
        
        # --- DEEP SEARCH FALLBACK (Triple Engine) ---
        best_match = verify_result.get("best_match")
        if not best_match or not best_match.get("verified", False):
            print("No verified match from Google Lens. Triggering Triple Engine Deep Search...")
            from search.web_search import search_all_engines
            from search.verify_match import verify_candidates
            
            # Collect existing links to avoid re-verifying duplicates
            existing_links = {c.get("link", "") for c in verify_result.get("all_scored", [])}
            existing_links.update(c.get("link", "") for c in verify_result.get("skipped", []))
            
            deep_candidates = search_all_engines(search_result["image_url"])
            # Filter out already-processed candidates and LIMIT to top 30 to save time
            new_candidates = [c for c in deep_candidates if c["link"] not in existing_links][:30]
            
            if new_candidates:
                print(f"Deep Search: {len(new_candidates)} NEW candidates to verify.")
                deep_verify = verify_candidates(face_result["embedding"], tmp_path, new_candidates)
                
                # Merge newly scored candidates
                verify_result["all_scored"].extend(deep_verify.get("all_scored", []))
                verify_result["skipped"].extend(deep_verify.get("skipped", []))
                
                # Re-sort all_scored by similarity
                verify_result["all_scored"].sort(key=lambda x: x.get("similarity", 0), reverse=True)
                
                # Re-evaluate best_match
                if verify_result["all_scored"]:
                    verify_result["best_match"] = verify_result["all_scored"][0]
                    if verify_result["best_match"].get("verified", False):
                        search_result["visual_matches"].append(verify_result["best_match"])
        # -------------------------------------------

        # Stage 4: Blockchain (try, skip if hardhat offline)
        try:
            blockchain_result = stage_blockchain(search_result, verify_result)
            tx_hash = blockchain_result.get("upload", {}).get("tx_hash", "N/A")
            block_num = blockchain_result.get("upload", {}).get("block_number", "N/A")
        except Exception as e:
            print("Blockchain failed:", e)
            tx_hash = "Hardhat offline"
            block_num = "N/A"
            
        best_match = verify_result.get("best_match")
        all_scored = verify_result.get("all_scored", [])
        skipped = verify_result.get("skipped", [])
        threshold = float(get_config()["SIMILARITY_THRESHOLD"])
        
        # Build all candidates for the frontend (with thumbnail URLs)
        candidates = []
        for c in all_scored:
            candidates.append({
                "thumbnail": c.get("thumbnail", ""),
                "link": c.get("link", "#"),
                "source": c.get("source", "Unknown"),
                "title": c.get("title", ""),
                "score": round(float(c.get("similarity", 0)), 4),
                "verified": c.get("verified", False),
            })
        
        social_count = len(search_result.get("social_media_matches", []))
        visual_count = len(search_result.get("visual_matches", []))
        
        return {
            # Summary
            "passed": best_match["verified"] if best_match else False,
            "best_score": float(best_match["similarity"]) if best_match else 0.0,
            "best_source": str(best_match.get("source", "N/A")) if best_match else "N/A",
            "best_link": str(best_match.get("link", "#")) if best_match else "#",
            "threshold": threshold,
            
            # Face info
            "faces_found": face_meta.get("num_faces", 0),
            "det_score": round(float(face_meta.get("det_score", 0)), 2),
            "age": face_meta.get("age", "N/A"),
            "gender": face_meta.get("gender", "N/A"),
            
            # Search stats
            "social_matches": social_count,
            "visual_matches": visual_count,
            "total_searched": social_count + visual_count,
            "scored_count": len(all_scored),
            "skipped_count": len(skipped),
            "from_cache": search_result.get("from_cache", False),
            
            # All candidates ranked by score
            "candidates": candidates,
            
            # Blockchain
            "blockchain_tx": tx_hash,
            "block_number": block_num,
        }
            
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
