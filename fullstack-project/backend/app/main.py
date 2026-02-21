import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .routers.items import router as items_router
from .routers.user_router import router as user_router

app = FastAPI()

origins = [
    "http://localhost:8000",
    "http://localhost:5173",
    "localhost:8000",
    "localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount static files directory (CSS, JS, images, etc.)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
frontend_path = os.path.normpath(frontend_path)
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

app.include_router(items_router)
app.include_router(user_router)

@app.get("/", tags=["root"])
async def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "index.html")
    html_path = os.path.normpath(html_path)
    return FileResponse(html_path)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
