FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 環境変数を明示的に設定
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/vertex-ai-service-account.json \
    PROJECT_ID=zen-app-e3485 \
    LOCATION=asia-northeast1 \
    PYTHONPATH=/app

# ファイルの存在確認
RUN ls -la /app/vertex-ai-service-account.json || echo "Credentials file not found"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]