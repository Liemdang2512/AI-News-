# News Aggregator Web Application

Ứng dụng web tổng hợp và tóm tắt tin tức từ các báo Việt Nam sử dụng AI (Google Gemini).

## 📋 Tổng quan

Ứng dụng này chuyển đổi quy trình tự động hóa trình duyệt (JSON workflow) thành một ứng dụng web full-stack hiện đại:

- **Backend**: Python FastAPI - Xử lý RSS feeds, lọc thời gian, phân loại và tóm tắt bài viết
- **Frontend**: Next.js (App Router) - Giao diện người dùng hiện đại với Tailwind CSS
- **AI**: Google Gemini API - Phân loại và tóm tắt nội dung

## ✨ Tính năng

1. **Khớp nguồn RSS**: Tự động tìm RSS feeds từ tên các đầu báo
2. **Lọc thời gian chính xác**: Sử dụng Python datetime thay vì AI để lọc bài viết theo ngày và giờ
3. **Phân loại thông minh**: AI phân loại bài viết vào 4 chuyên mục (Xã hội, Kinh tế, Pháp luật, Thế giới)
4. **Tóm tắt tự động**: Tạo tóm tắt ngắn gọn cho các bài viết đã chọn

## 🚀 Cài đặt

### Yêu cầu

- Python 3.9+
- Node.js 18+
- Google Gemini API Key

### Backend Setup

```bash
# Di chuyển vào thư mục backend
cd backend

# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# hoặc: venv\Scripts\activate  # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Tạo file .env từ template
cp .env.example .env

# Chỉnh sửa .env và thêm Gemini API key
# GEMINI_API_KEY=your_actual_api_key_here
```

### Frontend Setup

```bash
# Di chuyển vào thư mục frontend
cd frontend

# Cài đặt dependencies
npm install

# Tạo file .env.local từ template
cp .env.local.example .env.local

# File .env.local sẽ có:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎯 Chạy ứng dụng

### Khởi động Backend

```bash
cd backend
source venv/bin/activate  # Kích hoạt virtual environment
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend sẽ chạy tại: http://localhost:8000
API Documentation: http://localhost:8000/docs

### Khởi động Frontend

```bash
cd frontend
npm run dev
```

Frontend sẽ chạy tại: http://localhost:3000

## 📖 Hướng dẫn sử dụng

1. **Nhập thông tin tìm kiếm**:
   - Tên các đầu báo (ví dụ: Lao Động, Dân Trí, VTV)
   - Ngày (định dạng DD/MM/YYYY)
   - Khoảng thời gian (chọn từ dropdown)

2. **Xem kết quả**:
   - Danh sách bài viết được lọc theo thời gian
   - Thông tin: tiêu đề, chuyên mục, thời gian đăng

3. **Tóm tắt bài viết**:
   - Chọn các bài viết muốn tóm tắt
   - Click "Tóm tắt" để tạo bản tóm tắt AI

## 🏗️ Cấu trúc dự án

```
App crwal/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration & RSS database
│   ├── requirements.txt        # Python dependencies
│   ├── routes/
│   │   └── news.py            # API endpoints
│   └── services/
│       ├── gemini_client.py   # Gemini API client
│       ├── rss_matcher.py     # RSS feed matching
│       ├── rss_fetcher.py     # RSS fetching & filtering
│       ├── categorizer.py     # Article categorization
│       └── summarizer.py      # Article summarization
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main page
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── InputForm.tsx      # Search form
│   │   ├── ArticleList.tsx    # Article display
│   │   ├── SummaryPanel.tsx   # Summary display
│   │   └── LoadingSpinner.tsx # Loading indicator
│   ├── lib/
│   │   ├── api.ts             # API client
│   │   └── types.ts           # TypeScript types
│   ├── package.json
│   └── tailwind.config.ts
│
└── AI lấy bài viết báo chính thống V2.json  # Original workflow
```

## 🔧 API Endpoints

### POST /api/rss/match
Khớp tên báo với RSS feeds
```json
{
  "newspapers": "Lao Động, Dân Trí"
}
```

### POST /api/rss/fetch
Lấy và lọc bài viết
```json
{
  "rss_urls": ["https://..."],
  "date": "24/01/2026",
  "time_range": "6h00 đến 8h00"
}
```

### POST /api/articles/categorize
Phân loại bài viết
```json
{
  "articles_text": "..."
}
```

### POST /api/articles/summarize
Tóm tắt bài viết
```json
{
  "urls": ["https://...", "https://..."]
}
```

## 🎨 Công nghệ sử dụng

**Backend:**
- FastAPI - Web framework
- feedparser - RSS parsing
- BeautifulSoup4 - HTML parsing
- httpx - Async HTTP client
- google-generativeai - Gemini API
- python-dateutil - Date parsing

**Frontend:**
- Next.js 14 - React framework
- TypeScript - Type safety
- Tailwind CSS - Styling
- Lucide React - Icons
- react-markdown - Markdown rendering

## 🔑 Lấy Gemini API Key

1. Truy cập: https://makersuite.google.com/app/apikey
2. Đăng nhập với Google account
3. Tạo API key mới
4. Copy và paste vào file `.env` của backend

## ⚡ Tối ưu hóa

- **Time Filtering**: Sử dụng Python datetime thay vì AI để lọc thời gian (100% chính xác, không tốn phí API)
- **Async Processing**: Xử lý đồng thời nhiều RSS feeds
- **Caching**: Có thể thêm Redis để cache kết quả RSS

## 🐛 Xử lý lỗi

- Kiểm tra API key Gemini đã được cấu hình đúng
- Đảm bảo backend đang chạy trước khi khởi động frontend
- Kiểm tra CORS nếu gặp lỗi kết nối

## 📝 License

MIT License - Tự do sử dụng và chỉnh sửa

## 👨‍💻 Hỗ trợ

Nếu gặp vấn đề, vui lòng kiểm tra:
1. Backend logs tại terminal chạy uvicorn
2. Frontend console tại browser DevTools
3. API documentation tại http://localhost:8000/docs
# AI-News-
