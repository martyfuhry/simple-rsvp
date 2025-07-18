# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create static directory if missing
RUN mkdir -p static

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
