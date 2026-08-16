import json
import os
from solcx import compile_standard, install_solc
from web3 import Web3

# -------------------------------------------------------------
# 1. SETUP PROVIDER & ACCOUNT
# -------------------------------------------------------------
# Replace with your Sepolia Alchemy/Infura RPC URL
ALCHEMY_RPC_URL = (
    'https://eth-sepolia.g.alchemy.com/v2/alch_V8PE21KInArfXDrG-Sg6A'
)
web3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))

# Replace with your MetaMask Account Address & Private Key
MY_ADDRESS = '0x0A2E3e774d593B17f30942CaBeb630e04048dF97'
# Get Private Key from MetaMask -> Account Details -> Show Private Key
PRIVATE_KEY = 'e7aacb1a0c49fe81965280d307143a1c6724b591ed7e7a97950fcf3f0432ea83'

print(f'Connected to Sepolia: {web3.is_connected()}')

# -------------------------------------------------------------
# 2. COMPILE SOLIDITY CONTRACT
# -------------------------------------------------------------
print('Installing Solidity Compiler v0.8.18...')
install_solc('0.8.18')

with open('contracts/CertificateStore.sol', 'r') as file:
  contract_file = file.read()

print('Compiling CertificateStore.sol with viaIR enabled...')
compiled_sol = compile_standard(
    {
        'language': 'Solidity',
        'sources': {'CertificateStore.sol': {'content': contract_file}},
        'settings': {
            'optimizer': {'enabled': True, 'runs': 200},
            'viaIR': True,  # Fixes the "Stack Too Deep" error!
            'outputSelection': {
                '*': {'*': ['abi', 'metadata', 'evm.bytecode', 'evm.sourceMap']}
            },
        },
    },
    solc_version='0.8.18',
)

# Extract Bytecode and ABI
bytecode = compiled_sol['contracts']['CertificateStore.sol'][
    'CertificateStore'
]['evm']['bytecode']['object']
abi = json.loads(
    compiled_sol['contracts']['CertificateStore.sol']['CertificateStore'][
        'metadata'
    ]
)['output']['abi']

# Save ABI to a file for Flask to use
with open('contract_abi.json', 'w') as f:
  json.dump(abi, f, indent=4)

# -------------------------------------------------------------
# 3. DEPLOY CONTRACT TO SEPOLIA
# -------------------------------------------------------------
print('Deploying contract to Sepolia...')
CertificateStore = web3.eth.contract(abi=abi, bytecode=bytecode)

# Get current transaction count (nonce)
nonce = web3.eth.get_transaction_count(MY_ADDRESS)

# Build deployment transaction
transaction = CertificateStore.constructor().build_transaction({
    'chainId': 11155111,  # Sepolia Chain ID
    'gasPrice': web3.eth.gas_price,
    'from': MY_ADDRESS,
    'nonce': nonce,
})

# Sign transaction using Private Key
signed_txn = web3.eth.account.sign_transaction(
    transaction, private_key=PRIVATE_KEY
)

# Send raw transaction to Sepolia blockchain
tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
print(f'Transaction sent! Hash: {tx_hash.hex()}')
print('Waiting for block confirmation...')

# Wait for transaction receipt
tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

print('\n' + '=' * 50)
print(f'SUCCESS! Contract Deployed At Address:')
print(f'{tx_receipt.contractAddress}')
print('=' * 50 + '\n')