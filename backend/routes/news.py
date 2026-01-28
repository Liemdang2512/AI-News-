from fastapi import APIRouter, HTTPException, Header, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
from services.rss_matcher import rss_matcher
from services.rss_fetcher import rss_fetcher
from services.categorizer import categorizer
from services.summarizer import summarizer
from services.article_categorizer import article_categorizer

router = APIRouter(prefix="/api", tags=["news"])

# Request/Response Models
class MatchRSSRequest(BaseModel):
    newspapers: str  # Comma-separated newspaper names

class MatchRSSResponse(BaseModel):
    rss_feeds: List[str]

class FetchArticlesRequest(BaseModel):
    rss_urls: List[str]
    date: str  # DD/MM/YYYY
    time_range: str  # e.g., "6h00 đến 8h00"

class Article(BaseModel):
    url: str
    title: str
    category: str
    published_at: str
    description: str
    source: str  # Newspaper name (e.g., "LÃO ĐỘNG", "VTV NEWS")
    thumbnail: str = ""  # Article thumbnail/image URL

class FetchArticlesResponse(BaseModel):
    articles: List[Article]

class CategorizeRequest(BaseModel):
    articles_text: str

class CategorizeResponse(BaseModel):
    categorized_text: str

class SummarizeRequest(BaseModel):
    urls: List[str]
    articles: List[Article] = []  # Optional: full article objects with source and category

class SummarizeResponse(BaseModel):
    summary: str


@router.post("/rss/match", response_model=MatchRSSResponse)
async def match_rss_feeds(request: MatchRSSRequest):
    """
    Match newspaper names to RSS feed URLs
    Replaces first ai_llm node in JSON workflow
    """
    try:
        matched_feeds = rss_matcher.match_feeds(request.newspapers)
        return MatchRSSResponse(rss_feeds=matched_feeds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/fetch", response_model=FetchArticlesResponse)
async def fetch_articles(request: FetchArticlesRequest):
    """
    Fetch RSS feeds and filter articles by date/time
    Category is automatically extracted from RSS URL path
    """
    try:
        # Fetch and filter articles (category extracted from RSS URL)
        articles = await rss_fetcher.fetch_and_filter(
            rss_urls=request.rss_urls,
            target_date=request.date,
            time_range=request.time_range
        )
        
        return FetchArticlesResponse(articles=articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/articles/categorize", response_model=CategorizeResponse)
async def categorize_articles(request: CategorizeRequest):
    """
    Categorize articles into 4 main categories using Gemini AI
    Replaces third ai_llm node in JSON workflow
    """
    try:
        categorized = await categorizer.categorize_articles(request.articles_text)
        return CategorizeResponse(categorized_text=categorized)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/articles/summarize", response_model=SummarizeResponse)
async def summarize_articles(
    request: SummarizeRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Fetch article content and generate AI summaries
    Replaces ai_multimodal node in JSON workflow
    """
    try:
        # Pass article metadata if available
        articles_metadata = {}
        if request.articles:
            for article in request.articles:
                articles_metadata[article.url] = {
                    'source': article.source,
                    'category': article.category,
                    'title': article.title
                }
        
        summary = await summarizer.summarize_articles(
            request.urls, 
            api_key=x_gemini_api_key,
            articles_metadata=articles_metadata
        )
        return SummarizeResponse(summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/summarize")
async def websocket_summarize(websocket: WebSocket):
    await websocket.accept()
    try:
        # Receive input data
        data = await websocket.receive_json()
        urls = data.get("urls", [])
        api_key = data.get("api_key")
        articles_data = data.get("articles", [])
        
        # Convert articles_data to dict for easier lookup
        articles_metadata = {}
        for article in articles_data:
            clean_url = article['url'].strip().rstrip('/')
            articles_metadata[clean_url] = {
                'source': article.get('source'),
                'category': article.get('category'),
                'title': article.get('title')
            }
            
        async def progress_callback(completed: int, total: int, url: str, status: str):
            await websocket.send_json({
                "type": "progress",
                "completed": completed,
                "total": total,
                "current_article": url,
                "status": status
            })

        # Keep-alive task to prevent connection timeout during heavy processing
        async def keep_alive():
            while True:
                await asyncio.sleep(5)
                try:
                    await websocket.send_json({"type": "ping"})
                except:
                    break
        
        keep_alive_task = asyncio.create_task(keep_alive())
            
        try:
            summary = await summarizer.summarize_articles(
                urls, 
                api_key=api_key, 
                articles_metadata=articles_metadata,
                progress_callback=progress_callback
            )
        finally:
            keep_alive_task.cancel()
        
        await websocket.send_json({
            "type": "complete",
            "summary": summary
        })
        
        await websocket.close()
            
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close()
        except:
            pass
