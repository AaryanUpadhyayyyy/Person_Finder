import os
import shutil
import tempfile
import json
import time
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from main import stage_face, stage_search, stage_verify, stage_blockchain
from utils.config import get_config, get_output_dir

app = FastAPI(title="Talaash Face ID API")

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

def format_sse(type_: str, data: any) -> str:
    return f"data: {json.dumps({'type': type_, 'data': data})}\n\n"

@app.post("/api/scan")
async def scan_face(file: UploadFile = File(...), serpapi_key: str = Form(None), groq_api_key: str = Form(None)):
    suffix = Path(file.filename).suffix if file.filename else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    if serpapi_key:
        get_config()["SERPAPI_API_KEY"] = serpapi_key
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Missing SerpApi key. Please provide it in the UI.")

    async def event_generator():
        try:
            def tstamp(): return time.strftime('%H:%M:%S')
            
            yield format_sse("log", f"[{tstamp()}] Target image loaded. Extracting facial features...")
            
            face_result = await run_in_threadpool(stage_face, tmp_path)
            face_meta = face_result["meta"]
            
            yield format_sse("log", f"[{tstamp()}] Face verified! Confidence: {round(float(face_meta.get('det_score', 0)), 2)}")
            yield format_sse("log", f"[{tstamp()}] Uploading target hash to global search node...")
            
            search_result = await run_in_threadpool(stage_search, tmp_path, face_result["cropped_path"], force_fresh=False)
            social_count = len(search_result.get("social_media_matches", []))
            visual_count = len(search_result.get("visual_matches", []))
            
            yield format_sse("log", f"[{tstamp()}] Global search complete. Found {social_count + visual_count} visual matches.")
            yield format_sse("log", f"[{tstamp()}] Verifying matches against baseline...")
            
            verify_result = await run_in_threadpool(stage_verify, face_result["embedding"], tmp_path, search_result)
            
            best_match = verify_result.get("best_match")
            if not best_match or not best_match.get("verified", False):
                yield format_sse("log", f"[{tstamp()}] Primary search failed to find match. Initiating DEEP SEARCH (Triple Engine)...")
                
                from search.web_search import search_all_engines
                from search.verify_match import verify_candidates
                
                existing_links = {c.get("link", "") for c in verify_result.get("all_scored", [])}
                existing_links.update(c.get("link", "") for c in verify_result.get("skipped", []))
                
                yield format_sse("log", f"[{tstamp()}] Dispatching to Yandex, Google Reverse, and Bing Visual Search...")
                deep_candidates = await run_in_threadpool(search_all_engines, search_result["image_url"])
                
                new_candidates = [c for c in deep_candidates if c["link"] not in existing_links][:30]
                
                if new_candidates:
                    yield format_sse("log", f"[{tstamp()}] Deep Search returned {len(new_candidates)} candidates. Verifying...")
                    deep_verify = await run_in_threadpool(verify_candidates, face_result["embedding"], tmp_path, new_candidates)
                    
                    verify_result["all_scored"].extend(deep_verify.get("all_scored", []))
                    verify_result["skipped"].extend(deep_verify.get("skipped", []))
                    verify_result["all_scored"].sort(key=lambda x: x.get("similarity", 0), reverse=True)
                    
                    if verify_result["all_scored"]:
                        verify_result["best_match"] = verify_result["all_scored"][0]
                        if verify_result["best_match"].get("verified", False):
                            search_result["visual_matches"].append(verify_result["best_match"])

            best_match = verify_result.get("best_match")
            all_scored = verify_result.get("all_scored", [])
            skipped = verify_result.get("skipped", [])
            threshold = float(get_config()["SIMILARITY_THRESHOLD"])
            
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
            
            main_result = {
                "passed": best_match["verified"] if best_match else False,
                "best_score": float(best_match["similarity"]) if best_match else 0.0,
                "best_source": str(best_match.get("source", "N/A")) if best_match else "N/A",
                "best_link": str(best_match.get("link", "#")) if best_match else "#",
                "llm_context": "PENDING...",
                "threshold": threshold,
                "faces_found": face_meta.get("num_faces", 0),
                "det_score": round(float(face_meta.get("det_score", 0)), 2),
                "age": face_meta.get("age", "N/A"),
                "gender": face_meta.get("gender", "N/A"),
                "social_matches": social_count,
                "visual_matches": visual_count,
                "total_searched": social_count + visual_count,
                "scored_count": len(all_scored),
                "skipped_count": len(skipped),
                "from_cache": search_result.get("from_cache", False),
                "candidates": candidates,
                "blockchain_tx": "PENDING...",
                "block_number": "PENDING...",
                "osint_profiles": None,
            }
            
            yield format_sse("result", main_result)
            
            yield format_sse("log_background", f"[{tstamp()}] Initializing Intelligence Brief generator...")
            llm_context_result = "N/A"
            if best_match and best_match.get("verified", False):
                try:
                    from utils.llm_context import analyze_context
                    # Use groq_api_key from form, fallback to env
                    final_groq = groq_api_key or os.getenv("GROQ_API_KEY", "")
                    best_link = best_match.get("link")
                    best_score = float(best_match.get("similarity", 0.0))
                    fallback_title = best_match.get("title", "")
                    llm_response = await run_in_threadpool(analyze_context, best_link, final_groq, best_score, fallback_title)
                    if llm_response:
                        llm_context_result = llm_response
                except Exception as e:
                    print("LLM analysis failed:", e)
            
            yield format_sse("update_llm", llm_context_result)
            
            # ── OSINT Social Profiling (Background Task B) ──────────
            yield format_sse("log_background", f"[{tstamp()}] Running OSINT Social Profiling & Indian Dorking...")
            osint_result = {"extracted": {}, "profiles": []}
            
            # Include only AI-VERIFIED social media matches (scored by InsightFace)
            from urllib.parse import urlparse
            social_domain_map = {
                "instagram.com": "Instagram", "x.com": "X (Twitter)", "twitter.com": "X (Twitter)",
                "facebook.com": "Facebook", "linkedin.com": "LinkedIn", "pinterest.com": "Pinterest",
                "youtube.com": "YouTube", "tiktok.com": "TikTok",
            }
            seen_urls = set()
            
            # Use scored candidates (already verified by InsightFace) — highest score first
            for candidate in all_scored:
                link = candidate.get("link", "")
                score = float(candidate.get("similarity", 0))
                if not link or link in seen_urls or score < 0.60:
                    continue
                try:
                    domain = urlparse(link).netloc.lower().replace("www.", "")
                except:
                    domain = ""
                # Only include social media domains
                platform = None
                for d, p in social_domain_map.items():
                    if d in domain:
                        platform = p
                        break
                if platform:
                    seen_urls.add(link)
                    osint_result["profiles"].append({
                        "platform": platform,
                        "url": link,
                        "title": candidate.get("title", "")[:200],
                        "snippet": f"Match Score: {round(score, 2)}",
                    })
            
            # Run OSINT dorking if LLM extracted useful text
            if llm_context_result and llm_context_result not in ("N/A", "PENDING...") and not llm_context_result.startswith("INTELLIGENCE FAILURE"):
                try:
                    from utils.osint_profiler import run_osint_profiling
                    final_groq = groq_api_key or os.getenv("GROQ_API_KEY", "")
                    dork_result = await run_in_threadpool(
                        run_osint_profiling,
                        llm_context_result,
                        final_groq,
                        serpapi_key,
                    )
                    if dork_result.get("extracted"):
                        osint_result["extracted"] = dork_result["extracted"]
                    for p in dork_result.get("profiles", []):
                        if p.get("url") not in seen_urls:
                            seen_urls.add(p["url"])
                            osint_result["profiles"].append(p)
                except Exception as e:
                    print(f"OSINT profiling failed: {e}")
            
            yield format_sse("update_osint", osint_result)
            
            yield format_sse("log_background", f"[{tstamp()}] Writing report hash to Sepolia Blockchain...")
            try:
                blockchain_result = await run_in_threadpool(stage_blockchain, search_result, verify_result)
                tx_hash = blockchain_result.get("upload", {}).get("tx_hash", "N/A")
                block_num = blockchain_result.get("upload", {}).get("block_number", "N/A")
            except Exception as e:
                print("Blockchain failed:", e)
                tx_hash = "Hardhat offline"
                block_num = "N/A"
                
            yield format_sse("update_blockchain", {"tx_hash": tx_hash, "block_number": block_num})
            yield format_sse("done", True)
            
        except Exception as overall_e:
            import traceback
            traceback.print_exc()
            yield format_sse("error", f"Backend Error: {str(overall_e)}")
            
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)

