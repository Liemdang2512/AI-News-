# Sử dụng Python slim để giảm dung lượng và RAM footprint
FROM python:3.11-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Copy requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code backend vào container
COPY . .

# Mở port 8000
EXPOSE 8000

# Lệnh chạy server
CMD ["python", "main.py"]
