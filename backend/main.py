import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.database import engine, Base
import os

# Create DB tables
Base.metadata.create_all(bind=engine)

# Create folders for uploads if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/flyers", exist_ok=True)

app = FastAPI(title="RNGPIT Facebook Setup API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to RNGPIT Facebook Automator API"}

from api import faculty, posts

app.include_router(faculty.router, prefix="/api/faculty", tags=["Faculty"])
app.include_router(posts.router, prefix="/api/posts", tags=["Posts"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
