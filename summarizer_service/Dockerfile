FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Launch service
CMD ["uvicorn", "summarizer_service_app:app", "--host", "0.0.0.0", "--port", "8006"]
