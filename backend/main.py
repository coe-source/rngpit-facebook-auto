import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from core.database import engine, Base
from core import models  # Import models so they are registered with Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    ADVANCED LEVEL: Lifespan hook ensures database schemas and dynamic folders
    are created strictly AFTER FastAPI starts and BEFORE requests are accepted.
    This resolves the missing table issues on serverless / Railway deployments.
    """
    print("🚀 [Lifespan] Initializing System Resources...")
    
    # 1. Ensure DB schemas exist reliably
    Base.metadata.create_all(bind=engine)
    print("✅ [Lifespan] Database schema synchronized.")
    
    # 2. Ensure persistence folders exist natively
    os.makedirs("uploads/flyers", exist_ok=True)
    print("✅ [Lifespan] File directories verified.")
    
    yield  # Hand over control to FastAPI to start accepting requests
    
    print("🛑 [Lifespan] Shutting down application gracefully...")

app = FastAPI(title="RNGPIT Facebook Setup API - Advanced Level", lifespan=lifespan)

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
