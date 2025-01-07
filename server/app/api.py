import os
import logging
import asyncio
from typing import Any
from fastapi import APIRouter
from app.schemas import BQListTablesRequest, BQDescribeTableRequest, BQExecuteQueryRequest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

router = APIRouter()
logger = logging.getLogger('mcp_api')

async def async_request(name: str, server_command: str, server_script: str, req: Any = None):
    # パスの確認
    script_path = os.path.join('/app', 'app', 'bigquery_manager', 'server.py')
    logger.debug(f"Current directory: {os.getcwd()}")
    logger.debug(f"Script path: {script_path}")
    logger.debug(f"Script exists: {os.path.exists(script_path)}")
    
    # 実行するコマンドの確認
    command = "which python"
    result = os.system(command)
    logger.debug(f"Python path check result: {result}")

    server_params = StdioServerParameters(
        command="/usr/local/bin/python",  # 完全なパスを指定
        args=[script_path],
        env={
            "GOOGLE_APPLICATION_CREDENTIALS": "/app/vertex-ai-service-account.json",
            "PROJECT_ID": "zen-app-e3485",
            "LOCATION": "asia-northeast1",
            "PYTHONPATH": "/app"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                name=name,
                arguments=req.dict() if req is not None else {},
            )
            return result.content[0].text

@router.get("/list-tables")
def list_tables(req: BQListTablesRequest = None):
    return asyncio.run(
        async_request(
            name="list-tables",
            server_command="python",
            server_script="server.py",  # この引数は実際には使用されません
            req=req,
        )
    )

@router.post("/describe-table")
def describe_table(req: BQDescribeTableRequest):
    return asyncio.run(
        async_request(
            name="describe-table",
            server_command="python",
            server_script="server.py",  # この引数は実際には使用されません
            req=req,
        )
    )

@router.post("/execute-query")
def execute_query(req: BQExecuteQueryRequest):
    return asyncio.run(
        async_request(
            name="execute-query",
            server_command="python",
            server_script="server.py",  # この引数は実際には使用されません
            req=req,
        )
    )