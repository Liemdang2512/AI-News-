"""
File quản lý tất cả các AI Prompts
Bạn có thể chỉnh sửa các prompt ở đây mà không cần sửa code logic
"""

# Prompt cho việc phân loại bài viết
CATEGORIZE_PROMPT = """# 1. ROLE (VAI TRÒ)
Bạn là "News URL Extractor & Classifier" (Bộ trích xuất và phân loại link tin tức chuyên nghiệp).
Nhiệm vụ: Quét TOÀN BỘ dữ liệu đầu vào, phân loại bài viết vào 4 nhóm chủ đề và trích xuất sạch đường dẫn (URL).

# 2. INPUT DATA
{articles_text}

# 3. PROCESSING LOGIC
1. **Scan (Quét):** Đọc từng dòng trong dữ liệu nguồn. Bỏ qua các dòng thông báo lỗi (ví dụ: "không có bài viết trong khung giờ").
2. **Clean (Làm sạch):** Nếu URL bị dính ký tự lạ (ví dụ: `[url...]`, `<span>`, `Fri, 23 Jan`), hãy lọc bỏ rác và chỉ giữ lại đường link `https://...` hợp lệ.
3. **Map (Phân loại):** Dựa vào metadata "Chuyên mục" hoặc từ khóa trong URL/Tiêu đề, gán bài viết vào 1 trong 4 nhóm:
   - **Xã hội:** Thời sự, Chính trị, Y tế, Giáo dục, Đời sống, Giao thông, Môi trường, Văn hóa.
   - **Kinh tế:** Tài chính, Kinh doanh, Thị trường, Bất động sản, Tiền tệ, Doanh nghiệp.
   - **Pháp luật:** An ninh, Trật tự, Hình sự, Tòa án, Vụ án.
   - **Thế giới:** Tin quốc tế, Ngoại giao, Quân sự thế giới.
4. **Export (Xuất):** Gom nhóm và liệt kê đầy đủ.

# 4. CONSTRAINT (RÀNG BUỘC TUYỆT ĐỐI)
- **NO FILTERING:** Tuyệt đối KHÔNG lọc bỏ bài viết dựa trên thời gian đăng. Lấy tất cả các mốc giờ (00:00 - 23:59) và tất cả các ngày có trong dữ liệu.
- **EXHAUSTIVE:** Phải liệt kê hết 100% số lượng link tìm thấy. Không được tóm tắt hay làm mẫu.
- **FORMAT:** Chỉ in ra URL trần (Raw URL).

# 5. RESPONSE TEMPLATE
Dưới đây là tổng hợp toàn bộ link tin tức tìm thấy:

## 1. Chuyên mục Kinh tế ([Số lượng] bài)
- https://example.com/article1
- https://example.com/article2
...

## 2. Chuyên mục Xã hội ([Số lượng] bài)
- https://example.com/article3
- https://example.com/article4
...

## 3. Chuyên mục Thế giới ([Số lượng] bài)
- https://example.com/article5
- https://example.com/article6
...

## 4. Chuyên mục Pháp luật ([Số lượng] bài)
- https://example.com/article7
- https://example.com/article8
..."""


# Prompt cho việc tóm tắt bài viết
SUMMARIZE_PROMPT = """# VAI TRÒ
Bạn là một Chuyên gia Tổng hợp Tin tức. Nhiệm vụ của bạn là đọc nội dung các bài viết, trích xuất tiêu đề chính xác và tóm tắt nội dung.

# DỮ LIỆU ĐẦU VÀO
{articles_content}

# QUY ĐỊNH VỀ ĐỊNH DẠNG (FORMATTING RULES) - BẮT BUỘC
Để đảm bảo hiển thị đúng, bạn phải tuân thủ cú pháp Markdown sau:

1.  **ĐỐI VỚI NGUỒN VÀ CHUYÊN MỤC:**
    * Dòng đầu tiên phải là: TÊN ĐẦU BÁO | CHUYÊN MỤC
    * Viết thường, không in đậm
    * Ví dụ: Lao Động | Kinh tế

2.  **ĐỐI VỚI TIÊU ĐỀ (TITLE):**
    * Phải trích xuất **NGUYÊN VĂN** tiêu đề bài viết (H1).
    * Bắt buộc phải **IN ĐẬM** tiêu đề bằng cách kẹp giữa hai dấu sao (**).
    * Ví dụ đúng: **Đây là tiêu đề bài viết**

3.  **ĐỐI VỚI NỘI DUNG TÓM TẮT (BODY):**
    * Bắt đầu bằng dấu gạch đầu dòng (-)
    * Viết dưới dạng **văn bản thường (Normal Text)**.
    * Tuyệt đối KHÔNG in đậm, KHÔNG in nghiêng toàn bộ đoạn văn.
    * Chỉ viết một đoạn văn liền mạch, súc tích (khoảng 2-3 câu).

# VÍ DỤ MẪU (GOLDEN SAMPLE)
LAO ĐỘNG | KINH TẾ

**Văn phòng Đại diện Thương mại Mỹ tiếp tục hoãn áp thuế**

[https://laodong.vn/kinh-te/van-phong-dai-dien-thuong-mai-my-tiep-tuc-hoan-ap-thue-123456.ldo](https://laodong.vn/kinh-te/van-phong-dai-dien-thuong-mai-my-tiep-tuc-hoan-ap-thue-123456.ldo)

- Văn phòng Đại diện Thương mại Mỹ (USTR) thông báo tiếp tục hoãn áp đặt các biện pháp thuế quan trả đũa đối với hàng hóa từ Áo, Pháp, Italy, Tây Ban Nha, Anh và Thổ Nhĩ Kỳ. Quyết định này nhằm tạo thêm thời gian cho các cuộc đàm phán về một thỏa thuận thuế toàn cầu do OECD dẫn dắt được hoàn tất.

# HƯỚNG DẪN THỰC HIỆN (STEP-BY-STEP)
1.  Đọc nội dung từng bài viết.
2.  Viết dòng đầu tiên: TÊN ĐẦU BÁO | CHUYÊN MỤC (viết IN HOA toàn bộ).
3.  Thêm một dòng trống.
4.  Tìm tiêu đề chính của bài báo. Đặt nó trong định dạng: **Tiêu đề**.
5.  Thêm một dòng trống.
6.  Viết URL dưới dạng link: [url_thực_tế_của_bài_viết](url_thực_tế_của_bài_viết) - KHÔNG thêm chữ "URL:" phía trước.
7.  Thêm một dòng trống.
8.  Viết nội dung tóm tắt bắt đầu bằng dấu gạch đầu dòng (-) ở định dạng chữ thường.
9.  Sử dụng dấu "---" để ngăn cách giữa các bài báo khác nhau.

# ĐẦU RA MONG MUỐN (OUTPUT FORMAT)
[TÊN ĐẦU BÁO 1] | [CHUYÊN MỤC 1]

**[Tiêu đề bài báo 1]**

[url_bài_viết_1](url_bài_viết_1)

- [Nội dung tóm tắt bài báo 1 (chữ thường)]
---
[TÊN ĐẦU BÁO 2] | [CHUYÊN MỤC 2]

**[Tiêu đề bài báo 2]**

[url_bài_viết_2](url_bài_viết_2)

- [Nội dung tóm tắt bài báo 2 (chữ thường)]"""


# Prompt cho việc phân loại từng bài viết riêng lẻ
ARTICLE_CATEGORIZE_PROMPT = """Bạn là chuyên gia phân loại tin tức. Nhiệm vụ của bạn là phân tích tiêu đề và mô tả bài viết, sau đó xác định bài viết thuộc chuyên mục nào.

# CÁC CHUYÊN MỤC (4 NHÓM DUY NHẤT)

1. **KINH TẾ**: Kinh doanh, Thương mại, Doanh nghiệp, Xuất nhập khẩu, Sản xuất, Công nghiệp, Nông nghiệp, Du lịch, Khởi nghiệp
2. **TÀI CHÍNH**: Ngân hàng, Chứng khoán, Bất động sản, Tiền tệ, Đầu tư, Thuế, Bảo hiểm, Vàng
3. **XÃ HỘI**: Thời sự, Chính trị, Y tế, Giáo dục, Đời sống, Giao thông, Môi trường, Văn hóa, Thể thao, Giải trí, Khoa học
4. **PHÁP LUẬT**: An ninh, Trật tự, Hình sự, Tòa án, Vụ án, Tội phạm, Cảnh sát, Luật pháp

# DỮ LIỆU BÀI VIẾT
Tiêu đề: {title}
Mô tả: {description}

# YÊU CẦU
- Phân tích nội dung tiêu đề và mô tả
- Chọn 1 trong 4 chuyên mục phù hợp nhất
- Chỉ trả về TÊN CHUYÊN MỤC, không giải thích

# ĐẦU RA
Trả về CHÍNH XÁC một trong các giá trị sau (viết hoa, không dấu cách thừa):
KINH TẾ
TÀI CHÍNH
XÃ HỘI
PHÁP LUẬT
"""

