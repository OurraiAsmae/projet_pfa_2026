FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir kafka-python faker
COPY streaming/producer/transaction_producer.py .
CMD ["python3", "transaction_producer.py", "--rate", "1.0"]
