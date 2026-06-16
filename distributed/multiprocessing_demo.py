# distributed/multiprocessing_demo.py
import multiprocessing as mp
import time
import numpy as np
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

def heavy_computation(grades_batch):
    """CPU-intensive grade processing"""
    result = 0
    for grade in grades_batch:
        result += grade ** 2 + np.sqrt(grade) * 10
    return result / len(grades_batch)

def single_threaded(grades):
    """Process sequentially"""
    results = []
    for chunk in grades:
        results.append(heavy_computation(chunk))
    return results

def multiprocessing_demo(grades, num_workers=4):
    """Process in parallel"""
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        return list(executor.map(heavy_computation, grades))

def threading_demo(grades, num_threads=4):
    """Process using threads"""
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        return list(executor.map(heavy_computation, grades))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PARALLEL PROCESSING PERFORMANCE COMPARISON")
    print("="*60)
    
    # Generate test data
    num_students = 50000
    num_chunks = 4
    chunk_size = num_students // num_chunks
    
    all_grades = np.random.randint(0, 100, num_students)
    chunks = []
    for i in range(num_chunks):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < num_chunks - 1 else num_students
        chunks.append(all_grades[start:end])
    
    print(f"Processing {num_students} grades across {num_chunks} chunks\n")
    
    # 1. Single-threaded
    print("1. Single-threaded...")
    start = time.time()
    single_result = single_threaded(chunks)
    single_time = time.time() - start
    print(f"   Time: {single_time:.3f} seconds")
    print(f"   Avg: {np.mean(single_result):.2f}")
    
    # 2. Multiprocessing
    print("\n2. Multiprocessing (4 workers)...")
    start = time.time()
    multi_result = multiprocessing_demo(chunks)
    multi_time = time.time() - start
    print(f"   Time: {multi_time:.3f} seconds")
    print(f"   Avg: {np.mean(multi_result):.2f}")
    
    # 3. Threading
    print("\n3. Threading (4 workers)...")
    start = time.time()
    thread_result = threading_demo(chunks)
    thread_time = time.time() - start
    print(f"   Time: {thread_time:.3f} seconds")
    print(f"   Avg: {np.mean(thread_result):.2f}")
    
    # Results
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON")
    print("="*60)
    print(f"Multiprocessing Speedup: {single_time/multi_time:.2f}x")
    print(f"Threading Speedup: {single_time/thread_time:.2f}x")
    print("="*60)