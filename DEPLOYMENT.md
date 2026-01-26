# 🚀 Hướng dẫn Deploy lên Vercel

## 📋 Yêu cầu
- Tài khoản GitHub (đã có)
- Tài khoản Vercel (đăng ký miễn phí tại [vercel.com](https://vercel.com))
- Google Gemini API Key

## 🔧 Các bước Deploy

### 1. Chuẩn bị Repository
✅ **Đã hoàn thành** - Code đã được push lên GitHub:
```
https://github.com/Liemdang2512/AI-News-.git
```

### 2. Deploy Frontend lên Vercel

#### Bước 2.1: Import Project
1. Truy cập [vercel.com](https://vercel.com)
2. Đăng nhập bằng GitHub
3. Click **"Add New..."** → **"Project"**
4. Chọn repository: `Liemdang2512/AI-News-`
5. Click **"Import"**

#### Bước 2.2: Cấu hình Project
- **Framework Preset**: Next.js
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`

#### Bước 2.3: Thêm Environment Variables
Click **"Environment Variables"** và thêm:
```
NEXT_PUBLIC_API_URL=https://your-backend-url.vercel.app
```
*(Sẽ cập nhật sau khi deploy backend)*

#### Bước 2.4: Deploy
- Click **"Deploy"**
- Đợi 2-3 phút để build hoàn tất
- Lưu lại URL frontend (ví dụ: `https://ai-news-frontend.vercel.app`)

### 3. Deploy Backend lên Vercel

#### Bước 3.1: Tạo Project mới
1. Click **"Add New..."** → **"Project"**
2. Chọn lại repository: `Liemdang2512/AI-News-`
3. Click **"Import"**

#### Bước 3.2: Cấu hình Project
- **Framework Preset**: Other
- **Root Directory**: `backend`
- **Build Command**: (để trống)
- **Output Directory**: (để trống)

#### Bước 3.3: Thêm Environment Variables
Click **"Environment Variables"** và thêm:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

#### Bước 3.4: Deploy
- Click **"Deploy"**
- Đợi 2-3 phút để deploy hoàn tất
- Lưu lại URL backend (ví dụ: `https://ai-news-backend.vercel.app`)

### 4. Cập nhật Frontend với Backend URL

#### Bước 4.1: Cập nhật Environment Variable
1. Vào project Frontend trên Vercel
2. Settings → Environment Variables
3. Cập nhật `NEXT_PUBLIC_API_URL` với URL backend vừa deploy
4. Click **"Save"**

#### Bước 4.2: Redeploy Frontend
1. Vào tab **"Deployments"**
2. Click **"..."** ở deployment mới nhất
3. Click **"Redeploy"**

### 5. Cấu hình CORS (nếu cần)

Nếu gặp lỗi CORS, cập nhật file `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-url.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## ✅ Kiểm tra Deployment

1. Truy cập URL frontend
2. Nhập Gemini API Key
3. Thử tìm kiếm và tóm tắt bài viết
4. Kiểm tra format:
   - Tên báo và chuyên mục IN HOA (14px)
   - URL không có prefix "URL:"
   - Export Word hoạt động đúng

## 🔍 Troubleshooting

### Lỗi: "API request failed"
- Kiểm tra `NEXT_PUBLIC_API_URL` đã đúng chưa
- Kiểm tra backend có deploy thành công không

### Lỗi: "Gemini API error"
- Kiểm tra `GEMINI_API_KEY` đã được set chưa
- Kiểm tra API key còn hạn sử dụng không

### Lỗi: Build failed
- Kiểm tra logs trong Vercel
- Đảm bảo tất cả dependencies trong `package.json` và `requirements.txt`

## 📝 Lưu ý

- Vercel miễn phí có giới hạn:
  - 100GB bandwidth/tháng
  - 100 deployments/ngày
  - Serverless function timeout: 10s (Hobby), 60s (Pro)
  
- Nếu cần timeout dài hơn cho AI summarization, cân nhắc nâng cấp lên Vercel Pro

## 🎉 Hoàn thành!

Ứng dụng của bạn đã sẵn sàng sử dụng tại:
- Frontend: `https://your-app.vercel.app`
- Backend: `https://your-api.vercel.app`
