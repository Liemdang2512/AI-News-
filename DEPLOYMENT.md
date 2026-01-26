# 🚀 Hướng dẫn Deploy: Vercel (Frontend) + Render (Backend)

Do backend sử dụng **Playwright** để bypass anti-bot (báo Lao Động), chúng ta cần deploy Backend lên **Render** (hỗ trợ Docker) thay vì Vercel Serverless.

## 📋 Chuẩn bị
- Tài khoản GitHub (đã có code)
- Tài khoản [Vercel](https://vercel.com) (Frontend)
- Tài khoản [Render](https://render.com) (Backend)
- Gemini API Key

---

## �️ Phần 1: Deploy Backend lên Render

1. **Đăng nhập Render**: Truy cập https://dashboard.render.com/
2. **Tạo Web Service mới**:
   - Chọn **"New +"** → **"Web Service"**
   - Chọn **"Build and deploy from a Git repository"**
   - Kết nối với repo GitHub: `Liemdang2512/AI-News-`

3. **Cấu hình Service**:
   - **Name**: `ai-news-backend`
   - **Region**: Singapore (cho nhanh)
   - **Root Directory**: `backend` (⚠️ Quan trọng)
   - **Runtime**: **Docker** (Render sẽ tự nhận diện Dockerfile trong thư mục backend)
   - **Instance Type**: Free

4. **Environment Variables** (Kéo xuống dưới):
   - Key: `GEMINI_API_KEY`
   - Value: `Paste_Key_Cua_Ban_Vao_Day`
   - Key: `PYTHONUNBUFFERED`
   - Value: `1`

5. **Deploy**:
   - Click **"Create Web Service"**
   - Đợi khoảng 3-5 phút để Render build Docker image và cài đặt Playwright.
   - Khi hoàn tất, copy URL backend (ví dụ: `https://ai-news-backend.onrender.com`)

---

## 🎨 Phần 2: Deploy Frontend lên Vercel

1. **Đăng nhập Vercel**: Truy cập https://vercel.com
2. **Import Project**:
   - Click **"Add New..."** → **"Project"**
   - Chọn repo `Liemdang2512/AI-News-`

3. **Cấu hình Project**:
   - **Root Directory**: Click "Edit" và chọn thư mục `frontend`
   - **Framework Preset**: Next.js (Mặc định)

4. **Environment Variables**:
   - Key: `NEXT_PUBLIC_API_URL`
   - Value: URL Backend bạn vừa copy ở Bước 1 (Ví dụ: `https://ai-news-backend.onrender.com`)
   - ⚠️ **Lưu ý**: Không có dấu `/` ở cuối URL

5. **Deploy**:
   - Click **"Deploy"**
   - Đợi 1-2 phút.

---

## ✅ Kiểm tra Hoạt động

1. Mở trang Frontend vừa deploy trên Vercel.
2. Thử tìm kiếm tin tức từ **Lao Động**.
3. Nếu thấy báo "Đang xử lý..." hơi lâu một chút (do Playwright khởi động), đó là bình thường.
4. Kiểm tra kết quả trả về.

---

## ℹ️ Lưu ý về Server Miễn phí

- **Render Free Tier**: Server sẽ "ngủ" (spin down) nếu không có request trong 15 phút. Request đầu tiên sau khi ngủ sẽ mất khoảng 50 giây để khởi động lại.
  - *Mẹo*: Dùng [UptimeRobot](https://uptimerobot.com/) ping vào URL backend mỗi 10 phút để giữ server luôn chạy.

- **Vercel**: Chạy rất nhanh và ổn định cho Frontend.
