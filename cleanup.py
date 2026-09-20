import os

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.startswith('from apscheduler.schedulers.background import BackgroundScheduler'):
        continue
    if 'get_all_discrepancies' in line or 'update_discrepancy_status' in line:
        continue
    if 'send_discrepancy_alert_email' in line:
        continue
    if line.startswith('def run_verification_script()'):
        skip = True
    if skip and line.startswith('# --- Password Reset Routes ---'):
        skip = False
    
    if line.startswith('if __name__ == '):
        skip = True
        
    if not skip:
        new_lines.append(line)

# Add standard app.run back
new_lines.append("\nif __name__ == '__main__':\n")
new_lines.append("    app.run(debug=True, use_reloader=False)\n")

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
