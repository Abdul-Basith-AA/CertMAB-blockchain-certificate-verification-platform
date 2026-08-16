```
# CertChain - Blockchain-Based Certificate Verification Platform

A decentralized credential verification platform built on Ethereum Sepolia and Python Flask. It secures academic records using Solidity smart contracts, IPFS file storage, SHA-256 cryptographic hashing, and Firebase.

---

## 🌐 Live Links

- **Live Application:** [https://certificate-verification-blockchain.onrender.com](https://certificate-verification-blockchain.onrender.com)
- **Sepolia Smart Contract:** [0x0Bb5DB41ff71D4F931f9702b9972572dF796C256](https://sepolia.etherscan.io/address/0x0Bb5DB41ff71D4F931f9702b9972572dF796C256)

---

## 🚀 Key Features

- **Multi-Role Portals:** Dedicated dashboards for Institution, Student, Verifier/Company, and Admin.
- **Tamper-Proof Verification:** Cryptographic hash generation stored immutably on Ethereum Sepolia.
- **Decentralized Storage:** Certificate image storage powered by IPFS/Pinata.
- **Automated Integrity Engine:** Daily cross-verification system comparing database states against on-chain records.
- **Instant Validation:** Verification via unique certificate IDs and dynamic QR codes.

---

## 🛠️ Tech Stack

- **Blockchain:** Solidity, Ethereum Sepolia Testnet, Alchemy RPC, Web3.py
- **Backend:** Python (Flask), Pyrebase4, APScheduler
- **Database & Cloud:** Firebase Firestore & Authentication, Pinata (IPFS)
- **Frontend:** HTML5, CSS3, JavaScript, Bootstrap
- **Hosting:** Render Cloud Services

This project demonstrates a basic Hardhat use case. It comes with a sample contract, a test for that contract, and a Hardhat Ignition module that deploys that contract.

Try running some of the following tasks:

```shell
npx hardhat help
npx hardhat test
REPORT_GAS=true npx hardhat test
npx hardhat node
npx hardhat ignition deploy ./ignition/modules/Lock.js