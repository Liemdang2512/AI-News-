# Sử dụng image chính thức của Playwright (đã bao gồm Python và Browsers)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Cài đặt trình duyệt Chromium cho Playwright
RUN playwright install chromium

# Copy toàn bộ code backend vào container
COPY . .

# Mở port 8000
EXPOSE 8000

# Lệnh chạy server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
