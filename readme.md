# PROJECT GENERATION PROMPT

You are a Staff-Level Python Backend Engineer.

Build a complete production-ready Django application named **LinkForge**.

## Project Overview

LinkForge is a scalable URL shortening platform that allows users to:

* Create shortened URLs
* Redirect users to original URLs
* Track click analytics
* View analytics dashboards
* Handle high read traffic efficiently
* Prevent abuse through rate limiting

The project must be portfolio-quality and interview-ready.

---

# Technology Stack

## Backend

* Django 5+
* PostgreSQL
* Redis

## Async Processing

Use Django native solutions where possible.

Choose ONE:

* Celery + Redis
  OR
* Django-RQ + Redis

Prefer Celery.

## Deployment

Application must deploy successfully on Render.

Generate all Render deployment files.

---

# Strict Requirements

DO NOT use:

* Django REST Framework
* GraphQL
* Flask
* FastAPI

Use only:

* Django Views
* Django Templates
* Django Forms
* Django ORM

---

# Core Features

## URL Shortening

User enters:

https://example.com/very/long/url

System generates:

https://domain.com/aB3xYz

Requirements:

* Unique short code
* Base62 encoding
* Collision prevention
* Configurable code length

---

## Redirect Service

When user visits:

/aB3xYz

System must:

1. Check Redis cache
2. If found:

   * redirect immediately
3. If not found:

   * query PostgreSQL
   * cache result
   * redirect

Return HTTP 301.

---

## Analytics

Track:

* Timestamp
* IP address
* Country
* Browser
* Operating system
* Referrer
* User agent

Store analytics asynchronously.

Redirect must not wait for analytics persistence.

---

## Dashboard

Create admin dashboard pages.

Show:

* Total links
* Total clicks
* Most clicked links
* Daily clicks
* Weekly clicks
* Monthly clicks

Use Django templates.

No React.

No Vue.

No frontend framework.

---

## Rate Limiting

Implement Redis-based rate limiting.

Example:

100 URL creations per hour per IP.

Return proper error message when exceeded.

---

# Database Design

Create models:

## ShortURL

Fields:

* id
* short_code
* original_url
* created_at
* updated_at
* click_count

Indexes required.

---

## ClickEvent

Fields:

* id
* short_url
* ip_address
* country
* browser
* operating_system
* referrer
* user_agent
* clicked_at

Indexes required.

---

# Performance Requirements

The project must demonstrate:

## Redis Caching

Cache URL mappings.

Cache analytics summaries.

---

## Database Optimization

Use:

* select_related
* prefetch_related
* indexes

Document why.

---

## Query Optimization

Avoid N+1 queries.

---

## Security

Implement:

* CSRF protection
* Security middleware
* Input validation
* URL validation
* XSS protection
* SQL injection protection

Use Django security best practices.

---

# Django Structure

Create clean architecture.

Example:

linkforge/
│
├── config/
├── apps/
│   ├── urls_app/
│   ├── analytics_app/
│   ├── dashboard_app/
│
├── templates/
├── static/
├── tests/
├── docs/
│
└── manage.py

Follow Django best practices.

---

# Testing

Create:

## Unit Tests

* URL generation
* Base62 encoding
* Analytics creation

## Integration Tests

* Redirect flow
* Cache behavior
* Dashboard pages

Coverage target:

80%+

---

# Environment Variables

Create .env.example

Include:

SECRET_KEY=

DEBUG=

DATABASE_URL=

REDIS_URL=

ALLOWED_HOSTS=

---

# Docker

Generate:

Dockerfile

docker-compose.yml

Production-ready.

---

# Render Deployment

Generate:

render.yaml

Requirements:

* Web Service
* PostgreSQL
* Redis

Environment variable setup

Health check endpoint:

/health/

Create health-check implementation.

---

# Logging

Implement structured logging.

Log:

* Redirect requests
* Failed redirects
* Background tasks
* Errors

---

# README

Generate a professional README containing:

* Project overview
* Architecture diagram
* Local setup
* Docker setup
* Render deployment
* Environment variables
* Testing instructions
* Database schema
* Scaling strategy
* Caching strategy
* Async analytics workflow

---

# Documentation

Create docs folder containing:

* architecture.md
* deployment.md
* scaling.md
* caching.md

---

# Interview Readiness

The project must clearly demonstrate:

* Django expertise
* PostgreSQL optimization
* Redis caching
* Async processing
* Rate limiting
* Scalability
* Production deployment

Code quality should reflect senior backend engineering standards.

Generate the complete project with all files and implementation details.
