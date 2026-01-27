# News Aggregator Desktop App

Ứng dụng desktop đóng gói News Aggregator với backend Python chạy local.

## Cấu trúc thư mục

```
desktop/
├── main.js              # Main process Electron
├── preload.js           # Preload script
├── package.json         # Cấu hình Electron + electron-builder
├── frontend-dist/       # Build static của Next.js frontend
└── resources/
    └── backend/
        ├── mac/         # Binary backend cho macOS
        └── win/         # Binary backend cho Windows
```

## Build thủ công (trên macOS)

### 1. Build backend binary

```bash
cd backend
pip install pyinstaller
pip install -r requirements.txt
pyinstaller --onefile --name news-backend-mac main.py
```

### 2. Copy backend binary

```bash
mkdir -p desktop/resources/backend/mac
cp backend/dist/news-backend-mac desktop/resources/backend/mac/
```

### 3. Build frontend

```bash
cd frontend
npm install
npm run build
cp -r out ../desktop/frontend-dist
```

### 4. Build Electron app

```bash
cd desktop
npm install
npm run build:mac
```

File `.dmg` sẽ nằm trong `desktop/dist/`

## Build tự động với GitHub Actions

Push code lên GitHub và:

1. Vào tab **Actions**
2. Chọn workflow **Build Desktop Apps**
3. Click **Run workflow**

Hoặc tạo tag mới:

```bash
git tag v1.0.0
git push --tags
```

Workflow sẽ tự động build cho cả macOS và Windows, rồi upload artifacts.

## Lưu ý

- **macOS**: App chưa được notarize, lần đầu mở có thể hiện cảnh báo. Click chuột phải → Open để mở.
- **Windows**: Có thể bị Windows Defender cảnh báo do binary chưa được sign. Click "More info" → "Run anyway".
