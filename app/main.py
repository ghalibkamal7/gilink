import os
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from .downloader import get_media_info, download_media

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="OmniDrop Media Downloader", version="1.0.0")

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

class InfoRequest(BaseModel):
    url: str

def remove_temp_file(path: str):
    """Deletes temporary file after download completes."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as e:
        print(f"Error removing temp file {path}: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/info")
async def fetch_info(req: InfoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    try:
        data = get_media_info(url)
        return JSONResponse(content={"success": True, "data": data})
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

# Support GET for backward compatibility
@app.get("/api/info")
async def fetch_info_get(url: str = Query(...)):
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url
    try:
        data = get_media_info(url)
        return JSONResponse(content={"success": True, "data": data})
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        data = get_media_info(url)
        return JSONResponse(content={"success": True, "data": data})
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.get("/api/download")
async def trigger_download(
    background_tasks: BackgroundTasks,
    url: str = Query(...),
    format_spec: str = Query("bestvideo+bestaudio/best"),
    is_audio: bool = Query(False)
):
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Invalid URL")

    try:
        result = download_media(url, format_spec, is_audio)
        filepath = result["filepath"]
        filename = result["filename"]

        # Schedule automatic cleanup of downloaded media after sending
        background_tasks.add_task(remove_temp_file, filepath)

        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "OmniDrop Media Downloader"}
