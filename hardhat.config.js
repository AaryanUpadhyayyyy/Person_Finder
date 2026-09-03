/**
 * Minimal Hardhat config for local dev chain.
 * The node is started inside Docker as a background process.
 */
module.exports = {
  solidity: "0.8.1",
  networks: {
    hardhat: {
      chainId: 31337,
    },
  },
};
