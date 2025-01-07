FROM python:3.10-slim

WORKDIR /app

# 必要なライブラリをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# host ディレクトリ内のすべてのファイル(app.py, tools.py等)をコピー
COPY . . 

# JSONファイルをコンテナにコピーし、環境変数を設定
COPY vertex-ai-service-account.json /app/vertex-ai-service-account.json
ENV GOOGLE_APPLICATION_CREDENTIALS="/app/vertex-ai-service-account.json"

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.headless=true", "--server.enableCORS=false", "--server.address=0.0.0.0"]
