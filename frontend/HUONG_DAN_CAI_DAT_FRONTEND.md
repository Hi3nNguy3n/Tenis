# HƯỚNG DẪN CÀI ĐẶT VÀ SỬ DỤNG MÃ NGUỒN FRONTEND (Saigontennistours)

Tài liệu này hướng dẫn cách thiết lập môi trường, cài đặt thư viện và chạy mã nguồn Frontend cho dự án Saigontennistours. Đây là tài liệu lý tưởng để bạn gửi cho bạn bè hoặc thành viên trong nhóm để họ có thể chạy dự án trên máy của mình.

---

## 1. Yêu cầu hệ thống (Prerequisites)
Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt các phần mềm sau:
- **Node.js**: Phiên bản khuyến nghị là từ v18 trở lên. Có thể tải tại [nodejs.org](https://nodejs.org/).
- **NPM (Node Package Manager)**: Được cài đặt kèm theo khi bạn cài Node.js.
- **Trình soạn thảo mã (IDE)**: Khuyến nghị sử dụng Visual Studio Code (VS Code).

---

## 2. Các thư viện chính (Dependencies)
Dự án sử dụng các công nghệ và thư viện hiện đại sau:
- **Vue.js 3**: Framework cốt lõi để xây dựng giao diện.
- **Vite**: Công cụ đóng gói (bundler) siêu tốc độ.
- **Element Plus**: Thư viện UI Component để thiết kế giao diện (nút bấm, bảng, dialog,...).
- **Pinia**: Quản lý trạng thái (State Management) để lưu trữ thông tin đăng nhập, v.v.
- **Vue Router**: Xử lý việc chuyển trang (Routing) giữa các màn hình.
- **vue-i18n** / **Hệ thống Locale custom**: Quản lý Đa ngôn ngữ (Anh / Việt).
- **jsQR**: Hỗ trợ tính năng quét mã QR.
- **file-saver**: Hỗ trợ xuất file (ví dụ xuất báo cáo Excel).

---

## 3. Các bước cài đặt và chạy dự án

Hãy làm theo tuần tự các bước sau trong ứng dụng Terminal / Command Prompt:

### Bước 3.1: Mở thư mục chứa mã nguồn Frontend
Sử dụng Terminal trong VS Code hoặc Command Prompt di chuyển đến đúng thư mục `frontend`:
```bash
cd duong_dan_toi_thu_muc/Tenis/frontend
```

### Bước 3.2: Cài đặt thư viện (Install Dependencies)
Chạy lệnh sau để tải và cài đặt toàn bộ các thư viện được định nghĩa trong `package.json`:
```bash
npm install
```
*(Lưu ý: Quá trình này có thể mất vài phút tùy thuộc vào tốc độ mạng).*

### Bước 3.3: Khởi chạy dự án (Run the Dev Server)
Sau khi cài đặt xong, hãy chạy lệnh sau để bật server phát triển:
```bash
npm run dev
```

Khi server chạy thành công, Terminal sẽ hiển thị đường link để bạn truy cập vào web. Thông thường sẽ là:
👉 **http://127.0.0.1:5173** (hoặc `http://localhost:5173`)

Hãy giữ Terminal chạy (không tắt) trong suốt quá trình bạn thao tác trên web.

---

## 4. Cấu trúc Đa ngôn ngữ (Localization - i18n)
Dự án đã được tích hợp hệ thống đa ngôn ngữ (Tiếng Việt và Tiếng Anh) một cách cực kỳ bài bản. Hệ thống ngôn ngữ được chia module (module-based) để dễ quản lý.

**Thư mục lưu trữ ngôn ngữ:**
- `src/locales/vi/` (Tiếng Việt)
- `src/locales/en/` (Tiếng Anh)

Đặc biệt ở giao diện Quản trị (Admin), các từ vựng đã được chia nhỏ theo từng màn hình (menu) vào thư mục `modules/`:
- `src/locales/vi/admin/modules/dashboard.js` (Cho màn hình chính)
- `src/locales/vi/admin/modules/players.js` (Cho quản lý Vận động viên)
- `src/locales/vi/admin/modules/tournaments.js` (Cho quản lý Giải đấu)
- ... (Các tệp khác tương ứng với từng màn hình)

**Cách thêm hoặc sửa từ vựng mới:**
1. Mở file `.js` tương ứng trong `modules` (ví dụ `players.js`).
2. Sửa nội dung của một khóa (key) hoặc thêm khóa mới.
3. Đảm bảo thực hiện thay đổi tương tự ở cả thư mục `vi` và `en` để hệ thống không bị lỗi thiếu chữ khi chuyển ngôn ngữ.

---

## 5. Lưu ý quan trọng
- **Đừng quên Backend**: Frontend này được thiết kế để gọi API tới Backend. Đảm bảo rằng Backend của bạn cũng đang được chạy và các đường dẫn API (`/api/...`) trong tệp `src/services/apiClient.js` (hoặc tương tự) khớp với địa chỉ của Backend.
- Nếu bạn gặp lỗi không tìm thấy module khi chạy `npm run dev`, hãy thử xóa thư mục `node_modules` và file `package-lock.json`, sau đó chạy lại lệnh `npm install`.
