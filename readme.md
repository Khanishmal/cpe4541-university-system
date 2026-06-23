# 🏫 Cloud-Native Distributed University Management System

## 📌 Overview
A cloud-native distributed university management system with 3 microservices using Docker, Docker Compose, and distributed computing.

## 🚀 Services

| Service | Port | Description |
|---------|------|-------------|
| Registration | 8000 | Student registration and course enrollment |
| LMS | 8001 | Learning Management System |
| Exam | 8002 | Examination and grade management |
| Redis | 6379 | Caching and distributed locking |

## 🛠️ Technologies

- Python 3.10
- FastAPI
- Docker & Docker Compose
- Redis
- Multiprocessing & Multithreading
- Socket Programming

## 📦 Quick Start

### Prerequisites
- Docker
- Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/Khanishmal/Distribued-university-system.git
cd cpe4541-university-system

# Build and start services
docker compose up -d --build

# Check running containers
docker compose ps

# Test APIs
curl http://localhost:8000/courses
curl http://localhost:8001/courses
curl http://localhost:8002/exam/stats