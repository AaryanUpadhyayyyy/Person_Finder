"""Upload a discovery-proof hash to the ProofOfExistence contract.

Hashing strategy mirrors the test pattern in proof-of-existence-master:
    SHA-256 of a deterministic string  →  bytes32
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from web3 import Web3

from utils.config import get_config

_HERE = Path(__file__).resolve().parent
_ABI_PATH = _HERE / "contract_abi.json"


# ── hashing ────────────────────────────────────────────────────────────

def compute_proof_hash(discovery_data: Dict[str, Any]) -> bytes:
    """Compute a SHA-256 digest of the discovery payload.

    The canonical string is built as:
        ``link | title | source | similarity | timestamp``

    Returns 32-byte ``bytes`` suitable for Solidity ``bytes32``.
    """
    canonical = "|".join([
        str(discovery_data.get("link", "")),
        str(discovery_data.get("title", "")),
        str(discovery_data.get("source", "")),
        str(discovery_data.get("similarity", "")),
        str(discovery_data.get("timestamp", "")),
    ])
    return hashlib.sha256(canonical.encode("utf-8")).digest()      # 32 bytes


def _record_id_from_hash(h: bytes) -> int:
    """Derive a deterministic uint256 record-ID from the first 8 hex chars."""
    return int(h[:4].hex(), 16)                                    # 0 – 65 535


# ── upload ─────────────────────────────────────────────────────────────

def upload_proof(
    discovery_data: Dict[str, Any],
    record_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Hash *discovery_data* and call ``notarizeHash`` on-chain.

    Parameters
    ----------
    discovery_data:
        Must contain at least ``link``, ``title``, ``source``.
        ``similarity`` and ``timestamp`` are added automatically if missing.
    record_id:
        Explicit uint256 id; if *None*, one is derived from the hash.

    Returns
    -------
    dict with ``tx_hash``, ``block_number``, ``record_id``,
    ``data_hash``, ``gas_used``.
    """
    # ensure timestamp exists
    discovery_data.setdefault("timestamp", int(time.time()))

    doc_hash = compute_proof_hash(discovery_data)
    rid = record_id if record_id is not None else _record_id_from_hash(doc_hash)

    cfg = get_config()
    w3 = Web3(Web3.HTTPProvider(cfg["ETH_RPC_URL"]))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot reach RPC: {cfg['ETH_RPC_URL']}")

    acct = w3.eth.account.from_key(cfg["ETH_PRIVATE_KEY"])
    abi = json.loads(_ABI_PATH.read_text(encoding="utf-8"))["abi"]
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(cfg["CONTRACT_ADDRESS"]),
        abi=abi,
    )

    tx = contract.functions.notarizeHash(rid, doc_hash).build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 100_000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    return {
        "tx_hash": tx_hash.hex(),
        "block_number": receipt["blockNumber"],
        "record_id": rid,
        "data_hash": "0x" + doc_hash.hex(),
        "gas_used": receipt["gasUsed"],
    }
