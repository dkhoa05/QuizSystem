# 🎯 Quiz System – Hệ Thống Thi Trắc Nghiệm Online  
Một hệ thống thi trắc nghiệm đầy đủ tính năng, hỗ trợ Admin quản lý ngân hàng câu hỏi, người dùng, bài thi và theo dõi thống kê. Sinh viên có thể làm bài, xem lịch sử và nhận chứng chỉ PDF tự động.

---

## 🚀 1. Chức năng chính

### 👨‍🎓 **Student**
- Đăng ký, đăng nhập
- Làm bài trắc nghiệm theo quiz
- Xem kết quả ngay sau khi nộp
- Nhận chứng chỉ PDF sau khi hoàn thành
- Xem lịch sử những bài đã làm

### 👨‍💼 **Admin**
- Quản lý câu hỏi:
  - Thêm, sửa, xóa câu hỏi
  - Hỗ trợ 3 loại câu hỏi: MCQ, True/False, Essay
- Quản lý Quiz:
  - Tạo bài quiz
  - Gán câu hỏi vào quiz
  - Xem danh sách bài thi
- Quản lý người dùng:
  - Thêm tài khoản
  - Sửa tài khoản
  - Xóa tài khoản
  - Chọn role: `admin` hoặc `student`
- Xem lịch sử làm bài của toàn hệ thống (tất cả user)
- Xuất chứng chỉ PDF cho mỗi người dùng

---

## 🏗️ 2. Công nghệ sử dụng

| Thành phần | Công nghệ |
|-----------|-----------|
| Backend | Flask (Python) |
| Database | SQLite + SQLAlchemy ORM |
| UI | HTML, Jinja2, Bootstrap 5 |
| Auth | Flask-Login |
| PDF Generator | ReportLab |
| Background Tasks | Celery (future-ready) |

---

## 📂 3. Cấu trúc thư mục quan trọng

QuizSystem/
│── app/
│ ├── auth/ # Đăng ký, đăng nhập
│ ├── quiz/ # Làm bài, xem kết quả, lịch sử
│ ├── templates/ # Giao diện
│ ├── certificates/ # Sinh chứng chỉ PDF
│ └── models.py # Models database
│
│── instance/
│ └── quiz.db # Database
│
│── migrations/ # Alembic
│
│── requirements.txt
│── run.py
└── README.md


---

## 🧪 4. Cách chạy project

### 1️⃣ Tạo môi trường ảo


### 2️⃣ Kích hoạt môi trường
**Windows**


### 3️⃣ Cài đặt thư viện


### 4️⃣ Chạy project


Hoặc:


Truy cập tại:

http://127.0.0.1:5000

---

## 📝 5. Tài khoản mặc định

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |

---

## 🗒️ 6. Ghi chú

- **Không commit thư mục `venv/`**
- **Không commit file PDF chứng chỉ**
- **Không commit file .pyc**

---

## ❤️ 7. Tác giả
Hệ thống phát triển phục vụ cho môn học, thực hành và trình bày đồ án.

---

