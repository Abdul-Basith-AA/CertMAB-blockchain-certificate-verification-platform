require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  // --- REPLACE YOUR EXISTING 'solidity' LINE WITH THIS OBJECT ---
  solidity: {
    // Note: Your contract uses version 0.8.18, so I've matched that here.
    version: "0.8.18", 
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      // This is the key setting that fixes the "Stack too deep" error
      viaIR: true, 
    },
  },
  
  // This section tells Hardhat how to connect to your Ganache instance
  networks: {
    ganache: {
      url: "http://127.0.0.1:8545", // Default Ganache RPC Server
      // ⬇️ ACTION: Paste one of your private keys from Ganache here
      accounts: ['0xd32fd4846c0ee47afb86aa3faafa89ce5e4c071d75ab5d767381beac14fb0130'] 
    }
  }
};