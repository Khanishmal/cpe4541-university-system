# services/exam/app.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import socket
import threading
import time
import numpy as np

app = FastAPI(title="Exam Service", port=8002)

# Storage
exam_results = {}
exam_schedules = {}

# Models
class GradeSubmission(BaseModel):
    student_id: str
    course_id: str
    exam_name: str
    score: float
    total: float

class ExamSchedule(BaseModel):
    course_id: str
    exam_name: str
    date: str
    duration_minutes: int

# ============== SOCKET SERVER (for distributed processing) ==============

def start_socket_server():
    """Background socket server for processing grades"""
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('0.0.0.0', 9999))
        server_socket.listen(5)
        server_socket.settimeout(1.0)
        
        while True:
            try:
                client_socket, addr = server_socket.accept()
                data = client_socket.recv(4096).decode()
                
                if data.startswith("PROCESS_GRADES:"):
                    grades_json = data.replace("PROCESS_GRADES:", "")
                    grades = json.loads(grades_json)
                    
                    # Calculate statistics
                    scores = [g.get("score", 0) for g in grades]
                    if scores:
                        stats = {
                            "mean": float(np.mean(scores)),
                            "median": float(np.median(scores)),
                            "std": float(np.std(scores)),
                            "max": max(scores),
                            "min": min(scores),
                            "count": len(scores)
                        }
                        client_socket.send(json.dumps(stats).encode())
                    else:
                        client_socket.send(json.dumps({"error": "No scores"}).encode())
                
                client_socket.close()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Socket error: {e}")
    except Exception as e:
        print(f"Socket server failed to start: {e}")

# Start socket server in background
socket_thread = threading.Thread(target=start_socket_server, daemon=True)
socket_thread.start()

# ============== API ENDPOINTS ==============

def get_letter_grade(percentage):
    if percentage >= 90: return "A"
    if percentage >= 80: return "B"
    if percentage >= 70: return "C"
    if percentage >= 60: return "D"
    return "F"

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "exam",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/exam/schedule")
def schedule_exam(exam: ExamSchedule):
    """Schedule an exam"""
    key = f"{exam.course_id}:{exam.exam_name}"
    exam_schedules[key] = exam.dict()
    return {
        "status": "scheduled",
        "exam": key,
        "details": exam.dict()
    }

@app.get("/exam/schedules")
def get_all_schedules():
    """Get all scheduled exams"""
    return list(exam_schedules.values())

@app.get("/exam/schedules/{course_id}")
def get_course_schedules(course_id: str):
    """Get schedules for a specific course"""
    return [
        v for k, v in exam_schedules.items() 
        if k.startswith(course_id)
    ]

@app.post("/exam/submit")
def submit_grade(submission: GradeSubmission, background_tasks: BackgroundTasks):
    """
    Submit a grade with background processing
    """
    key = f"{submission.student_id}:{submission.course_id}:{submission.exam_name}"
    
    percentage = (submission.score / submission.total) * 100
    grade = get_letter_grade(percentage)
    
    result = {
        **submission.dict(),
        "percentage": percentage,
        "grade": grade,
        "submitted_at": datetime.now().isoformat()
    }
    
    exam_results[key] = result
    
    # Process in background (simulate distributed processing)
    background_tasks.add_task(
        update_course_statistics, 
        submission.course_id, 
        submission.exam_name
    )
    
    return {
        "status": "submitted",
        "percentage": percentage,
        "grade": grade,
        "submission_id": key
    }

@app.post("/exam/submit-batch")
def submit_batch_grades(submissions: List[GradeSubmission]):
    """Submit multiple grades at once"""
    results = []
    for sub in submissions:
        key = f"{sub.student_id}:{sub.course_id}:{sub.exam_name}"
        percentage = (sub.score / sub.total) * 100
        results.append({
            "student": sub.student_id,
            "course": sub.course_id,
            "percentage": percentage,
            "grade": get_letter_grade(percentage)
        })
        exam_results[key] = {
            **sub.dict(),
            "percentage": percentage,
            "grade": get_letter_grade(percentage)
        }
    
    return {
        "status": "batch_submitted",
        "count": len(submissions),
        "results": results
    }

def update_course_statistics(course_id: str, exam_name: str):
    """Background task: update statistics"""
    # Find all submissions for this course/exam
    relevant = {
        k: v for k, v in exam_results.items() 
        if course_id in k and exam_name in k
    }
    
    scores = [v["percentage"] for v in relevant.values()]
    
    if scores:
        stats = {
            "course": course_id,
            "exam": exam_name,
            "average": np.mean(scores),
            "total_students": len(scores),
            "max": max(scores),
            "min": min(scores),
            "updated_at": datetime.now().isoformat()
        }
        print(f"📊 Statistics updated: {stats}")
        return stats
    return None

@app.get("/exam/statistics/{course_id}/{exam_name}")
def get_exam_statistics(course_id: str, exam_name: str):
    """Get statistics for an exam"""
    relevant = {
        k: v for k, v in exam_results.items() 
        if course_id in k and exam_name in k
    }
    
    scores = [v["percentage"] for v in relevant.values()]
    
    if not scores:
        raise HTTPException(404, "No submissions found")
    
    return {
        "course_id": course_id,
        "exam_name": exam_name,
        "total_students": len(scores),
        "average": np.mean(scores),
        "median": np.median(scores),
        "std": np.std(scores),
        "max": max(scores),
        "min": min(scores),
        "grade_distribution": {
            "A": len([s for s in scores if s >= 90]),
            "B": len([s for s in scores if 80 <= s < 90]),
            "C": len([s for s in scores if 70 <= s < 80]),
            "D": len([s for s in scores if 60 <= s < 70]),
            "F": len([s for s in scores if s < 60])
        }
    }

@app.get("/student/{student_id}/grades")
def get_student_grades(student_id: str):
    """Get all grades for a student"""
    student_results = {
        k: v for k, v in exam_results.items() 
        if k.startswith(student_id)
    }
    return {
        "student_id": student_id,
        "grades": list(student_results.values()),
        "total": len(student_results)
    }

@app.post("/exam/process-batch")
def process_batch_grades(scores: List[float]):
    """
    Call the socket server for distributed processing
    """
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(('localhost', 9999))
        
        # Send grades for processing
        message = f"PROCESS_GRADES:{json.dumps([{'score': s} for s in scores])}"
        client.send(message.encode())
        
        result = client.recv(4096).decode()
        client.close()
        
        return {
            "status": "processed",
            "input_count": len(scores),
            "statistics": json.loads(result)
        }
    except Exception as e:
        raise HTTPException(500, f"Socket processing failed: {str(e)}")

# ============== FOR LOCAL TESTING ==============
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Exam Service on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)