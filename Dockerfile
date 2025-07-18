# Use official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Safer: copy requirements separately and explicitly
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy app code
COPY . .

# Create static directory if missing
RUN mkdir -p static

# Expose port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
