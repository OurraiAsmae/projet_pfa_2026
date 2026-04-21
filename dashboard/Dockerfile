FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN pip install --no-cache-dir \
    streamlit==1.31.0 \
    httpx==0.26.0 \
    plotly==5.18.0 \
    mlflow==2.9.2 \
    pandas==2.2.3 \
    scikit-learn==1.8.0 \
    xgboost==2.0.3 \
    lightgbm
COPY app.py .
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0"]
