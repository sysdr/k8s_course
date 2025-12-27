FROM python:3.9-slim
WORKDIR /app
COPY gateway.py .
RUN pip install flask requests flask-cors
CMD ["python", "gateway.py"]
