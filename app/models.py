from sqlalchemy import Column, Integer, String, ForeignKey, Time, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


# ---------------- USERS ----------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)  # admin / teacher / student


# ---------------- SUBJECTS ----------------
class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    weekly_hours = Column(Integer, nullable=False)


# ---------------- CLASSES ----------------
class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    student_count = Column(Integer)


# ---------------- TEACHER ASSIGNMENT ----------------
class TeacherAssignment(Base):
    __tablename__ = "teacher_assignments"

    id = Column(Integer, primary_key=True, index=True)

    teacher_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))


# ---------------- TIME SLOTS ----------------
class TimeSlot(Base):
    __tablename__ = "timeslots"

    id = Column(Integer, primary_key=True, index=True)

    day = Column(String, nullable=False)  # Monday, Tuesday...
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_break = Column(Boolean, default=False)


# ---------------- TIMETABLE ----------------
class Timetable(Base):
    __tablename__ = "timetable"

    id = Column(Integer, primary_key=True, index=True)

    class_id = Column(Integer, ForeignKey("classes.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"))
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"))

    # 🔥 Prevent clashes
    __table_args__ = (
        UniqueConstraint("teacher_id", "timeslot_id", name="no_teacher_overlap"),
        UniqueConstraint("class_id", "timeslot_id", name="no_class_overlap"),
    )


# ---------------- TEACHER AVAILABILITY ----------------
class TeacherAvailability(Base):
    __tablename__ = "teacher_availability"

    id = Column(Integer, primary_key=True, index=True)

    teacher_id = Column(Integer, ForeignKey("users.id"))
    timeslot_id = Column(Integer, ForeignKey("timeslots.id"))