import os
import re

svg_logo_dashboard = '''<div class="flex items-center space-x-3 mb-10">
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
                <div><h2 class="text-xl font-bold text-slate-800 tracking-tight">CertMAB</h2><p class="text-xs text-slate-500">'''

dashboard_pattern = r'<div class="flex items-center space-x-3 mb-10">\s*<div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">\s*<svg[^>]*>.*?</svg>\s*</div>\s*<div><h2 class="text-xl font-bold text-slate-800">CertMAB</h2><p class="text-xs text-slate-500">'

directory = r'templates'
for filename in os.listdir(directory):
    if filename.endswith('.html') and filename != 'home_page.html':
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace dashboard patterns
        if re.search(dashboard_pattern, content, flags=re.DOTALL):
            new_content = re.sub(dashboard_pattern, svg_logo_dashboard, content, flags=re.DOTALL)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f'Updated {filename} (Dashboard style)')
