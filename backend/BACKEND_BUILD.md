## Build backend thành binary với PyInstaller

Tài liệu này hướng dẫn cách đóng gói backend FastAPI thành binary chạy độc lập
trên từng hệ điều hành, phục vụ cho desktop app (Electron).

### 1. Chuẩn bị môi trường

Yêu cầu:

- Python 3.10+ cài trên máy.
- Đã cài các dependency trong `requirements.txt`.
- Cài thêm PyInstaller:

```bash
pip install pyinstaller
```

### 2. Entry point backend

Backend sử dụng file `main.py` với hàm `run()`:

- Host/port được cấu hình trong `config.Settings`:
  - `BACKEND_HOST` (mặc định: `127.0.0.1`)
  - `BACKEND_PORT` (mặc định: `8000`)

PyInstaller sẽ đóng gói dựa trên file này.

### 3. Lệnh build cho macOS

Chạy trong thư mục `backend/`:

```bash
cd backend
pyinstaller \
  --onefile \
  --name news-backend-mac \
  main.py
```

Kết quả:

- Binary nằm trong thư mục `dist/news-backend-mac`.
- Khi chạy:

```bash
./dist/news-backend-mac
```

Backend sẽ lắng trên `http://127.0.0.1:8000`.

### 4. Lệnh build cho Windows

Trên Windows, trong thư mục `backend/`:

```bash
cd backend
pyinstaller ^
  --onefile ^
  --name news-backend-win.exe ^
  main.py
```

Kết quả:

- Binary nằm trong thư mục `dist/news-backend-win.exe`.
- Khi chạy:

```bash
dist\\news-backend-win.exe
```

Backend sẽ lắng trên `http://127.0.0.1:8000`.

### 5. Lưu ý khi build

- Nếu backend cần thêm file dữ liệu (JSON, prompt, v.v.), thêm tham số
  `--add-data` tương ứng cho PyInstaller.
- Nếu thay đổi `BACKEND_PORT` trong `config.py`, cần chỉnh lại Electron app
  cho khớp port.

