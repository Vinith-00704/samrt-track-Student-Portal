from app import app, db, User, Course, StudentCourse, Timetable
from werkzeug.security import generate_password_hash

def add_sample_data():
    with app.app_context():
        # Add sample courses
        courses = [
            # CSE Courses
            Course(code='CS101', name='Introduction to Programming', credits=3, department='CSE', year=1),
            Course(code='CS102', name='Data Structures', credits=4, department='CSE', year=2),
            Course(code='CS103', name='Database Management', credits=3, department='CSE', year=3),
            Course(code='CS104', name='Web Development', credits=3, department='CSE', year=4),
            Course(code='CS105', name='Operating Systems', credits=4, department='CSE', year=3),
            Course(code='CS106', name='Computer Networks', credits=4, department='CSE', year=3),
            Course(code='CS107', name='Software Engineering', credits=3, department='CSE', year=4),
            Course(code='CS108', name='Artificial Intelligence', credits=4, department='CSE', year=4),
            
            # ECE Courses
            Course(code='EC101', name='Basic Electronics', credits=3, department='ECE', year=1),
            Course(code='EC102', name='Digital Electronics', credits=4, department='ECE', year=2),
            Course(code='EC103', name='Microprocessors', credits=3, department='ECE', year=3),
            Course(code='EC104', name='Communication Systems', credits=4, department='ECE', year=3),
            Course(code='EC105', name='VLSI Design', credits=4, department='ECE', year=4),
            Course(code='EC106', name='Embedded Systems', credits=3, department='ECE', year=4),
            
            # ME Courses
            Course(code='ME101', name='Engineering Mechanics', credits=3, department='ME', year=1),
            Course(code='ME102', name='Thermodynamics', credits=4, department='ME', year=2),
            Course(code='ME103', name='Fluid Mechanics', credits=4, department='ME', year=2),
            Course(code='ME104', name='Machine Design', credits=4, department='ME', year=3),
            Course(code='ME105', name='Heat Transfer', credits=3, department='ME', year=3),
            Course(code='ME106', name='Automobile Engineering', credits=4, department='ME', year=4),
            
            # CE Courses
            Course(code='CE101', name='Engineering Drawing', credits=3, department='CE', year=1),
            Course(code='CE102', name='Surveying', credits=4, department='CE', year=2),
            Course(code='CE103', name='Structural Analysis', credits=4, department='CE', year=3),
            Course(code='CE104', name='Concrete Technology', credits=3, department='CE', year=3),
            Course(code='CE105', name='Environmental Engineering', credits=4, department='CE', year=4),
            Course(code='CE106', name='Transportation Engineering', credits=4, department='CE', year=4)
        ]
        
        for course in courses:
            db.session.add(course)
        
        # Add sample students
        students = [
            # CSE Students
            User(email='student1@example.com', password_hash=generate_password_hash('student123'),
                 name='John Doe', department='CSE', section='A', registration_number='CSE001', year=2, is_admin=False),
            User(email='student2@example.com', password_hash=generate_password_hash('student123'),
                 name='Jane Smith', department='CSE', section='B', registration_number='CSE002', year=3, is_admin=False),
            User(email='student3@example.com', password_hash=generate_password_hash('student123'),
                 name='Mike Johnson', department='CSE', section='A', registration_number='CSE003', year=4, is_admin=False),
            
            # ECE Students
            User(email='student4@example.com', password_hash=generate_password_hash('student123'),
                 name='Sarah Williams', department='ECE', section='A', registration_number='ECE001', year=2, is_admin=False),
            User(email='student5@example.com', password_hash=generate_password_hash('student123'),
                 name='David Brown', department='ECE', section='B', registration_number='ECE002', year=3, is_admin=False),
            
            # ME Students
            User(email='student6@example.com', password_hash=generate_password_hash('student123'),
                 name='Emily Davis', department='ME', section='A', registration_number='ME001', year=2, is_admin=False),
            User(email='student7@example.com', password_hash=generate_password_hash('student123'),
                 name='Robert Wilson', department='ME', section='B', registration_number='ME002', year=3, is_admin=False),
            
            # CE Students
            User(email='student8@example.com', password_hash=generate_password_hash('student123'),
                 name='Lisa Anderson', department='CE', section='A', registration_number='CE001', year=2, is_admin=False),
            User(email='student9@example.com', password_hash=generate_password_hash('student123'),
                 name='James Taylor', department='CE', section='B', registration_number='CE002', year=3, is_admin=False)
        ]
        
        for student in students:
            db.session.add(student)
        
        try:
            db.session.commit()
            print("Added sample courses and students successfully!")
            
            # Enroll students in courses
            for student in students:
                # Get courses for student's department and year
                student_courses = Course.query.filter_by(
                    department=student.department,
                    year=student.year
                ).all()
                
                # Enroll in courses
                for course in student_courses:
                    enrollment = StudentCourse(
                        student_id=student.id,
                        course_id=course.id
                    )
                    db.session.add(enrollment)
            
            db.session.commit()
            print("Enrolled students in courses successfully!")
            
            # Add sample timetable entries
            timetable_entries = [
                # CSE Section A - Year 2
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS102').first().id, day='Monday', period=1),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS102').first().id, day='Monday', period=2),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS105').first().id, day='Tuesday', period=1),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS105').first().id, day='Tuesday', period=2),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS106').first().id, day='Wednesday', period=1),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS106').first().id, day='Wednesday', period=2),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS102').first().id, day='Thursday', period=3),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS102').first().id, day='Thursday', period=4),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS105').first().id, day='Friday', period=3),
                Timetable(department='CSE', section='A', course_id=Course.query.filter_by(code='CS105').first().id, day='Friday', period=4),
                
                # CSE Section B - Year 2
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS102').first().id, day='Monday', period=3),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS102').first().id, day='Monday', period=4),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS105').first().id, day='Tuesday', period=3),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS105').first().id, day='Tuesday', period=4),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS106').first().id, day='Wednesday', period=3),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS106').first().id, day='Wednesday', period=4),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS102').first().id, day='Thursday', period=1),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS102').first().id, day='Thursday', period=2),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS105').first().id, day='Friday', period=1),
                Timetable(department='CSE', section='B', course_id=Course.query.filter_by(code='CS105').first().id, day='Friday', period=2),
                
                # ECE Section A - Year 2
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC102').first().id, day='Monday', period=1),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC102').first().id, day='Monday', period=2),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC103').first().id, day='Tuesday', period=1),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC103').first().id, day='Tuesday', period=2),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC104').first().id, day='Wednesday', period=1),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC104').first().id, day='Wednesday', period=2),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC102').first().id, day='Thursday', period=3),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC102').first().id, day='Thursday', period=4),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC103').first().id, day='Friday', period=3),
                Timetable(department='ECE', section='A', course_id=Course.query.filter_by(code='EC103').first().id, day='Friday', period=4),
                
                # ME Section A - Year 2
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME102').first().id, day='Monday', period=3),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME102').first().id, day='Monday', period=4),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME103').first().id, day='Tuesday', period=3),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME103').first().id, day='Tuesday', period=4),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME104').first().id, day='Wednesday', period=3),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME104').first().id, day='Wednesday', period=4),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME102').first().id, day='Thursday', period=1),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME102').first().id, day='Thursday', period=2),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME103').first().id, day='Friday', period=1),
                Timetable(department='ME', section='A', course_id=Course.query.filter_by(code='ME103').first().id, day='Friday', period=2),
                
                # CE Section A - Year 2
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE102').first().id, day='Monday', period=5),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE102').first().id, day='Monday', period=6),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE103').first().id, day='Tuesday', period=5),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE103').first().id, day='Tuesday', period=6),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE104').first().id, day='Wednesday', period=5),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE104').first().id, day='Wednesday', period=6),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE102').first().id, day='Thursday', period=5),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE102').first().id, day='Thursday', period=6),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE103').first().id, day='Friday', period=5),
                Timetable(department='CE', section='A', course_id=Course.query.filter_by(code='CE103').first().id, day='Friday', period=6)
            ]
            
            for entry in timetable_entries:
                db.session.add(entry)
            
            db.session.commit()
            print("Added timetable entries successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    add_sample_data() 