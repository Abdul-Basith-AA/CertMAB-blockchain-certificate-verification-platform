from dotenv import load_dotenv
load_dotenv()
import json
import os
from web3 import Web3

# -------------------------------------------------------------
# 1. LIVE SEPOLIA CONNECTION (Alchemy RPC)
# -------------------------------------------------------------
ALCHEMY_RPC_URL = os.getenv(
    'ALCHEMY_RPC_URL',
    ''
)
w3 = Web3(Web3.HTTPProvider(ALCHEMY_RPC_URL))

# -------------------------------------------------------------
# 2. DEPLOYED SEPOLIA CONTRACT & WALLET DETAILS
# -------------------------------------------------------------
CONTRACT_ADDRESS = '0x0Bb5DB41ff71D4F931f9702b9972572dF796C256'
ADMIN_ADDRESS = '0x0A2E3e774d593B17f30942CaBeb630e04048dF97'
ADMIN_PRIVATE_KEY = os.getenv('ADMIN_PRIVATE_KEY', '')

# Use absolute path based on this file's location to ensure it works on Render
_abi_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'contract_abi.json')
with open(_abi_path, 'r') as f:
    abi = json.load(f)

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)


def store_on_blockchain(hash_hex_string, cert_data):
    """
    Signs and broadcasts certificate data to the Sepolia testnet.
    """
    try:
        hash_in_bytes = bytes.fromhex(hash_hex_string)
        nonce = w3.eth.get_transaction_count(ADMIN_ADDRESS)

        # Build transaction calling your smart contract on Sepolia
        tx = contract.functions.storeCertificate(
            hash_in_bytes,
            cert_data.get('name', ''),
            cert_data.get('email', ''),
            cert_data.get('institution_name', ''),
            cert_data.get('course', ''),
            str(cert_data.get('cid', '')),
            cert_data.get('cert_type', ''),
            cert_data.get('student_id', ''),
            cert_data.get('stream', ''),
            cert_data.get('batch', ''),
            cert_data.get('department', ''),
            str(cert_data.get('cgpa', '')),
            str(cert_data.get('issue_date', '')),
            '',
            str(cert_data.get('start', '')),
            str(cert_data.get('end', ''))
        ).build_transaction({
            'chainId': 11155111,  # Sepolia Chain ID
            'gasPrice': w3.eth.gas_price,
            'from': ADMIN_ADDRESS,
            'nonce': nonce
        })

        # Cryptographically sign transaction with your admin private key
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=ADMIN_PRIVATE_KEY)

        # Broadcast raw transaction
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Success! Data stored on Sepolia blockchain. Tx: {receipt.transactionHash.hex()}")
        return receipt.transactionHash.hex()

    except Exception as e:
        print(f"ERROR: Failed to store data on blockchain for hash {hash_hex_string}.")
        print(f"DETAILS: {e}")
        raise e


def verify_on_blockchain(hash_hex_string):
    """
    Checks if a certificate hash exists on the Sepolia blockchain.
    Returns True if the hash is found on-chain, False otherwise.
    """
    try:
        hash_in_bytes = bytes.fromhex(hash_hex_string)
        # Call the read-only getter on the smart contract (no gas needed)
        result = contract.functions.getCertificateDetails(hash_in_bytes).call()
        # result is a tuple of all stored fields; if studentEmail (index 1) is non-empty, cert exists
        student_email_on_chain = result[1]
        if student_email_on_chain and student_email_on_chain.strip():
            print(f"✅ BLOCKCHAIN VERIFY: Hash {hash_hex_string[:16]}... found on Sepolia.")
            return True
        else:
            print(f"❌ BLOCKCHAIN VERIFY: Hash {hash_hex_string[:16]}... NOT found on Sepolia.")
            return False
    except Exception as e:
        print(f"ERROR: Blockchain verify failed for hash {hash_hex_string}. DETAILS: {e}")
        # Return False so verification fails safely if blockchain is unreachable
        return False