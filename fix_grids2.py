import os
import re

directory = r'templates'
files = ['admin_dashboard.html', 'institution_dashboard.html', 'student_dashboard.html']
for filename in files:
    filepath = os.path.join(directory, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # regex replace grid-cols-3 that is not preceded by md: lg: xl: or sm:
    new_content = re.sub(r'(?<!md:)(?<!lg:)(?<!xl:)(?<!sm:)grid-cols-3', 'grid-cols-1 md:grid-cols-3', content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Fixed grids properly in {filename}')
