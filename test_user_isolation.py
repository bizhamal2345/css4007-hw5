
import sys
import sqlite3
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.sqlite import SqliteSaver

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

from main import make_user_config


def test_same_thread_different_users(tmp_path):

    # Временная SQLite-база
    db_path = tmp_path / "users.sqlite"

    def chatbot(state):
        return {
            "messages": [
                AIMessage(content="Message received.")
            ]
        }

    with sqlite3.connect(
        db_path, check_same_thread=False
    ) as conn:

        memory = SqliteSaver(conn)

        builder = StateGraph(MessagesState)
        builder.add_node("chatbot", chatbot)
        builder.add_edge(START, "chatbot")
        builder.add_edge("chatbot", END)

        graph = builder.compile(checkpointer=memory)

        # Одинаковый thread_id, разные пользователи
        config_a = make_user_config("demo-user-a", "chat-1")
        config_b = make_user_config("demo-user-b", "chat-1")

        graph.invoke(
            {"messages": [HumanMessage(content="My Wi-Fi is broken")]},
            config=config_a
        )

        graph.invoke(
            {"messages": [HumanMessage(content="My password is forgotten")]},
            config=config_b
        )

        # Проверяем историю каждого студента
        messages_a = graph.get_state(config_a).values["messages"]
        messages_b = graph.get_state(config_b).values["messages"]

        assert len(messages_a) == 2
        assert len(messages_b) == 2

        assert messages_a[0].content == "My Wi-Fi is broken"
        assert messages_b[0].content == "My password is forgotten"

        assert config_a["configurable"]["thread_id"] != \
               config_b["configurable"]["thread_id"]
