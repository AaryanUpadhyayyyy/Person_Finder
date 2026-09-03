# TALAASH — Facial Intelligence & OSINT Reconnaissance System

<div align="center">

**An AI-powered face identification pipeline that searches the global internet, verifies biometric matches, extracts intelligence, hunts social media profiles, and creates tamper-proof blockchain evidence.**

```
Photo → Quad-Engine Search → AI Verification → LLM Intel Brief → OSINT Profiling → Blockchain Proof
```

</div>

---

## What Is TALAASH?

TALAASH (meaning "Search" in Hindi/Urdu) is a full-stack OSINT (Open Source Intelligence) tool built for face-based identity reconnaissance. You upload a single photograph, and the system:

1. **Scans the global internet** using 4 search engines simultaneously
2. **Biometrically verifies** every candidate match using AI facial embeddings
3. **Generates an intelligence brief** about the person using LLM analysis
4. **Hunts for social media profiles** across Instagram, X, LinkedIn, Facebook, and Indian platforms
5. **Creates immutable blockchain proof** of every discovery

---

## Pipeline Architecture

```
                            ┌──────────────────────────┐
                            │     TARGET PHOTO INPUT    │
                            └────────────┬─────────────┘
                                         │
                            ┌────────────▼─────────────┐
                            │   STAGE 1: FACE ENCODING  │
                            │  InsightFace SCRFD+ArcFace│
                            │  512-dim L2-normalized    │
                            └────────────┬─────────────┘
                                         │
                 ┌───────────────────────┬┴┬───────────────────────┐
                 │                       │ │                       │
    ┌────────────▼──────────┐  ┌─────────▼─▼─────────┐  ┌────────▼────────────┐
    │   GOOGLE LENS (Dual)  │  │   YANDEX REVERSE     │  │  BING VISUAL SEARCH │
    │   Original + Cropped  │  │   Unfiltered Results  │  │  LinkedIn/Pinterest │
    └────────────┬──────────┘  └─────────┬───────────┘  └────────┬────────────┘
                 │                       │                       │
                 └───────────────────────┼───────────────────────┘
                                         │
                            ┌────────────▼─────────────┐
                            │ STAGE 3: AI VERIFICATION  │
                            │  10-thread parallel scan   │
                            │  Multi-face cosine sim     │
                            │  High-res fallback         │
                            └────────────┬─────────────┘
                                         │
                     ┌───────────────────┬┴┬───────────────────┐
                     │                   │ │                   │
        ┌────────────▼──────┐  ┌────────▼─▼────────┐  ┌──────▼──────────────┐
        │   LLM INTEL BRIEF │  │  OSINT SOCIAL      │  │ BLOCKCHAIN PROOF    │
        │  Jina Reader+Groq │  │  PROFILER           │  │ Sepolia/Hardhat     │
        │  Context analysis │  │  8 Google Dorks     │  │ SHA-256 notarize    │
        └───────────────────┘  │  India Dorking      │  └─────────────────────┘
                               └────────────────────┘
```

---

## Features

### Quad-Engine Deep Search
| Engine | What It Searches | Strength |
|--------|-----------------|----------|
| **Google Lens** | General web, news, blogs | Largest index |
| **Yandex Reverse** | Russian web, unfiltered results | No privacy filters |
| **Google Reverse Image** | Older indexed pages | Comprehensive coverage |
| **Bing Visual Search** | LinkedIn, Pinterest, Facebook | Microsoft ecosystem (free, no API key) |

### AI-Powered Verification
- **InsightFace** (SCRFD + ArcFace) generates 512-dimensional facial embeddings
- **Multi-face scoring** — matches targets even in group photos
- **High-res fallback** — re-downloads full-resolution images for borderline matches
- **10-thread parallel processing** for speed

### LLM Intelligence Brief
- Uses **Jina Reader API** to extract clean text from JS-heavy pages (Facebook, X, Instagram)
- **Groq LLaMA 3** analyzes the text and generates a military-style intelligence brief
- Answers: *Who is this person? What's the context? When was this published?*

### OSINT Social Profiler
After LLM extracts a person's name, the system automatically runs **Google Dorks** across:

| Platform | Dork Query |
|----------|-----------|
| Instagram | `site:instagram.com "{name}" {location}` |
| X (Twitter) | `site:x.com OR site:twitter.com "{name}"` |
| LinkedIn | `site:linkedin.com/in/ "{name}" {org}` |
| Facebook | `site:facebook.com "{name}" {location}` |
| **Shaadi.com** 🇮🇳 | `site:shaadi.com "{name}"` |
| **JeevanSathi** 🇮🇳 | `site:jeevansathi.com "{name}"` |
| **BharatMatrimony** 🇮🇳 | `site:bharatmatrimony.com "{name}"` |
| **Naukri.com** 🇮🇳 | `site:naukri.com "{name}" {org}` |

### Blockchain Proof
- SHA-256 hash of all discovery data stored on **Ethereum (Sepolia Testnet)**
- Tamper-evident — if anyone modifies the data, the hash won't match
- On-chain re-verification via `doesProofExist(id, hash)`

### Real-Time Dashboard (TALAASH UI)
- **Live Terminal** — SSE (Server-Sent Events) stream shows real-time pipeline logs
- **3D Earth Globe** — animated globe background with starfield
- **Framer Motion** animations on all panels
- **Dark intelligence-dashboard aesthetic** — pure black, red accent, JetBrains Mono
- **Mobile responsive** design

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React, TypeScript, Tailwind CSS, Framer Motion, Three.js |
| **Backend** | FastAPI, Python 3.10, Server-Sent Events (SSE) |
| **AI/ML** | InsightFace (SCRFD + ArcFace), Groq LLaMA 3 8B |
| **Search** | SerpApi (Google Lens, Yandex, Google Reverse), Bing Visual Search (free scraper) |
| **Blockchain** | Solidity, web3.py, Hardhat, Sepolia Testnet |
| **Deployment** | Vercel (frontend), AWS EC2 + Docker (backend) |

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Git

### 1. Install Dependencies

```bash
cd face_id_blockchain
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### 2. Set Up Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it | Required? |
|----------|----------------|-----------|
| `SERPAPI_API_KEY` | [serpapi.com](https://serpapi.com/manage-api-key) | ✅ Yes |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/keys) | ✅ Yes (for LLM + OSINT) |
| `IMGBB_API_KEY` | [api.imgbb.com](https://api.imgbb.com/) | Optional (uguu.se fallback) |
| `ETH_RPC_URL` | `http://127.0.0.1:8545` for local Hardhat | Optional |
| `ETH_PRIVATE_KEY` | Hardhat default key is pre-filled | Optional |
| `SIMILARITY_THRESHOLD` | Face match threshold (default: `0.4`) | Optional |

### 3. Run Backend

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run Frontend

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and start scanning!

### 5. (Optional) Blockchain Setup

```bash
# Compile smart contract
python -m blockchain.compile_contract

# Start local Hardhat node (separate terminal)
npx hardhat node

# Deploy contract
python -m blockchain.deploy_contract
```

---

## Project Structure

```
face_id_blockchain/
├── face/
│   └── face_scan.py              # InsightFace wrapper (SCRFD + ArcFace)
├── search/
│   ├── web_search.py             # Google Lens, Yandex, Google Reverse, Bing
│   └── verify_match.py           # Multi-candidate face verification
├── blockchain/
│   ├── contracts/
│   │   └── ProofOfExistence.sol  # Solidity smart contract
│   ├── compile_contract.py       # Compiler
│   ├── deploy_contract.py        # Deployer
│   ├── blockchain_upload.py      # Hash upload
│   └── blockchain_verify.py      # Hash re-verification
├── utils/
│   ├── config.py                 # Environment config loader
│   ├── image_utils.py            # Image download/upload/compare
│   ├── llm_context.py            # LLM Intelligence Brief (Jina + Groq)
│   ├── bing_search.py            # Free Bing Visual Search scraper
│   └── osint_profiler.py         # OSINT Social Profiler + Indian Dorking
├── frontend/
│   └── src/app/
│       ├── page.tsx              # Main TALAASH dashboard
│       └── components/
│           └── EarthGlobe.tsx    # 3D Globe component
├── api.py                        # FastAPI backend (SSE streaming)
├── main.py                       # CLI pipeline entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## API Endpoints

### `POST /api/scan`

Upload a face image and receive a real-time SSE stream of pipeline events.

**Form Data:**
| Field | Type | Description |
|-------|------|-------------|
| `file` | File | Target face image (JPEG/PNG) |
| `serpapi_key` | String | SerpApi API key |
| `groq_api_key` | String | Groq API key (optional, falls back to env) |

**SSE Events:**
| Event Type | Payload | Description |
|-----------|---------|-------------|
| `log` | `string` | Real-time pipeline status |
| `result` | `ScanResult` | Verified candidates + biometrics |
| `update_llm` | `string` | Intelligence Brief text |
| `update_osint` | `OsintResult` | Social media profiles |
| `update_blockchain` | `{tx_hash, block_number}` | Blockchain proof |
| `done` | `true` | Stream complete |
| `error` | `string` | Error message |

---

## Known Limitations

- **Search coverage** depends on what Google/Yandex/Bing have indexed. Private accounts and un-indexed content won't appear.
- **SerpApi credits** — each scan uses ~2 Google Lens + ~2 deep search + ~8 OSINT dork credits ≈ **12 credits per scan**.
- **Bing scraper** is best-effort — Bing may block requests with CAPTCHAs. It silently fails and the pipeline continues.
- **Face accuracy** depends on image quality, lighting, and angle.
- **Testnet-only** blockchain — mainnet deployment requires real ETH and security audits.
- **Ethical use only** — face identification technology requires explicit consent. This project is for educational and hackathon purposes.

---

## Deployment

| Component | Platform | Method |
|-----------|----------|--------|
| Frontend | Vercel | Auto-deploy on `git push` to `main` |
| Backend | AWS EC2 | Docker container on port 10000 |

---

## License

MIT

---

<div align="center">

**Built by [Aaryan Upadhyay](https://github.com/AaryanUpadhyayyyy)**

*TALAASH — Because every face tells a story.*

</div>
