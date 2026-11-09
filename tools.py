import json
from pathlib import Path
from langchain_core.tools import tool

# Находим папку с данными
DATA_DIR = Path(__file__).resolve().parent / "data"

# Загружаем инструкции
with open(DATA_DIR / "helpdesk.json", encoding="utf-8") as f:
    helpdesk = json.load(f)


# Инструмент для поиска инструкций
@tool
def find_instructions(topic: str) -> str:
    """Find Wi-Fi or password instructions."""

    # Приводим текст к одному формату
    topic = topic.lower().replace("-", "").replace(" ", "")

    # Определяем тему
    if "wifi" in topic:
        topic = "wifi"
    elif "password" in topic:
        topic = "password"
    else:
        return "No instructions found."

    # Получаем инструкции
    steps = helpdesk["instructions"][topic]["steps"]

    return "\n".join(steps)


# Проверяем инструмент
if __name__ == "__main__":

    print("TEST 1: Wi-Fi")
    result = find_instructions.invoke({
        "topic": "Wi-Fi troubleshooting"
    })
    print(result)

    print("\nTEST 2: Password")
    result = find_instructions.invoke({
        "topic": "Password recovery"
    })
    print(result)

    print("\nTEST 3: Unknown")
    result = find_instructions.invoke({
        "topic": "Laptop screen"
    })
    print(result)

# SECOND TOOL: Check service status

# Загружаем данные о сервисах
with open(DATA_DIR / "service_status.json", encoding="utf-8") as f:
    service_data = json.load(f)


# Создаём инструмент для выбранного сценария
def make_status_tool(profile):

    @tool
    def check_service_status(service: str) -> str:
        """Check Wi-Fi or account recovery service status."""

        # Приводим название к одному формату
        service = service.lower().replace("-", "_")

        if service == "password":
            service = "account_recovery"

        if service == "wi_fi":
            service = "wifi"

        # Получаем данные нужного сервиса
        result = service_data["profiles"][profile].get(service)

        if result is None:
            return "Unknown service."

        # Возвращаем результат
        return (
            "Status: " + result["status"] +
            "\nMessage: " + result["message"]
        )

    return check_service_status

# THIRD TOOL: Prepare ticket

import uuid


def make_ticket_tool(profile, user_id, thread_id, conditional=True):

    @tool
    def prepare_ticket(
        problem: str,
        steps_tried: list[str],
        category: str
    ) -> str:
        """Create a local support ticket draft for Wi-Fi or password problems."""

        # 1. Проверяем информацию студента
        if not problem.strip() or not steps_tried:
            return "Please provide the problem and steps tried."

        if not all(step.strip() for step in steps_tried):
            return "Please provide valid steps tried."

        # 2. Определяем категорию
        topic = category.lower().replace("-", "").replace(" ", "")

        if "wifi" in topic:
            category_name = "wifi"
            service = "wifi"

        elif "password" in topic or "account_recovery" in topic:
            category_name = "password"
            service = "account_recovery"

        else:
            return "Unknown ticket category."

        # 3. Проверяем состояние сервиса
        status = service_data["profiles"][profile][service]["status"]

        if conditional and status != "operational":
            return "Ticket not created. Service status: " + status

        # 4. Загружаем шаблон
        with open(DATA_DIR / "ticket_template.json", encoding="utf-8") as f:
            template = json.load(f)

        ticket = template["ticket"].copy()

        # 5. Заполняем заявку
        ticket["ticket_id"] = "T-" + uuid.uuid4().hex[:12]
        ticket["user_id"] = user_id
        ticket["thread_id"] = thread_id
        ticket["category"] = category_name
        ticket["summary"] = problem
        ticket["steps_tried"] = steps_tried
        ticket["service_status"] = status
        ticket["status_profile"] = profile

        # 6. Создаём папку
        folder = DATA_DIR.parent / "outputs" / "tickets"
        folder.mkdir(parents=True, exist_ok=True)

        # 7. Сохраняем JSON
        filename = folder / (ticket["ticket_id"] + ".json")

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(
                {"ticket": ticket},
                f,
                indent=4,
                ensure_ascii=False
            )

        return "Ticket draft saved: " + str(filename)

    return prepare_ticket

# SAFE TICKET TOOL

from typing import Annotated
from langgraph.prebuilt import InjectedState


def make_safe_ticket_tool(profile, user_id, thread_id):

    # Наш предыдущий инструмент
    original_tool = make_ticket_tool(
        profile, user_id, thread_id
    )

    @tool("prepare_ticket")
    def safe_prepare_ticket(
        problem: str,
        steps_tried: list[str],
        category: str,
        messages: Annotated[list, InjectedState("messages")]
    ) -> str:
        """Create a ticket only when the user explicitly requests it."""

        # Берём только сообщения студента
        user_messages = [
            m.content.lower()
            for m in messages
            if m.type == "human" and isinstance(m.content, str)
        ]

        # Проверяем, не запретил ли студент заявку
        if user_messages:
            last = user_messages[-1]

            if any(word in last for word in [
                "do not", "don't", "without a ticket",
                "не созда", "не делай"
            ]):
                return "Ticket not created. User did not authorize it."

        # Ищем явную просьбу создать заявку
        requested = any(
            "ticket" in text and
            any(word in text for word in [
                "prepare", "create", "open",
                "file", "draft"
            ])
            for text in user_messages[-1:]
        )

        if not requested:
            return "Ticket not created. User did not request a ticket."

        # Если просьба была, вызываем настоящий инструмент
        return original_tool.invoke({
            "problem": problem,
            "steps_tried": steps_tried,
            "category": category
        })

    return safe_prepare_ticket
