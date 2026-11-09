
import sqlite3

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.sqlite import SqliteSaver


# Простой граф без OpenAI API
def create_test_graph(memory):

    def chatbot(state):
        return {
            "messages": [
                AIMessage(content="Message received.")
            ]
        }

    builder = StateGraph(MessagesState)

    builder.add_node("chatbot", chatbot)
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)

    return builder.compile(checkpointer=memory)


# TEST 6: Memory survives restart
def test_memory_after_restart(tmp_path):

    db_path = tmp_path / "conversations.sqlite"

    config = {
        "configurable": {
            "thread_id": "student-a"
        }
    }

    # Первый запуск программы
    with sqlite3.connect(
        db_path, check_same_thread=False
    ) as conn:

        memory = SqliteSaver(conn)
        graph = create_test_graph(memory)

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content="My Wi-Fi is not working.")
                ]
            },
            config=config
        )

        assert len(result["messages"]) == 2

    # Первый процесс завершил работу с базой.
    # Открываем SQLite заново.
    with sqlite3.connect(
        db_path, check_same_thread=False
    ) as conn:

        memory = SqliteSaver(conn)
        graph = create_test_graph(memory)

        old_messages = graph.get_state(
            config
        ).values["messages"]

        assert len(old_messages) == 2
        assert old_messages[0].content == "My Wi-Fi is not working."

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content="I tried reconnecting.")
                ]
            },
            config=config
        )

        assert len(result["messages"]) == 4


# TEST 7: Different threads remain separate
def test_different_threads(tmp_path):

    db_path = tmp_path / "separate.sqlite"

    with sqlite3.connect(
        db_path, check_same_thread=False
    ) as conn:

        memory = SqliteSaver(conn)
        graph = create_test_graph(memory)

        config_a = {
            "configurable": {"thread_id": "thread-a"}
        }

        config_b = {
            "configurable": {"thread_id": "thread-b"}
        }

        graph.invoke(
            {"messages": [HumanMessage(content="Wi-Fi problem")]},
            config=config_a
        )

        graph.invoke(
            {"messages": [HumanMessage(content="Password problem")]},
            config=config_b
        )

        messages_a = graph.get_state(
            config_a
        ).values["messages"]

        messages_b = graph.get_state(
            config_b
        ).values["messages"]

        assert len(messages_a) == 2
        assert len(messages_b) == 2

        assert messages_a[0].content == "Wi-Fi problem"
        assert messages_b[0].content == "Password problem"
