# Sử dụng Python slim để giảm dung lượng và RAM footprint
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài system deps cho Playwright Chromium
RUN apt-get update && apt-get install -y \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libasound2 libpango-1.0-0 libpangocairo-1.0-0 \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cài Chromium cho Playwright (chỉ Chromium, không cần Firefox/WebKit)
RUN playwright install chromium

# Pre-download CloakBrowser stealth binary
RUN python -c "from cloakbrowser import ensure_binary; ensure_binary()"

# Copy toàn bộ code backend vào container
COPY . .

# Mở port 8000
EXPOSE 8000

# Lệnh chạy server
CMD ["python", "main.py"]
