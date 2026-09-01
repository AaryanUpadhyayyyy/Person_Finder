"""Compile ProofOfExistence.sol and emit ABI + bytecode JSON.

Uses ``py_solc_x`` so the user does not need a system-wide solc install.
The compiler version (0.8.1) is pinned to match the contract pragma.
Run this file once:

    python -m blockchain.compile_contract
"""

from __future__ import annotations

import json
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SOL_PATH = _HERE / "contracts" / "ProofOfExistence.sol"
_OUT_PATH = _HERE / "contract_abi.json"
_SOLC_VERSION = "0.8.1"


def compile_contract() -> dict:
    """Compile the Solidity file and return ``{abi, bytecode}``."""
    from solcx import compile_source, install_solc

    install_solc(_SOLC_VERSION, show_progress=True)
    source = _SOL_PATH.read_text(encoding="utf-8")

    compiled = compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=_SOLC_VERSION,
    )

    # key looks like "<stdin>:ProofOfExistence"
    contract_key = next(
        k for k in compiled if k.endswith(":ProofOfExistence")
    )
    contract = compiled[contract_key]

    result = {
        "abi": contract["abi"],
        "bytecode": contract["bin"],
    }

    _OUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"OK: ABI + bytecode written to {_OUT_PATH}")
    return result


if __name__ == "__main__":
    compile_contract()
