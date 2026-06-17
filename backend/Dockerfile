# Sử dụng Python slim để giảm dung lượng và RAM footprint
FROM python:3.11-slim

# Cài system deps cho Playwright/Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    libx11-xcb1 libxcb-dri3-0 libxshmfence1 \
    fonts-liberation libappindicator3-1 xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cài Chromium cho Playwright
RUN playwright install chromium

# Copy toàn bộ code backend vào container
COPY . .

# Mở port 8000
EXPOSE 8000

# Lệnh chạy server
CMD ["python", "main.py"]
