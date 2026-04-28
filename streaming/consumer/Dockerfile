FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir kafka-python httpx
COPY streaming/consumer/kafka_consumer.py .
CMD ["python3", "kafka_consumer.py"]
