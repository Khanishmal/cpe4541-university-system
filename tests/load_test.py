# tests/load_test.py
import requests
import time
import threading
from datetime import datetime
import statistics

BASE_URLS = {
    'registration': 'http://localhost:8000',
    'lms': 'http://localhost:8001',
    'exam': 'http://localhost:8002'
}

def test_registration():
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URLS['registration']}/register",
            json={"student_id": "TEST001", "course_id": "CS101"},
            timeout=5
        )
        status = response.status_code
    except:
        status = 500
    elapsed = time.time() - start
    return elapsed, status

def test_lms():
    start = time.time()
    try:
        response = requests.get(f"{BASE_URLS['lms']}/courses", timeout=5)
        status = response.status_code
    except:
        status = 500
    elapsed = time.time() - start
    return elapsed, status

def test_exam():
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URLS['exam']}/exam/submit",
            json={"student_id": "TEST001", "course_id": "CS101", 
                  "exam_name": "Test", "score": 75, "total": 100},
            timeout=5
        )
        status = response.status_code
    except:
        status = 500
    elapsed = time.time() - start
    return elapsed, status

def run_concurrent_test(num_requests=50):
    """Run concurrent requests"""
    results = {'registration': [], 'lms': [], 'exam': []}
    errors = {'registration': 0, 'lms': 0, 'exam': 0}
    
    def worker(endpoint, func):
        for _ in range(num_requests):
            elapsed, status = func()
            if status == 200:
                results[endpoint].append(elapsed * 1000)  # ms
            else:
                errors[endpoint] += 1
    
    threads = []
    for endpoint, func in [('registration', test_registration), 
                           ('lms', test_lms), 
                           ('exam', test_exam)]:
        t = threading.Thread(target=worker, args=(endpoint, func))
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Print results
    print("\n" + "="*60)
    print("LOAD TEST RESULTS")
    print("="*60)
    print(f"Requests per service: {num_requests}")
    print()
    
    for endpoint, times in results.items():
        if times:
            print(f"{endpoint.upper()} Service:")
            print(f"  Avg Response: {statistics.mean(times):.2f} ms")
            print(f"  Min Response: {min(times):.2f} ms")
            print(f"  Max Response: {max(times):.2f} ms")
            print(f"  Std Dev: {statistics.stdev(times):.2f} ms")
            print(f"  Errors: {errors[endpoint]}")
            print(f"  Success Rate: {(len(times)/num_requests)*100:.1f}%")
            print()
    
    # Overall summary
    total_success = sum(len(t) for t in results.values())
    total_errors = sum(errors.values())
    total_requests = num_requests * 3
    
    print("="*60)
    print("OVERALL SUMMARY")
    print("="*60)
    print(f"Total Requests: {total_requests}")
    print(f"Successful: {total_success}")
    print(f"Errors: {total_errors}")
    print(f"Success Rate: {(total_success/total_requests)*100:.1f}%")
    print("="*60)

def run_scalability_test():
    """Test scalability by increasing concurrent users"""
    print("\n" + "="*60)
    print("SCALABILITY TEST")
    print("="*60)
    print()
    
    user_counts = [10, 25, 50, 100]
    
    for users in user_counts:
        print(f"Testing with {users} concurrent users...")
        start = time.time()
        
        def worker():
            for _ in range(5):
                test_registration()
                test_lms()
                test_exam()
        
        threads = []
        for _ in range(users):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        elapsed = time.time() - start
        print(f"  Completed in: {elapsed:.2f} seconds")
        print(f"  Throughput: {users * 15 / elapsed:.1f} requests/second")
        print()

if __name__ == "__main__":
    print("🚀 Starting Load Tests...")
    run_concurrent_test(num_requests=30)
    run_scalability_test()