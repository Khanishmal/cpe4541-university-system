# services/shared_models.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Student(BaseModel):
    student_id: str
    name: str
    email: str

class Course(BaseModel):
    course_id: str
    name: str
    capacity: int
    enrolled: int = 0

class Registration(BaseModel):
    student_id: str
    course_id: str
    status: str  # REGISTERED, WAITLISTED, DROPPED
    timestamp: datetime