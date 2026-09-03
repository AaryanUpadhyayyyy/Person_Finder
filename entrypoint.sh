#!/bin/bash
set -e

echo "[TALAASH] Starting Hardhat local blockchain node..."
npx hardhat node --hostname 0.0.0.0 &
HARDHAT_PID=$!

# Wait for Hardhat to be ready (polls localhost:8545)
echo "[TALAASH] Waiting for Hardhat RPC to be ready..."
for i in $(seq 1 30); do
  if curl -s -X POST -H "Content-Type: application/json" \
    --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
    http://127.0.0.1:8545 > /dev/null 2>&1; then
    echo "[TALAASH] Hardhat node is ready!"
    break
  fi
  sleep 1
done

# Override RPC and private key env vars to point to local Hardhat
export ETH_RPC_URL="http://127.0.0.1:8545"
export ETH_PRIVATE_KEY="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

# Compile and deploy the smart contract
echo "[TALAASH] Compiling ProofOfExistence contract..."
python -m blockchain.compile_contract || echo "[WARN] Compile failed, using existing ABI"

echo "[TALAASH] Deploying contract to local Hardhat chain..."
DEPLOY_OUTPUT=$(python -m blockchain.deploy_contract 2>&1) || echo "[WARN] Deploy failed"
echo "$DEPLOY_OUTPUT"

# Extract contract address from deploy output and export it
CONTRACT_ADDR=$(echo "$DEPLOY_OUTPUT" | grep -oP 'deployed at \K0x[a-fA-F0-9]+')
if [ -n "$CONTRACT_ADDR" ]; then
  export CONTRACT_ADDRESS="$CONTRACT_ADDR"
  echo "[TALAASH] Contract address exported: $CONTRACT_ADDRESS"
else
  echo "[WARN] Could not extract contract address from deploy output"
fi

# Start the FastAPI backend
echo "[TALAASH] Starting TALAASH API server..."
exec uvicorn api:app --host 0.0.0.0 --port 7860
