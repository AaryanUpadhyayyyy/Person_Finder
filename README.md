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
        │  Jina Reader+Groq │  │  PROFILER           │  │ Hardhat Local Chain │
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
- **Groq** LLM analyzes the text and generates a military-style intelligence brief
- Model fallback chain: `openai/gpt-oss-20b` → `qwen/qwen3.8-27b` → `openai/gpt-oss-120b`
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

Only AI-verified social media matches (score > 0.60) are shown in the Social Profiles card.

### Blockchain Proof (Hardhat Local Chain)
- **Hardhat** local Ethereum node runs inside the Docker container (10 accounts × 10,000 ETH)
- Smart contract (`ProofOfExistence.sol`) auto-compiled via `py_solc_x` and auto-deployed on container start
- SHA-256 hash of all discovery data stored on-chain via `notarizeHash(id, hash)`
- Tamper-evident — if anyone modifies the data, the hash won't match
- On-chain re-verification via `doesProofExist(id, hash)`
- **Zero cost, instant finality, no testnet faucets needed**

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
| **AI/ML** | InsightFace (SCRFD + ArcFace), Groq LLM (GPT-OSS / Qwen) |
| **Search** | SerpApi (Google Lens, Yandex, Google Reverse), Bing Visual Search (free scraper) |
| **Blockchain** | Solidity 0.8.1, web3.py, Hardhat (local chain inside Docker) |
| **Deployment** | Vercel (frontend), AWS EC2 + Docker (backend) |

---

## Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+ (included in Docker)
- Git
- Docker (recommended)

### Option A: Docker (Recommended)

```bash
cd face_id_blockchain

# Build the Docker image (includes Hardhat + Node.js + Python)
docker build -t talaash .

# Create .env file
cp .env.example .env
# Edit .env with your SERPAPI_API_KEY and GROQ_API_KEY

# Run (Hardhat auto-starts, contract auto-deploys)
docker run -d -p 7860:7860 --env-file .env --name talaash talaash
```

The container automatically:
1. Starts a Hardhat local blockchain (localhost:8545)
2. Compiles `ProofOfExistence.sol`
3. Deploys the contract
4. Starts the TALAASH API on port 7860

### Option B: Manual Setup

```bash
cd face_id_blockchain

# Python dependencies
pip install -r requirements.txt

# Node dependencies (for Hardhat)
npm install

# Start Hardhat node (separate terminal)
npx hardhat node

# Compile and deploy contract
python -m blockchain.compile_contract
python -m blockchain.deploy_contract

# Start API
uvicorn api:app --host 0.0.0.0 --port 7860 --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Environment Variables

| Variable | Where to get it | Required? |
|----------|----------------|-----------|
| `SERPAPI_API_KEY` | [serpapi.com](https://serpapi.com/manage-api-key) | ✅ Yes |
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com/keys) | ✅ Yes |
| `ETH_RPC_URL` | Auto-set to `http://127.0.0.1:8545` (Hardhat) | Auto |
| `ETH_PRIVATE_KEY` | Hardhat Account #0 (pre-filled) | Auto |
| `CONTRACT_ADDRESS` | Auto-deployed on container start | Auto |
| `SIMILARITY_THRESHOLD` | Face match threshold (default: `0.4`) | Optional |

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
│   ├── compile_contract.py       # py_solc_x compiler
│   ├── deploy_contract.py        # Contract deployer
│   ├── blockchain_upload.py      # Hash upload to chain
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
├── Dockerfile                    # Multi-layer: Python + Node.js + Hardhat
├── entrypoint.sh                 # Starts Hardhat → deploys contract → starts API
├── hardhat.config.js             # Hardhat configuration
├── package.json                  # Node.js dependencies (Hardhat)
├── requirements.txt              # Python dependencies
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
| `update_osint` | `OsintResult` | Social media profiles (score > 0.60) |
| `update_blockchain` | `{tx_hash, block_number}` | Blockchain proof |
| `done` | `true` | Stream complete |
| `error` | `string` | Error message |

---

## How Blockchain Verification Works

1. Discovery data (URL + title + source + similarity + timestamp) is concatenated into a canonical string
2. SHA-256 hash is computed (32 bytes = Solidity `bytes32`)
3. Hash is stored on-chain via `notarizeHash(id, hash)` on the local Hardhat chain
4. Re-verification recomputes the hash and calls `doesProofExist(id, hash)`
5. If anyone tampers with the data, the recomputed hash won't match → `FALSE`

The Hardhat chain runs inside the Docker container with instant block mining, zero gas cost, and 10,000 ETH per account. No testnet faucets required.

---

## Known Limitations

- **Search coverage** depends on what Google/Yandex/Bing have indexed. Small accounts (<1K followers) are often invisible to search engines.
- **SerpApi credits** — each scan uses ~2 Google Lens + ~2 deep search + ~8 OSINT dork credits ≈ **12 credits per scan**.
- **Bing scraper** is best-effort — Bing may block with CAPTCHAs. Fails silently.
- **Face accuracy** depends on image quality, lighting, and angle.
- **Hardhat chain resets on container restart** — blockchain data is ephemeral. For persistent storage, mount a Docker volume.
- **Ethical use only** — face identification technology requires explicit consent. This project is for educational and hackathon purposes.

---

## Deployment

| Component | Platform | Method |
|-----------|----------|--------|
| Frontend | Vercel | Auto-deploy on `git push` to `main` |
| Backend | AWS EC2 | Docker container (Hardhat + API on port 10000) |

```bash
# AWS deployment
docker build -t backend .
docker run -d -p 10000:7860 --env-file .env --name talaash backend
```

---

## License

MIT

---

<div align="center">

**Built by [Aaryan Upadhyay](https://github.com/AaryanUpadhyayyyy)**

*TALAASH — Because every face tells a story.*

</div>
