import os, re

content = open('web_app.py', 'r', encoding='utf-8').read()

# Remove HTML variable
content = re.sub(r'HTML = r\"\"\"(.*?)\"\"\"', '', content, flags=re.DOTALL)

# Add imports
content = content.replace(
    'from fastapi import FastAPI, File, HTTPException, UploadFile',
    'from fastapi import FastAPI, File, HTTPException, UploadFile, Request'
)
content = content.replace(
    'from fastapi.responses import FileResponse, HTMLResponse, JSONResponse\nfrom pydantic import BaseModel',
    'from fastapi.responses import FileResponse, HTMLResponse, JSONResponse\nfrom fastapi.templating import Jinja2Templates\nfrom pydantic import BaseModel'
)

# Add templates instance
content = content.replace(
    'app = FastAPI(title="MiniMax Web Console")',
    'app = FastAPI(title="MiniMax Web Console")\ntemplates = Jinja2Templates(directory="templates")'
)

# Update index function
old_index = '''@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return HTML'''

new_index = '''@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})'''

content = content.replace(old_index, new_index)

with open('web_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('web_app.py updated successfully.')
