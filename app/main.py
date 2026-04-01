from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine, Base
import app.models as models

# ---------------- INIT ---------------- #

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Static + Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# ---------------- DB DEPENDENCY ---------------- #

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- PAGE ROUTES ---------------- #

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    teachers = db.query(models.User).filter(models.User.role == "teacher").all()
    subjects = db.query(models.Subject).all()
    classes = db.query(models.Class).all()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "teachers": teachers,
        "subjects": subjects,
        "classes": classes
    })


@app.get("/student", response_class=HTMLResponse)
def student_page(request: Request, db: Session = Depends(get_db)):
    data = db.query(models.Timetable).all()
    timetable = []
    for row in data:
        cls = db.query(models.Class).filter(models.Class.id == row.class_id).first()
        timetable.append({
            "class_id": row.class_id,
            "subject_id": cls.subject_id if cls else None,
            "teacher_id": cls.teacher_id if cls else None,
            "timeslot_id": row.timeslot_id
        })

    classes_orm = db.query(models.Class).all()
    # Serialize to plain dicts for JSON embedding in the template
    classes_json = [
        {"id": c.id, "name": c.name, "teacher_id": c.teacher_id, "subject_id": c.subject_id}
        for c in classes_orm
    ]

    students = db.query(models.User).filter(models.User.role == "student").all()
    enrollments = db.query(models.StudentEnrollment).all()

    return templates.TemplateResponse("student.html", {
        "request": request,
        "timetable": timetable,
        "classes": classes_orm,        # used in Jinja loops
        "classes_json": classes_json,  # used in JS
        "students": students,
        "enrollments": enrollments
    })


@app.get("/teacher", response_class=HTMLResponse)
def teacher_page(request: Request, db: Session = Depends(get_db)):
    teachers = db.query(models.User).filter(models.User.role == "teacher").all()
    timeslots = db.query(models.TimeSlot).all()
    availability = db.query(models.TeacherAvailability).all()
    return templates.TemplateResponse("teacher.html", {
        "request": request,
        "teachers": teachers,
        "timeslots": timeslots,
        "availability": availability
    })


# ---------------- API ROUTES ---------------- #

# ➕ Add User (Teacher / Student)
@app.post("/add-user")
def add_user(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user = models.User(
        name=name,
        email=email,
        password=password,
        role=role
    )
    db.add(user)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


# ➕ Add Subject
@app.post("/add-subject")
def add_subject(
    name: str = Form(...),
    theory_hours: int = Form(...),
    lab_hours: int = Form(...),
    db: Session = Depends(get_db)
):
    subject = models.Subject(
        name=name, 
        theory_hours=theory_hours,
        lab_hours=lab_hours
    )
    db.add(subject)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


# ➕ Add Class
@app.post("/add-class")
def add_class(
    name: str = Form(...),
    teacher_id: int = Form(...),
    subject_id: int = Form(...),
    db: Session = Depends(get_db)
):
    new_class = models.Class(
        name=name, 
        teacher_id=teacher_id, 
        subject_id=subject_id
    )
    db.add(new_class)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


# 🎓 Enroll Student
@app.post("/enroll-student")
def enroll_student(
    student_id: int = Form(...),
    class_id: int = Form(...),
    db: Session = Depends(get_db)
):
    enrollment = models.StudentEnrollment(
        student_id=student_id,
        class_id=class_id
    )
    db.add(enrollment)
    db.commit()
    
    return RedirectResponse("/student", status_code=303)

# ⏰ Add Time Slot
@app.post("/add-timeslot")
def add_timeslot(
    day: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...),
    is_break: bool = Form(False),
    db: Session = Depends(get_db)
):
    slot = models.TimeSlot(
        day=day,
        start_time=start_time,
        end_time=end_time,
        is_break=is_break
    )
    db.add(slot)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


# 📅 Create Timetable Entry (CORE)
@app.post("/create-timetable")
def create_timetable(
    class_id: int = Form(...),
    timeslot_id: int = Form(...),
    entry_type: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # ---------------- THEORY ----------------
        if entry_type == "theory":
            entry = models.Timetable(
                class_id=class_id,
                timeslot_id=timeslot_id
            )
            db.add(entry)

        # ---------------- LAB ----------------
        elif entry_type == "lab":

            # Get current slot
            slot1 = db.query(models.TimeSlot).filter(models.TimeSlot.id == timeslot_id).first()

            # Find next consecutive slot (same day, next time)
            slot2 = db.query(models.TimeSlot).filter(
                models.TimeSlot.day == slot1.day,
                models.TimeSlot.start_time == slot1.end_time
            ).first()

            if not slot2:
                return {"error": "No consecutive slot available for lab"}

            # Insert BOTH slots
            entry1 = models.Timetable(
                class_id=class_id,
                timeslot_id=slot1.id
            )

            entry2 = models.Timetable(
                class_id=class_id,
                timeslot_id=slot2.id
            )

            db.add(entry1)
            db.add(entry2)

        db.commit()

    except:
        db.rollback()
        return {"error": "Conflict detected or invalid slot"}

    return RedirectResponse("/admin", status_code=303)

@app.post("/add-availability")
def add_availability(
    teacher_id: int = Form(...),
    timeslot_id: int = Form(...),
    db: Session = Depends(get_db)
):
    availability = models.TeacherAvailability(
        teacher_id=teacher_id,
        timeslot_id=timeslot_id
    )

    db.add(availability)
    db.commit()

    return RedirectResponse("/teacher", status_code=303)



# ⏰ Timeslots API (for calendar JS)
@app.get("/api/timeslots")
def get_timeslots(db: Session = Depends(get_db)):
    slots = db.query(models.TimeSlot).all()
    result = []
    for s in slots:
        result.append({
            "id": s.id,
            "day": s.day,
            "start_time": s.start_time.strftime("%H:%M") if s.start_time else "",
            "end_time": s.end_time.strftime("%H:%M") if s.end_time else "",
            "is_break": s.is_break
        })
    return result


# 📊 View Timetable (API)
@app.get("/api/timetable")
def get_timetable(db: Session = Depends(get_db)):
    data = db.query(models.Timetable).all()

    result = []
    for row in data:
        cls = db.query(models.Class).filter(models.Class.id == row.class_id).first()
        result.append({
            "class_id": row.class_id,
            "subject_id": cls.subject_id,
            "teacher_id": cls.teacher_id,
            "timeslot_id": row.timeslot_id
        })

    return result