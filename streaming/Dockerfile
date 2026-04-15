FROM python:3.10-slim
WORKDIR /app
RUN pip install --no-cache-dir \
    redis==5.0.1 \
    httpx==0.26.0
COPY streaming/consumer/governance_processor.py .
CMD ["python3", "governance_processor.py"]
