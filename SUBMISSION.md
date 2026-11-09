# HW5 — My LangGraph Helpdesk

## Part 1 — How the graph works

### My graph and state

Original graph:

START -> read_request
              |-> wifi_help -> END
              |-> password_help -> END
              |-> other_help -> END

My state has three fields:
- message: the original user message
- category: the detected problem
- reply: the answer to the user

The read_request node reads the message and updates
the category. The help nodes read the current state
and return a reply using helpdesk.json.

A node returns updates to the state. A conditional
edge chooses which node to run next. It does not
change the state.

Each next node receives the current graph state,
including updates from previous nodes.

START is the entry point. END finishes the graph.
Compiling creates a runnable graph.

### Predictions before running

| Message | Predicted route | Actual route | Result |
| --- | --- | --- | --- |
| I cannot connect to Wi-Fi. | wifi_help | wifi_help | Correct |
| I forgot my PASSWORD. | password_help | password_help | Correct |
| My laptop screen is broken. | other_help | other_help | Correct |
| My Wi-Fi password does not work. | wifi_help | wifi_help | Correct |

All four predictions matched the actual results.

The program converts messages to lowercase,
so PASSWORD and password are treated equally.

In the original graph, Wi-Fi has priority.
When both topics are mentioned, wifi_help is selected
because the Wi-Fi condition is checked first.

### My change to the graph

Updated graph:

START -> read_request
              |-> wifi_help -> END
              |-> password_help -> END
              |-> other_help -> END
              |-> clarify_problem -> END

I added a new category called "both".

If a message mentions Wi-Fi and password,
the graph now uses clarify_problem.

For S04, the original route was:
START -> read_request -> wifi_help -> END

For S05, the updated route was:
START -> read_request -> clarify_problem -> END

In S05, the category changed to "both".
The assistant asked which problem to solve first.

LangGraph controls the execution order and
the transitions between nodes.

My Python functions check the message,
choose a category and create the answer.

There is no LLM in Part 1.

### Execution logs

The actual results are saved in:
- outputs/S01.json
- outputs/S02.json
- outputs/S03.json
- outputs/S04.json
- outputs/S05.json

Each log shows the nodes visited and the
state after each node.

## Part 2 — Model and tools

To be completed after implementation.

## Part 3 — Memory

To be completed after implementation.

## Part 4 — Running and checking my work

To be completed after implementation.

## Choices and limitations

Part 1 uses fixed Python rules, not an LLM.
It supports Wi-Fi and password topics only.
Other problems require clarification.
