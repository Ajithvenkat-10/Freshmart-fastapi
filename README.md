# Freshmart-fastapi
fastapi-grocery-delivery-app
Run this in PowerShell to create the README:
powershellcd C:\Users\ajith\downloads\freshmart
Then create the file:
powershellNew-Item README.md
notepad README.md
Notepad will open. Paste this:
markdown# FreshMart Grocery Delivery App 🛵

A complete FastAPI backend for a grocery delivery system built as part of Innomatics Research Labs internship.

## Features
- REST APIs with FastAPI
- Pydantic data validation & error handling
- CRUD operations (Create, Read, Update, Delete)
- Cart & Checkout multi-step workflow
- Search, sorting, and pagination
- API testing using Swagger UI

## Tech Stack
- Python
- FastAPI
- Pydantic
- Uvicorn

## Run Locally

Install dependencies:
pip install -r requirements.txt

Run the server:
uvicorn main:app --reload

Open Swagger UI:
http://127.0.0.1:8000/docs

## API Endpoints
- GET / — Home route
- GET /items — All items
- GET /items/{item_id} — Item by ID
- GET /items/summary — Summary
- GET /items/filter — Filter items
- GET /items/search — Search items
- GET /items/sort — Sort items
- GET /items/page — Paginate items
- GET /items/browse — Combined browse
- POST /items — Add new item
- PUT /items/{item_id} — Update item
- DELETE /items/{item_id} — Delete item
- GET /orders — All orders
- POST /orders — Place order
- POST /cart/add — Add to cart
- GET /cart — View cart
- DELETE /cart/{item_id} — Remove from cart
- POST /cart/checkout — Checkout

## Author
Ajith V — Innomatics Research Labs FastAPI Internship
