import os
import re

directory = r'templates'
for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace <table ...> with <div class="overflow-x-auto"><table ...>
        # but only if it's not already wrapped.
        
        if '<table' in content:
            # We will use regex to wrap tables in a div with overflow-x-auto
            # Pattern matches <table> to </table>
            # Wait, easier to just find the container of the table. Usually it's in a white card.
            # Most tailwind users wrap tables in <div class="overflow-x-auto"> already. Let's check.
            if 'overflow-x-auto' not in content:
                content = content.replace('<table', '<div class="overflow-x-auto w-full"><table')
                content = content.replace('</table>', '</table></div>')
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f'Wrapped tables in {filename}')
