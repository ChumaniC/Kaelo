import threading
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

# Custom Project Packages
from backend.routers import farmer, vet, general, admin
from backend.database import engine
from backend.models import Base
from backend.ingestion import run_ingestion_loop

# Create tables
Base.metadata.create_all(bind=engine)

# Lifespan handler to start ingestion thread
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: spawn ingestion thread
    thread = threading.Thread(
        target=run_ingestion_loop,
        args=(30,),   # poll every 30s
        daemon=True
    )
    thread.start()
    yield
    # Shutdown logic (if any) goes here

# Instantiate FastAPI with lifespan
app = FastAPI(lifespan=lifespan)

# Determine project root (the parent of this file’s directory)
BASE_DIR = Path(__file__).resolve().parent.parent

#  Mount static files directory (adjusted path)
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

# Point Jinja2 at your templates folder
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Routers
app.include_router(farmer.router)
app.include_router(vet.router)
app.include_router(general.router)
app.include_router(admin.router)

# Homepage
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

@app.get("/lookup", response_class=HTMLResponse)
async def lookup_page(request: Request):
    return templates.TemplateResponse("lookup.html", {"request": request})

@app.get("/farmer", response_class=HTMLResponse)
async def farmer_page(request: Request):
    return templates.TemplateResponse("farmer.html", {"request": request})

@app.get("/vet", response_class=HTMLResponse)
async def vet_page(request: Request):
    return templates.TemplateResponse("vet.html", {"request": request})

@app.get("/lookup-chain", response_class=HTMLResponse)
async def lookup_chain_page(request: Request):
    return templates.TemplateResponse("lookup-chain.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

if __name__ == "__main__":
    import uvicorn, webbrowser
    # Start the server in a thread
    from threading import Timer
    Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

