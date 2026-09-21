import os
import re

dashboards = ['admin_dashboard.html', 'company_dashboard.html', 'institution_dashboard.html', 'student_dashboard.html']
directory = r'templates'

mobile_header = '''<!-- Mobile Header -->
<div class="lg:hidden fixed top-0 left-0 w-full h-16 bg-white border-b border-gray-200 z-40 flex items-center justify-between px-4">
    <div class="flex items-center">
        <button onclick="document.getElementById('sidebar').classList.toggle('-translate-x-full'); document.getElementById('mobile-overlay').classList.toggle('hidden');" class="text-gray-600 focus:outline-none">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
        </button>
        <span class="ml-4 font-bold text-lg text-gray-800">CertMAB</span>
    </div>
</div>
<!-- Mobile Overlay -->
<div id="mobile-overlay" class="lg:hidden fixed inset-0 bg-gray-900 bg-opacity-50 z-40 hidden" onclick="document.getElementById('sidebar').classList.add('-translate-x-full'); this.classList.add('hidden');"></div>
'''

for d in dashboards:
    filepath = os.path.join(directory, d)
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Update aside classes
        # Look for <aside class="... w-64 h-full ...">
        pattern_aside = r'<aside class="([^"]*)sidebar([^"]*)">'
        def replace_aside(m):
            cls = m.group(1) + 'sidebar' + m.group(2)
            # Add translation classes and an ID
            cls = cls.replace('fixed', 'fixed').replace('w-64', 'w-64')
            return f'<aside id="sidebar" class="{cls} transform -translate-x-full lg:translate-x-0 transition-transform duration-300 ease-in-out bg-white border-r border-slate-200 shadow-xl lg:shadow-none">'
        
        content = re.sub(pattern_aside, replace_aside, content, count=1)
        
        # 2. Inject mobile header right after <body>
        pattern_body = r'(<body[^>]*>)'
        content = re.sub(pattern_body, r'\1\n' + mobile_header, content, count=1)
        
        # 3. Update main padding
        pattern_main = r'<main class="([^"]*)">'
        def replace_main(m):
            cls = m.group(1)
            if 'pt-16' not in cls:
                cls += ' pt-16 lg:pt-0'
            return f'<main class="{cls}">'
        content = re.sub(pattern_main, replace_main, content, count=1)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Updated {d}')

