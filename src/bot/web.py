# Telegram Account Management Bot - Web Server
# Health check endpoint for Docker health checks

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time

app = FastAPI(
    title="Telegram Account Manager",
    description="Health check and metrics endpoint",
    version="1.0.0"
)

# Store startup time
startup_time = time.time()


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": time.time() - startup_time
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "timestamp": time.time()
    }


@app.get("/")
async def root():
    """Root endpoint with basic info"""
    return {
        "service": "Telegram Account Manager Bot",
        "status": "running",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
