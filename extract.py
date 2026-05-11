import os, re
content = open('web_app.py', 'r', encoding='utf-8').read()
match = re.search(r'HTML = r\"\"\"(.*?)\"\"\"', content, re.DOTALL)
if match:
    os.makedirs('templates', exist_ok=True)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(match.group(1))
    print('HTML extracted successfully.')
else:
    print('Could not find HTML.')