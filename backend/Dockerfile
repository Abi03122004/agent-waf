FROM python:3.11-slim

WORKDIR /app

# Install standard dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Ensure sample_data directory exists
RUN mkdir -p sample_data

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
