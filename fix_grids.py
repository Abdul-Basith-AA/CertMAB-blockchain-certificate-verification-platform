import os
import re

directory = r'templates'
for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # We need to replace class="grid grid-cols-3 gap-x" or similar.
        # But we only want to replace grid-cols-3 if it's NOT prefixed.
        # It's safer to just replace 'grid-cols-3' with 'grid-cols-1 md:grid-cols-3'
        # Let's ensure we don't duplicate md:grid-cols-1 md:grid-cols-3
        
        if 'grid-cols-3' in content and 'md:grid-cols-3' not in content and 'lg:grid-cols-3' not in content:
            new_content = content.replace('grid-cols-3', 'grid-cols-1 md:grid-cols-3')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Fixed grid in {filename}')
