# High-Concurrency Movie Ticket Reservation System

A production-ready, highly available RESTful API service for real-time movie ticket bookings built with Django REST Framework, Celery, Redis, and PostgreSQL. The system uses pessimistic database locking to prevent overbooking during high-traffic bursts and offloads PDF receipt generation to background workers asynchronously.

---

## Key Features

- **Atomic Transactions & Pessimistic Locking**: Prevents race conditions and overbooking when multiple users attempt to purchase remaining tickets simultaneously using `select_for_update()`.
- **Asynchronous Task Queue**: Uses Celery with Redis as a broker to generate PDF receipts without blocking HTTP request/response cycles.
- **Dynamic Receipt Generation**: Automatically builds downloadable PDF receipts using `ReportLab` upon successful booking confirmation.
- **Fully Containerized**: Complete Docker Compose setup isolating the API web server, Celery worker pool, PostgreSQL database, and Redis cache/broker.
- **Persistent Volume Mounts**: Host-to-container bind mounting ensures generated media (PDF receipts) and database state persist across container restarts.

---

## Architecture Overview

```
[ Client / Postman / cURL ]
          │
          ▼
   ┌──────────────┐
   │  Django REST │ (Producer)
   │  Framework   │
   └──────┬───────┘
          │ 1. Atomic Transaction & Lock
          ├────────────────────────────────┐
          │                                ▼
          │                     ┌────────────────────┐
          │                     │ PostgreSQL Database│
          │                     └────────────────────┘
          │ 2. Dispatch Task
          ▼
   ┌──────────────┐
   │ Redis Broker │
   └──────┬───────┘
          │ 3. Consume Task
          ▼
   ┌──────────────┐
   │Celery Worker │ (Consumer)
   └──────┬───────┘
          │ 4. Generate PDF Receipt
          ▼
   ┌──────────────┐
   │  /media/*.pdf│
   └──────────────┘
```

---

## Tech Stack

- **Framework**: Django 5.x / Django REST Framework
- **Database**: PostgreSQL
- **Message Broker & Result Backend**: Redis
- **Task Queue**: Celery
- **PDF Engine**: ReportLab
- **Containerization**: Docker & Docker Compose

---

## System Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- `docker compose` support.

---

## Quickstart & Installation

### 1. Environment Configuration

Create a `.env` file in the root directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,web

POSTGRES_DB=ticket_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

MEDIA_URL=/media/
MEDIA_ROOT=/app/media/
```

### 2. Build and Launch Containers

Spin up all microservices in detached mode:

```bash
docker compose up --build -d
```

Verify that all 3 main application services are active:

```bash
docker ps
```
*Expected Services: `django_ticket_api`, `ticket_redis`, and `celery_ticket_worker`.*

### 3. Run Database Migrations

Apply database schemas to the PostgreSQL container:

```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

---

## API Reference & Testing Guide

### 1. Create Events (Movies)

**Endpoint:** `POST /api/events/`

```bash
# Seed 'American Psycho'
curl -X POST http://localhost:8000/api/events/ \
     -H "Content-Type: application/json" \
     -d '{"name": "American Psycho", "total_tickets": 100, "available_tickets": 100, "price_per_ticket": "12.50"}'

# Seed 'Taxi Driver'
curl -X POST http://localhost:8000/api/events/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Taxi Driver", "total_tickets": 80, "available_tickets": 80, "price_per_ticket": "10.00"}'
```

### 2. List All Events

**Endpoint:** `GET /api/events/`

```bash
curl -X GET http://localhost:8000/api/events/
```

**Example Output:**
```json
[
  {
    "id": 1,
    "name": "American Psycho",
    "total_tickets": 100,
    "available_tickets": 100,
    "price_per_ticket": "12.50"
  },
  {
    "id": 2,
    "name": "Taxi Driver",
    "total_tickets": 80,
    "available_tickets": 80,
    "price_per_ticket": "10.00"
  }
]
```

### 3. Book Movie Tickets

**Endpoint:** `POST /api/tickets/book/`

```bash
curl -X POST http://localhost:8000/api/tickets/book/ \
     -H "Content-Type: application/json" \
     -d '{"event": 1, "user_email": "cinemafan@example.com", "quantity": 2}'
```

**Example Response:**
```json
{
  "message": "Booking successful!",
  "booking_id": 1,
  "status": "CONFIRMED"
}
```

---

## Monitoring Background Processing

To observe Celery picking up tasks and generating receipts in real time, view the worker container logs:

```bash
docker compose logs -f celery_worker
```

**Expected Log Stream:**
```text
[INFO/MainProcess] Task tickets.tasks.generate_receipt_and_send_email[...] received
[WARNING/MainProcess] [CELERY WORKER] Generated PDF receipt at /app/media/receipt_1.pdf and sent to cinemafan@example.com
[INFO/MainProcess] Task tickets.tasks.generate_receipt_and_send_email[...] succeeded in 0.08s
```

Generated PDF receipts will immediately sync to your host machine inside the local `./media/` directory.