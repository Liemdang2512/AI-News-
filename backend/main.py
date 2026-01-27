from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.news import router as news_router
from config import settings

app = FastAPI(
    title="News Aggregator API",
    description="API for Vietnamese news aggregation and summarization",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Vercel deployment debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(news_router)


@app.get("/")
async def root():
    return {
        "message": "News Aggregator API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


def run():
    """
    Start the FastAPI backend using configuration from settings.

    This function is used both for local development and when the backend is
    started as a bundled binary for the desktop app.
    """
    import uvicorn

    uvicorn.run(
        app,
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
    )


if __name__ == "__main__":
    run()
