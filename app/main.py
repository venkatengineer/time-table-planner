from fastapi import FastAPI, Request, Depends, Form, Response
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


# ---------------- AUTH ROUTES ---------------- #

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, role: str = "student", error: str = None):
    return templates.TemplateResponse("login.html", {"request": request, "role": role, "error": error})

@app.post("/login")
def login_post(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == email,
        models.User.password == password,
        models.User.role == role
    ).first()

    if not user:
        return templates.TemplateResponse("login.html", {
            "request": {},
            "role": role,
            "error": "Invalid email or password."
        })

    # Successful login, redirect to dashboard and set cookies
    redirect_url = f"/{role}"
    res = RedirectResponse(redirect_url, status_code=303)
    res.set_cookie(key="user_id", value=str(user.id))
    res.set_cookie(key="user_role", value=user.role)
    return res

@app.get("/logout")
def logout():
    res = RedirectResponse("/", status_code=303)
    res.delete_cookie("user_id")
    res.delete_cookie("user_role")
    return res


# ---------------- PAGE ROUTES ---------------- #

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("user_role") != "admin":
        return RedirectResponse("/login?role=admin", status_code=303)

    teachers = db.query(models.User).filter(models.User.role == "teacher").all()
    subjects = db.query(models.Subject).all()
    classes = db.query(models.Class).all()
    timeslots = db.query(models.TimeSlot).all()
    timetable = db.query(models.Timetable).all()

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "teachers": teachers,
        "subjects": subjects,
        "classes": classes,
        "timeslots": timeslots,
        "timetable": timetable
    })


@app.get("/student", response_class=HTMLResponse)
def student_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    user_role = request.cookies.get("user_role")
    
    if not user_id or user_role != "student":
        return RedirectResponse("/login?role=student", status_code=303)

    # Only pass this student's enrollments
    enrollments = db.query(models.StudentEnrollment).filter(models.StudentEnrollment.student_id == int(user_id)).all()
    enrolled_class_ids = [e.class_id for e in enrollments]

    # Only show timetable for enrolled classes
    data = db.query(models.Timetable).filter(models.Timetable.class_id.in_(enrolled_class_ids)).all() if enrolled_class_ids else []
    
    timetable = []
    for row in data:
        cls = db.query(models.Class).filter(models.Class.id == row.class_id).first()
        if cls:
            timetable.append({
                "class_id": row.class_id,
                "subject_id": cls.subject_id,
                "teacher_id": cls.teacher_id,
                "timeslot_id": row.timeslot_id
            })

    classes_orm = db.query(models.Class).all()
    classes_json = [
        {"id": c.id, "name": c.name, "teacher_id": c.teacher_id, "subject_id": c.subject_id}
        for c in classes_orm
    ]

    return templates.TemplateResponse("student.html", {
        "request": request,
        "timetable": timetable,
        "classes": classes_orm,
        "classes_json": classes_json,
        "enrollments": enrollments,
        "student_id": user_id
    })


@app.get("/teacher", response_class=HTMLResponse)
def teacher_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if request.cookies.get("user_role") != "teacher":
        return RedirectResponse("/login?role=teacher", status_code=303)

    timeslots = db.query(models.TimeSlot).all()
    # Only get this teacher's availability
    availability = db.query(models.TeacherAvailability).filter(models.TeacherAvailability.teacher_id == int(user_id)).all()
    
    return templates.TemplateResponse("teacher.html", {
        "request": request,
        "timeslots": timeslots,
        "availability": availability,
        "teacher_id": user_id
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


# 🎓 Toggle Student Enrollment
@app.post("/toggle-enroll")
async def toggle_enroll(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    class_id = int(data.get("class_id"))
    student_id = request.cookies.get("user_id")
    if not student_id:
        return {"error": "Unauthorized"}
        
    student_id = int(student_id)

    existing = db.query(models.StudentEnrollment).filter(
        models.StudentEnrollment.student_id == student_id,
        models.StudentEnrollment.class_id == class_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "removed"}
    
    enrollment = models.StudentEnrollment(student_id=student_id, class_id=class_id)
    db.add(enrollment)
    db.commit()
    return {"status": "added"}

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

# 👨‍🏫 Toggle Teacher Availability
@app.post("/toggle-availability")
async def toggle_availability(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    timeslot_id = int(data.get("timeslot_id"))
    teacher_id = request.cookies.get("user_id")
    if not teacher_id:
        return {"error": "Unauthorized"}
    
    teacher_id = int(teacher_id)

    # Check if this teacher already has an entry for this slot
    existing = db.query(models.TeacherAvailability).filter(
        models.TeacherAvailability.teacher_id == teacher_id,
        models.TeacherAvailability.timeslot_id == timeslot_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "removed"}
    
    # Check max limit: Prevent more than 2 teachers picking the same slot
    count = db.query(models.TeacherAvailability).filter(
        models.TeacherAvailability.timeslot_id == timeslot_id
    ).count()

    if count >= 2:
        return {"error": "Slot capacity reached (Max 2 teachers). Please pick another time."}

    availability = models.TeacherAvailability(teacher_id=teacher_id, timeslot_id=timeslot_id)
    db.add(availability)
    db.commit()

    return {"status": "added"}



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