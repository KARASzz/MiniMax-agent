import re, os

with open('web_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Extract HTML
match = re.search(r'HTML = r\"\"\"(.*?)\"\"\"[\r\n]+', content, re.DOTALL)
if match:
    os.makedirs('templates', exist_ok=True)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(match.group(1))
    # Keep two newlines before the next definition
    content = content[:match.start()] + "\n\n" + content[match.end():]
else:
    print("Warning: HTML string not found!")

# 2. Add Jinja2 imports
content = content.replace(
    "from fastapi import FastAPI, File, HTTPException, UploadFile",
    "from fastapi import FastAPI, File, HTTPException, UploadFile, Request"
)
content = content.replace(
    "from fastapi.responses import FileResponse, HTMLResponse, JSONResponse",
    "from fastapi.responses import FileResponse, HTMLResponse, JSONResponse\nfrom fastapi.templating import Jinja2Templates"
)

# 3. Setup templates dir
setup_old = """VOICE_ID_FILE = PROJECT_DIR / "Voice ID.md"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="MiniMax Web Console")
MCP_PROCESS: asyncio.subprocess.Process | None = None"""

setup_new = """VOICE_ID_FILE = PROJECT_DIR / "Voice ID.md"
TEMPLATES_DIR = PROJECT_DIR / "templates"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

app = FastAPI(title="MiniMax Web Console")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
MCP_PROCESS: asyncio.subprocess.Process | None = None"""

content = content.replace(setup_old, setup_new)

# 4. Update index endpoint
index_old = """@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return HTML"""

index_new = """@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})"""

content = content.replace(index_old, index_new)

# 5. Set reload=True
content = content.replace("reload=False", "reload=True")

with open('web_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("web_app.py updated successfully.")
