"""Re-verify a discovery proof against the on-chain record.

Re-hashes the same payload and calls ``doesProofExist`` — a pure
``view`` function that costs zero gas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from web3 import Web3

from blockchain.blockchain_upload import compute_proof_hash, _record_id_from_hash
from utils.config import get_config

_HERE = Path(__file__).resolve().parent
_ABI_PATH = _HERE / "contract_abi.json"


def verify_proof(
    discovery_data: Dict[str, Any],
    record_id: int | None = None,
) -> Dict[str, Any]:
    """Re-hash *discovery_data* and check the on-chain record.

    Parameters
    ----------
    discovery_data:
        Same dict that was passed to ``upload_proof``.
    record_id:
        Must match the id used during upload; auto-derived if *None*.

    Returns
    -------
    dict with ``verified`` (bool), ``data_hash``, ``record_id``,
    ``contract_address``.
    """
    doc_hash = compute_proof_hash(discovery_data)
    rid = record_id if record_id is not None else _record_id_from_hash(doc_hash)

    cfg = get_config()
    w3 = Web3(Web3.HTTPProvider(cfg["ETH_RPC_URL"]))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot reach RPC: {cfg['ETH_RPC_URL']}")

    abi = json.loads(_ABI_PATH.read_text(encoding="utf-8"))["abi"]
    contract_addr = Web3.to_checksum_address(cfg["CONTRACT_ADDRESS"])
    contract = w3.eth.contract(address=contract_addr, abi=abi)

    verified: bool = contract.functions.doesProofExist(rid, doc_hash).call()

    return {
        "verified": verified,
        "data_hash": "0x" + doc_hash.hex(),
        "record_id": rid,
        "contract_address": contract_addr,
    }
