const hre = require("hardhat");

async function main() {
  const CertificateStore = await hre.ethers.getContractFactory("CertificateStore");
  const contract = await CertificateStore.deploy();
  await contract.waitForDeployment();

  console.log("Contract deployed to:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});