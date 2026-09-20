import os
import re

svg_core = '''<svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2l8 4.5v9L12 20l-8-4.5v-9L12 2z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4"></path>
                        <circle cx="12" cy="2" r="1.5" fill="currentColor" stroke="none"></circle>
                        <circle cx="20" cy="6.5" r="1.5" fill="currentColor" stroke="none"></circle>
                        <circle cx="20" cy="15.5" r="1.5" fill="currentColor" stroke="none"></circle>
                        <circle cx="12" cy="20" r="1.5" fill="currentColor" stroke="none"></circle>
                        <circle cx="4" cy="15.5" r="1.5" fill="currentColor" stroke="none"></circle>
                        <circle cx="4" cy="6.5" r="1.5" fill="currentColor" stroke="none"></circle>
                    </svg>'''

directory = r'templates'
for filename in os.listdir(directory):
    if filename.endswith('.html') and filename != 'home_page.html':
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the logo div in login/signup pages
        # Usually it's <div class="w-16 h-16 ..."><svg ...>...</svg></div>
        pattern = r'(<div class="[^"]*w-16 h-16[^"]*flex items-center justify-center[^"]*">)\s*<svg[^>]*>.*?</svg>\s*(</div>)'
        if re.search(pattern, content, flags=re.DOTALL):
            new_content = re.sub(pattern, r'\1\n                    ' + svg_core.replace('\\n', '\\n                    ') + r'\n                \2', content, flags=re.DOTALL)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filename}')

