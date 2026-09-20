import os
import re

svg_logo_html = '''<div class="flex items-center space-x-3">
                    <div class="flex items-center justify-center w-10 h-10 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl shadow-lg shadow-indigo-200 flex-shrink-0">
                        <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 2l8 4.5v9L12 20l-8-4.5v-9L12 2z"></path>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4"></path>
                            <circle cx="12" cy="2" r="1.5" fill="currentColor" stroke="none"></circle>
                            <circle cx="20" cy="6.5" r="1.5" fill="currentColor" stroke="none"></circle>
                            <circle cx="20" cy="15.5" r="1.5" fill="currentColor" stroke="none"></circle>
                            <circle cx="12" cy="20" r="1.5" fill="currentColor" stroke="none"></circle>
                            <circle cx="4" cy="15.5" r="1.5" fill="currentColor" stroke="none"></circle>
                            <circle cx="4" cy="6.5" r="1.5" fill="currentColor" stroke="none"></circle>
                        </svg>
                    </div>
                    <span class="text-2xl font-bold text-gray-900 tracking-tight">CertMAB</span>
                </div>'''

path = r'templates/home_page.html'
if os.path.exists(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # In home_page.html we replaced it with <img src="...logo.png...">
    pattern = r'<div class="flex items-center space-x-3">\s*<img src="{{ url_for\(\'static\', filename=\'logo\.png\'\) }}"[^>]*>\s*</div>'
    new_content = re.sub(pattern, svg_logo_html, content, flags=re.DOTALL)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Updated home_page.html')
