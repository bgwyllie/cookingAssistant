FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Run the app
CMD ["uvicorn", "html_fetcher_app:app", "--host", "0.0.0.0", "--port", "8003"]
