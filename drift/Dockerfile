FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir \
    evidently==0.4.16 \
    pandas==2.2.3 \
    numpy==1.26.4 \
    scikit-learn==1.8.0 \
    httpx==0.26.0 \
    redis==5.0.1 \
    schedule==1.2.0
COPY drift_monitor.py .
CMD ["python3", "drift_monitor.py"]
