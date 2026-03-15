import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from .routers.user_router import router as user_router
from .routers.restaurant_router import router as restaurant_router
from .routers.cart_router import router as cart_router
from .routers.websocket_router import router as websocket_router
from .routers.order_router import router as order_router

description = """
*Why bother cooking your own meals...*

Just a few clicks and food from your favourite restaurant will be at your doorstep!
"""

app = FastAPI(
    title = "Food Delivery App",
    description = description,
    summary = "Food delivery with exceptional service!"
)

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

# Include routers
app.include_router(user_router)
app.include_router(restaurant_router)
app.include_router(cart_router)
app.include_router(websocket_router)
app.include_router(order_router)

@app.get("/", tags=["root"])
async def read_root():
    html_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "index.html")
    html_path = os.path.normpath(html_path)
    return FileResponse(html_path)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
