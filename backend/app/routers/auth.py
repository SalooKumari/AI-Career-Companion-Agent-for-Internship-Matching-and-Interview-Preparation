"""
Registration, login, and "who am I" endpoints.
A student registering IS creating their profile (name, email, password) —
this replaces the old public POST /students/ from Milestone 1; profile
fields beyond name/email are filled in afterwards on the Profile dashboard.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_student
from app.core.security import create_access_token, hash_password, verify_password
from app.models.student import Student
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.student import StudentOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Student).filter(Student.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists. Try logging in instead.",
        )

    if len(payload.password) < 6:
        raise HTTPException(status_code=422, detail="Password must be at least 6 characters.")

    student = Student(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    token = create_access_token(student.id)
    return TokenResponse(access_token=token, student_id=student.id, full_name=student.full_name)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.email == payload.email).first()
    if not student or not verify_password(payload.password, student.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(student.id)
    return TokenResponse(access_token=token, student_id=student.id, full_name=student.full_name)


@router.get("/me", response_model=StudentOut)
def get_me(current_student: Student = Depends(get_current_student)):
    return current_student
