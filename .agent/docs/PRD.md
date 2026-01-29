# Product Requirements Document (PRD)
# AI News Aggregator

**Version:** 3.0  
**Last Updated:** 2026-01-29  
**Status:** Active Development

---

## 1. Product Overview

### 1.1 Vision
An intelligent news aggregation platform that helps Vietnamese users efficiently consume news from multiple sources with AI-powered summarization, duplicate detection, and official source verification.

### 1.2 Target Users
- Journalists and media professionals
- Researchers and analysts
- Business professionals tracking industry news
- General users seeking comprehensive news coverage

### 1.3 Core Value Proposition
- **Time-saving:** Aggregate news from 10+ Vietnamese newspapers in seconds
- **AI-powered:** Smart deduplication and summarization using Google Gemini
- **Verified:** Cross-reference with Báo Nhân Dân (official source)
- **Transparent:** Real-time progress tracking for all operations

---

## 2. Feature Requirements

### 2.1 Phase 1: Core Functionality ✅ COMPLETED

#### F1.1 Multi-source News Aggregation
- **Description:** Fetch articles from multiple Vietnamese news sources
- **Supported Sources:** VnExpress, Dân Trí, VTV News, Lao Động, Hà Nội Mới, Sài Gòn Giải Phóng, VietnamPlus, Tiền Phong, Báo tin tức, Báo tuổi trẻ, Báo Nhân Dân
- **Filters:**
  - Date selection (DD/MM/YYYY)
  - Time range (hourly intervals or full day)
  - Category-based filtering (auto-detected)

#### F1.2 Article Categorization
- **Categories:** KINH TẾ, TÀI CHÍNH, XÃ HỘI, PHÁP LUẬT, THẾ GIỚI
- **Method:** URL path-based classification
- **Display:** Category statistics with article counts

#### F1.3 AI Summarization
- **Model:** Google Gemini 2.0 Flash
- **Input:** User-selected articles
- **Output:** Structured summary by source and category
- **Format:** Markdown with bold titles and bullet points

### 2.2 Phase 2: Advanced Features ✅ COMPLETED

#### F2.1 Semantic Duplicate Detection
- **Purpose:** Group articles about the same specific event
- **Technology:** AI-powered entity extraction and reasoning
- **Scope:** Cross-newspaper deduplication
- **Display:** 
  - Master article with "+N nguồn khác" badge
  - Expandable list of duplicate sources
  - Checkbox selection for duplicates
- **Limit:** 30 articles per category (performance optimization)

#### F2.2 Official Source Verification
- **Purpose:** Verify if articles are covered by Báo Nhân Dân
- **Method:** Batch semantic matching with Gemini AI
- **Display:** "✅ Báo Nhân Dân" badge with link
- **Cache:** Background RSS fetching every 30 minutes
- **Limit:** 30 articles per category (performance optimization)

### 2.3 Phase 3: Real-time Progress Tracking ✅ COMPLETED

#### F3.1 Progress Visualization
- **Technology:** Server-Sent Events (SSE)
- **Display Components:**
  - Step-by-step progress indicator
  - Percentage-based progress bar
  - Real-time status messages
  - Animated icons (pending, running, done, error, skipped)

#### F3.2 Processing Steps
1. **Fetch RSS:** Load and filter articles from selected sources
2. **Deduplication:** AI clustering of similar articles
3. **Verification:** Cross-check with Báo Nhân Dân database

---

## 3. Technical Requirements

### 3.1 Backend
- **Framework:** FastAPI (Python)
- **API Model:** REST + Server-Sent Events (SSE)
- **AI Integration:** Google Gemini 2.0 Flash
- **RSS Parsing:** feedparser + curl_cffi (anti-bot bypass)
- **Async Processing:** asyncio for parallel operations

### 3.2 Frontend
- **Framework:** Next.js 14 (React)
- **Styling:** Tailwind CSS
- **State Management:** React Hooks
- **API Communication:** Fetch API + EventSource (SSE)

### 3.3 Performance Requirements
- **Article Fetch:** < 10 seconds for 5 sources
- **AI Processing:** < 30 seconds for 30 articles
- **Progress Updates:** Real-time (< 500ms latency)
- **UI Responsiveness:** 60 FPS animations

### 3.4 Scalability Limits
- **Max Articles per Category:** 30 (AI stability)
- **Max Concurrent Requests:** 10 (Gemini rate limit)
- **Cache Duration:** 30 minutes (Nhan Dan RSS)

---

## 4. User Experience Requirements

### 4.1 Workflow
```
1. User enters API key (one-time setup)
   ↓
2. Select newspapers + date + time range
   ↓
3. Click "Tìm kiếm" → Real-time progress display
   ↓
4. View categorized articles with badges
   ↓
5. Select articles for summarization
   ↓
6. View AI-generated summary report
```

### 4.2 UI/UX Principles
- **Clarity:** Clear visual hierarchy and labeling
- **Feedback:** Real-time progress and status updates
- **Efficiency:** Minimal clicks to complete tasks
- **Accessibility:** Vietnamese language throughout
- **Responsiveness:** Mobile-friendly design

### 4.3 Error Handling
- **Network Errors:** Retry mechanism with user notification
- **API Errors:** Fallback to basic functionality
- **Empty Results:** Clear messaging with suggestions
- **Timeout:** Automatic cancellation after 60 seconds

---

## 5. Data Requirements

### 5.1 Article Schema
```typescript
{
  url: string;
  title: string;
  category: string;
  published_at: string;
  description: string;
  source: string;
  thumbnail: string;
  
  // Phase 2 fields
  group_id: string;
  is_master: boolean;
  duplicate_count: number;
  event_summary: string;
  official_source_link: string | null;
}
```

### 5.2 Data Sources
- **RSS Feeds:** Primary data source
- **Gemini API:** AI processing
- **LocalStorage:** API key persistence

---

## 6. Security & Privacy

### 6.1 API Key Management
- **Storage:** Browser localStorage (client-side only)
- **Transmission:** HTTPS headers
- **Validation:** Server-side verification

### 6.2 Data Privacy
- **No User Data Collection:** No personal information stored
- **No Server-side Storage:** Articles fetched on-demand
- **CORS Policy:** Restricted to localhost/deployment domain

---

## 7. Success Metrics

### 7.1 Performance Metrics
- Average article fetch time
- AI processing success rate
- Duplicate detection accuracy
- User session duration

### 7.2 User Satisfaction
- Task completion rate
- Error rate
- Feature usage statistics
- User feedback scores

---

## 8. Future Enhancements (Backlog)

### 8.1 Phase 4: Advanced Analytics
- Trend analysis across sources
- Sentiment analysis
- Topic clustering
- Historical data tracking

### 8.2 Phase 5: Personalization
- Saved search preferences
- Custom RSS sources
- Notification system
- Bookmark functionality

### 8.3 Phase 6: Collaboration
- Shared summaries
- Team workspaces
- Export to various formats
- Integration with productivity tools

---

## 9. Constraints & Assumptions

### 9.1 Constraints
- **Gemini API Rate Limits:** 60 requests/minute
- **RSS Feed Availability:** Dependent on source uptime
- **Browser Compatibility:** Modern browsers only (ES6+)

### 9.2 Assumptions
- Users have stable internet connection
- Users can obtain Gemini API key
- News sources maintain RSS feed structure
- Vietnamese language content only

---

## 10. Appendix

### 10.1 Supported News Sources
| Source | Categories | RSS Format |
|--------|-----------|------------|
| VnExpress | All | Standard RSS 2.0 |
| Dân Trí | All | Standard RSS 2.0 |
| VTV News | All | Standard RSS 2.0 |
| Lao Động | All | Anti-bot protected |
| Hà Nội Mới | All | Anti-bot protected |
| Báo Nhân Dân | All | Standard RSS 2.0 |

### 10.2 Category Mapping
- **KINH TẾ:** kinh-te, kinh-doanh, tai-chinh
- **PHÁP LUẬT:** phap-luat
- **XÃ HỘI:** xa-hoi, doi-song
- **THẾ GIỚI:** the-gioi, quoc-te

---

**Document Owner:** Development Team  
**Stakeholders:** Product Manager, Engineering Lead, UX Designer  
**Review Cycle:** Bi-weekly
