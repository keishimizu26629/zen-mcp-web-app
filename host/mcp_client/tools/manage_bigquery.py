import requests
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field


class BQListTablesRequest(BaseModel):
    datasets_filter: list[str] = Field(
        description="テーブル一覧を取得したいデータセット名。空リスト`[]`で全データセット対象"
    )

@tool(args_schema=BQListTablesRequest)
def list_tables(datasets_filter: list[str]) -> str:
    """
    BigQueryのテーブル一覧を取得するためのツール。
    """
    # ローカルのdocker-compose環境での例。HuggingFace/本番環境ではCloud Run URLを設定
    url = "http://server:8000/bigquery/list-tables"
    payload = {"datasets_filter": datasets_filter}
    response = requests.get(url, json=payload)
    response.raise_for_status()
    return response.text


class BQDescribeTableRequest(BaseModel):
    table_name: str = Field(description="説明を取得したいテーブルの名前")

@tool(args_schema=BQDescribeTableRequest)
def describe_table(table_name: str) -> str:
    """
    BigQueryテーブル情報取得ツール。
    """
    url = "http://server:8000/bigquery/describe-table"
    payload = {"table_name": table_name}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.text


class BQExecuteQueryRequest(BaseModel):
    query: str = Field(description="実行したいクエリ")

@tool(args_schema=BQExecuteQueryRequest)
def execute_query(query: str) -> str:
    """
    BigQuery クエリ実行ツール。
    """
    url = "http://server:8000/bigquery/execute-query"
    payload = {"query": query}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.text
