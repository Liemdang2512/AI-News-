# 🚀 Hướng Dẫn Deploy Full-Stack lên Vercel

## 📋 Tổng Quan

Ứng dụng của bạn sẽ được deploy thành **2 projects riêng biệt** trên Vercel:
1. **Frontend** (Next.js) - từ thư mục `frontend/`
2. **Backend** (FastAPI Python) - từ thư mục `backend/`

---

## 🎯 BƯỚC 1: Deploy Backend

### 1.1. Tạo Project Backend trên Vercel

1. Đăng nhập vào https://vercel.com
2. Click **"Add New..."** → **"Project"**
3. Chọn repository GitHub của bạn: `AI-News-`
4. **QUAN TRỌNG**: Ở phần **"Configure Project"**:
   - **Root Directory**: Chọn **`backend`** ✅
   - **Framework Preset**: Chọn **"Other"**
   - Click **"Deploy"**

### 1.2. Thêm Environment Variables cho Backend

Sau khi deploy xong, vào **Settings** → **Environment Variables** và thêm:

| Key | Value | Giải thích |
|-----|-------|------------|
| `GEMINI_API_KEY` | `your_api_key_here` | API key của Google Gemini |
| `BACKEND_HOST` | `0.0.0.0` | Host binding |
| `BACKEND_PORT` | `8000` | Port (không quan trọng trên Vercel) |

### 1.3. Lưu URL Backend

Sau khi deploy thành công, bạn sẽ có URL backend, ví dụ:
```
https://ai-news-backend.vercel.app
```

**Lưu lại URL này** để dùng cho bước tiếp theo! ✅

---

## 🎯 BƯỚC 2: Deploy Frontend

### 2.1. Tạo Project Frontend trên Vercel

1. Quay lại Vercel Dashboard
2. Click **"Add New..."** → **"Project"**
3. Chọn lại repository GitHub: `AI-News-`
4. **QUAN TRỌNG**: Ở phần **"Configure Project"**:
   - **Root Directory**: Chọn **`frontend`** ✅
   - **Framework Preset**: Sẽ tự động nhận diện **"Next.js"**

### 2.2. Thêm Environment Variables cho Frontend

**TRƯỚC KHI CLICK DEPLOY**, kéo xuống phần **Environment Variables** và thêm:

| Key | Value | Giải thích |
|-----|-------|------------|
| `NEXT_PUBLIC_API_URL` | `https://ai-news-backend.vercel.app` | URL backend từ bước 1.3 |

### 2.3. Deploy

Click **"Deploy"** và đợi Vercel build xong!

---

## ✅ BƯỚC 3: Kiểm Tra

### 3.1. Test Backend

Mở trình duyệt và truy cập:
```
https://ai-news-backend.vercel.app/health
```

Bạn sẽ thấy:
```json
{"status": "healthy"}
```

### 3.2. Test Frontend

Truy cập URL frontend của bạn:
```
https://ai-news-frontend.vercel.app
```

Kiểm tra xem có fetch được RSS feeds không.

---

## 🐛 Xử Lý Lỗi

### Lỗi: "Failed to match RSS feeds"

**Nguyên nhân**: Backend không kết nối được với frontend

**Giải pháp**:
1. Kiểm tra `NEXT_PUBLIC_API_URL` trong frontend settings
2. Đảm bảo URL backend đúng (không có dấu `/` ở cuối)
3. Redeploy frontend

### Lỗi: "Gemini API Error"

**Nguyên nhân**: Thiếu hoặc sai API key

**Giải pháp**:
1. Vào Backend project → Settings → Environment Variables
2. Kiểm tra `GEMINI_API_KEY`
3. Redeploy backend

### Lỗi: "curl_cffi not available"

**Nguyên nhân**: Đây là warning bình thường trên Vercel

**Giải pháp**: Không cần làm gì! Code đã tự động fallback sang `httpx` ✅

---

## 🔄 Cập Nhật Code

Sau khi push code lên GitHub:
- Vercel sẽ **tự động rebuild** cả 2 projects
- Không cần làm gì thêm!

---

## 📝 Checklist

- [ ] Backend deployed với Root Directory = `backend`
- [ ] Backend có `GEMINI_API_KEY` trong Environment Variables
- [ ] Frontend deployed với Root Directory = `frontend`
- [ ] Frontend có `NEXT_PUBLIC_API_URL` trỏ đến backend URL
- [ ] Test `/health` endpoint của backend
- [ ] Test frontend có fetch được RSS feeds

---

## 🎉 Hoàn Thành!

Nếu tất cả các bước trên đều OK, ứng dụng của bạn đã chạy thành công trên Vercel! 🚀
