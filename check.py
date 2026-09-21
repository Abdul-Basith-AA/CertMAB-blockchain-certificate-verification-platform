with open('templates/student_dashboard.html', 'r', encoding='utf-8') as f:
    c = f.read()
if 'id="sidebar"' in c:
    print('Sidebar found in student dashboard')
