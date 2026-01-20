from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import papers
import os
from dotenv import load_dotenv
import phoenix as px
from phoenix.otel import register
from openinference.instrumentation.openai import OpenAIInstrumentor

# Load environment variables
load_dotenv()

# Launch Phoenix for LLM observability
phoenix_session = px.launch_app()
print(f"\n🔭 Phoenix is running at: {phoenix_session.url}")
print("   View your LLM traces and evaluations in the Phoenix UI\n")

# Register Phoenix as the OTLP endpoint (Phoenix auto-detects the endpoint)
tracer_provider = register(
    project_name="research-agent"
)
print(f"📡 OpenTelemetry traces will be sent to Phoenix")
print(f"   Default endpoint: http://127.0.0.1:6006/v1/traces\n")

# Instrument OpenAI to capture traces
OpenAIInstrumentor().instrument(tracer_provider=tracer_provider)
print("✅ OpenAI instrumented for tracing\n")

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
    return {
        "message": "Research Paper Analyzer API", 
        "status": "running",
        "phoenix_url": phoenix_session.url,
        "tracing_enabled": True
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "phoenix_status": "running",
        "phoenix_url": phoenix_session.url
    }
