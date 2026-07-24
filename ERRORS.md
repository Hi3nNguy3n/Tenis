# ERRORS.md - Nhật ký Lỗi & Học tập từ sự cố

Hồ sơ ghi nhận các lỗi xảy ra trong quá trình phát triển để tránh lặp lại.

---

## [2026-06-29 17:20] - FastAPIError: Invalid args for response field (Session in Pydantic)

- **Type**: Syntax/Logic
- **Severity**: High
- **File**: `backend/app/api/players.py:65`
- **Agent**: jarvis
- **Root Cause**: Khi chèn hàm helper `get_recent_match_result` vào file, script tự động replace đã đặt hàm helper này ngay sau decorator `@router.get("/list")` (vốn thuộc về `list_players`). FastAPI quét decorator và coi `get_recent_match_result` là endpoint, sau đó báo lỗi vì tham số `db: Session` không có `Depends` và không phải là kiểu Pydantic hợp lệ.
- **Error Message**: 
  ```
  fastapi.exceptions.FastAPIError: Invalid args for response field! Hint: check that <class 'sqlalchemy.orm.session.Session'> is a valid Pydantic field type.
  ```
- **Fix Applied**: Di chuyển decorator `@router.get("/list")` xuống đúng vị trí trước khai báo hàm `list_players` và đưa `get_recent_match_result` trở về thành hàm helper bình thường.
- **Prevention**: Khi dùng script tự động replace code, cần kiểm tra chính xác cấu trúc ngữ cảnh xung quanh để tránh làm dịch chuyển hoặc đảo lộn thứ tự các decorators của API router.
- **Status**: Fixed

---
