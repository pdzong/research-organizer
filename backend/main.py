from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import papers
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Research Paper Analyzer API",
    description="API for analyzing research papers from HuggingFace and ArXiv",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(papers.router, prefix="/api", tags=["papers"])

@app.get("/")
async def root():
    return {"message": "Research Paper Analyzer API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
