import os
import re

files_to_fix = ['company_forgot_password.html', 'result.html', 'verify.html']
directory = r'templates'
viewport_tag = '\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">'

for filename in files_to_fix:
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Inject after <head> or <title>
        if '<head>' in content:
            content = content.replace('<head>', '<head>' + viewport_tag)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed {filename}')
