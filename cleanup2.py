import os
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'all_discrepancies=all_discrepancies' in line:
        line = line.replace(',all_discrepancies=all_discrepancies', '')
    new_lines.append(line)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
