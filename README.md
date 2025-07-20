# Vendor Order Processor 

Event-driven system for processing vendor orders asynchronously and aggregate vendor metrics.

## Setup Instructions

### Prerequisites
- Docker & Docker Compose installed

Build and run the app:
```bash
docker-compose up --build
```

## Features
- Submit vendor order events via API
- Redis Streams for message queueing
- Asynchronous event consumer with FastAPI
- Persistence of data in SQLite with SQLAlchemy
- Vendor metrics
- Token-based authentication for APIs
- Generate Vendor-Revenue plot using Matplotlib
- Swagger Documentation: Accessible using ```http://localhost:8000/docs ```


## Tech Stack
- **Language:** Python 
- **Framework:** FastAPI
- **Queue:** Redis Streams
- **DB:** SQLite
- **ORM:** SQLAlchemy
- **Auth:** Simple token-based auth
- **Container:** Docker + Docker Compose
