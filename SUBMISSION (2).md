# HW5 — My LangGraph Helpdesk

## Part 1 — How the graph works

### My graph and state

**Original graph (Part 1):**

![Original LangGraph with separate Wi-Fi, password, and other routes](diagrams/part1_original.png)

My state has three fields:

- message: the original user message
- category: the detected problem
- reply: the answer to the user

The read_request node reads the message and updates the category. The help nodes read the current state and return a reply using helpdesk.json.

A node returns updates to the state. A conditional edge chooses which node to run next. It does not change the state.

Each next node receives the current graph state, including updates from previous nodes.

START is the entry point. END finishes the graph. Compiling creates a runnable graph.

### Predictions before running

| **Message**                      | **Predicted route** | **Actual route** | **Result** |
| -------------------------------- | ------------------- | ---------------- | ---------- |
| I cannot connect to Wi-Fi.       | wifi_help           | wifi_help        | Correct    |
| I forgot my PASSWORD.            | password_help       | password_help    | Correct    |
| My laptop screen is broken.      | other_help          | other_help       | Correct    |
| My Wi-Fi password does not work. | wifi_help           | wifi_help        | Correct    |

All four predictions matched the actual results.

The program converts messages to lowercase, so PASSWORD and password are treated equally.

In the original graph, Wi-Fi has priority. When both topics are mentioned, wifi_help is selected because the Wi-Fi condition is checked first.

### My change to the graph

**Updated graph with clarification (Part 1):**

![Updated LangGraph: if both Wi-Fi and password appear, ask for clarification](diagrams/part1_updated.png)

I added a new category called "both".

If a message mentions Wi-Fi and password, the graph now uses clarify_problem.

For S04, the original route was: START -> read_request -> wifi_help -> END

For S05, the updated route was: START -> read_request -> clarify_problem -> END

In S05, the category changed to "both". The assistant asked which problem to solve first.

LangGraph controls the execution order and the transitions between nodes.

My Python functions check the message, choose a category and create the answer.

There is no LLM in Part 1.

### Execution logs

The actual results are saved in:

- outputs/S01.json
- outputs/S02.json
- outputs/S03.json
- outputs/S04.json
- outputs/S05.json

Each log shows the nodes visited and the state after each node.

## Part 2 — Model and tools

### Model and architecture

I used OpenAI's `gpt-4.1-mini` model with LangGraph. The model was configured with temperature 0.

The graph contains a chatbot node and a tools node.

**Model and tool execution graph:**

![LangGraph model and tool execution loop](diagrams/part2_tools.png)

The chatbot requests a tool when additional information or an action is needed. The ToolNode executes the requested Python function and returns the result to the chatbot.

The `tools_condition` decides whether to continue to the tools node or end the conversation.

The state stores conversation messages and tool results. A recursion limit prevents unlimited graph execution.

### Three reusable tools

**1. find_instructions**

This tool retrieves Wi-Fi and password recovery instructions from the local `helpdesk.json` file.

**2. check_service_status**

This tool checks the selected service status profile. For Wi-Fi it checks the `wifi` service. For password recovery it checks `account_recovery`.

**3. prepare_ticket**

This tool creates a local JSON ticket draft. It uses the problem description and steps already tried.

The system does not submit real university tickets.

A protective wrapper checks whether the user requested a ticket. It is a demonstration safeguard rather than a complete production authorization system.

### Part 1 versus Part 2

In Part 1, Python rules decide which node runs next.

In Part 2, the language model selects which tool to request. However, the tool itself performs the actual operation.

### Comparison of service status scenarios

**S06 — Normal service**

The Wi-Fi service was operational. The model called find_instructions, check_service_status, and prepare_ticket. One local ticket draft was created.

**S07 — Wi-Fi outage**

The model checked Wi-Fi status. The result showed a campus-wide outage. No ticket was created.

**S08 — Unknown service status**

The status source was unavailable. The model did not claim that Wi-Fi was operational or that an outage was confirmed.

No conditional ticket was created. The assistant offered the user a separate ticket option.

**S09 — Missing details**

The student initially requested a ticket without details and supplied the problem and attempted steps later.

This scenario requires careful handling of pending ticket requests. The current latest-message authorization rule may be too strict for this follow-up. Its saved log should be distinguished from a fresh replay.

## Part 3 — Memory

### Conversation memory

I used SQLite with the LangGraph SqliteSaver checkpointer to persist conversation messages.

Conversation memory stores the current problem, previous messages and troubleshooting steps.

A thread ID identifies an individual conversation.

### User memory

User memory stores information that should be available across different conversations for the same user, such as their preferred reply language.

User memory is different from conversation memory.

A new conversation should not automatically contain all messages from an earlier conversation.

However, the user's saved language preference should remain available.

### Memory demonstrations

**S10:** The assistant recalls earlier troubleshooting steps within the same conversation.

**S11:** Conversation state is restored after a separate Python process starts with the same saved storage.

**S12:** A saved Kazakh language preference is available in a new conversation for the same user.

**S13:** A different user should not receive the first user's conversation or preferences.

### SQLite restart demonstration

I executed:

`python memory_demo.py start`

The output showed:

- Messages before: 0
- Messages after: 4

Then I executed:

`python memory_demo.py resume`

The output showed:

- Messages before: 4
- Messages after: 6

The assistant recalled the Wi-Fi problem and the steps already attempted, including enabling Wi-Fi and reconnecting.

### Retrieval versus memory

Retrieving Wi-Fi instructions from helpdesk.json is retrieval.

Remembering what a student already tried is conversation memory.

Remembering a preferred language is user memory.

## Part 4 — Running and checking my work

### Environment

Python version: 3.13.18

LLM provider: OpenAI

Model: gpt-4.1-mini

The required Python libraries are listed with fixed versions in requirements.txt.

### Installation

From the project root:

```
python -m pip install -r requirements.txt
```

Set the OPENAI_API_KEY environment variable for model runs.

### Run the application

```
python main.py
```

### Check conversation memory

```
python memory_demo.py start
python memory_demo.py resume
```

### Run automated tests

```
python -m pytest -v tests/
```

### Run Part 1 scenarios

```
python run_scenarios.py
```

Individual model scenarios can be executed with the run_model_scenario function.

The existing direct script execution replays S01-S05. A complete single-command S01-S14 replay with process restarts is not yet verified in this version.

### Automated testing

I implemented eight pytest tests.

The tests cover:

1. Instruction retrieval.
2. Service status handling.
3. Blocking ticket creation without authorization.
4. Creating an authorized ticket draft.
5. Rejecting reuse of an old ticket request.
6. SQLite memory after reopening the database.
7. Separation of different conversation threads.
8. Separation of users with the same displayed thread ID.

The local test result was:

**8 passed**

These tests do not require an OpenAI API key.

### GitHub Actions

I configured GitHub Actions to install dependencies and run pytest automatically.

The initial GitHub run failed because the tests were not located in the tests directory.

After fixing the repository structure, GitHub Actions displayed successful green runs.

### Security

The application uses fictional university data.

API keys are stored in environment variables and should never be committed to GitHub.

SQLite databases and generated ticket drafts are excluded through .gitignore.

Tickets are local drafts, not real submissions.

In a production application, user identity must be verified. Thread separation alone is not authentication.

### Limitations

The current system has several limitations:

- Ticket authorization needs stronger conversation handling.
- Repeated ticket creation requires additional safeguards.
- Full automatic replay of all 14 scenarios is not yet verified.
- No real university helpdesk is connected.

The project demonstrates the LangGraph workflow, tool execution, memory persistence and automated testing.

## Scenario execution results

The table below is generated from the actual saved JSON logs. New replay logs are distinguished from earlier manual runs.

**Available logs:** 14/14

**New replay logs:** 9/14

| **Scenario** | **Part** | **Description**                          | **Evidence**                            |
| ------------ | -------- | ---------------------------------------- | --------------------------------------- |
| S01          | 1        | Simple Wi-Fi route                       | `outputs/replay/S01.json` (New replay)  |
| S02          | 1        | Case-insensitive password route          | `outputs/replay/S02.json` (New replay)  |
| S03          | 1        | Unsupported request                      | `outputs/replay/S03.json` (New replay)  |
| S04          | 1        | Two topics before the graph change       | `outputs/replay/S04.json` (New replay)  |
| S05          | 1        | Two topics after adding clarification    | `outputs/replay/S05.json` (New replay)  |
| S06          | 2        | Instructions then local ticket           | `outputs/replay/S06.json` (New replay)  |
| S07          | 2        | The same request during a Wi-Fi outage   | `outputs/replay/S07.json` (New replay)  |
| S08          | 2        | Status source unavailable                | `outputs/replay/S08.json` (New replay)  |
| S09          | 2        | Missing ticket details                   | `outputs/replay/S09.json` (New replay)  |
| S10          | 3        | Use the current conversation             | `outputs/S10.json` (Earlier manual run) |
| S11          | 3        | Persist and recall after restart         | `outputs/S11.json` (Earlier manual run) |
| S12          | 3        | Preference across threads without replay | `outputs/S12.json` (Earlier manual run) |
| S13          | 3        | Do not share memory between users        | `outputs/S13.json` (Earlier manual run) |
| S14          | 2        | Password recovery outage                 | `outputs/S14.json` (Earlier manual run) |

## Detailed scenario observations

### S01 — Simple Wi-Fi route

**Status profile:** `normal`

**Visited nodes:** read_request, wifi_help

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** Check that Wi-Fi is enabled and airplane mode is off. Select the fictional Campus-Demo network. If connection fails, forget the saved network and try connecting again. If the problem remains, check the service status before preparing a ticket.

**Evidence:** `outputs/replay/S01.json` (New replay)

### S02 — Case-insensitive password route

**Status profile:** `normal`

**Visited nodes:** read_request, password_help

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** Open the practice sign-in screen and choose Forgot password. Follow the recovery instructions shown by the practice application. If recovery is unavailable, prepare a ticket describing the error. Never include a password or recovery code in a ticket.

**Evidence:** `outputs/replay/S02.json` (New replay)

### S03 — Unsupported request

**Status profile:** `normal`

**Visited nodes:** read_request, other_help

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** Is your problem about Wi-Fi or a password?

**Evidence:** `outputs/replay/S03.json` (New replay)

### S04 — Two topics before the graph change

**Status profile:** `normal`

**Visited nodes:** read_request, wifi_help

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** Check that Wi-Fi is enabled and airplane mode is off. Select the fictional Campus-Demo network. If connection fails, forget the saved network and try connecting again. If the problem remains, check the service status before preparing a ticket.

**Evidence:** `outputs/replay/S04.json` (New replay)

### S05 — Two topics after adding clarification

**Status profile:** `normal`

**Visited nodes:** read_request, clarify_problem

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** You mentioned both Wi-Fi and password. Which problem should we solve first?

**Evidence:** `outputs/replay/S05.json` (New replay)

### S06 — Instructions then local ticket

**Status profile:** `normal`

**Visited nodes:** chatbot, tools, chatbot, chatbot, tools, chatbot, tools, chatbot

**Tools requested:** find_instructions, check_service_status, prepare_ticket

**New ticket files recorded:** 1

**Final response:** The Wi-Fi service is operational with no reported outages. I have prepared a ticket for your problem about being unable to connect to the Campus-Demo Wi-Fi network despite enabling Wi-Fi and forgetting the saved network. Let me know if you want to review or submit the ticket.

**Evidence:** `outputs/replay/S06.json` (New replay)

### S07 — The same request during a Wi-Fi outage

**Status profile:** `wifi_outage`

**Visited nodes:** chatbot, tools, chatbot

**Tools requested:** check_service_status

**New ticket files recorded:** 0

**Final response:** The Wi-Fi service is currently down across the campus, including the Campus-Demo network. Since the service is unavailable, the connection issue is due to this outage. If you need further assistance or updates, please let me know.

**Evidence:** `outputs/replay/S07.json` (New replay)

### S08 — Status source unavailable

**Status profile:** `status_unavailable`

**Visited nodes:** chatbot, tools, chatbot

**Tools requested:** check_service_status

**New ticket files recorded:** 0

**Final response:** The current status of the Wi-Fi service is unavailable, so I cannot confirm if it is down or operating. Would you like me to prepare a ticket based on the issue you described?

**Evidence:** `outputs/replay/S08.json` (New replay)

### S09 — Missing ticket details

**Status profile:** `normal`

**Visited nodes:** chatbot, chatbot, tools, chatbot

**Tools requested:** prepare_ticket

**New ticket files recorded:** 0

**Final response:** I have prepared a draft ticket for your Wi-Fi connection issue. If you would like me to save or submit it, please let me know.

**Evidence:** `outputs/replay/S09.json` (New replay)

### S10 — Use the current conversation

**Status profile:** `normal`

**Visited nodes:** See log

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** You have tried enabling Wi-Fi and forgetting the saved network, but reconnecting still failed. These are the steps you have already attempted.

**Evidence:** `outputs/S10.json` (Earlier manual run)

### S11 — Persist and recall after restart

**Status profile:** `normal`

**Visited nodes:** See log

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** See original log

**Evidence:** `outputs/S11.json` (Earlier manual run)

### S12 — Preference across threads without replay

**Status profile:** `normal`

**Visited nodes:** See log

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** See original log

**Evidence:** `outputs/S12.json` (Earlier manual run)

### S13 — Do not share memory between users

**Status profile:** `normal`

**Visited nodes:** See log

**Tools requested:** Not recorded

**New ticket files recorded:** Not counted in log

**Final response:** See original log

**Evidence:** `outputs/S13.json` (Earlier manual run)

### S14 — Password recovery outage

**Status profile:** `recovery_outage`

**Visited nodes:** chatbot, tools, chatbot

**Tools requested:** check_service_status

**New ticket files recorded:** 0

**Final response:** See original log

**Evidence:** `outputs/S14.json` (Earlier manual run)

## Final conclusion

This project demonstrates how LangGraph can coordinate an AI assistant, reusable tools and persistent memory.

The deterministic graph handles simple requests. The LLM-based graph selects tools based on user questions. SQLite preserves conversation history after a restart.

Automated tests provide repeatable checks of core functions.

The saved scenario logs document the observed behaviour. Remaining limitations are reported rather than treated as successfully completed requirements.