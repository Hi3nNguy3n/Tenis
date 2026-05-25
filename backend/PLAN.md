# Kế Hoạch Triển Khai Refactor Backend An Toàn

## Summary
Triển khai theo `implementation_plan_6` và `task_2`, ưu tiên **không phá hệ thống đang chạy**. Trọng tâm là làm mỏng API router, đưa truy vấn DB/logic thao tác dữ liệu xuống CRUD từng module, giữ nguyên URL, response JSON, DB schema và toàn bộ nghiệp vụ nhạy cảm như bốc thăm, ELO, playoff, thanh toán/VNPay.

Không thực hiện đại phẫu kiến trúc. Không đổi public CRUD function đang được dùng. Không cải cách `HTTPException` trong CRUD ở đợt này.

## Key Changes
- **Phase 0: Baseline + API Contract Snapshot**
  - Chạy `python -m compileall backend/app` và `npm run build`.
  - Tạo snapshot request/response/status cho các API: matches, tournaments matches/admin-update/public-bracket/standings/registrations/validate-registration, registrations, upload, marketing.
  - Snapshot là chuẩn so sánh bắt buộc sau mỗi refactor.

- **Phase 1: Security Quick-Fix**
  - Xóa log debug OTP trong `auth.py`.
  - Sửa global exception handler trong `main.py` để log server-side bằng `logger.exception`, client chỉ nhận thông báo lỗi chung.
  - Không đổi logic OTP/register/login.

- **Phase 2: Upload Tương Thích Ngược**
  - Thêm `/api/upload/media`.
  - Giữ nguyên `/api/upload/image`.
  - Dùng chung helper validate ảnh/video: ảnh tối đa 10MB, video tối đa 80MB và 60 giây.
  - Không bắt frontend đổi endpoint ngay.

- **Phase 3: Dọn API Xuống CRUD Theo Module**
  - `matches.py`: chuyển logic query/format danh sách trận xuống `crud_match.py`, tối ưu N+1 bằng `joinedload`, explicit joins hoặc bulk prefetch tùy relationship thực tế. Response JSON phải khớp snapshot 100%.
  - `registrations.py`: chuyển add-player, check-in, pay-and-check-in, payment status mutation xuống `crud_registration.py`; giữ nguyên behavior và response.
  - `tournaments.py`: tách riêng category CRUD trước, sau đó mới tách `validate_registration_early`; giữ nguyên logic validate đơn/đôi/giới tính/partner và thông báo lỗi.
  - `challenges.py` và `payments.py`: chỉ rà soát; với `payments.py`, không chỉnh VNPay/QR/callback nếu không có dữ liệu test đủ tin cậy.

- **Phase 4-6: Optional / Sau Khi API Ổn**
  - Phase 4 Excel service là optional; nếu làm thì giữ wrapper cũ trong `crud_tournament.py`.
  - Phase 5 thêm `AUTO_CREATE_TABLES` nhưng không làm lệch dev/prod hiện tại.
  - Phase 6 chỉ sửa encoding cục bộ ở file đã chạm, không sửa hàng loạt.

## Test Plan
- Sau **mỗi phase** bắt buộc chạy:
  - `python -m compileall backend/app`
  - `npm run build` trong `frontend`
- Sau các phase có API thay đổi, so sánh response JSON với snapshot Phase 0.
- Kiểm thử nghiệp vụ bắt buộc:
  - OTP/register/login không rò OTP ở log.
  - Upload ảnh/video hợp lệ thành công; video quá 60 giây bị chặn.
  - VĐV đăng ký giải đơn/đôi, tự hủy đơn, admin duyệt đơn.
  - Admin thu tiền mặt và check-in tạo payment record đúng.
  - Bốc thăm knockout/round robin vẫn hoạt động.
  - Điều hành trận, cập nhật tỉ số, người thắng đi tiếp, ELO/wins/losses không cộng trùng khi cập nhật lại trận completed.
  - Marketing banner/sponsor và ATP stats vẫn hiển thị bình thường.
  - Xuất Excel vẫn hoạt động nếu Phase 4 được thực hiện.

## Assumptions
- Triển khai từng phase/commit độc lập; lỗi phase nào thì revert phase đó, không vá chồng sang phase sau.
- Không đổi URL API, response shape, status code, hoặc DB schema trừ khi người dùng phê duyệt riêng.
- Draw/ELO/playoff giữ nguyên trong `crud_tournament.py` trong đợt này.
- `HTTPException` trong CRUD giữ nguyên, chưa chuyển sang domain exceptions.
- `task_2` là checklist thực thi chính; chỉ cần chỉnh nhẹ lệnh compile thống nhất thành `python -m compileall backend/app`.
