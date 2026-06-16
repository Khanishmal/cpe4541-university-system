# distributed/socket_load_balancer.py
import socket
import threading
import json
import time
import random
from queue import Queue

class Worker:
    def __init__(self, worker_id, port=None):
        self.worker_id = worker_id
        self.port = port or 9000 + worker_id
        self.running = False
        self.socket = None
        
    def start(self):
        """Start worker server"""
        self.running = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('0.0.0.0', self.port))
        self.socket.listen(5)
        self.socket.settimeout(1.0)
        
        print(f"🔷 Worker {self.worker_id} listening on port {self.port}")
        
        while self.running:
            try:
                client, addr = self.socket.accept()
                data = client.recv(4096).decode()
                
                if data:
                    try:
                        grades = json.loads(data)
                        result = sum(grades) / len(grades)
                        client.send(str(result).encode())
                    except:
                        client.send("ERROR".encode())
                
                client.close()
            except socket.timeout:
                continue
            except:
                pass
    
    def stop(self):
        self.running = False

class LoadBalancer:
    def __init__(self, num_workers=3):
        self.workers = []
        self.current_worker = 0
        
        # Start workers
        for i in range(num_workers):
            worker = Worker(i)
            threading.Thread(target=worker.start, daemon=True).start()
            self.workers.append(worker)
        
        time.sleep(2)
        print(f"✅ Load balancer started with {num_workers} workers\n")
    
    def process(self, grades):
        """Send task to worker using round-robin"""
        worker = self.workers[self.current_worker]
        self.current_worker = (self.current_worker + 1) % len(self.workers)
        
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(5.0)
        client.connect(('localhost', worker.port))
        
        client.send(json.dumps(grades).encode())
        result = client.recv(4096).decode()
        client.close()
        
        return float(result)

def demo():
    print("\n" + "="*60)
    print("SOCKET-BASED LOAD BALANCER DEMO")
    print("="*60)
    print()
    
    # Create load balancer with 3 workers
    lb = LoadBalancer(num_workers=3)
    
    # Simulate student grade batches
    batch_results = []
    
    for i in range(10):
        # Random batch of 20-50 grades
        batch_size = random.randint(20, 50)
        grades = [random.randint(40, 100) for _ in range(batch_size)]
        
        start = time.time()
        result = lb.process(grades)
        elapsed = (time.time() - start) * 1000  # ms
        
        batch_results.append({
            'batch': i + 1,
            'size': batch_size,
            'average': result,
            'time_ms': elapsed
        })
        
        print(f"Batch {i+1:2d}: {batch_size:3d} grades → "
              f"Avg: {result:.2f} (took {elapsed:.1f}ms)")
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    total_grades = sum(r['size'] for r in batch_results)
    avg_time = sum(r['time_ms'] for r in batch_results) / len(batch_results)
    print(f"Total Batches: {len(batch_results)}")
    print(f"Total Grades Processed: {total_grades}")
    print(f"Average Processing Time: {avg_time:.1f}ms")
    print(f"Workers Used: 3 (distributed)")
    print("="*60)

if __name__ == "__main__":
    demo()