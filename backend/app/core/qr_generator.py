# backend/app/core/qr_generator.py
import qrcode
from io import BytesIO
import cloudinary.uploader

def generate_registration_qr(registration_id: int, tournament_name: str):
    # 1. Tạo nội dung QR (Ví dụ: Chứa ID để Admin quét check-in)
    qr_data = f"STT_REG_{registration_id}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # 2. Lưu ảnh vào bộ nhớ tạm (BytesIO)
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # 3. Upload lên Cloudinary
    result = cloudinary.uploader.upload(
        img_byte_arr,
        folder="saigon_tennis/qrcodes",
        public_id=f"qr_reg_{registration_id}"
    )
    
    return result.get("secure_url")