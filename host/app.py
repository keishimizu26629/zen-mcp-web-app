import streamlit as st
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.callbacks import StreamlitCallbackHandler
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
import vertexai
from langchain_google_vertexai import ChatVertexAI

# MCPツール関数のインポート
from mcp_client.tools.manage_bigquery import list_tables, describe_table, execute_query

CUSTOM_SYSTEM_PROMPT = """
あなたは、ユーザーのリクエストに基づいて、ツールを用いて情報を取得してユーザーを支援するアシスタントです。
ユーザーのコメントから判断して、もし利用可能なツールがある場合は、
そのツールを使用して、取得内容をわかりやすい表現や出力形式にした上でユーザーに提供してください。
もし利用可能がない場合はその旨を伝えながら、自然に回答してください。
ユーザーが使用する言語で回答するようにしてください。
"""

def initialize():
    st.header("Gemini-BigQuery Agent")
    # Vertex AI プロジェクト設定 (ご自身のプロジェクトID、リージョンを指定)
    vertexai.init(project="zen-app-e3485", location="asia-northeast1")
    return StreamlitChatMessageHistory(key="chat_messages")

def create_agent():
    tools = [list_tables, describe_table, execute_query]
    prompt = ChatPromptTemplate.from_messages([
        ("system", CUSTOM_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    # Gemini 2.0 Flashモデルを指定
    llm = ChatVertexAI(temperature=0, model="gemini-2.0-flash-exp")
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        memory=None
    )

def main():
    chat_history = initialize()
    agent = create_agent()

    for chat in chat_history.messages:
        st.chat_message(chat.type).write(chat.content)

    # ユーザーからの入力を取得
    if prompt := st.chat_input(placeholder="どんなテーブルがあるか教えてください"):
        st.chat_message("user").write(prompt)

        with st.chat_message("assistant"):
            # ストリームハンドラー設定（エージェント思考過程等を表示可能）
            st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=True)
            # エージェントに指示を渡す
            response = agent.invoke(
                {"input": prompt, "chat_history": chat_history.messages},
                {"callbacks": [st_cb]},
            )
            st.write(response["output"])

        chat_history.add_messages(
            [
                HumanMessage(content=prompt),
                AIMessage(content=response["output"]),
            ]
        )

if __name__ == "__main__":
    main()