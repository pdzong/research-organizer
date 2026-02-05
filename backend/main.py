from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import papers
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pathlib import Path

# Load environment variables
load_dotenv()

# Global variables for Phoenix
phoenix_session = None
tracer_provider = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events for Phoenix"""
    global phoenix_session, tracer_provider
    
    # Startup: Initialize Phoenix with persistent database
    try:
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.openai import OpenAIInstrumentor
        
        # Use persistent database in project directory instead of temp
        phoenix_db_dir = Path(__file__).parent / "data" / "phoenix"
        phoenix_db_dir.mkdir(parents=True, exist_ok=True)
        
        # Launch Phoenix with persistent storage
        phoenix_session = px.launch_app(
            host="127.0.0.1",
            port=6006,
            # Use working_dir to ensure consistent database location
        )
        print(f"\n🔭 Phoenix is running at: {phoenix_session.url}")
        print("   View your LLM traces and evaluations in the Phoenix UI\n")

        # Register Phoenix as the OTLP endpoint
        tracer_provider = register(
            project_name="research-agent"
        )
        print(f"📡 OpenTelemetry traces will be sent to Phoenix")
        print(f"   Default endpoint: http://127.0.0.1:6006/v1/traces\n")

        # Instrument OpenAI to capture traces
        OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
        print("✅ OpenAI instrumented for tracing\n")
    except Exception as e:
        print(f"⚠️  Phoenix initialization failed: {e}")
        print("   Continuing without observability...\n")
    
    yield  # Application runs here
    
    # Shutdown: Clean up Phoenix (optional, commented out to avoid Windows issues)
    # if phoenix_session:
    #     try:
    #         phoenix_session.close()
    #     except:
    #         pass

app = FastAPI(
    title="Research Paper Analyzer API",
    description="API for analyzing research papers from HuggingFace and ArXiv",
    version="1.0.0",
    lifespan=lifespan
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
    return {
        "message": "Research Paper Analyzer API", 
        "status": "running",
        "phoenix_url": phoenix_session.url if phoenix_session else None,
        "tracing_enabled": phoenix_session is not None
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "phoenix_status": "running" if phoenix_session else "disabled",
        "phoenix_url": phoenix_session.url if phoenix_session else None
    }
