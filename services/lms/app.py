# services/lms/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import os

app = FastAPI(title="LMS Service", port=8001)

# ============== DATA MODELS ==============

class Course(BaseModel):
    course_id: str
    name: str
    instructor: str
    description: Optional[str] = ""

class CourseContent(BaseModel):
    course_id: str
    title: str
    content: str
    week: int

class Assignment(BaseModel):
    course_id: str
    title: str
    description: str
    due_date: str
    max_score: int

class Submission(BaseModel):
    student_id: str
    course_id: str
    assignment_title: str
    content: str
    submitted_at: str = datetime.now().isoformat()

class Announcement(BaseModel):
    course_id: str
    title: str
    message: str
    timestamp: str = datetime.now().isoformat()

# ============== STORAGE ==============

# In-memory storage (can be replaced with database)
courses_db = {}
content_db = {}
assignments_db = {}
submissions_db = []
announcements_db = []

# Sample data
sample_courses = [
    {"course_id": "CS101", "name": "Programming Fundamentals", "instructor": "Dr. Ahmed"},
    {"course_id": "CS201", "name": "Data Structures", "instructor": "Dr. Fatima"},
    {"course_id": "CS301", "name": "Operating Systems", "instructor": "Dr. Ali"},
]

for course in sample_courses:
    courses_db[course["course_id"]] = course

# ============== API ENDPOINTS ==============

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "lms",
        "timestamp": datetime.now().isoformat()
    }

# -------- COURSE MANAGEMENT --------

@app.get("/courses")
def get_all_courses():
    """Get all available courses"""
    return list(courses_db.values())

@app.get("/courses/{course_id}")
def get_course(course_id: str):
    """Get specific course details"""
    course = courses_db.get(course_id)
    if not course:
        raise HTTPException(404, f"Course {course_id} not found")
    return course

@app.post("/courses")
def create_course(course: Course):
    """Create a new course"""
    if course.course_id in courses_db:
        raise HTTPException(400, f"Course {course.course_id} already exists")
    courses_db[course.course_id] = course.dict()
    return {"status": "created", "course": course.course_id}

# -------- COURSE CONTENT --------

@app.get("/courses/{course_id}/content")
def get_course_content(course_id: str, week: Optional[int] = None):
    """Get course content (optionally filtered by week)"""
    if course_id not in content_db:
        return []
    
    content = content_db[course_id]
    if week:
        content = [c for c in content if c["week"] == week]
    return content

@app.post("/courses/{course_id}/content")
def add_course_content(course_id: str, content: CourseContent):
    """Add content to a course"""
    if course_id not in content_db:
        content_db[course_id] = []
    
    content_db[course_id].append(content.dict())
    return {
        "status": "added",
        "course": course_id,
        "total_items": len(content_db[course_id])
    }

# -------- ASSIGNMENT MANAGEMENT --------

@app.post("/assignments/create")
def create_assignment(assignment: Assignment):
    """Create a new assignment"""
    key = f"{assignment.course_id}:{assignment.title}"
    if key in assignments_db:
        raise HTTPException(400, f"Assignment {assignment.title} already exists")
    
    assignments_db[key] = assignment.dict()
    return {
        "status": "created",
        "assignment_id": key,
        "course": assignment.course_id
    }

@app.get("/assignments/{course_id}")
def get_course_assignments(course_id: str):
    """Get all assignments for a course"""
    return [
        v for k, v in assignments_db.items() 
        if k.startswith(f"{course_id}:")
    ]

@app.get("/assignments/{course_id}/{assignment_title}")
def get_assignment(course_id: str, assignment_title: str):
    """Get specific assignment details"""
    key = f"{course_id}:{assignment_title}"
    assignment = assignments_db.get(key)
    if not assignment:
        raise HTTPException(404, f"Assignment {assignment_title} not found")
    return assignment

# -------- SUBMISSION MANAGEMENT --------

@app.post("/submissions/submit")
def submit_assignment(submission: Submission):
    """Submit an assignment"""
    # Check if assignment exists
    key = f"{submission.course_id}:{submission.assignment_title}"
    if key not in assignments_db:
        raise HTTPException(404, f"Assignment {submission.assignment_title} not found")
    
    # Check if already submitted
    for sub in submissions_db:
        if (sub["student_id"] == submission.student_id and 
            sub["course_id"] == submission.course_id and
            sub["assignment_title"] == submission.assignment_title):
            return {
                "status": "already_submitted",
                "message": "You have already submitted this assignment",
                "submission": sub
            }
    
    submissions_db.append(submission.dict())
    return {
        "status": "submitted",
        "student": submission.student_id,
        "course": submission.course_id,
        "assignment": submission.assignment_title,
        "submitted_at": submission.submitted_at
    }

@app.get("/submissions/{student_id}")
def get_student_submissions(student_id: str):
    """Get all submissions by a student"""
    student_submissions = [
        s for s in submissions_db 
        if s["student_id"] == student_id
    ]
    return {
        "student_id": student_id,
        "submissions": student_submissions,
        "total": len(student_submissions)
    }

@app.get("/submissions/course/{course_id}")
def get_course_submissions(course_id: str):
    """Get all submissions for a course"""
    course_submissions = [
        s for s in submissions_db 
        if s["course_id"] == course_id
    ]
    return {
        "course_id": course_id,
        "submissions": course_submissions,
        "total": len(course_submissions)
    }

# -------- ANNOUNCEMENTS --------

@app.post("/announcements")
def create_announcement(announcement: Announcement):
    """Create a course announcement"""
    announcements_db.append(announcement.dict())
    return {
        "status": "created",
        "course": announcement.course_id,
        "title": announcement.title
    }

@app.get("/announcements/{course_id}")
def get_course_announcements(course_id: str):
    """Get announcements for a course"""
    return [
        a for a in announcements_db 
        if a["course_id"] == course_id
    ]

# -------- STATISTICS --------

@app.get("/statistics/course/{course_id}")
def get_course_statistics(course_id: str):
    """Get statistics for a course"""
    # Count assignments
    course_assignments = [
        v for k, v in assignments_db.items() 
        if k.startswith(f"{course_id}:")
    ]
    
    # Count submissions
    course_submissions = [
        s for s in submissions_db 
        if s["course_id"] == course_id
    ]
    
    # Count content items
    course_content = content_db.get(course_id, [])
    
    return {
        "course_id": course_id,
        "total_assignments": len(course_assignments),
        "total_submissions": len(course_submissions),
        "total_content_items": len(course_content),
        "unique_students": len(set(s["student_id"] for s in course_submissions))
    }

# ============== FOR LOCAL TESTING ==============
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting LMS Service on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)