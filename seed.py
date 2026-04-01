from app.database import SessionLocal, engine, Base
from app.models import User, Subject, Class, TimeSlot, StudentEnrollment, Timetable
import datetime

# Make sure tables exist
Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).first():
            print("Database already contains data, skipping seed.")
            return

        print("Seeding Users...")
        admin = User(name="Admin User", email="admin@example.com", password="password", role="admin")
        t1 = User(name="John Doe", email="john.teacher@example.com", password="password", role="teacher")
        t2 = User(name="Jane Smith", email="jane.teacher@example.com", password="password", role="teacher")
        s1 = User(name="Student Bob", email="bob.student@example.com", password="password", role="student")
        
        db.add_all([admin, t1, t2, s1])
        db.commit()

        print("Seeding Subjects...")
        sub1 = Subject(name="Physics", theory_hours=3, lab_hours=2)
        sub2 = Subject(name="Mathematics", theory_hours=4, lab_hours=0)
        sub3 = Subject(name="Computer Science", theory_hours=2, lab_hours=4)

        db.add_all([sub1, sub2, sub3])
        db.commit()

        print("Seeding Classes...")
        c1 = Class(name="Physics 101 - Mr. Doe", subject_id=sub1.id, teacher_id=t1.id)
        c2 = Class(name="Math 101 - Ms. Smith", subject_id=sub2.id, teacher_id=t2.id)
        c3 = Class(name="CS 101 - Mr. Doe", subject_id=sub3.id, teacher_id=t1.id)

        db.add_all([c1, c2, c3])
        db.commit()

        print("Seeding Time Slots (Monday)...")
        t_slots = [
            TimeSlot(day="Monday", start_time=datetime.time(9, 0), end_time=datetime.time(10, 0), is_break=False),
            TimeSlot(day="Monday", start_time=datetime.time(10, 0), end_time=datetime.time(11, 0), is_break=False),
            TimeSlot(day="Monday", start_time=datetime.time(11, 0), end_time=datetime.time(11, 30), is_break=True),
            TimeSlot(day="Monday", start_time=datetime.time(11, 30), end_time=datetime.time(12, 30), is_break=False),
            TimeSlot(day="Monday", start_time=datetime.time(12, 30), end_time=datetime.time(13, 30), is_break=False),
        ]
        db.add_all(t_slots)
        db.commit()

        print("Seeding Student Enrollments...")
        en1 = StudentEnrollment(student_id=s1.id, class_id=c1.id)
        en2 = StudentEnrollment(student_id=s1.id, class_id=c3.id)
        
        db.add_all([en1, en2])
        db.commit()

        print("Seeding Timetable Entries...")
        # Physics Theory
        tt1 = Timetable(class_id=c1.id, timeslot_id=t_slots[0].id)
        # CS Labs
        tt2 = Timetable(class_id=c3.id, timeslot_id=t_slots[3].id)
        tt3 = Timetable(class_id=c3.id, timeslot_id=t_slots[4].id)

        db.add_all([tt1, tt2, tt3])
        db.commit()

        print("Successfully seeded sample data!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
