# services/registration/app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import redis
import json
import os

# Create FastAPI app
app = FastAPI(title="Registration Service", port=8000)

# Connect to Redis (will run in Kubernetes)
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=6379,
    decode_responses=True
)

# Request/Response Models
class RegisterRequest(BaseModel):
    student_id: str
    course_id: str

# In-memory course database (for demo)
courses = {
    "CS101": {"course_id": "CS101", "name": "Programming Fundamentals", "capacity": 50, "enrolled": 0},
    "CS201": {"course_id": "CS201", "name": "Data Structures", "capacity": 40, "enrolled": 0},
    "CS301": {"course_id": "CS301", "name": "Operating Systems", "capacity": 35, "enrolled": 0},
    "CS401": {"course_id": "CS401", "name": "Database Systems", "capacity": 30, "enrolled": 0},
    "CS501": {"course_id": "CS501", "name": "Computer Networks", "capacity": 25, "enrolled": 0},
}

# ============== API ENDPOINTS ==============

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "registration",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/courses")
def get_all_courses():
    """Get all available courses"""
    return list(courses.values())

@app.get("/courses/{course_id}")
def get_course(course_id: str):
    """Get specific course details"""
    course = courses.get(course_id)
    if not course:
        raise HTTPException(404, f"Course {course_id} not found")
    return course

@app.post("/register")
def register_student(request: RegisterRequest):
    """
    Register a student for a course with waitlist support
    """
    # Check if course exists
    course = courses.get(request.course_id)
    if not course:
        raise HTTPException(404, f"Course {request.course_id} not found")
    
    # Check if already registered
    reg_key = f"reg:{request.student_id}:{request.course_id}"
    if redis_client.exists(reg_key):
        return {
            "status": "ALREADY_REGISTERED",
            "course": request.course_id,
            "student": request.student_id
        }
    
    # Check capacity
    if course["enrolled"] < course["capacity"]:
        # Register student
        course["enrolled"] += 1
        
        # Store registration in Redis (with 24hr expiry)
        redis_client.setex(
            reg_key,
            86400,
            json.dumps({
                "student_id": request.student_id,
                "course_id": request.course_id,
                "timestamp": datetime.now().isoformat(),
                "status": "REGISTERED"
            })
        )
        
        return {
            "status": "REGISTERED",
            "course": request.course_id,
            "student": request.student_id,
            "message": "Successfully registered"
        }
    else:
        # Course is full - add to waitlist
        waitlist_key = f"waitlist:{request.course_id}"
        position = redis_client.llen(waitlist_key) + 1
        redis_client.rpush(waitlist_key, request.student_id)
        
        return {
            "status": "WAITLISTED",
            "position": position,
            "course": request.course_id,
            "student": request.student_id,
            "message": f"Course full. Position {position} on waitlist"
        }

@app.get("/student/{student_id}/courses")
def get_student_courses(student_id: str):
    """Get all courses a student is registered for"""
    # Find all registrations for this student
    keys = redis_client.keys(f"reg:{student_id}:*")
    courses_list = []
    
    for key in keys:
        data = json.loads(redis_client.get(key))
        # Add course name
        course_info = courses.get(data["course_id"])
        if course_info:
            data["course_name"] = course_info["name"]
        courses_list.append(data)
    
    return {
        "student_id": student_id,
        "courses": courses_list,
        "total": len(courses_list)
    }

@app.delete("/drop/{student_id}/{course_id}")
def drop_course(student_id: str, course_id: str):
    """Drop a course"""
    reg_key = f"reg:{student_id}:{course_id}"
    
    if not redis_client.exists(reg_key):
        raise HTTPException(404, "Registration not found")
    
    # Remove registration
    redis_client.delete(reg_key)
    
    # Update course enrollment
    course = courses.get(course_id)
    if course and course["enrolled"] > 0:
        course["enrolled"] -= 1
        
        # Check waitlist and promote next student
        waitlist_key = f"waitlist:{course_id}"
        next_student = redis_client.lpop(waitlist_key)
        if next_student:
            # Register the waitlisted student
            redis_client.setex(
                f"reg:{next_student}:{course_id}",
                86400,
                json.dumps({
                    "student_id": next_student,
                    "course_id": course_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "REGISTERED"
                })
            )
            course["enrolled"] += 1
    
    return {
        "status": "DROPPED",
        "student": student_id,
        "course": course_id
    }

# ============== FOR LOCAL TESTING ==============
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Registration Service on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)