import os
import logging
import asyncio
from typing import Any

# google.cloud と MCP 関連のライブラリ
from google.cloud import bigquery
from dotenv import load_dotenv
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

# =========================================================
# 環境変数やログ設定
# =========================================================
load_dotenv()  # .env ファイル読み込み

logger = logging.getLogger('mcp_bigquery_server')
handler_stdout = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler_stdout.setFormatter(formatter)
logger.addHandler(handler_stdout)
logger.setLevel(logging.DEBUG)

# 環境変数の読み込みとデバッグ情報の出力
logger.debug("Current working directory: %s", os.getcwd())
logger.debug("Listing all environment variables:")
for key, value in os.environ.items():
    logger.debug(f"{key}: {value}")

# 環境変数の設定（バックアップ値付き）
PROJECT_ID = os.environ.get('PROJECT_ID', 'zen-app-e3485')
LOCATION = os.environ.get('LOCATION', 'asia-northeast1')
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '/app/vertex-ai-service-account.json')

# 環境変数とクレデンシャルファイルの検証
if not GOOGLE_APPLICATION_CREDENTIALS:
    logger.error("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set")
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS must be set")
elif not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    logger.error(f"Credentials file not found at {GOOGLE_APPLICATION_CREDENTIALS}")
    raise FileNotFoundError(f"Credentials file not found at {GOOGLE_APPLICATION_CREDENTIALS}")
else:
    logger.info(f"Found credentials file at {GOOGLE_APPLICATION_CREDENTIALS}")
    logger.debug(f"File permissions: {oct(os.stat(GOOGLE_APPLICATION_CREDENTIALS).st_mode)[-3:]}")

if not PROJECT_ID:
    logger.error("PROJECT_ID environment variable is not set")
    raise ValueError("PROJECT_ID must be set")

if not LOCATION:
    logger.error("LOCATION environment variable is not set")
    raise ValueError("LOCATION must be set")

logger.info(f"Initialized with PROJECT_ID={PROJECT_ID}, LOCATION={LOCATION}")

# =========================================================
# BigQueryDatabase クラス
# =========================================================
class BigQueryDatabase:
    def __init__(self, project: str, location: str):
        if not project:
            raise ValueError("Project is required")
        if not location:
            raise ValueError("Location is required")

        # BigQueryクライアントの初期化時にエラーログを取得しやすいよう try-except
        try:
            logger.debug(f"Initializing BigQuery client: project={project}, location={location}")
            self.client = bigquery.Client(project=project, location=location)
            logger.info("BigQuery client initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize BigQuery client. Please check credentials and settings.")
            raise  # 例外を再度送出

    def execute_query(self, query: str, params: list[bigquery.ScalarQueryParameter] | None = None) -> list[dict[str, Any]]:
        logger.debug(f"Executing query: {query}")
        try:
            if params:
                job = self.client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params))
            else:
                job = self.client.query(query)

            results = job.result()
            rows = [dict(row.items()) for row in results]
            logger.debug(f"Query returned {len(rows)} rows")
            return rows

        except Exception as e:
            logger.error(f"Database error executing query: {e}")
            # スタックトレースを含むログ出力
            logger.exception("Error details:")
            raise

    def list_tables(self, datasets_filter: list[str] = None) -> list[str]:
        logger.debug("Listing all tables")
        try:
            if datasets_filter:
                datasets = [self.client.dataset(dataset) for dataset in datasets_filter]
            else:
                datasets = list(self.client.list_datasets())

            logger.debug(f"Found {len(datasets)} datasets")

            tables = []
            for dataset in datasets:
                dataset_tables = self.client.list_tables(dataset.dataset_id)
                tables.extend([
                    f"{dataset.dataset_id}.{table.table_id}" for table in dataset_tables
                ])

            logger.debug(f"Found {len(tables)} tables")
            return tables

        except Exception as e:
            logger.error(f"Error listing tables: {e}")
            logger.exception("Error details:")
            raise

    def describe_table(self, table_name: str) -> list[dict[str, Any]]:
        logger.debug(f"Describing table: {table_name}")
        parts = table_name.split(".")
        if len(parts) != 2:
            raise ValueError(f"Invalid table name: {table_name}")

        dataset_id, table_id = parts
        query = f"""
            SELECT ddl
            FROM `{dataset_id}.INFORMATION_SCHEMA.TABLES`
            WHERE table_name = @table_name;
        """
        return self.execute_query(query, params=[
            bigquery.ScalarQueryParameter("table_name", "STRING", table_id),
        ])

# =========================================================
# main 関数 (MCPサーバーのエントリポイント)
# =========================================================
async def main(project: str, location: str):
    logger.info(f"Starting BigQuery MCP Server with project: {project} and location: {location}")
    db = BigQueryDatabase(project, location)

    server = Server("bigquery-manager")

    # MCPサーバーに登録するツール一覧
    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="execute-query",
                description="Execute a SELECT query on the BigQuery database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SELECT SQL query"},
                    },
                    "required": ["query"],
                },
            ),
            types.Tool(
                name="list-tables",
                description="List all tables in the BigQuery database",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "datasets_filter": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by these dataset names"
                        }
                    },
                },
            ),
            types.Tool(
                name="describe-table",
                description="Get the schema information for a specific table",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "e.g. dataset.table"},
                    },
                    "required": ["table_name"],
                },
            ),
        ]

    # MCPサーバーでのツール呼び出しハンドラ
    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent]:
        logger.debug(f"Handling tool execution request: {name}, arguments: {arguments}")
        try:
            if name == "list-tables":
                datasets_filter = arguments.get("datasets_filter", [])
                results = db.list_tables(datasets_filter)
                return [types.TextContent(type="text", text=str(results))]

            elif name == "describe-table":
                table_name = arguments["table_name"]
                results = db.describe_table(table_name)
                return [types.TextContent(type="text", text=str(results))]

            elif name == "execute-query":
                query = arguments["query"]
                results = db.execute_query(query)
                return [types.TextContent(type="text", text=str(results))]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Error in {name} tool call: {e}")
            logger.exception("Error details:")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        logger.info("Server running with stdio transport")
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="bigquery",
                server_version="0.2.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(
        main(
            project=PROJECT_ID,
            location=LOCATION,
        )
    )
