# distributed/mpi_processor.py
from mpi4py import MPI
import numpy as np
import time
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

def generate_grades(num_students=10000):
    """Generate random grades"""
    return np.random.randint(40, 100, num_students)

def process_chunk(grades_chunk):
    """Process a chunk of grades"""
    return {
        'mean': float(np.mean(grades_chunk)),
        'std': float(np.std(grades_chunk)),
        'min': float(np.min(grades_chunk)),
        'max': float(np.max(grades_chunk)),
        'count': len(grades_chunk),
        'sum': float(np.sum(grades_chunk))
    }

if __name__ == "__main__":
    if rank == 0:
        print("\n" + "="*60)
        print("MPI DISTRIBUTED GRADE PROCESSING")
        print("="*60)
        print(f"Running with {size} processes\n")
        
        # Generate grades
        num_students = 10000
        all_grades = generate_grades(num_students)
        print(f"Generated {num_students} grades")
        
        # Split data
        chunk_size = num_students // size
        chunks = []
        for i in range(size):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < size - 1 else num_students
            chunks.append(all_grades[start:end])
        
        # Send chunks to workers
        start_time = time.time()
        
        for i in range(1, size):
            comm.send(chunks[i], dest=i, tag=11)
        
        # Process own chunk
        local_result = process_chunk(chunks[0])
        
        # Collect results
        all_results = [local_result]
        for i in range(1, size):
            result = comm.recv(source=i, tag=22)
            all_results.append(result)
        
        # Aggregate results
        total_count = sum(r['count'] for r in all_results)
        total_sum = sum(r['sum'] for r in all_results)
        global_mean = total_sum / total_count
        
        elapsed = time.time() - start_time
        
        print(f"\n--- RESULTS ---")
        print(f"Global Mean Grade: {global_mean:.2f}")
        print(f"Total Students Processed: {total_count}")
        print(f"Execution Time: {elapsed:.4f} seconds")
        print(f"Throughput: {total_count/elapsed:.0f} grades/second")
        print("="*60)
        
    else:
        # Worker processes
        chunk = comm.recv(source=0, tag=11)
        result = process_chunk(chunk)
        comm.send(result, dest=0, tag=22)