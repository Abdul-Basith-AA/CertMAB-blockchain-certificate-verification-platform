import requests

PINATA_API_KEY = 'ced76d645159a8e7d604'
PINATA_SECRET_API_KEY = '7b0be9f21cbdc5faf526d16429cba47b0e68ea5dd52406eb330996726321120a'

def upload_to_pinata(image_file):
    url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_API_KEY
    }

    files = {
        'file': (image_file.filename, image_file.stream, image_file.content_type)
    }

    response = requests.post(url, files=files, headers=headers)

    if response.status_code == 200:
        ipfs_hash = response.json()['IpfsHash']
        return f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
    else:
        print("Failed to upload to Pinata:", response.text)
        return ""
