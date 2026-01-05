FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app/backend

EXPOSE 5000

# note the module path: backend.app:app
CMD ["gunicorn", "-b", "0.0.0.0:5000", "backend.app:app", "--workers", "2", "--threads", "4", "--timeout", "60"]
