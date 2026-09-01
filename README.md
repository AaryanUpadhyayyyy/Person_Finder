# Face Identification & Blockchain Verification

An end-to-end pipeline that takes a **face image** as input, searches the web for matching social-media posts, verifies the match using face embeddings, and creates a **tamper-evident blockchain record** of the discovery.

```
Face scan → Reverse image search → Face verification → Blockchain proof
```

## Pipeline Stages

| Stage | What it does | Technology |
|-------|-------------|------------|
| **1. Face Encoding** | Detects a face and extracts a 512-d embedding | InsightFace (SCRFD + ArcFace) |
| **2. Web Search** | Reverse-image search via Google Lens | SerpApi |
| **3. Face Verification** | Compares embeddings with cosine similarity | InsightFace + NumPy |
| **4. Blockchain Proof** | Hashes discovery data and stores on-chain | Solidity + web3.py |

## Quick Start

### 1. Prerequisites

- Python 3.9+
- Node.js 16+ (for local Hardhat blockchain)
- Git

### 2. Install Dependencies

```bash
cd face_id_blockchain
pip install -r requirements.txt
```

### 3. Set Up Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

| Variable | Where to get it |
|----------|----------------|
| `SERPAPI_API_KEY` | [serpapi.com](https://serpapi.com/manage-api-key) (free: 100 searches/month) |
| `IMGBB_API_KEY` | [api.imgbb.com](https://api.imgbb.com/) (free, optional — catbox.moe fallback) |
| `ETH_RPC_URL` | `http://127.0.0.1:8545` for local Hardhat |
| `ETH_PRIVATE_KEY` | Hardhat default key is pre-filled in `.env.example` |

### 4. Compile & Deploy Smart Contract

```bash
# Compile (downloads solc 0.8.1 automatically)
python -m blockchain.compile_contract

# Start a local Hardhat node (in a separate terminal)
npx hardhat node

# Deploy contract
python -m blockchain.deploy_contract
```

The contract address is auto-saved to `.env`.

### 5. Run the Pipeline

```bash
python main.py --image path/to/face.jpg
```

**Options:**
```
--threshold 0.5    # Custom similarity threshold (default 0.4)
--no-blockchain    # Skip blockchain step (search-only test)
--no-search        # Skip web search (face + blockchain test)
```

## Example Output

```
==========================================================
  Face Identification & Blockchain Verification Pipeline
==========================================================

[1/4] 🔍 Encoding Face...
--------------------------------------------------
  ✓ Face detected — score 0.97, age 25, gender M
  ✓ Embedding: 512-dim vector (L2-normalised)
  ✓ Annotated image → output/face_detected.jpg
  ✓ ⏱  1.2s

[2/4] 🌐 Searching Web for Matches...
--------------------------------------------------
  ✓ Google Lens returned 8 visual match(es)
  ✓ Social-media matches: 2
  ✓   → Instagram: https://instagram.com/p/...
  ✓ ⏱  3.4s

[3/4] ✅ Verifying Face Match...
--------------------------------------------------
  ✓ MATCH — similarity 0.72 (threshold passed)
  ✓ Comparison image → output/comparison.jpg
  ✓ ⏱  2.1s

[4/4] ⛓️  Blockchain Upload + Verification
--------------------------------------------------
  ✓ Data hash : 0xa1b2c3...
  ✓ TX hash   : 0xdef789...
  ✓ Record ID : 41394
  ✓ On-chain re-verification: TRUE ✓
  ✓ ⏱  1.8s

==========================================================
  Pipeline complete — total time 8.5s
  Results saved → output/result.json
==========================================================
```

## Project Structure

```
face_id_blockchain/
├── face/
│   └── face_scan.py           # InsightFace wrapper
├── search/
│   ├── web_search.py          # SerpApi Google Lens search
│   └── verify_match.py        # Multi-candidate face verification
├── blockchain/
│   ├── contracts/
│   │   └── ProofOfExistence.sol
│   ├── contract_abi.json      # Compiled ABI (generated)
│   ├── compile_contract.py    # Solidity compiler
│   ├── deploy_contract.py     # Contract deployer
│   ├── blockchain_upload.py   # Hash upload
│   └── blockchain_verify.py   # Hash re-verification
├── utils/
│   ├── config.py              # Environment config loader
│   └── image_utils.py         # Image download/upload/compare
├── output/                    # Generated at runtime
├── main.py                    # Pipeline CLI entry point
├── requirements.txt
├── .env.example
└── .gitignore
```

## Blockchain Choice

**Local Hardhat** is the default for demonstrations:
- Instant transactions (no block confirmation wait)
- Free — no testnet ETH required
- Deterministic — same results every run

**Sepolia testnet** is supported by changing `ETH_RPC_URL` in `.env` to an Infura/Alchemy Sepolia endpoint. You'll need Sepolia ETH from a faucet.

The smart contract (`ProofOfExistence.sol`) is adapted from the [proof-of-existence](https://github.com/) Ethereum pattern. It stores SHA-256 hashes keyed by numeric ID, with owner-only write access and public verification.

## How Verification Works

1. Discovery data (URL + title + source + similarity + timestamp) is concatenated into a canonical string
2. SHA-256 hash is computed (32 bytes = Solidity `bytes32`)
3. Hash is stored on-chain via `notarizeHash(id, hash)`
4. Re-verification recomputes the hash from the same data and calls `doesProofExist(id, hash)`
5. If anyone tampers with the data, the recomputed hash won't match → `FALSE`

## Known Limitations

- **Face search accuracy** depends heavily on image quality, lighting, and angle. Low-resolution or occluded faces may not match.
- **SerpApi rate limits** — free tier allows 100 searches/month. Each pipeline run uses 1 search.
- **Social-media coverage** — Google Lens may not find matches for private profiles or uncommon faces. The pipeline falls back to any visual match or self-hash mode.
- **Testnet-only** — this is a demonstration. Mainnet deployment would require real ETH and security audits.
- **Consent required** — any real-world use of face identification technology requires explicit consent from the person whose face is scanned. This project is for educational/hackathon purposes only.
- **Thumbnail quality** — candidate verification depends on the quality of thumbnails returned by Google Lens. Small or cropped thumbnails may fail face detection.

## License

MIT
