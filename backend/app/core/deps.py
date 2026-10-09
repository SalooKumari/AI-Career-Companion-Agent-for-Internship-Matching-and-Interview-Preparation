"""
FastAPI dependencies for authentication.
Use `get_current_student` for any endpoint that just needs "who is logged
in". Use `require_self` on endpoints shaped like /students/{student_id}/...
so a logged-in student can only read/write their own data.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.student import Student

# tokenUrl is only used to populate FastAPI's auto-generated /docs "Authorize"
# button; our actual login endpoint accepts JSON, not form-encoded data.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_student(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Student:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_error

    student_id = decode_access_token(token)
    if student_id is None:
        raise credentials_error

    student = db.query(Student).filter(Student.id == student_id).first()
    if student is None:
        raise credentials_error

    return student


def require_self(
    student_id: int,
    current_student: Student = Depends(get_current_student),
) -> Student:
    """Dependency for routes with a {student_id} path param: ensures the
    logged-in student can only act on their own data."""
    if current_student.id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own data.",
        )
    return current_student
