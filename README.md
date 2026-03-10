# 📚 BookStore Microservices — Assignment 5

Dự án **BookStore Microservices** xây dựng một hệ thống bán sách thương mại điện tử trực tuyến, áp dụng **Kiến trúc Hướng Dịch vụ (Microservices Architecture)**. Hệ thống bao gồm 10 dịch vụ Microservices độc lập và 1 API Gateway (BFF), mỗi dịch vụ được tích hợp Cơ sở dữ liệu riêng, hoạt động song song qua cấu hình Docker Compose.

Tài liệu này cung cấp cái nhìn tổng quan về thiết kế kiến trúc, các mô hình (patterns) đã được triển khai, và cách khởi chạy hệ thống nội hạt (local environment).

---

## 1. Điểm nhấn Kiến trúc (Architecture Highlights)

Trong phiên bản **Assignment 5**, hệ thống sử dụng giao thức **REST HTTP** làm phương thức giao tiếp chính (Synchronous Communication) giữa các dịch vụ. 

### 1.1 API Gateway (BFF & Đầu mối duy nhất)
- Trình duyệt khách hàng (Browsers) **chỉ** giao tiếp trực tiếp với **API Gateway** tại thiết bị cuối (cổng `18000`). Bản thân API Gateway không lưu trữ cơ sở dữ liệu (ngoại trừ Session), mà nó hoạt động như một Backend-for-Frontend (BFF).
- Gateway sẽ thực hiện các lời gọi hàm API tới các service nội bộ ở phía sau thông qua thư viện `requests` của Python. Thay vì phơi bày API cho client tự gọi, Gateway gọi và lấy dữ liệu, sau đó Server-Side Rendering (SSR) render trực tiếp vào HTML Template trước khi trả kết quả nguyên khối cho user.

### 1.2 Mạng ảo Docker (Internal Network)
- Toàn bộ các dịch vụ nội bộ cấu hình cùng chung một mạng ảo Docker có tên `bookstore-network`. 
- Sự định tuyến này cho phép chúng gọi ngang cấp với nhau qua tên service (DNS nội bộ do Docker dựng lên) thay vì phải nhớ địa chỉ IP cứng. Ví dụ: URL kết nối là `http://book-service:8000/books/`.

### 1.3 Database-per-Service
Mỗi microservice sở hữu một logical database riêng (được tạo phân chia tự động bên trong cụm PostgreSQL qua `init_db.sql`). Thiết kế "cơ sở dữ liệu mỗi dịch vụ" này triệt tiêu hoàn toàn sự lệ thuộc khóa ngoại (Foreign key coupling) xuyên bảng, đảm bảo tính tự trị (Autonomy).

---

## 2. Mô hình Thiết kế (Design Patterns)

### 2.1 Cơ chế Điều phối Đặt hàng (Orchestration Pattern)
Hệ thống áp dụng mô hình **Orchestration** tại dịch vụ Đơn hàng (`order-service`).
- Khi khách hàng nhấn nút "Đặt hàng", `order-service` sẽ đóng vai trò là "nhạc trưởng".
- Lần lượt, nó sẽ thực hiện các cuộc gọi đồng bộ (REST HTTP) tới `cart-service` để lấy danh sách mục hàng giỏ, tới `book-service` để chốt & xác nhận giá bán, sau đó gọi `pay-service` để tạo mã thanh toán, và `ship-service` để tạo mã vận chuyển hoàn tất quy trình.
- Ưu điểm của mô hình này: Luồng nghiệp vụ được tập trung điều hành tại một nơi duy nhất quản lý, rất dễ dàng theo dõi dòng chảy trạng thái đơn hàng (Saga Orchestration sơ khai).

### 2.2 Xử lý lỗi & Khả năng chịu lỗi (Resilience Design)
Để ngăn chặn tình trạng **sập dây chuyền (Cascading Failure)** – một nhược điểm chí mạng trong ứng dụng mạng phân tán – hệ thống đã triển khai các cơ chế phòng vệ cơ bản (Anti-Corruption):
- **Timeout & Try-Except (Circuit Breaker tĩnh):** Tại Gateway API, mọi lời gọi yêu cầu lấy dữ liệu tới Service con (`_get()`, `_post()`) đều được cấu hình thời gian bóp cò (Timeout định trước 5 giây). Đặc biệt là với các dịch vụ phụ trợ như `comment-service` hoặc `manager-service`. 
- Nếu dịch vụ bị nghẽn mạng ảo hoặc sập tiến trình, Gateway sẽ lập tức bắt ngoại lệ (Catch Exception) và ngầm thay thế bằng dữ liệu mặc định rỗng ([] hoặc lỗi cục bộ). Việc này giúp cấu trúc các thành phần cốt lõi của HTML web không bị tê liệt. Một lỗi đánh giá không làm hỏng trải nghiệm Trang chủ mua hàng.

---

## 3. Bản đồ Microservices (Port Mapping)

Mọi service bên trong Internal có port là `8000`, tuy nhiên Docker expose chúng ra Host theo cấu trúc sau để bạn dễ dàng test API chéo:

| Dịch vụ (Service) | Chức năng | Port | Schema / API Docs (Swagger UI) |
|---|---|---|---|
| `api-gateway` | SSR, Proxy kết nối tổng | 18000 | `/api/docs/` (Tổng hợp mọi schema) |
| `customer-service`| Xác thực (auth, token), JWT | 18001 | `/api/docs/` |
| `book-service` | Quản lý kho Sách, Stock | 18002 | `/api/docs/` |
| `cart-service` | Quản lý Giỏ hàng ngầm | 18003 | `/api/docs/` |
| `order-service` | Nhạc trưởng Orchestrator | 18004 | `/api/docs/` |
| `pay-service` | Trạng thái Thanh toán | 18005 | `/api/docs/` |
| `ship-service` | Quản lý Vận chuyển & Địa chỉ | 18006 | `/api/docs/` |
| `comment-service` | Đánh giá sao, Bình luận | 18007 | `/api/docs/` |
| `catalog-service` | Danh mục Category, Thể loại | 18008 | `/api/docs/` |
| `manager-service` | Promotions (Khuyến mãi), Supply | 18010 | `/api/docs/` |
| `postgres-db` | RDBMS chung - Shared Container | 15432 | Connection: `localhost:15432` |

---

## 4. Phân Quyền Xã Hội (Role-based Authentication)

Việc kiểm soát truy cập (RBAC) được xác nhận thông qua Token tĩnh ở `customer-service` và được API Gateway lưu Cookie bảo toàn session trạng thái HTML qua:

- **Customer:** Được duyệt sách, thêm vào giỏ, đặt đơn hàng, đánh giá và xem lịch sử đơn hàng cá nhân.
- **Staff (Nhân viên):** Có nghiệp vụ về dữ liệu thô: Edit thông tin Sách (Book Service), Cập nhật kho hàng (Supply/Inventory Manager Service), và Đổi trạng thái xử lý đơn hàng (Pending -> Shipping).
- **Manager (Người quản lý):** Quyền lớn nhất ở tầm C-Levels: Xem Dashboard chỉ số chung, khởi động chiến dịch giảm giá (Promotions Manager Service), và Sửa đổi cây phân loại sách gốc (Catalog Service).

| Role | Email | Password |
|---|---|---|
| Manager | `manager@bookstore.com` | `manager123` |
| Staff | `staff@bookstore.com` | `staff123` |
| Customer 1 | `customer1@example.com` | `cust123` |
| Customer 2 | `customer2@example.com` | `cust123` |

---

## 5. Hướng dẫn Dựng hệ thống (Setup Guide)

Hệ thống được thiết kế gói gọn toàn vẹn trong Docker Compose. Bạn chỉ cần thực hiện 1 câu lệnh duy nhất là hệ thống sẽ tự động Pull, Build các layer và giăng ra lưới mạng ảo chứa 10 Service cùng CSDL Postgres.

### 5.1 Khởi động Docker toàn phần

Mở Terminal tại thư mục gốc chứa `docker-compose.yml`, sau đó chạy:
```bash
docker-compose up --build -d
```
Hệ thống sẽ xây dựng hình ảnh (build) cho từng folder Django và mount mã nguồn bằng Volumes (bạn lập trình Python sửa file tại Host OS sẽ tự sync thẳng vào Container mà không cần rebuild).

### 5.2 Truy cập Ứng dụng & Tooling

Sau khi Docker báo trạng thái "Started" hoặc "Healthy", hãy truy cập các link sau:

- **Giao diện mua sắm:** `http://localhost:18000/`
- **Swagger UI Danh Mục Tổng (API Docs):** `http://localhost:18000/api/docs/` (Trang này có tính năng Drop-down gộp toàn bộ các 10 Microservices lại để dễ dàng tìm kiếm endpoints mà không cần nhớ từng Port một).

### 5.3 Reset Cơ Sở Dữ Liệu
Khi container database bị hỏng hay cần khôi phục về mock data sạch tinh chỉnh, chạy command Python sau tại máy Host:
```bash
python seed_data.py
```
*(Script có nhiệm vụ xoá sạch Table và Inject lại cấu trúc Category, List Books, cũng như 3 Roles Account tự động qua REST HTTP Call API).*

---
*(Bản Tóm tắt Tài liệu Dự án hoàn thành trong nửa vòng đời môn học. Mục tiêu Assignment 6 sẽ tập trung nâng cấp cơ chế Asynchronous Event-Driven kết hợp Message Broker và mở rộng Token xác thực).*
