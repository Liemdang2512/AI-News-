from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
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
                    'category': article.category
                }
        
        summary = await summarizer.summarize_articles(
            request.urls, 
            api_key=x_gemini_api_key,
            articles_metadata=articles_metadata
        )
        return SummarizeResponse(summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
