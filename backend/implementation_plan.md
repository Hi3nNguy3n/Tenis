# Kế hoạch Tái cấu trúc (Refactoring) Backend Saigon Tennis Tour

Kế hoạch này vạch ra lộ trình chi tiết để dọn dẹp cấu trúc, tối ưu hiệu năng và nâng cấp bảo mật hệ thống Backend mà không làm gián đoạn hay phá vỡ các chức năng hiện có của dự án.

---

## Ý kiến phản hồi cần Người dùng xác nhận (User Review Required)

> [!IMPORTANT]
> **Đồng bộ hóa với Frontend đối với API Upload:** 
> Việc đổi tên hoặc chuẩn hóa endpoint upload từ `/api/upload/image` thành `/api/upload/media` sẽ yêu cầu cập nhật lại đường dẫn tương ứng ở phía mã nguồn Frontend. Chúng tôi đề xuất tạo thêm endpoint `/api/upload/media` và giữ nguyên endpoint cũ `/api/upload/image` dưới dạng *Deprecated* để đảm bảo Frontend không bị lỗi trong quá trình chuyển dịch.

> [!WARNING]
> **Loại bỏ HTTPException khỏi tầng CRUD:**
> Sự thay đổi này sẽ làm thay đổi chữ ký trả về của các hàm CRUD (trả về `None` hoặc ném exception tùy chỉnh thay vì trả trực tiếp lỗi HTTP). Điều này yêu cầu cập nhật đồng loạt tại tầng API để bắt các exception này. Chúng tôi sẽ thực hiện theo từng module nhỏ để tránh sót lỗi.

---

## Các câu hỏi mở (Open Questions)

> [!NOTE]
> 1. **Kiểm thử tự động (Unit Test):** Dự án hiện tại đã có bộ kiểm thử tự động (Unit Tests/Integration Tests) nào chưa? Nếu có, hãy cung cấp lệnh chạy để chúng tôi có thể tự động kiểm định độ hồi quy (regression) của code sau khi sửa.
> 2. **Cấu hình DB Startup:** Bạn có đồng ý tắt việc tự động gọi `create_all()` ở môi trường Production thông qua biến môi trường (ví dụ: `ENV=production`) và chỉ cho phép chạy qua Alembic migrations không?

---

## Đề xuất Thay đổi (Proposed Changes)

Lộ trình được chia làm 5 giai đoạn thực hiện tuần tự để kiểm soát rủi ro:

### Giai đoạn 1: Chuẩn hóa Mã hóa Ký tự, Dọn dẹp Log và Exception Handler
*Mục tiêu: Sửa nhanh các lỗi Clean code, rò rỉ OTP và bảo mật mà không thay đổi cấu trúc file.*

#### [MODIFY] [main.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/main.py)
- Cập nhật Exception Handler của `Exception` chung: Không trả trực tiếp `str(exc)` (rò rỉ stack trace) ra client. Thay vào đó, ghi log lỗi hệ thống và trả về thông báo thân thiện `"Đã xảy ra lỗi hệ thống. Vui lòng liên hệ quản trị viên."` trên môi trường production.

#### [MODIFY] [auth.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/api/auth.py)
- Xóa bỏ các dòng debug `print` in mã OTP ra console tại các hàm gửi OTP và verify OTP để đảm bảo an toàn thông tin.

#### [MODIFY] [crud_tournament.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/crud/crud_tournament.py)
- Chuyển đổi định dạng file (Encoding) từ Windows-1252/ISO-8859-1 về UTF-8 chuẩn để hiển thị đúng các comment tiếng Việt bị lỗi ký tự lạ (Mojibake).

---

### Giai đoạn 2: Tách biệt Business Logic và Báo cáo ra lớp Dịch vụ (Services Layer)
*Mục tiêu: Giải quyết vấn đề phình to và vi phạm SRP của file `crud_tournament.py`.*

#### [NEW] [excel_service.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/services/excel_service.py)
- Di chuyển toàn bộ hàm `export_tournament_data_to_excel` từ `crud_tournament.py` sang đây. Tầng này sẽ chịu trách nhiệm định dạng bảng biểu bằng `openpyxl`.

#### [NEW] [tournament_draw_service.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/services/tournament_draw_service.py)
- Di chuyển các hàm sinh nhánh đấu và xếp lịch đấu phức tạp khỏi tầng CRUD:
  * `generate_knockout_draw`
  * `generate_round_robin_draw`
  * `generate_playoff_draw`
  * Các hàm phụ trợ kết nối nhánh: `_auto_link_manual_match`, `validate_next_match_assignment`, `_advance_winner_to_next_match`.

#### [NEW] [elo_service.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/services/elo_service.py)
- Di chuyển logic tính toán điểm ELO và cập nhật chỉ số thắng/thua của VĐV (`calculate_elo_and_update_match`) ra khỏi `crud_tournament.py`.

#### [MODIFY] [crud_tournament.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/crud/crud_tournament.py)
- Xóa bỏ các hàm thuật toán vẽ nhánh, xuất Excel và tính ELO đã được chuyển đi. Chỉ giữ lại các hàm CRUD thuần túy tác động DB của Giải đấu.

---

### Giai đoạn 3: Gom nhóm và làm sạch Tầng CRUD của Trận đấu (Match CRUD)
*Mục tiêu: Đưa các hàm xử lý Match về đúng vị trí.*

#### [MODIFY] [crud_match.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/crud/crud_match.py)
- Tiếp nhận các hàm CRUD quản lý trận đấu từ `crud_tournament.py` chuyển sang:
  * `create_manual_match_db` (đổi tên cho nhất quán)
  * `update_match_admin_db`
  * `delete_match_from_draw_db`
  * `schedule_match_db`
  * `get_all_matches_detail`

---

### Giai đoạn 4: Dọn dẹp Logic DB trong Tầng API (API Clean-up & N+1 Fix)
*Mục tiêu: Loại bỏ hoàn toàn các câu query DB trực tiếp từ API routers.*

#### [MODIFY] [matches.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/api/matches.py)
- Viết lại hàm `get_list_matches` trong `crud_match.py` để sử dụng `joinedload` liên kết các bảng `Tournament`, `Court`, `TournamentCategory`, `Registration`, `Player`, `User` trong 1 câu JOIN duy nhất.
- Thay thế toàn bộ logic lặp query trong hàm `list_matches` của router bằng cách gọi hàm CRUD tối ưu trên.

#### [MODIFY] [registrations.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/api/registrations.py)
- Di chuyển các thao tác DB trực tiếp (như thêm VĐV vào giải tại `admin_add_player_to_tournament` và thu tiền tại `admin_pay_and_check_in`) xuống các hàm tương ứng trong `crud_registration.py`.

#### [MODIFY] [tournaments.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/api/tournaments.py)
- Di chuyển logic validate đăng ký cực kỳ dài của `validate_registration_early` xuống một lớp Validator chuyên biệt (`app/services/registration_validator.py` [NEW]).
- Tạo các hàm CRUD chuẩn cho `TournamentCategory` trong `crud_tournament.py` và gọi từ Router thay vì gọi `db.add` trực tiếp.

---

### Giai đoạn 5: Tách rời FastAPI khỏi CRUD & Chuẩn hóa API Contract
*Mục tiêu: Đạt tiêu chuẩn phân tầng sạch hoàn toàn.*

#### [MODIFY] [crud/*.py] (Tất cả file CRUD)
- Thay thế việc `raise HTTPException` bằng việc ném ra các lỗi tùy chỉnh (ví dụ: `class EntityNotFoundError(Exception)`).

#### [MODIFY] [api/*.py] (Tất cả Router)
- Bổ sung khối lệnh `try...except` hoặc sử dụng FastAPI Exception Handlers chung để bắt các lỗi tùy chỉnh từ tầng CRUD và chuyển thành `HTTPException` với mã trạng thái phù hợp.

#### [MODIFY] [upload.py](file:///d:/Thực%20Tập/Dự%20án%203%20-%20Tennis/clone/Tenis/backend/app/api/upload.py)
- Bổ sung endpoint `/api/upload/media` hỗ trợ cả hình ảnh và video. Đánh dấu endpoint cũ `/image` là deprecated để chuẩn bị loại bỏ sau khi Frontend đã cập nhật.

---

## Kế hoạch Kiểm tra & Nghiệm thu (Verification Plan)

Hệ thống bắt buộc phải vượt qua tất cả các bài thử nghiệm hồi quy sau đây trước khi được coi là hoàn thành tái cấu trúc:

### Thử nghiệm Thủ công (Manual Verification)
1. **Luồng Đăng ký & Đăng nhập**: Gửi OTP về email và thực hiện đăng ký tài khoản mới. Kiểm tra xem OTP có bị in ra log server hay không.
2. **Luồng Quản lý Giải đấu & Nhánh đấu**:
   - Tạo giải đấu mới qua trang Admin.
   - Thêm nội dung thi đấu (Category) cho giải.
   - Sinh nhánh đấu ngẫu nhiên (Knockout/Round Robin) và kiểm tra sơ đồ thi đấu hiển thị trên UI.
3. **Luồng Trận đấu & Điểm ELO**:
   - Xếp lịch đấu và gán sân cho trận đấu.
   - Nhập tỉ số kết quả trận đấu từ trang Admin, kiểm tra xem điểm ELO của hai bên thắng/thua và các chỉ số thống kê (wins, losses) có được cập nhật chính xác hay không.
4. **Luồng Báo cáo**:
   - Xuất file Excel báo cáo giải đấu từ trang Admin. Tải về và kiểm tra tính toàn vẹn của dữ liệu trong file Excel.
5. **Luồng Upload**:
   - Thử tải lên hình ảnh định dạng PNG/JPG và video định dạng MP4 có thời lượng dưới 60 giây. Kiểm tra xem có bị chặn file lỗi không.
