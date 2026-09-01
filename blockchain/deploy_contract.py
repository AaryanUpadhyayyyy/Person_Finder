"""Deploy ProofOfExistence to a local or testnet chain.

Usage:
    python -m blockchain.deploy_contract

On success the contract address is printed and appended to ``.env``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from web3 import Web3

from utils.config import get_config

_HERE = Path(__file__).resolve().parent
_ABI_PATH = _HERE / "contract_abi.json"
_ENV_PATH = _HERE.parent / ".env"


def _load_abi() -> dict:
    """Load ABI + bytecode; compile first if the file is missing."""
    if not _ABI_PATH.is_file():
        from blockchain.compile_contract import compile_contract
        return compile_contract()
    return json.loads(_ABI_PATH.read_text(encoding="utf-8"))


def deploy(*, rpc_url: str | None = None, private_key: str | None = None) -> str:
    """Deploy the contract and return the on-chain address.

    Parameters
    ----------
    rpc_url / private_key:
        Override values; otherwise read from env.

    Returns
    -------
    str – deployed contract address (checksummed).
    """
    cfg = get_config()
    rpc = rpc_url or cfg["ETH_RPC_URL"]
    pk = private_key or cfg["ETH_PRIVATE_KEY"]

    w3 = Web3(Web3.HTTPProvider(rpc))
    if not w3.is_connected():
        raise ConnectionError(f"Cannot connect to RPC: {rpc}")

    acct = w3.eth.account.from_key(pk)
    data = _load_abi()

    Contract = w3.eth.contract(abi=data["abi"], bytecode=data["bytecode"])

    tx = Contract.constructor().build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 500_000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    addr: str = receipt["contractAddress"]
    print(f"✓ Contract deployed at {addr}")
    print(f"  TX hash : {tx_hash.hex()}")
    print(f"  Block   : {receipt['blockNumber']}")
    print(f"  Gas used: {receipt['gasUsed']}")

    _persist_address(addr)
    return addr


def _persist_address(addr: str) -> None:
    """Append CONTRACT_ADDRESS to .env so subsequent runs find it."""
    if _ENV_PATH.is_file():
        text = _ENV_PATH.read_text(encoding="utf-8")
        if "CONTRACT_ADDRESS=" in text:
            # replace existing (even if blank)
            lines = text.splitlines(keepends=True)
            with _ENV_PATH.open("w", encoding="utf-8") as f:
                for line in lines:
                    if line.strip().startswith("CONTRACT_ADDRESS"):
                        f.write(f"CONTRACT_ADDRESS={addr}\n")
                    else:
                        f.write(line)
            return
    # append
    with _ENV_PATH.open("a", encoding="utf-8") as f:
        f.write(f"\nCONTRACT_ADDRESS={addr}\n")


if __name__ == "__main__":
    deploy()
