# mariaZero

Personal assistant agent with an OpenAI ReAct/tool-calling core. You can trigger it via **CLI** (local) or **Telegram**. The first integration is **Google Calendar** (create events from natural language); more tools can be added without changing the core.

## Requirements

- Python 3.10+
- OpenAI API key
- (Optional) Telegram bot token, if you use the Telegram trigger
- (Optional) Google OAuth client ID/secret, if you use the calendar tool

## Setup

1. **Clone and install**

   ```bash
   cd mariaZero
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Environment variables**

   Copy `.env.example` to `.env` and fill in:

   | Variable | Required for | Description |
   |----------|--------------|-------------|
   | `OPENAI_API_KEY` | Agent (always) | Your OpenAI API key |
   | `TELEGRAM_BOT_TOKEN` | Telegram trigger | Bot token from BotFather |
   | `GOOGLE_CLIENT_ID` | Calendar tool | Google Cloud OAuth client ID |
   | `GOOGLE_CLIENT_SECRET` | Calendar tool | Google Cloud OAuth client secret |
   | `USER_TIMEZONE` | Optional | IANA timezone for calendar times (default: `America/New_York`). User times like "10am" are in this zone. |
   | `LOG_LEVEL` | Optional | `DEBUG`, `INFO` (default), `WARNING`, `ERROR` |
   | `TELEGRAM_ALLOWED_USER_ID` | Optional | Restrict bot to one Telegram user ID |
   | `TELEGRAM_PROXY` | Optional | Proxy URL for Telegram (e.g. `http://host:port`). Also uses `HTTPS_PROXY`/`HTTP_PROXY` if set. |
   | `TELEGRAM_CONNECT_TIMEOUT` | Optional | Connect timeout in seconds (default: 30) |
   | `TELEGRAM_READ_TIMEOUT` | Optional | Read timeout in seconds (default: 30) |
   | `AGENT_MAX_STEPS` | Optional | Max ReAct steps (default: 10) |
   | `OPENAI_MODEL` | Optional | Model name (default: `gpt-4o-mini`) |

3. **Google Calendar (if using calendar tool)**

   - Create a project in [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the **Google Calendar API**.
   - Create **OAuth 2.0 credentials** (Desktop app type).
   - Put the Client ID and Client Secret in `.env`.
   - On first use of the calendar tool, a browser will open for one-time sign-in; the refresh token is stored in `tokens/google_token.json` (gitignored).

## Run

**CLI (local, no Telegram)**

```bash
python main.py chat "Meeting with John tomorrow at 3pm"
# or
echo "Add team standup every Monday 9am" | python main.py chat
```

**Telegram**

```bash
python main.py telegram
```

Then send a message to your bot (e.g. “Meeting tomorrow at 3pm”). The agent will run and reply.

**If you see `telegram.error.NetworkError: httpx.ConnectError`:** the app cannot reach Telegram’s API. Try (1) set `HTTPS_PROXY` or `TELEGRAM_PROXY` in `.env` if you’re behind a proxy/VPN, (2) increase `TELEGRAM_CONNECT_TIMEOUT` / `TELEGRAM_READ_TIMEOUT` (default 30s), or (3) check firewall/DNS. For SOCKS5 use `TELEGRAM_PROXY=socks5://host:port` and `pip install python-telegram-bot[socks]`.

## Logging and traces

Structured logs go to stdout. Each agent run has a **trace_id** (UUID). Log events include:

- `agent_run_start` – trigger, user message
- `llm_request` / `llm_response` – step, tool_calls if any
- `tool_call_start` / `tool_call_end` – tool name, args, result or error
- `agent_run_end` – steps, response length

With CLI, the trace_id is also printed to stderr so you can grep logs. Set `LOG_LEVEL=DEBUG` for more detail.

## Adding a new tool

1. **Implement the tool** in `src/tools/`, e.g. `src/tools/weather.py`:
   - Use `make_tool(name, description, parameters, callable_fn)` from `src.tools.base`.
   - `parameters` is a JSON Schema dict for the function arguments.
   - The callable takes those arguments and returns a **string** (for the LLM).

2. **Register it** by calling `register(definition, callable_fn)` from `src.tools.registry`.

3. **Import it** in `src/tools/__init__.py` so it registers on load (e.g. `import src.tools.weather`).

No changes are needed in the agent loop or triggers; the new tool is picked up automatically.

## Project layout

```
mariaZero/
├── main.py              # Entry: python main.py chat | telegram
├── src/
│   ├── agent.py         # ReAct loop + tool-calling
│   ├── config.py        # Env and settings
│   ├── logging_utils.py # Structured logging, trace_id
│   ├── tools/
│   │   ├── base.py      # make_tool()
│   │   ├── registry.py  # register, get_openai_tools, execute
│   │   └── calendar.py # create_calendar_event
│   └── triggers/
│       ├── cli.py       # CLI trigger
│       └── telegram.py  # Telegram trigger
├── tokens/              # Google token (gitignored)
├── .env.example
└── requirements.txt
```
