import uvicorn
from fastapi import FastAPI
from app.api import router as bigquery_router

app = FastAPI(
    title="MCP BigQuery API",
    description="API that interacts with BigQuery via MCP server",
    version="0.1.0"
)

# 簡易的なHello Worldエンドポイント(疎通確認用)
@app.get("/hello")
def hello():
    return {"message": "Hello World"}

# BigQuery関連のルーターをマウント
app.include_router(bigquery_router, prefix="/bigquery", tags=["bigquery"])

if __name__ == "__main__":
    # ローカル実行用
    uvicorn.run(app, host="0.0.0.0", port=8000)
