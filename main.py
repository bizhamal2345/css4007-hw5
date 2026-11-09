
import json
from pathlib import Path

# 1. Находим папку проекта
BASE_DIR = Path(__file__).resolve().parent

# 2. Находим папку с данными
DATA_DIR = BASE_DIR / "data"

# 3. Функция для чтения JSON-файлов
def load_data(filename):

    path = DATA_DIR / filename

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


# 4. Загружаем наши файлы
helpdesk = load_data("helpdesk.json")

service_data = load_data("service_status.json")

ticket_template = load_data("ticket_template.json")

demo_users = load_data("demo_users.json")

scenarios = load_data("scenarios.json")


# 5. Проверяем программу
if __name__ == "__main__":

    print("HW5 Helpdesk started!")

    print("Instructions:", list(helpdesk["instructions"].keys()))

    print("Status profiles:", list(service_data["profiles"].keys()))

    print("Demo users:", len(demo_users["users"]))

    print("Scenarios:", len(scenarios["scenarios"]))

# LANGGRAPH AI AGENT

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from tools import (
    find_instructions,
    make_status_tool,
    make_safe_ticket_tool
)


# Создаём нашего AI-помощника
def create_agent(profile, user_id, thread_id, checkpointer=None):

    # 1. Создаём три инструмента
    tools = [
        find_instructions,
        make_status_tool(profile),
        make_safe_ticket_tool(profile, user_id, thread_id)
    ]

    # 2. Подключаем LLM
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0
    )

    model = llm.bind_tools(tools)

    # 3. Узел модели
    def chatbot(state):

        system = SystemMessage(
            content=(
                "You are a university IT helpdesk. "
                "Use tools for instructions and service status. "
                "Use only the fictional helpdesk data. "
                "Do not invent information. "
                "Prepare a ticket only when requested. "
                "Never request passwords or recovery codes. "
                "Tickets are local drafts, not submitted tickets. Never claim a ticket was created unless the tool confirms Ticket draft saved."
            )
        )

        answer = model.invoke(
            [system] + state["messages"]
        )

        return {"messages": [answer]}

    # 4. Создаём LangGraph
    builder = StateGraph(MessagesState)

    builder.add_node("chatbot", chatbot)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "chatbot")
    builder.add_conditional_edges("chatbot", tools_condition)
    builder.add_edge("tools", "chatbot")

    return builder.compile(checkpointer=checkpointer)


# Тестируем программу
if __name__ == "__main__":

    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not configured.")

    else:
        agent = create_agent(
            profile="normal",
            user_id="demo-user-a",
            thread_id="test-main"
        )

        question = (
            "Give me Wi-Fi instructions and check "
            "the Wi-Fi service status. "
            "Do not create a ticket."
        )

        for event in agent.stream(
            {"messages": [HumanMessage(content=question)]},
            config={"recursion_limit": 12},
            stream_mode="updates"
        ):

            for node, update in event.items():

                print("\nNODE:", node)

                for message in update["messages"]:

                    if getattr(message, "tool_calls", None):
                        for call in message.tool_calls:
                            print("TOOL:", call["name"])

                    elif message.type == "tool":
                        print("TOOL RESULT:")
                        print(message.content)

                    elif message.type == "ai":
                        print("FINAL ANSWER:")
                        print(message.content)


# USER MEMORY CONFIGURATION
def make_user_config(user_id: str, thread_id: str) -> dict:

    if not user_id or not thread_id:
        raise ValueError("user_id and thread_id are required")

    # Уникальный ID для каждого студента и разговора
    internal_thread_id = (
        f"user:{len(user_id)}:{user_id}|"
        f"thread:{len(thread_id)}:{thread_id}"
    )

    return {
        "configurable": {
            "thread_id": internal_thread_id,
            "user_id": user_id
        },
        "recursion_limit": 12
    }


# USER MEMORY CONFIGURATION
def make_user_config(user_id: str, thread_id: str) -> dict:

    if not user_id or not thread_id:
        raise ValueError("user_id and thread_id are required")

    # Уникальный ID для каждого студента и разговора
    internal_thread_id = (
        f"user:{len(user_id)}:{user_id}|"
        f"thread:{len(thread_id)}:{thread_id}"
    )

    return {
        "configurable": {
            "thread_id": internal_thread_id,
            "user_id": user_id
        },
        "recursion_limit": 12
    }

