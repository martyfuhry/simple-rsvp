FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install flask
ENV ADMIN_PASSWORD=letmein
CMD ["python", "app.py"]
