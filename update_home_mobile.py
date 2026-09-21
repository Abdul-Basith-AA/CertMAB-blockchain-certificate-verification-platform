import os
import re

filepath = r'templates/home_page.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Let's add a hamburger button to the navbar
# Find: <div class="flex items-center space-x-4">
# Replace with:
# <div class="hidden md:flex items-center space-x-4">...</div>
# <div class="md:hidden flex items-center"><button id="mobile-menu-btn">...</button></div>

# We will just replace the entire <nav>...</nav> with a fully responsive version.
# First, let's extract the exact current <nav> to replace it safely, or just use regex.

# We can replace the <body> tag to include a mobile menu script at the bottom.
script = '''
<script>
    function toggleMobileMenu() {
        const menu = document.getElementById('mobile-menu');
        menu.classList.toggle('hidden');
    }
</script>
</body>
'''
content = content.replace('</body>', script)

# Add the hamburger button in the navbar right after "Get Started" div
pattern_getstarted = r'(<div class="flex items-center space-x-4">\s*<a href="#access-points" class="btn-primary[^"]*">Get Started</a>\s*</div>)'
hamburger = r'''\1
                <div class="md:hidden flex items-center ml-4">
                    <button onclick="toggleMobileMenu()" class="text-gray-600 focus:outline-none">
                        <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
                    </button>
                </div>'''

content = re.sub(pattern_getstarted, hamburger, content)

# Now, add the actual mobile dropdown menu right after </nav>
mobile_menu = '''</nav>
    <!-- Mobile Navigation Menu -->
    <div id="mobile-menu" class="hidden md:hidden fixed top-[72px] left-0 w-full bg-white border-b border-gray-200 shadow-lg z-30">
        <div class="flex flex-col px-6 py-4 space-y-4">
            <a href="#home" class="text-gray-700 font-medium hover:text-indigo-600" onclick="toggleMobileMenu()">Home</a>
            <a href="#features" class="text-gray-700 font-medium hover:text-indigo-600" onclick="toggleMobileMenu()">Features</a>
            <a href="#security" class="text-gray-700 font-medium hover:text-indigo-600" onclick="toggleMobileMenu()">Security</a>
            <a href="#contact" class="text-gray-700 font-medium hover:text-indigo-600" onclick="toggleMobileMenu()">Contact</a>
            <a href="#access-points" class="text-indigo-600 font-bold" onclick="toggleMobileMenu()">Get Started</a>
        </div>
    </div>
'''
content = content.replace('</nav>', mobile_menu)

# Make "Get Started" wrapper hidden on mobile so it doesn't crowd the navbar
content = content.replace('<div class="flex items-center space-x-4">', '<div class="hidden md:flex items-center space-x-4">')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated home_page.html responsiveness')
