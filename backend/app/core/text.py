# backend/app/utils/text.py
import re
import unicodedata

def slugify(text: str) -> str:
    """Tạo slug an toàn từ chuỗi tiếng Việt."""
    if not text:
        return ""
    # Xóa dấu tiếng Việt
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    # Chuyển thành chữ thường
    text = text.lower()
    # Chỉ giữ lại chữ cái, số và dấu gạch ngang
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    # Thay khoảng trắng bằng dấu gạch ngang
    text = re.sub(r'[\s-]+', '-', text).strip('-')
    return text