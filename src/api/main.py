import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import (
    companies,
    health,
    peers,
    portfolio,
    screener,
    sectors,
    valuation,
)

app = FastAPI(
    title="N100 Financial Intelligence API",
    description="REST API serving financial intelligence indicators and clustering labels for Nifty 100 companies.",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    print(
        f"Request: {request.method} {request.url.path} - Completed in {duration:.4f}s with status {response.status_code}"
    )
    return response


# Register routers with prefix /api/v1
app.include_router(health.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(screener.router, prefix="/api/v1")
app.include_router(sectors.router, prefix="/api/v1")
app.include_router(peers.router, prefix="/api/v1")
app.include_router(valuation.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {
        "message": "Welcome to N100 Financial Intelligence Platform API. Go to /docs for OpenAPI documentation."
    }
