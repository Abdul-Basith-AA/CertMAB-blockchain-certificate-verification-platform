import os
import re

directory = r'templates'
for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        matches = re.findall(r'w-\[[0-9]+px\]', content)
        if matches:
            print(f'{filename}: {matches}')
