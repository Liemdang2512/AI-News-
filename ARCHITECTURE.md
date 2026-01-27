# 🔍 Cơ chế Chọn lọc Bài viết - Phân tích Chi tiết

## 📊 Tổng quan

Hệ thống sử dụng **HYBRID APPROACH** - kết hợp cả Python và AI:
- **Python**: Xử lý lọc theo thời gian, ngày tháng, phân loại cơ bản
- **AI (Gemini)**: Tóm tắt nội dung, phân loại chi tiết (nếu cần)

---

## 🔄 Quy trình Xử lý (Pipeline)

### **Bước 1: Match RSS Feeds** 
📍 File: `backend/services/rss_matcher.py`
- **Công nghệ**: Python (hardcoded mapping)
- **Input**: Tên báo (ví dụ: "Lao Động, Dân Trí")
- **Output**: Danh sách RSS URLs
- **Cách hoạt động**: 
  ```python
  "Lao Động" → "https://laodong.vn/rss/kinh-te.rss"
  ```

### **Bước 2: Fetch & Filter Articles** ⭐ **PYTHON-BASED**
📍 File: `backend/services/rss_fetcher.py`
- **Công nghệ**: 100% Python (feedparser + datetime)
- **Input**: 
  - RSS URLs
  - Ngày (DD/MM/YYYY)
  - Khung giờ (ví dụ: "6h00 đến 8h00")
- **Output**: Danh sách bài viết đã lọc

#### **Chi tiết cơ chế lọc:**

```python
def _process_entry(entry, target_date, start_time, end_time):
    # 1. Parse thời gian xuất bản từ RSS
    pub_date = date_parser.parse(entry.published)
    
    # 2. Lọc theo NGÀY (Python datetime)
    if pub_date.date() != target_date.date():
        return None  # Bỏ qua bài không đúng ngày
    
    # 3. Lọc theo GIỜ (Python time comparison)
    pub_time = pub_date.time()
    if not (start_time <= pub_time <= end_time):
        return None  # Bỏ qua bài ngoài khung giờ
    
    # 4. Trích xuất CATEGORY từ URL (Python regex)
    category = extract_category_from_url(rss_url)
    # Ví dụ: "kinh-te" → "KINH TẾ"
    
    return article
```

#### **Phân loại Category (Rule-based):**
```python
def _extract_category_from_url(rss_url):
    url_lower = rss_url.lower()
    
    # Mapping keywords → category
    if 'phap-luat' in url_lower:
        return "PHÁP LUẬT"
    elif 'kinh-te' in url_lower or 'kinh-doanh' in url_lower:
        return "KINH TẾ"
    elif 'xa-hoi' in url_lower or 'doi-song' in url_lower:
        return "XÃ HỘI"
    elif 'the-gioi' in url_lower or 'quoc-te' in url_lower:
        return "THẾ GIỚI"
    else:
        return "XÃ HỘI"  # Default
```

### **Bước 3: Summarize Articles** ⭐ **AI-BASED**
📍 File: `backend/services/summarizer.py`
- **Công nghệ**: Google Gemini AI
- **Input**: 
  - URLs của bài viết đã chọn
  - Metadata (source, category)
- **Output**: Tóm tắt markdown

#### **Quy trình:**
```python
async def summarize_articles(urls, articles_metadata):
    summaries = []
    
    for url in urls:
        # 1. Crawl nội dung bài viết (Python httpx + BeautifulSoup)
        content = await fetch_article_content(url)
        
        # 2. Gửi cho Gemini AI để tóm tắt
        prompt = f"""
        Tóm tắt bài viết này:
        Nguồn: {metadata['source']}
        Chuyên mục: {metadata['category']}
        Nội dung: {content}
        """
        
        summary = gemini.generate_content(prompt)
        summaries.append(summary)
    
    return format_summaries(summaries)
```

---

## 📋 So sánh: Python vs AI

| Tính năng | Python | AI (Gemini) |
|-----------|--------|-------------|
| **Lọc theo thời gian** | ✅ Chính xác 100% | ❌ Không cần |
| **Lọc theo ngày** | ✅ Nhanh, chính xác | ❌ Không cần |
| **Phân loại category** | ✅ Rule-based (từ URL) | ⚠️ Có thể dùng nhưng chậm |
| **Tóm tắt nội dung** | ❌ Không thể | ✅ AI xuất sắc |
| **Hiểu ngữ cảnh** | ❌ Hạn chế | ✅ Rất tốt |
| **Tốc độ** | ⚡ Rất nhanh | 🐌 Chậm hơn |
| **Chi phí** | 💰 Miễn phí | 💰 Tốn API calls |

---

## 🎯 Tại sao dùng Python cho việc lọc?

### **Ưu điểm:**
1. ✅ **Chính xác tuyệt đối**: Datetime comparison không bao giờ sai
2. ✅ **Nhanh**: Xử lý hàng trăm bài viết trong vài giây
3. ✅ **Miễn phí**: Không tốn API calls
4. ✅ **Ổn định**: Không phụ thuộc vào AI model
5. ✅ **Dễ debug**: Logic rõ ràng, dễ kiểm tra

### **Nhược điểm:**
1. ❌ **Cứng nhắc**: Phải định nghĩa rules trước
2. ❌ **Không linh hoạt**: Không hiểu ngữ cảnh phức tạp

---

## 🤖 Tại sao dùng AI cho việc tóm tắt?

### **Ưu điểm:**
1. ✅ **Hiểu ngữ cảnh**: Nắm bắt ý chính của bài viết
2. ✅ **Tóm tắt thông minh**: Giữ lại thông tin quan trọng
3. ✅ **Linh hoạt**: Xử lý được nhiều định dạng khác nhau
4. ✅ **Chất lượng cao**: Tóm tắt tự nhiên, dễ đọc

### **Nhược điểm:**
1. ❌ **Chậm**: Mỗi request mất 2-5 giây
2. ❌ **Tốn kém**: Mỗi request tốn API quota
3. ❌ **Không ổn định**: Đôi khi AI trả về kết quả không đúng format

---

## 💡 Kết luận

### **Cơ chế hiện tại (Tối ưu):**
```
[User Input] 
    ↓
[Python: Match RSS] → Nhanh, chính xác
    ↓
[Python: Fetch & Filter by Date/Time] → Nhanh, chính xác
    ↓
[Python: Extract Category from URL] → Rule-based, nhanh
    ↓
[User: Select articles] → Manual selection
    ↓
[AI: Summarize content] → Chất lượng cao
    ↓
[Output: Formatted summary]
```

### **Nếu dùng 100% AI:**
```
❌ Chậm (mỗi bước phải gọi AI)
❌ Tốn kém (nhiều API calls)
❌ Không chính xác (AI có thể hiểu sai thời gian)
❌ Khó debug (không biết AI suy nghĩ gì)
```

### **Khuyến nghị:**
✅ **Giữ nguyên cơ chế hiện tại** - đây là best practice:
- Python xử lý những gì nó làm tốt (lọc, so sánh)
- AI xử lý những gì nó làm tốt (hiểu ngữ nghĩa, tóm tắt)
- Kết hợp 2 công nghệ = Tối ưu nhất về tốc độ, chi phí và chất lượng

---

## 🔧 Nếu muốn cải tiến

### **Option 1: Thêm AI cho phân loại chi tiết**
- Dùng Python lọc thời gian (như hiện tại)
- Thêm AI để phân loại category chi tiết hơn
- **Trade-off**: Chậm hơn, tốn kém hơn, nhưng chính xác hơn

### **Option 2: Thêm AI cho ranking/scoring**
- Python lọc bài viết
- AI đánh giá độ quan trọng của từng bài
- Tự động chọn top N bài quan trọng nhất
- **Trade-off**: Tốn thêm API calls

### **Option 3: Hybrid filtering**
- Python lọc thô (90% bài viết)
- AI lọc tinh (10% bài viết còn lại)
- **Trade-off**: Cân bằng giữa tốc độ và chất lượng
