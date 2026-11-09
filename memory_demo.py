
import sys
import sqlite3
from pathlib import Path

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

# Берём нашу основную программу
from main import create_agent, make_user_config

# 1. Выбираем этап
phase = sys.argv[1]

# 2. Создаём папку памяти
folder = Path(__file__).resolve().parent / "local-storage"
folder.mkdir(exist_ok=True)

# 3. Файл базы данных
db_path = folder / "memory_isolated_demo.sqlite"

# 4. Выбираем сообщение студента
if phase == "start":
    question = (
        "I cannot connect to Wi-Fi. "
        "I enabled Wi-Fi and tried reconnecting, "
        "but it still fails."
    )

elif phase == "resume":
    question = "Which problem and steps did I already try?"

else:
    raise ValueError("Use start or resume")

# 5. Открываем SQLite
with sqlite3.connect(
    db_path,
    check_same_thread=False
) as connection:

    memory = SqliteSaver(connection)

    # 6. Создаём нашего помощника с памятью
    agent = create_agent(
        profile="normal",
        user_id="demo-user-a",
        thread_id="memory-demo",
        checkpointer=memory
    )

    # 7. Настройки разговора
    config = make_user_config(
        user_id="demo-user-a",
        thread_id="memory-demo"
    )

    # 8. Проверяем старую историю
    previous = agent.get_state(config)

    before = len(
        previous.values.get("messages", [])
    )

    # 9. Отправляем новое сообщение
    result = agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config=config
    )

    # 10. Показываем результат
    print("Phase:", phase)
    print("Messages before:", before)
    print("Messages after:", len(result["messages"]))

    print("\nAI ANSWER:")
    print(result["messages"][-1].content)

print("\nPython process finished.")
