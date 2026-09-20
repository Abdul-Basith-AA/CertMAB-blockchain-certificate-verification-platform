import os
import re

svg_core = '''<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        
        # In dashboards, the logo container is a div containing an SVG, just before <h2>CertMAB</h2>
        # We will replace the <svg ...>...</svg> inside the logo container.
        # Find <div><h2 ...>CertMAB</h2>
        
        # Let's use a simpler approach. Search for <svg class="w-6 h-6 text-white" up to </svg>
        # but only if it's right before CertMAB.
        # Actually, let's just replace ALL instances of the generic checkmark/tick svg if it's the main logo.
        # Let's write a targeted regex for the logo block.
        
        # General pattern for the dashboard logo container:
        # <div class="w-12 h-12 bg-gradient-to-r from-red-600 to-red-800 ...">
        # <svg ...>...</svg>
        # </div>
        # <div><h2 ...>CertMAB</h2>
        
        pattern = r'(<div class="[^"]*w-1[02] h-1[02][^"]*rounded-xl[^"]*flex items-center justify-center[^"]*">)\s*<svg[^>]*>.*?</svg>\s*(</div>\s*<div>\s*<h[12][^>]*>CertMAB</h[12]>)'
        
        if re.search(pattern, content, flags=re.DOTALL):
            new_content = re.sub(pattern, r'\1\n                    ' + svg_core.replace('\\n', '\\n                    ') + r'\n                \2', content, flags=re.DOTALL)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filename}')
        
        # There are also Login pages and signup pages!
        login_pattern = r'(<div class="[^"]*w-16 h-16[^"]*rounded-2xl[^"]*flex items-center justify-center[^"]*">)\s*<svg[^>]*>.*?</svg>\s*(</div>\s*<h2[^>]*>)'
        if re.search(login_pattern, content, flags=re.DOTALL):
            new_content = re.sub(login_pattern, r'\1\n                    ' + svg_core.replace('w-6 h-6', 'w-8 h-8').replace('\\n', '\\n                    ') + r'\n                \2', content, flags=re.DOTALL)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filename} (Login/Signup style)')

