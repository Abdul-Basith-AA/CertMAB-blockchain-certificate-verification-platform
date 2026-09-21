import os
import re

directory = r'templates'
for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for grid-cols-2, 3, 4 without responsive prefix
        matches = re.findall(r'(?<!md:)(?<!lg:)(?<!xl:)(?<!sm:)grid-cols-[2-9]', content)
        if matches:
            print(f'{filename} has hardcoded grids: {set(matches)}')
