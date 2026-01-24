# Hướng dẫn sử dụng - Ứng dụng Tổng hợp Tin tức AI

Chào mừng bạn đến với ứng dụng **Tổng hợp và Tóm tắt Tin tức Báo chí Việt Nam**. Ứng dụng này giúp bạn tự động tìm kiếm, lọc và tóm tắt tin tức từ các đầu báo lớn như Lao Động, Dân Trí, VTV, v.v. sử dụng trí tuệ nhân tạo (Google Gemini).

---

## 🚀 1. Chuẩn bị & Cài đặt (Lần đầu tiên)

Nếu đây là lần đầu bạn chạy ứng dụng, hãy đảm bảo bạn đã thực hiện các bước sau:

### Bước 1: Lấy khóa API Google Gemini
1. Truy cập: [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Đăng nhập và tạo một API Key mới.
3. Copy mã khóa này.

### Bước 2: Cấu hình ứng dụng
1. Mở thư mục `backend` trong dự án.
2. Mở file `.env` (hoặc tạo mới nếu chưa có, đổi tên từ `.env.example`).
3. Dán khóa API của bạn vào dòng:
   ```env
   GEMINI_API_KEY=mã_khóa_api_của_bạn_ở_đây
   ```
4. Lưu file lại.

---

## ▶️ 2. Khởi động ứng dụng

Bạn cần chạy cả Backend (Xử lý dữ liệu) và Frontend (Giao diện) đồng thời.

### Cửa sổ 1: Chạy Backend (Server)
Mở terminal (Terminal 1) và chạy các lệnh sau:
```bash
cd "/Users/tanliem/Desktop/App crwal/backend"
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
✅ **Thành công khi:** Terminal hiện dòng chữ `Application startup complete`.

### Cửa sổ 2: Chạy Frontend (Giao diện)
Mở một terminal mới (Terminal 2) và chạy:
```bash
cd "/Users/tanliem/Desktop/App crwal/frontend"
npm run dev
```
✅ **Thành công khi:** Terminal hiện `Ready in ...` và `Local: http://localhost:3000`.

👉 **Truy cập ứng dụng tại:** [http://localhost:3000](http://localhost:3000)

---

## 📖 3. Hướng dẫn sử dụng tính năng

### Bước 1: Nhập thông tin tìm kiếm
Tại màn hình chính, bạn sẽ thấy 3 ô thông tin cần điền:
1. **Tên các đầu báo:** Nhập tên các báo bạn muốn tìm (ví dụ: `Lao Động, Dân Trí, VTV`). Ngăn cách bằng dấu phẩy.
2. **Ngày:** Nhập ngày cần lấy tin (định dạng `DD/MM/YYYY`, ví dụ: `24/01/2026`). Mặc định ứng dụng sẽ điền ngày hôm nay.
3. **Khoảng thời gian:** Chọn khung giờ bạn quan tâm (ví dụ: `6h00 đến 8h00`).

👉 Bấm nút **"Tìm kiếm bài viết"** và chờ vài giây.

### Bước 2: Xem kết quả & Lọc tin
- Ứng dụng sẽ hiển thị danh sách các bài viết phù hợp với tiêu chí của bạn.
- Mỗi bài viết hiển thị: Tiêu đề, Chuyên mục (Xã hội, Kinh tế, v.v.), và Giờ đăng.
- Bạn có thể bấm vào link "Xem bài viết" để mở bài gốc trên trình duyệt.

### Bước 3: Tóm tắt bài viết bằng AI
1. **Chọn bài:** Tích vào ô vuông bên cạnh các bài viết bạn muốn tóm tắt. (Có thể dùng nút "Chọn tất cả").
2. **Bấm nút "Tóm tắt"**: Nút này nằm ở góc trên danh sách bài viết.
3. **Xem kết quả:** AI sẽ đọc nội dung các bài đã chọn và tạo ra một bản tóm tắt ngắn gọn, dễ hiểu ở bên dưới.

---

## ❓ 4. Các lỗi thường gặp

| Vấn đề | Nguyên nhân & Cách khắc phục |
|--------|------------------------------|
| **Lỗi "Không kết nối được với server"** | Bạn chưa chạy Backend (Cửa sổ 1). Hãy kiểm tra lại xem cửa sổ Backend có đang chạy không. |
| **Lỗi "403 Forbidden" hoặc API Error** | Key Gemini API của bạn bị sai hoặc hết hạn. Hãy kiểm tra lại file `backend/.env`. |
| **Không tìm thấy bài viết nào** | Có thể khung giờ đó không có bài viết nào khớp, hoặc tên báo bạn nhập không chính xác. Hãy thử mở rộng khung giờ hoặc thêm tên báo khác. |
| **Ngày tháng bị sai** | Hãy chắc chắn bạn nhập đúng định dạng `DD/MM/YYYY` (Ngày/Tháng/Năm). |

---

Chúc bạn có trải nghiệm đọc tin tức hiệu quả!
