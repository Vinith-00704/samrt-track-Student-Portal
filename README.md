# 🎓 Smart Track — Student Academic Portal

A web-based Student Academic Management System built with **Flask** and **MySQL**, designed to help students and administrators manage academic records efficiently.

---

## 📌 Features

### 👨‍🎓 Student
- Secure registration & login with account lockout protection
- View enrolled courses, attendance, and IA marks (IA1, IA2, IA3)
- Weekly timetable based on department & section
- Forgot/reset password via email

### 🛡️ Admin
- Manage courses, timetables, and student enrollments
- Update student attendance and internal assessment marks
- View all registered students across departments

---

## 🛠️ Tech Stack

| Layer        | Technology                          |
|--------------|--------------------------------------|
| Backend      | Python, Flask                        |
| Database     | MySQL (PyMySQL + SQLAlchemy ORM)     |
| Frontend     | HTML, CSS (Jinja2 Templates)         |
| Auth         | Flask-Login, Werkzeug                |
| Email        | Flask-Mail                           |
| Security     | Flask-Limiter, Flask-Caching         |

---

## 🗄️ Database Schema

```
user            → Student & Admin accounts
course          → Course catalogue (department + year)
student_course  → Enrollment table (attendance + IA marks)
timetable       → Weekly schedule (dept + section + day + period)
password_reset  → Token-based password recovery
```

---

## 🏫 Supported Departments

| Code | Full Name                                  |
|------|--------------------------------------------|
| CSE  | Computer Science & Engineering             |
| ECE  | Electronics & Communication Engineering   |
| ME   | Mechanical Engineering                     |
| CE   | Civil Engineering                          |

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/smart-track.git
cd smart-track
```

### 2. Create a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:
```env
SECRET_KEY=your_secret_key
DB_USER=root
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_NAME=student_portal
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

### 5. Set Up the Database
```bash
# Option 1: Using SQL file
mysql -u root -p < setup_database.sql

# Option 2: Using Python script
python init_db.py
```

### 6. Add Sample Data (Optional)
```bash
python add_sample_data.py
```

### 7. Create Admin User
```bash
python create_admin.py
```
> Default admin credentials:
> - **Email:** `admin@example.com`
> - **Password:** `Admin@123`

### 8. Run the Application
```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```
smart-track/
│
├── app.py                  # Main Flask application
├── init_db.py              # Database initialization script
├── create_admin.py         # Admin user creation script
├── add_sample_data.py      # Sample data seeder
├── reset_db.py             # Database reset utility
├── setup_database.sql      # SQL schema file
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
│
├── templates/              # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── attendance.html
│   ├── marks.html
│   ├── timetable.html
│   └── admin/
│       ├── dashboard.html
│       ├── courses.html
│       ├── students.html
│       ├── timetable.html
│       └── student_courses.html
│
└── static/                 # Static assets (CSS, images)
    ├── css/
    └── images/
```

---

## 🔐 Security Features

- Password hashing using **Werkzeug**
- Account lockout after **5 failed login attempts**
- **Rate limiting** on login and register routes (5 requests/minute)
- Secure token-based **password reset** via email (expires in 1 hour)
- Admin-only routes protected with custom decorators

---

## 📋 Requirements

- Python 3.8+
- MySQL 5.7+ or MariaDB
- pip

---

## 📄 License

This project was developed as a **DBMS course project**. Feel free to use it for educational purposes.

---

## 👨‍💻 Author

**Vinith Kumar**  
[GitHub](https://github.com/Vinith-00704)
