
import sys
from pathlib import Path

# Находим папку проекта
PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR))

# Импортируем инструменты проекта
from tools import (
    find_instructions,
    make_status_tool,
    make_safe_ticket_tool
)

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage


# TEST 1: Instructions
def test_find_instructions():

    wifi = find_instructions.invoke({"topic": "Wi-Fi"})
    password = find_instructions.invoke({"topic": "password"})
    unknown = find_instructions.invoke({"topic": "screen"})

    assert "Campus-Demo" in wifi
    assert "Forgot password" in password
    assert unknown == "No instructions found."


# TEST 2: Service status
def test_service_status():

    normal = make_status_tool("normal")
    outage = make_status_tool("wifi_outage")
    unknown = make_status_tool("status_unavailable")

    assert "Status: operational" in normal.invoke({
        "service": "wifi"
    })

    assert "Status: outage" in outage.invoke({
        "service": "wifi"
    })

    assert "Status: unknown" in unknown.invoke({
        "service": "wifi"
    })


# TEST 3: No permission
def test_ticket_without_permission():

    ticket_tool = make_safe_ticket_tool(
        "normal",
        "demo-user-a",
        "pytest-no-permission"
    )

    # Создаём граф без LLM
    builder = StateGraph(MessagesState)
    builder.add_node("tools", ToolNode([ticket_tool]))
    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)
    graph = builder.compile()

    # Студент не просит заявку
    user = HumanMessage(
        content="My Wi-Fi does not work."
    )

    # Имитируем неправильное действие LLM
    ai = AIMessage(
        content="",
        tool_calls=[{
            "name": "prepare_ticket",
            "args": {
                "problem": "Wi-Fi does not work",
                "steps_tried": ["Tried reconnecting"],
                "category": "wifi"
            },
            "id": "pytest-call-1",
            "type": "tool_call"
        }]
    )

    folder = PROJECT_DIR / "outputs" / "tickets"
    before = set(folder.glob("*.json"))

    result = graph.invoke({
        "messages": [user, ai]
    })

    after = set(folder.glob("*.json"))

    assert "Ticket not created" in result["messages"][-1].content
    assert before == after

# TEST 4 AND TEST 5: Ticket authorization

import json
import shutil
import tools as helpdesk_tools


def make_test_graph(tmp_path, monkeypatch):

    # Создаём временную папку для тестов
    data_folder = tmp_path / "data"
    data_folder.mkdir()

    # Копируем настоящий шаблон заявки
    shutil.copy2(
        PROJECT_DIR / "data" / "ticket_template.json",
        data_folder / "ticket_template.json"
    )

    # Направляем тестовые заявки во временную папку
    monkeypatch.setattr(
        helpdesk_tools,
        "DATA_DIR",
        data_folder
    )

    ticket_tool = helpdesk_tools.make_safe_ticket_tool(
        "normal",
        "demo-user-a",
        "pytest-authorization"
    )

    builder = StateGraph(MessagesState)
    builder.add_node("tools", ToolNode([ticket_tool]))
    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)

    return builder.compile()


def make_ticket_call():
    return AIMessage(
        content="",
        tool_calls=[{
            "name": "prepare_ticket",
            "args": {
                "problem": "Wi-Fi does not connect",
                "steps_tried": [
                    "Enabled Wi-Fi",
                    "Tried reconnecting"
                ],
                "category": "wifi"
            },
            "id": "test-ticket-call",
            "type": "tool_call"
        }]
    )


# TEST 4: Explicit permission
def test_ticket_with_permission(tmp_path, monkeypatch):

    graph = make_test_graph(tmp_path, monkeypatch)

    user = HumanMessage(
        content=(
            "Please create a support ticket for my Wi-Fi. "
            "I enabled Wi-Fi and tried reconnecting."
        )
    )

    result = graph.invoke({
        "messages": [user, make_ticket_call()]
    })

    # Проверяем, что инструмент создал заявку
    assert "Ticket draft saved" in result["messages"][-1].content

    files = list((tmp_path / "outputs" / "tickets").glob("*.json"))

    assert len(files) == 1

    # Проверяем содержимое JSON
    with open(files[0], encoding="utf-8") as f:
        ticket = json.load(f)["ticket"]

    assert ticket["status"] == "draft"
    assert ticket["user_id"] == "demo-user-a"
    assert ticket["category"] == "wifi"
    assert ticket["service_status"] == "operational"
    assert len(ticket["steps_tried"]) == 2


# TEST 5: Old permission is not valid
def test_old_permission_not_reused(tmp_path, monkeypatch):

    graph = make_test_graph(tmp_path, monkeypatch)

    old_message = HumanMessage(
        content="Please create a support ticket for my Wi-Fi."
    )

    new_message = HumanMessage(
        content="What Wi-Fi instructions should I try?"
    )

    result = graph.invoke({
        "messages": [
            old_message,
            new_message,
            make_ticket_call()
        ]
    })

    assert "Ticket not created" in result["messages"][-1].content

    files = list((tmp_path / "outputs" / "tickets").glob("*.json"))

    assert len(files) == 0
