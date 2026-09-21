import os

directory = r'templates'
missing = []
for filename in os.listdir(directory):
    if filename.endswith('.html'):
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'viewport' not in content:
            missing.append(filename)
print('Missing viewport tag:', missing)
