from pydantic import BaseModel, Field
from typing import List

class BQListTablesRequest(BaseModel):
    datasets_filter: List[str] = Field(
        default=[],
        description="取得したいデータセット名のリスト。空リストの場合は全てのデータセットを対象"
    )

class BQDescribeTableRequest(BaseModel):
    table_name: str = Field(..., description="説明を取得したいテーブル名(例: dataset.table)")

class BQExecuteQueryRequest(BaseModel):
    query: str = Field(..., description="実行したいSQLクエリ")
