# 🚀 Hướng dẫn Deploy & Sửa lỗi Vercel

Hệ thống của bạn đã được kiểm tra Local thành công 100%. Nếu Vercel vẫn báo lỗi, chắc chắn do **Cấu hình trên Vercel** chưa đúng.

## 🛠️ Bước 1: Kiểm tra Cấu hình Vercel (QUAN TRỌNG)

Bạn hãy vào trang quản lý dự án trên Vercel, chọn tab **Settings** -> **Build & Deployment** và đối chiếu chính xác từng mục sau:

| Mục (Setting) | Giá trị Yêu cầu (Value) | Nút Override | Giải thích |
| :--- | :--- | :--- | :--- |
| **Framework Preset** | **`Next.js`** | - | Bắt buộc phải chọn Next.js. Nếu không chọn được, hãy chọn Override rồi chọn Next.js. |
| **Root Directory** | **`frontend`** | - | Phải nằm trong tab **Global** -> mục Root Directory. |
| **Build Command** | `next build` | **TẮT** (Màu xám) | Không được tự điền lệnh. Hãy tắt nút Override để Vercel tự quản lý. |
| **Output Directory** | `Next.js default` | **TẮT** (Màu xám) | Tuyệt đối không bật cái này. Nếu bật, nó sẽ tìm thư mục `public` và gây lỗi. |
| **Install Command** | `npm install` | **TẮT** (Màu xám) | Để mặc định. |

---

## 🛑 Cách Xử lý khi đã chỉnh đúng mà vẫn lỗi

Nếu bạn đã chỉnh y hệt bảng trên mà vẫn không được (do Vercel lưu cache cũ), hãy làm cách "Đập đi xây lại" này (Nhanh nhất):

1. **Xóa Project hiện tại**:
   - Vào **Settings** -> Cuối trang chọn **Delete Project**.

2. **Tạo Project Mới**:
   - Về trang chủ Vercel -> **Add New...** -> **Project**.
   - Chọn repo `AI-News-`.
   - **QUAN TRỌNG**: Ở bước **Configure Project**, tìm mục **Root Directory**, bấm **Edit** và chọn thư mục **`frontend`**.
   - Bấm **Deploy**.

Cách này đảm bảo Vercel tự động nhận diện "À, đây là Next.js" ngay từ đầu và tự điền mọi cấu hình chuẩn xác cho bạn.

---

## 🌍 URL Backend

Khi deploy Frontend, đừng quên thêm biến môi trường:
- Key: `NEXT_PUBLIC_API_URL`
- Value: `https://ai-news-yqan.onrender.com` (URL Backend đã chạy thành công)
