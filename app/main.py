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
    timetable = db.query(models.Timetable).all()

    return templates.TemplateResponse("student.html", {
        "request": request,
        "timetable": timetable
    })


@app.get("/teacher", response_class=HTMLResponse)
def teacher_page(request: Request):
    return templates.TemplateResponse("teacher.html", {"request": request})


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
    weekly_hours: int = Form(...),
    db: Session = Depends(get_db)
):
    subject = models.Subject(name=name, weekly_hours=weekly_hours)
    db.add(subject)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


# ➕ Add Class
@app.post("/add-class")
def add_class(
    name: str = Form(...),
    student_count: int = Form(...),
    db: Session = Depends(get_db)
):
    new_class = models.Class(name=name, student_count=student_count)
    db.add(new_class)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


# 🧠 Assign Teacher to Subject + Class
@app.post("/assign-teacher")
def assign_teacher(
    teacher_id: int = Form(...),
    subject_id: int = Form(...),
    class_id: int = Form(...),
    db: Session = Depends(get_db)
):
    assignment = models.TeacherAssignment(
        teacher_id=teacher_id,
        subject_id=subject_id,
        class_id=class_id
    )
    db.add(assignment)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


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
    subject_id: int = Form(...),
    teacher_id: int = Form(...),
    timeslot_id: int = Form(...),
    db: Session = Depends(get_db)
):
    try:
        entry = models.Timetable(
            class_id=class_id,
            subject_id=subject_id,
            teacher_id=teacher_id,
            timeslot_id=timeslot_id
        )
        db.add(entry)
        db.commit()
    except:
        db.rollback()
        return {"error": "Conflict detected (teacher/class already booked)"}

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

# 📊 View Timetable (API)
@app.get("/api/timetable")
def get_timetable(db: Session = Depends(get_db)):
    data = db.query(models.Timetable).all()

    result = []
    for row in data:
        result.append({
            "class_id": row.class_id,
            "subject_id": row.subject_id,
            "teacher_id": row.teacher_id,
            "timeslot_id": row.timeslot_id
        })

    return result