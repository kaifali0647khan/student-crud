"""CRUD endpoints for /students."""
import sqlite3
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from . import crud
from .database import get_conn
from .schemas import StudentCreate, StudentOut, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])


def _get_or_404(conn, student_id: int):
    row = crud.get_student(conn, student_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")
    return row


def _write(conn, fn, *args):
    """Run a write and turn the UNIQUE(email) violation into a clean 409."""
    try:
        return fn(conn, *args)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="A student with this email already exists")


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, conn=Depends(get_conn)):
    new_id = _write(conn, crud.create_student, student.model_dump())
    return dict(crud.get_student(conn, new_id))


@router.get("", response_model=list[StudentOut])
def list_students(
    response: Response,
    name: Optional[str] = Query(None, description="Partial name match"),
    course: Optional[str] = Query(None, description="Partial course match"),
    email: Optional[str] = Query(None, description="Exact email"),
    born_after: Optional[date] = Query(None, description="DOB strictly after this date"),
    born_before: Optional[date] = Query(None, description="DOB strictly before this date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    conn=Depends(get_conn),
):
    total, rows = crud.list_students(conn, name, course, email, born_after, born_before, skip, limit)
    response.headers["X-Total-Count"] = str(total)
    return [dict(r) for r in rows]


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, conn=Depends(get_conn)):
    return dict(_get_or_404(conn, student_id))


@router.put("/{student_id}", response_model=StudentOut)
def replace_student(student_id: int, student: StudentCreate, conn=Depends(get_conn)):
    """Full update: every required field must be sent again."""
    _get_or_404(conn, student_id)
    data = student.model_dump()  # omitted optional fields become None -> cleared
    _write(conn, crud.update_student, student_id, data)
    return dict(crud.get_student(conn, student_id))


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, changes: StudentUpdate, conn=Depends(get_conn)):
    """Partial update: only the fields you send are changed."""
    current = _get_or_404(conn, student_id)
    data = changes.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=422, detail="No fields provided to update")
    for required in ("name", "date_of_birth"):
        if required in data and data[required] is None:
            raise HTTPException(status_code=422, detail=f"{required} cannot be null")
    merged_email = data["email"] if "email" in data else current["email"]
    merged_phone = data["phone"] if "phone" in data else current["phone"]
    if not merged_email and not merged_phone:
        raise HTTPException(status_code=422, detail="Student must keep at least one contact (email or phone)")
    _write(conn, crud.update_student, student_id, data)
    return dict(crud.get_student(conn, student_id))


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, conn=Depends(get_conn)):
    if not crud.delete_student(conn, student_id):
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
