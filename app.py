from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import re
from dotenv import load_dotenv
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_mail import Mail, Message
import secrets

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
mail = Mail(app)

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Initialize cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Validation functions
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""

def validate_course_code(code):
    pattern = r'^[A-Z]{2,3}\d{3}$'
    return bool(re.match(pattern, code))

def validate_registration_number(reg_no):
    pattern = r'^[A-Z]{2,3}\d{3,5}$'
    return bool(re.match(pattern, reg_no))

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(20), nullable=False)
    registration_number = db.Column(db.String(20), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime)
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    courses = db.relationship('StudentCourse', backref='student', lazy=True)
    
    def set_password(self, password):
        is_valid, message = validate_password(password)
        if not is_valid:
            raise ValueError(message)
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def increment_failed_attempts(self):
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.account_locked = True
        db.session.commit()
    
    def reset_failed_attempts(self):
        self.failed_login_attempts = 0
        self.account_locked = False
        db.session.commit()

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    prerequisites = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    students = db.relationship('StudentCourse', backref='course', lazy=True)

class StudentCourse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
    attendance = db.Column(db.Integer, default=0)
    total_classes = db.Column(db.Integer, default=60)
    ia1 = db.Column(db.Float, default=0)
    ia2 = db.Column(db.Float, default=0)
    ia3 = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Timetable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    department = db.Column(db.String(100), nullable=False)
    section = db.Column(db.String(20), nullable=False)
    day = db.Column(db.String(10), nullable=False)
    period = db.Column(db.Integer, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id', ondelete='CASCADE'))
    is_break = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    course = db.relationship('Course', lazy=True)

class PasswordReset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Error handlers
@app.errorhandler(Exception)
def handle_error(error):
    db.session.rollback()
    flash('An error occurred. Please try again.', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Admin check decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@cache.memoize(timeout=300)
def get_department_courses(department, year):
    return Course.query.filter_by(department=department, year=year).all()

def enroll_student_in_department_courses(student):
    try:
        courses = get_department_courses(student.department, student.year)
        
        if not courses:
            raise ValueError(f"No courses found for department {student.department} and year {student.year}")
        
        for course in courses:
            existing_enrollment = StudentCourse.query.filter_by(
                student_id=student.id,
                course_id=course.id
            ).first()
            
            if not existing_enrollment:
                enrollment = StudentCourse(
                    student_id=student.id,
                    course_id=course.id,
                    total_classes=60
                )
                db.session.add(enrollment)
        
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            registration_number = request.form.get('registration_number')
            department = request.form.get('department')
            section = request.form.get('section')
            year = int(request.form.get('year'))
            
            # Validate inputs
            if not validate_registration_number(registration_number):
                flash('Invalid registration number format', 'danger')
                return redirect(url_for('register'))
            
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('register'))
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))
            
            if User.query.filter_by(registration_number=registration_number).first():
                flash('Registration number already exists', 'danger')
                return redirect(url_for('register'))
            
            # Create new user
            user = User(
                name=name,
                email=email,
                registration_number=registration_number,
                department=department,
                section=section,
                year=year,
                is_admin=False
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Enroll in courses
            enroll_student_in_department_courses(user)
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user:
            if user.account_locked:
                flash('Account is locked. Please reset your password.', 'danger')
                return redirect(url_for('forgot_password'))
            
            if user.check_password(password):
                user.reset_failed_attempts()
                user.last_login = datetime.utcnow()
                db.session.commit()
                login_user(user)
                
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                if user.is_admin:
                    return redirect(url_for('admin_dashboard'))
                return redirect(url_for('dashboard'))
            else:
                user.increment_failed_attempts()
        
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            reset = PasswordReset(
                user_id=user.id,
                token=token,
                expires_at=expires_at
            )
            
            db.session.add(reset)
            db.session.commit()
            
            reset_link = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request',
                         recipients=[user.email])
            msg.body = f'Click the following link to reset your password: {reset_link}'
            mail.send(msg)
            
            flash('Password reset link has been sent to your email', 'success')
            return redirect(url_for('login'))
        
        flash('Email not found', 'danger')
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = PasswordReset.query.filter_by(token=token).first()
    
    if not reset or reset.expires_at < datetime.utcnow():
        flash('Invalid or expired reset token', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        try:
            user = User.query.get(reset.user_id)
            user.set_password(password)
            user.reset_failed_attempts()
            
            db.session.delete(reset)
            db.session.commit()
            
            flash('Password has been reset successfully', 'success')
            return redirect(url_for('login'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while resetting password', 'danger')
    
    return render_template('reset_password.html', token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get student's courses and timetable
    student_courses = StudentCourse.query.filter_by(student_id=current_user.id).all()
    print(f"Found {len(student_courses)} courses for student {current_user.name}")
    
    timetable = Timetable.query.filter_by(
        department=current_user.department,
        section=current_user.section
    ).all()
    
    return render_template('dashboard.html', 
                         student_courses=student_courses,
                         timetable=timetable)

@app.route('/attendance')
@login_required
def attendance():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    student_courses = StudentCourse.query.filter_by(student_id=current_user.id).all()
    return render_template('attendance.html', student_courses=student_courses)

@app.route('/marks')
@login_required
def marks():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    student_courses = StudentCourse.query.filter_by(student_id=current_user.id).all()
    return render_template('marks.html', student_courses=student_courses)

@app.route('/timetable')
@login_required
def timetable():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Get timetable for the student's section
    timetable = Timetable.query.filter_by(
        department=current_user.department,
        section=current_user.section
    ).all()
    return render_template('timetable.html', timetable=timetable)

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/courses', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_courses():
    if request.method == 'POST':
        code = request.form.get('course_code')
        name = request.form.get('course_name')
        credits = int(request.form.get('credits'))
        department = request.form.get('department')
        year = int(request.form.get('year'))
        
        course = Course(
            code=code,
            name=name,
            credits=credits,
            department=department,
            year=year
        )
        db.session.add(course)
        try:
            db.session.commit()
            flash('Course added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding course. Make sure the course code is unique.', 'danger')
    
    departments = ['CSE', 'ECE', 'ME', 'CE']
    courses = Course.query.order_by(Course.department, Course.year, Course.code).all()
    return render_template('admin/courses.html', courses=courses, departments=departments)

@app.route('/admin/timetable', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_timetable():
    departments = ['CSE', 'ECE', 'ME', 'CE']
    sections = ['A', 'B', 'C', 'D']
    
    if request.method == 'POST':
        department = request.form.get('department')
        section = request.form.get('section')
        course_id = request.form.get('course_id')
        day = request.form.get('day')
        period = request.form.get('period')
        
        # Validate required fields
        if not all([department, section, course_id, day, period]):
            flash('Please fill in all required fields!', 'danger')
            return redirect(url_for('admin_timetable'))
        
        try:
            course_id = int(course_id)
            period = int(period)
        except ValueError:
            flash('Invalid course or period value!', 'danger')
            return redirect(url_for('admin_timetable'))
        
        # Check if the time slot is already taken for this section
        existing = Timetable.query.filter_by(
            department=department,
            section=section,
            day=day,
            period=period
        ).first()
        
        if existing:
            flash('This time slot is already taken for this section!', 'danger')
            return redirect(url_for('admin_timetable'))
        
        # Check if the course exists
        course = Course.query.get(course_id)
        if not course:
            flash('Selected course does not exist!', 'danger')
            return redirect(url_for('admin_timetable'))
        
        timetable = Timetable(
            department=department,
            section=section,
            course_id=course_id,
            day=day,
            period=period
        )
        
        try:
            db.session.add(timetable)
            db.session.commit()
            flash('Timetable entry added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error adding timetable entry. Please try again.', 'danger')
    
    # Get filter parameters from request
    selected_dept = request.args.get('department', departments[0])
    selected_year = request.args.get('year', '1')
    
    # Get courses for the selected department and year
    courses = Course.query.filter_by(
        department=selected_dept,
        year=int(selected_year)
    ).all()
    
    # Get timetable entries for the selected department
    timetable = Timetable.query.filter_by(
        department=selected_dept
    ).all()
    
    return render_template('admin/timetable.html',
                         departments=departments,
                         sections=sections,
                         courses=courses,
                         timetable=timetable,
                         selected_dept=selected_dept,
                         selected_year=selected_year)

@app.route('/admin/delete-timetable-entry', methods=['POST'])
@login_required
@admin_required
def delete_timetable_entry():
    timetable_id = request.form.get('timetable_id')
    entry = Timetable.query.get(timetable_id)
    if entry:
        db.session.delete(entry)
        db.session.commit()
        flash('Timetable entry deleted successfully!', 'success')
    return redirect(url_for('admin_timetable'))

@app.route('/admin/student-courses', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_student_courses():
    student_id = request.args.get('student_id')
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id')
        
        if student_id and course_id:
            existing = StudentCourse.query.filter_by(
                student_id=student_id,
                course_id=course_id
            ).first()
            
            if existing:
                flash('Student is already enrolled in this course!', 'warning')
            else:
                enrollment = StudentCourse(
                    student_id=student_id,
                    course_id=course_id
                )
                db.session.add(enrollment)
                db.session.commit()
                flash('Student enrolled in course successfully!', 'success')
    
    students = User.query.filter_by(is_admin=False).all()
    courses = Course.query.all()
    
    if student_id:
        student_courses = StudentCourse.query.filter_by(student_id=student_id).all()
        selected_student = User.query.get(student_id)
    else:
        student_courses = StudentCourse.query.all()
        selected_student = None
    
    return render_template('admin/student_courses.html',
                         students=students,
                         courses=courses,
                         student_courses=student_courses,
                         selected_student=selected_student)

@app.route('/admin/students')
@login_required
@admin_required
def admin_students():
    students = User.query.filter_by(is_admin=False).all()
    departments = ['CSE', 'ECE', 'ME', 'CE']
    return render_template('admin/students.html', 
                         students=students,
                         departments=departments)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin/update-attendance', methods=['POST'])
@login_required
@admin_required
def update_attendance():
    student_course_id = request.form.get('student_course_id')
    attendance = int(request.form.get('attendance'))
    total_classes = int(request.form.get('total_classes'))
    
    student_course = StudentCourse.query.get(student_course_id)
    if student_course:
        student_course.attendance = attendance
        student_course.total_classes = total_classes
        db.session.commit()
        flash('Attendance updated successfully!')
    
    return redirect(url_for('admin_student_courses'))

@app.route('/admin/update-marks', methods=['POST'])
@login_required
@admin_required
def update_marks():
    student_course_id = request.form.get('student_course_id')
    ia_type = request.form.get('ia_type')
    marks = float(request.form.get('marks'))
    
    student_course = StudentCourse.query.get(student_course_id)
    if student_course:
        if ia_type == 'ia1':
            student_course.ia1 = marks
        elif ia_type == 'ia2':
            student_course.ia2 = marks
        elif ia_type == 'ia3':
            student_course.ia3 = marks
        db.session.commit()
        flash('Marks updated successfully!')
    
    return redirect(url_for('admin_student_courses'))

@app.route('/admin/delete-enrollment', methods=['POST'])
@login_required
@admin_required
def delete_enrollment():
    student_course_id = request.form.get('student_course_id')
    
    student_course = StudentCourse.query.get(student_course_id)
    if student_course:
        db.session.delete(student_course)
        db.session.commit()
        flash('Enrollment removed successfully!')
    
    return redirect(url_for('admin_student_courses'))

@app.route('/admin/view-courses')
@login_required
@admin_required
def view_courses():
    courses = Course.query.order_by(Course.department, Course.year, Course.code).all()
    return render_template('admin/view_courses.html', courses=courses)

def create_sample_courses():
    """Create sample courses for all departments and years"""
    print("Checking for existing courses...")
    existing_courses = Course.query.all()
    print(f"Found {len(existing_courses)} existing courses")
    
    # Define departments and their course prefixes
    departments = {
        'CSE': {
            'name': 'Computer Science and Engineering',
            'prefix': 'CS'
        },
        'ECE': {
            'name': 'Electronics and Communication Engineering',
            'prefix': 'EC'
        },
        'ME': {
            'name': 'Mechanical Engineering',
            'prefix': 'ME'
        },
        'CE': {
            'name': 'Civil Engineering',
            'prefix': 'CE'
        }
    }
    
    # Course templates for each year
    year_courses = {
        1: [
            ('Mathematics I', 4),
            ('Physics', 4),
            ('Chemistry', 4),
            ('Engineering Drawing', 3),
            ('Basic Electronics', 3),
            ('Programming Fundamentals', 4)
        ],
        2: [
            ('Mathematics II', 4),
            ('Data Structures', 4),
            ('Digital Electronics', 4),
            ('Computer Organization', 3),
            ('Object Oriented Programming', 4),
            ('Database Systems', 4)
        ],
        3: [
            ('Design and Analysis of Algorithms', 4),
            ('Operating Systems', 4),
            ('Computer Networks', 4),
            ('Software Engineering', 3),
            ('Web Technologies', 3),
            ('Machine Learning', 4)
        ],
        4: [
            ('Artificial Intelligence', 4),
            ('Cloud Computing', 4),
            ('Information Security', 4),
            ('Big Data Analytics', 3),
            ('Project Management', 3),
            ('Elective Course', 4)
        ]
    }
    
    # Department specific courses
    dept_specific_courses = {
        'CSE': {
            1: [
                ('Introduction to Computing', 'Basic concepts of computer science'),
                ('Programming Lab', 'Basic programming concepts'),
                ('Computer Networks Lab', 'Network fundamentals'),
                ('Web Development', 'Basic web technologies'),
                ('Python Programming', 'Python basics'),
                ('Data Science Basics', 'Introduction to data science')
            ],
            2: [
                ('Data Structures and Algorithms', 'Advanced data structures'),
                ('Database Management Systems', 'Database concepts'),
                ('Operating Systems', 'OS concepts'),
                ('Computer Architecture', 'Computer organization'),
                ('Java Programming', 'Java fundamentals'),
                ('Software Engineering', 'Software development lifecycle')
            ],
            3: [
                ('Artificial Intelligence', 'AI concepts'),
                ('Machine Learning', 'ML algorithms'),
                ('Web Technologies', 'Advanced web development'),
                ('Cloud Computing', 'Cloud platforms'),
                ('Cyber Security', 'Security fundamentals'),
                ('Mobile App Development', 'App development basics')
            ],
            4: [
                ('Deep Learning', 'Neural networks'),
                ('Big Data Analytics', 'Big data processing'),
                ('Internet of Things', 'IoT fundamentals'),
                ('Blockchain Technology', 'Blockchain basics'),
                ('Natural Language Processing', 'NLP concepts'),
                ('Project Work', 'Final year project')
            ]
        },
        'ECE': {
            1: [
                ('Basic Electronics', 'Electronics fundamentals'),
                ('Circuit Theory', 'Basic circuits'),
                ('Digital Electronics', 'Digital logic'),
                ('Signals and Systems', 'Signal processing'),
                ('Communication Systems', 'Basic communication'),
                ('Electronic Devices', 'Device physics')
            ],
            2: [
                ('Analog Electronics', 'Analog circuits'),
                ('Digital Signal Processing', 'DSP basics'),
                ('Microprocessors', 'Processor architecture'),
                ('Control Systems', 'Control theory'),
                ('Electromagnetic Theory', 'EM waves'),
                ('VLSI Design', 'VLSI basics')
            ],
            3: [
                ('Communication Engineering', 'Advanced communication'),
                ('Antenna Theory', 'Antenna design'),
                ('Embedded Systems', 'Embedded programming'),
                ('Wireless Communication', 'Wireless systems'),
                ('Digital Image Processing', 'Image processing'),
                ('Microwave Engineering', 'Microwave theory')
            ],
            4: [
                ('Satellite Communication', 'Satellite systems'),
                ('Optical Communication', 'Optical networks'),
                ('RADAR Systems', 'Radar technology'),
                ('Mobile Communication', '4G/5G systems'),
                ('IoT Systems', 'IoT architecture'),
                ('Project Work', 'Final year project')
            ]
        },
        'ME': {
            1: [
                ('Engineering Mechanics', 'Basic mechanics'),
                ('Thermodynamics', 'Heat and energy'),
                ('Manufacturing Processes', 'Basic manufacturing'),
                ('Material Science', 'Material properties'),
                ('Workshop Practice', 'Basic workshop'),
                ('Engineering Graphics', 'Technical drawing')
            ],
            2: [
                ('Fluid Mechanics', 'Fluid dynamics'),
                ('Strength of Materials', 'Material strength'),
                ('Machine Drawing', 'Machine design'),
                ('Heat Transfer', 'Heat transfer modes'),
                ('Kinematics', 'Motion analysis'),
                ('Manufacturing Technology', 'Advanced manufacturing')
            ],
            3: [
                ('Design of Machine Elements', 'Machine design'),
                ('Industrial Engineering', 'Industry processes'),
                ('Dynamics of Machinery', 'Machine dynamics'),
                ('Heat and Mass Transfer', 'Transfer phenomena'),
                ('CAD/CAM', 'Computer aided design'),
                ('Robotics', 'Industrial robots')
            ],
            4: [
                ('Automobile Engineering', 'Vehicle systems'),
                ('Power Plant Engineering', 'Power generation'),
                ('Industrial Automation', 'Automation systems'),
                ('Renewable Energy', 'Green energy'),
                ('Quality Engineering', 'Quality control'),
                ('Project Work', 'Final year project')
            ]
        },
        'CE': {
            1: [
                ('Engineering Mechanics', 'Basic mechanics'),
                ('Building Materials', 'Construction materials'),
                ('Surveying', 'Land surveying'),
                ('Construction Technology', 'Construction basics'),
                ('Environmental Engineering', 'Environment basics'),
                ('Engineering Geology', 'Geological concepts')
            ],
            2: [
                ('Structural Analysis', 'Structure mechanics'),
                ('Fluid Mechanics', 'Fluid flow'),
                ('Concrete Technology', 'Concrete properties'),
                ('Soil Mechanics', 'Soil properties'),
                ('Transportation Engineering', 'Transport systems'),
                ('Water Resources', 'Water management')
            ],
            3: [
                ('Design of Structures', 'Structure design'),
                ('Foundation Engineering', 'Foundation systems'),
                ('Highway Engineering', 'Road construction'),
                ('Environmental Engineering', 'Pollution control'),
                ('Construction Management', 'Project planning'),
                ('Hydrology', 'Water resources')
            ],
            4: [
                ('Advanced Structures', 'Complex structures'),
                ('Bridge Engineering', 'Bridge design'),
                ('Urban Planning', 'City planning'),
                ('Earthquake Engineering', 'Seismic design'),
                ('Green Buildings', 'Sustainable construction'),
                ('Project Work', 'Final year project')
            ]
        }
    }
    
    # Create courses for each department and year
    for dept, dept_info in departments.items():
        for year in range(1, 5):
            courses = dept_specific_courses[dept][year]
            for i, (name, description) in enumerate(courses, 1):
                code = f"{dept_info['prefix']}{year}0{i}"
                
                # Check if course already exists
                existing_course = Course.query.filter_by(
                    code=code,
                    department=dept,
                    year=year
                ).first()
                
                if not existing_course:
                    print(f"Creating course: {code} - {name}")
                    course = Course(
                        code=code,
                        name=name,
                        credits=4,  # Default credits
                        department=dept,
                        year=year
                    )
                    db.session.add(course)
                else:
                    print(f"Course already exists: {code} - {name}")
    
    try:
        db.session.commit()
        print("Successfully committed course changes")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample courses: {str(e)}")

@app.route('/get-courses')
def get_courses():
    department = request.args.get('department')
    year = request.args.get('year')
    
    if not department or not year:
        return jsonify({'error': 'Department and year are required'}), 400
    
    try:
        year = int(year)
        courses = Course.query.filter_by(department=department, year=year).all()
        return jsonify({
            'courses': [{
                'code': course.code,
                'name': course.name,
                'credits': course.credits
            } for course in courses]
        })
    except ValueError:
        return jsonify({'error': 'Invalid year'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def update_existing_enrollments():
    """Update all existing student-course enrollments to have 60 total classes"""
    enrollments = StudentCourse.query.filter(StudentCourse.total_classes != 60).all()
    for enrollment in enrollments:
        enrollment.total_classes = 60
    try:
        db.session.commit()
        print(f"Updated {len(enrollments)} enrollments to have 60 total classes")
    except Exception as e:
        db.session.rollback()
        print(f"Error updating enrollments: {str(e)}")

def create_sample_timetable():
    """Create sample timetable data for all departments and sections"""
    print("\nCreating sample timetable data...")
    
    # Days of the week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Periods in a day (assuming 6 periods with breaks)
    periods = [1, 2, 3, 4, 5, 6]
    
    # Departments and their sections
    departments = ['CSE', 'ECE', 'ME', 'CE']
    sections = ['A', 'B', 'C', 'D']
    
    # Get all courses
    courses = Course.query.all()
    
    # Create timetable entries for each department and section
    for department in departments:
        for section in sections:
            print(f"\nCreating timetable for {department} - Section {section}")
            
            # Get courses for this department and year
            dept_courses = [course for course in courses if course.department == department]
            
            # Distribute courses across days and periods
            for day in days:
                for period in periods:
                    # Skip if this slot is already taken
                    existing = Timetable.query.filter_by(
                        department=department,
                        section=section,
                        day=day,
                        period=period
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Add break after period 2 and period 4
                    if period == 3 or period == 5:
                        timetable = Timetable(
                            department=department,
                            section=section,
                            course_id=None,
                            is_break=True,
                            day=day,
                            period=period
                        )
                        db.session.add(timetable)
                        print(f"Added BREAK to {day} period {period}")
                        continue
                    
                    # Find a course that hasn't been scheduled too many times
                    for course in dept_courses:
                        # Count how many times this course is already scheduled
                        scheduled_count = Timetable.query.filter_by(
                            department=department,
                            section=section,
                            course_id=course.id
                        ).count()
                        
                        # If course is scheduled less than 2 times per week, use it
                        if scheduled_count < 2:
                            timetable = Timetable(
                                department=department,
                                section=section,
                                course_id=course.id,
                                is_break=False,
                                day=day,
                                period=period
                            )
                            db.session.add(timetable)
                            print(f"Added {course.code} to {day} period {period}")
                            break
    
    try:
        db.session.commit()
        print("\nSuccessfully created sample timetable data")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating timetable data: {str(e)}")
        raise e

def create_admin_user():
    """Create an admin user if it doesn't exist"""
    print("\nChecking for admin user...")
    admin = User.query.filter_by(email='admin@admin.com').first()
    if not admin:
        print("Creating admin user...")
        admin = User(
            email='admin@admin.com',
            name='Admin',
            department='ADMIN',
            section='A',
            registration_number='ADMIN001',
            year=1,
            is_admin=True
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
        try:
            db.session.commit()
            print("Admin user created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {str(e)}")
            raise e
    else:
        print("Admin user already exists")

if __name__ == '__main__':
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create admin user first
        create_admin_user()
        
        # Create sample data
        create_sample_courses()
        update_existing_enrollments()
        create_sample_timetable()
    
    app.run(debug=True) 