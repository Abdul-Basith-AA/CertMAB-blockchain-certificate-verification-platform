import os

# web3_utils.py
with open('web3_utils.py', 'r', encoding='utf-8') as f:
    w3_code = f.read()
w3_code = w3_code.replace("'https://eth-sepolia.g.alchemy.com/v2/alch_V8PE21KInArfXDrG-Sg6A'", "''")
w3_code = w3_code.replace("'e7aacb1a0c49fe81965280d307143a1c6724b591ed7e7a97950fcf3f0432ea83'", "''")
w3_code = "from dotenv import load_dotenv\nload_dotenv()\n" + w3_code
with open('web3_utils.py', 'w', encoding='utf-8') as f:
    f.write(w3_code)

# pinata_utils.py
with open('pinata_utils.py', 'r', encoding='utf-8') as f:
    pinata_code = f.read()
pinata_code = pinata_code.replace("'ced76d645159a8e7d604'", "os.getenv('PINATA_API_KEY', '')")
pinata_code = pinata_code.replace("'7b0be9f21cbdc5faf526d16429cba47b0e68ea5dd52406eb330996726321120a'", "os.getenv('PINATA_SECRET_API_KEY', '')")
pinata_code = "import os\nfrom dotenv import load_dotenv\nload_dotenv()\n" + pinata_code
with open('pinata_utils.py', 'w', encoding='utf-8') as f:
    f.write(pinata_code)

# email_utils.py
with open('email_utils.py', 'r', encoding='utf-8') as f:
    email_code = f.read()
email_code = email_code.replace('"ootv nqeu bdxv ftmk"', "os.getenv('SENDER_PASSWORD', '')")
email_code = "import os\nfrom dotenv import load_dotenv\nload_dotenv()\n" + email_code
with open('email_utils.py', 'w', encoding='utf-8') as f:
    f.write(email_code)

