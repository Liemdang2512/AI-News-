from fastapi import APIRouter, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import json
import asyncio
from services.rss_matcher import rss_matcher
from services.rss_fetcher import rss_fetcher
from services.categorizer import categorizer
from services.summarizer import summarizer
from services.article_categorizer import article_categorizer
from services.dedup_service import dedup_service
from services.nhandan_fetcher import nhandan_fetcher

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
    # Phase 2: Duplicate Detection fields
    group_id: str = ""  # ID nhóm bài viết trùng lặp
    is_master: bool = True  # Bài chính trong nhóm
    duplicate_count: int = 0  # Số bài trùng lặp
    event_summary: str = ""  # Tóm tắt sự kiện (từ AI)
    # Phase 2: Official Source Verification
    official_source_link: Optional[str] = None  # Link Báo Nhân Dân nếu có

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
async def fetch_articles(
    request: FetchArticlesRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Fetch RSS feeds and filter articles by date/time
    Category is automatically extracted from RSS URL path
    Phase 2: Apply duplicate detection and Nhan Dan verification
    """
    try:
        # Fetch and filter articles (category extracted from RSS URL)
        articles = await rss_fetcher.fetch_and_filter(
            rss_urls=request.rss_urls,
            target_date=request.date,
            time_range=request.time_range
        )
        
        # Phase 2: Semantic duplicate detection (RE-ENABLED with advanced prompt)
        if len(articles) > 1:
            articles = await dedup_service.cluster_articles_semantically(
                articles, 
                api_key=x_gemini_api_key
            )
        
        # Phase 2: Check Nhan Dan official coverage (ENABLED)
        articles = await nhandan_fetcher.check_official_coverage(
            articles,
            api_key=x_gemini_api_key
        )
        
        return FetchArticlesResponse(articles=articles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/fetch_stream")
async def fetch_articles_stream(
    request: FetchArticlesRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Streaming version of /rss/fetch with real-time progress updates
    Returns Server-Sent Events (SSE) stream
    """
    async def event_generator():
        try:
            # Step 1: Fetch RSS
            yield f"data: {json.dumps({'step': 'fetch_rss', 'status': 'running', 'message': f'Đang tải từ {len(request.rss_urls)} nguồn RSS...'}, ensure_ascii=False)}\n\n"
            
            articles = await rss_fetcher.fetch_and_filter(
                rss_urls=request.rss_urls,
                target_date=request.date,
                time_range=request.time_range
            )
            
            yield f"data: {json.dumps({'step': 'fetch_rss', 'status': 'done', 'message': f'✅ Đã tải {len(articles)} bài viết'}, ensure_ascii=False)}\n\n"
            
            # Step 2: Deduplication
            if len(articles) > 1 and x_gemini_api_key:
                yield f"data: {json.dumps({'step': 'dedup', 'status': 'running', 'message': 'Đang phân tích trùng lặp (AI)...'}, ensure_ascii=False)}\n\n"
                
                articles = await dedup_service.cluster_articles_semantically(
                    articles, 
                    api_key=x_gemini_api_key
                )
                
                # Count duplicates
                duplicate_count = sum(1 for a in articles if a.get('duplicate_count', 0) > 0)
                yield f"data: {json.dumps({'step': 'dedup', 'status': 'done', 'message': f'✅ Tìm thấy {duplicate_count} nhóm trùng lặp'}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'step': 'dedup', 'status': 'skipped', 'message': '⊘ Bỏ qua phân tích trùng lặp'}, ensure_ascii=False)}\n\n"
            
            # Step 3: Nhan Dan Verification
            if x_gemini_api_key:
                yield f"data: {json.dumps({'step': 'verification', 'status': 'running', 'message': 'Đang xác thực Báo Nhân Dân...'}, ensure_ascii=False)}\n\n"
                
                articles = await nhandan_fetcher.check_official_coverage(
                    articles,
                    api_key=x_gemini_api_key
                )
                
                verified_count = sum(1 for a in articles if a.get('official_source_link'))
                yield f"data: {json.dumps({'step': 'verification', 'status': 'done', 'message': f'✅ Tìm thấy {verified_count} bài trên Báo Nhân Dân'}, ensure_ascii=False)}\n\n"
            else:
                yield f"data: {json.dumps({'step': 'verification', 'status': 'skipped', 'message': '⊘ Bỏ qua xác thực'}, ensure_ascii=False)}\n\n"
            
            # Final: Send articles (ensure proper serialization)
            try:
                articles_json = json.dumps({
                    'step': 'complete', 
                    'status': 'done', 
                    'articles': articles
                }, ensure_ascii=False, default=str)
                yield f"data: {articles_json}\n\n"
            except Exception as json_err:
                print(f"JSON serialization error: {json_err}")
                yield f"data: {json.dumps({'step': 'error', 'status': 'error', 'message': f'Lỗi serialize: {str(json_err)}'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'step': 'error', 'status': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


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

from fastapi.responses import StreamingResponse
import json

@router.post("/articles/summarize_stream")
async def summarize_articles_stream(
    request: SummarizeRequest,
    x_gemini_api_key: Optional[str] = Header(None)
):
    """
    Stream summarization progress and result using NDJSON formatting.
    Vercel compatible replacement for WebSockets.
    """
    async def event_generator():
        # Pass article metadata if available
        articles_metadata = {}
        if request.articles:
            for article in request.articles:
                clean_url = article.url.strip().rstrip('/')
                articles_metadata[clean_url] = {
                    'source': article.source,
                    'category': article.category,
                    'title': article.title
                }

        async for update in summarizer.summarize_articles_generator(
            request.urls,
            api_key=x_gemini_api_key,
            articles_metadata=articles_metadata
        ):
            # Yield JSON line
            yield json.dumps(update, ensure_ascii=False) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")
            

