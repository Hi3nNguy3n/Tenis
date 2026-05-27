# 🚀 Hướng Dẫn Triển Khai (Deploy) Saigon Tennis Lên VPS Bằng Docker

Tài liệu này cung cấp hướng dẫn chi tiết, từng bước một để bạn tự động hóa quy trình đóng gói và triển khai (deploy) toàn bộ hệ thống Saigon Tennis lên VPS chạy Linux (Ubuntu/Debian...) bằng **Docker** và **Docker Compose**.

---

## 🏗️ 1. Kiến Trúc Triển Khai & Giải Pháp Tránh Trùng Cổng (Port Conflict)

Để tránh xung đột với rất nhiều container hiện có trên VPS của bạn (đang chiếm giữ các dải cổng như `3001-3005`, `3010`, `3011`, `5001-5005`, `6006-6009`, `7001-7011`, `8081-8088`, `3307`), hệ thống Saigon Tennis được cấu hình theo kiến trúc **Mạng Cô Lập Nội Bộ (Isolated Docker Network)** cực kỳ an toàn:

```mermaid
graph TD
    Client[Trình duyệt Khách hàng] <-->|Cổng Công Khai 3012| Frontend[Frontend Container: Nginx Gateway - Port 3012]
    
    subgraph Docker Network
        Frontend -->|Phục vụ File Tĩnh| Static[Vue 3 SPA Assets]
        Frontend -->|Reverse Proxy /api/*| Backend[Backend Container: FastAPI - Port 8000]
        Frontend -->|Reverse Proxy /api/chat/* & WebSockets| Chat[Chat Service Container: FastAPI - Port 8001]
        
        Backend <-->|Kết nối DB| Postgres[Database Container: PostgreSQL 15 - Port 5432]
        Chat <-->|Kết nối DB| Postgres
    end
```

### 🔒 Giải pháp thiết lập cổng thông minh:
1. **Né Trùng Cổng 100%**: Thay vì dùng cổng mặc định `80`, **Frontend (Nginx Gateway)** được map ra cổng **`3012`** trên host VPS (Né được cổng `3011` của `napzed_frontend`, cổng `3010` của `speedlight_storage_frontend_1`, và các cổng khác).
2. **Ẩn Cổng Dịch Vụ**: Các cổng của **Backend (8000)**, **Chat Service (8001)** và **Database (5432)** hoàn toàn **KHÔNG map ra ngoài host VPS** (đã loại bỏ phần `ports` ở host). Chúng được ẩn hoàn toàn sau mạng nội bộ của Docker.
3. **Không Bị Lỗi CORS**: Toàn bộ API chính, API Chat và WebSockets đều đi qua một cổng duy nhất là **Nginx Gateway (cổng 3012 của VPS)** dưới dạng các đường dẫn tương đối (`/api/`, `/api/chat/`).

---

## 🛠️ 2. Chuẩn Bị Môi Trường Trên VPS

### Bước 2.1: Cập nhật hệ thống và cài đặt Docker & Docker Compose
Đăng nhập vào VPS của bạn qua SSH và chạy các lệnh sau:

```bash
# Cập nhật danh sách gói
sudo apt update && sudo apt upgrade -y

# Cài đặt các gói hỗ trợ
sudo apt install -y curl git apt-transport-https ca-certificates gnupg lsb-release

# Cài đặt Docker Engine bản mới nhất
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Cài đặt Docker Compose CLI
sudo apt install -y docker-compose-plugin

# Kiểm tra phiên bản cài đặt thành công
docker --version
docker compose version
```

### Bước 2.2: Clone mã nguồn dự án lên VPS
```bash
git clone <URL_KHO_MA_NGUON_CUA_BAN> tennis-project
cd tennis-project
```

---

## ⚙️ 3. Cấu Hình Biến Môi Trường (`.env`)

Bạn cần thiết lập các tệp cấu hình `.env` cho Backend và Chat Service trước khi khởi chạy Docker Compose.

### KỊCH BẢN A: Sử dụng Database PostgreSQL TỰ HOST trong Docker (Khuyên Dùng cho VPS Mới)
Phương án này tự động khởi tạo cơ sở dữ liệu PostgreSQL ngay bên trong Docker, giúp dự án độc lập hoàn toàn.

#### 1. Cấu hình tệp `backend/.env`
Tạo/sửa tệp `backend/.env` với nội dung sau:
```env
# --- DATABASE CONFIG (Docker Container) ---
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=DB_saigontenis
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://admin:admin123@db:5432/DB_saigontenis

# --- AUTHENTICATION ---
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256

# --- CLOUDINARY (Để upload ảnh) ---
CLOUDINARY_CLOUD_NAME=dfs9o3bny
CLOUDINARY_API_KEY=513954498387371
CLOUDINARY_API_SECRET=Brss7LepXirwlYHuPWMfnsLguko

# --- MAIL CONFIG ---
MAIL_USERNAME=minhphu25102005@gmail.com
MAIL_PASSWORD=gfnt djph anuf vdxi
MAIL_FROM=minhphu25102005@gmail.com

```

#### 2. Cấu hình tệp `chat_service/.env`
Tạo/sửa tệp `chat_service/.env` với nội dung sau:
```env
# --- DATABASE CONFIG (Dùng chung DB của Docker ở trên) ---
DATABASE_URL=postgresql://admin:admin123@db:5432/DB_saigontenis

# --- SECURITY ---
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
```

---

### KỊCH BẢN B: Kết nối Database PostgreSQL BÊN NGOÀI (Ví dụ máy chủ 125.234.102.243)
Nếu bạn muốn sử dụng Database PostgreSQL đã chạy sẵn ở một Server/VPS khác.

#### 1. Cấu hình tệp `backend/.env`
```env
# --- DATABASE CONFIG (External Server) ---
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=DB_saigontenis
POSTGRES_HOST=125.234.102.243
POSTGRES_PORT=5432
# Lưu ý: Nếu password chứa ký tự đặc biệt như '@', hãy URL-encode nó (ví dụ: admin@123 -> admin%40123)
DATABASE_URL=postgresql://admin:admin%40123@125.234.102.243:5432/DB_saigontenis

# --- CÁC CẤU HÌNH KHÁC GIỮ NGUYÊN NHƯ KỊCH BẢN A ---
...
```

#### 2. Cấu hình tệp `chat_service/.env`
```env
DATABASE_URL=postgresql://admin:admin%40123@125.234.102.243:5432/DB_tenischat
SECRET_KEY=09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7
ALGORITHM=HS256
```

*(Lưu ý: Nếu sử dụng Kịch bản B, bạn có thể comment hoặc xoá service `db` ra khỏi tệp `docker-compose.yml` ở thư mục gốc để tiết kiệm tài nguyên VPS).*

---

## 🚀 4. Triển Khai Hệ Thống Bằng Docker Compose

Sau khi đã hoàn tất cấu hình các file `.env`, bạn chỉ cần chạy đúng các lệnh dưới đây.

### Bước 4.1: Build và Triển khai

```bash
# Build và chạy ngầm dự án
docker compose build
docker compose up -d
```

> Frontend sẽ tự dùng API tương đối `/api/...` và tự chọn WebSocket `ws://` hoặc `wss://` theo domain hiện tại. Không build cứng `localhost`, IP VPS, hoặc `http://` khi chạy production HTTPS.

> **Lưu ý**: Quá trình build lần đầu tiên có thể mất từ 3 - 5 phút vì Docker cần tải các base image (Node, Python, Postgres) và cài đặt các thư viện `npm` & `pip`.

### Bước 4.2: Kiểm tra trạng thái các container
Kiểm tra xem toàn bộ các container đã ở trạng thái `running` hay chưa bằng lệnh:
```bash
docker compose ps
```
Kết quả mong đợi:
```text
NAME                     IMAGE                  COMMAND                  SERVICE        CREATED         STATUS                   PORTS
tennis_backend           tennis-backend         "sh -c 'uvicorn app.…"   backend        2 minutes ago   Up 2 minutes             
tennis_chat_service      tennis-chat_service    "sh -c 'uvicorn main…"   chat_service   2 minutes ago   Up 2 minutes             
tennis_db                postgres:15-alpine     "docker-entrypoint.s…"   db             2 minutes ago   Up 2 minutes (healthy)   
tennis_frontend          tennis-frontend        "/docker-entrypoint.…"   frontend       2 minutes ago   Up 2 minutes             0.0.0.0:3012->80/tcp, :::3012->80/tcp
```
*(Bạn sẽ thấy chỉ duy nhất cổng `3012` của frontend được map ra bên ngoài, các cổng khác hoàn toàn ẩn để bảo mật hệ thống).*

---

## 🛠️ 5. Các Lệnh Quản Trị Hệ Thống Tiện Ích

Trong quá trình vận hành hệ thống trên VPS, bạn sẽ cần sử dụng các lệnh dưới đây:

### Xem Logs (Nhật ký hoạt động) để Debug:
```bash
# Xem log của tất cả các service theo thời gian thực
docker compose logs -f

# Chỉ xem log của Backend chính
docker compose logs -f backend

# Chỉ xem log của Chat Service
docker compose logs -f chat_service
```

### Khởi động lại hệ thống:
```bash
# Restart toàn bộ container
docker compose restart

# Chỉ restart riêng Frontend (ví dụ sau khi cập nhật giao diện)
docker compose restart frontend
```

### Dừng hệ thống:
```bash
# Dừng các container nhưng giữ lại dữ liệu trong Database Volume
docker compose down

# Dừng và xóa sạch toàn bộ container cùng Database Volume (CẢNH BÁO: Mất sạch dữ liệu)
docker compose down -v
```

---

## 🔒 6. Cấu Hình SSL/HTTPS Miễn Phí Với Let's Encrypt (Nâng Cao)

Khi chạy sản phẩm thực tế (Production), bạn bắt buộc phải cấu hình HTTPS để bảo mật thông tin đăng nhập và chạy được WebSocket tin cậy (`wss://`).

Do bạn có nhiều container chạy các cổng khác nhau trên VPS, phương án tối ưu nhất là sử dụng một **Nginx Reverse Proxy tổng trên host VPS** (hoặc dùng **Nginx Proxy Manager** chạy bằng Docker).
Khi đó:
1. Bạn trỏ domain `tennis.yourdomain.com` về IP VPS.
2. Cấu hình Nginx tổng trỏ domain `tennis.yourdomain.com` vào cổng **`3012`** của VPS.
3. Kích hoạt SSL Let's Encrypt cho domain đó. Lúc này, bạn sẽ truy cập web an toàn qua `https://tennis.yourdomain.com` và WebSocket tự động chạy dạng `wss://tennis.yourdomain.com/api/chat/ws`.

---

Chúc bạn triển khai dự án **Saigon Tennis** lên VPS thành công rực rỡ! Nếu gặp bất kỳ khó khăn nào trong quá trình cài đặt, hãy gọi `jarvis` để được hỗ trợ gỡ lỗi ngay lập tức. 🎾🔥
