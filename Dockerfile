FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install flask pillow
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
