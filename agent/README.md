# Beyond Presence — End-to-End Agent

A simple Python example that creates and manages an end-to-end avatar agent using the Beyond Presence API. This repository shows how to create an interview/recruiter agent, inject contextual memory into the agent's system prompt, and fetch call transcripts.

Contents
- `create.py` — Create a new avatar agent with a customizable system prompt (supports injecting a memory JSON block).
- `fetch_calls.py` — Retrieve historical calls and transcripts for an agent.
- `requirements.txt` — Python dependencies.
- `.env.template` — Template for the required environment variables (copy to `.env`).

## Prerequisites
- macOS / Linux / Windows with Python 3.8+
- A Beyond Presence account and API key: https://app.bey.chat

## Setup
1) Copy and configure the environment file
   - Copy `.env.template` to `.env` and add your Beyond Presence API key:
     BEY_API_KEY=sk_...

2) Create and activate a virtual environment (zsh example on macOS):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## How it works (high level)
- `create.py` builds a JSON payload containing:
  - `name` — friendly agent name
  - `system_prompt` — your personality/prompt template (the repo contains `SYSTEM_PROMPT_TEMPLATE`), with an injected `{memory}` placeholder
  - `greeting` — initial greeting shown to users
  - `avatar_id` — which avatar to use
- The script calls the Beyond Presence API to create the agent and prints the agent ID and a call link.

- `fetch_calls.py` calls the API to list calls for an agent and prints call transcripts.

## Usage
Change into the `e2e-agent` directory before running the examples below:

cd e2e-agent

### Create an agent (basic)

```bash
python create.py \
  --role-name 'Data Scientist' \
  --role-description 'Analyze data and build models to inform product decisions.' \
  --candidate-name 'Acme Corp'
```

### Create an agent with an avatar ID

```bash
python create.py \
  --role-name 'Frontend Engineer' \
  --role-description 'Build React applications and internal design systems.' \
  --candidate-name 'Acme Corp' \
  --avatar-id b9be11b8-89fb-4227-8f86-4a881393cbdb
```

### Inject memory into the system prompt

- Option A: Pass a JSON string inline

```bash
python create.py \
  --role-name 'ServiceNow Engineer' \
  --role-description 'Maintain and extend ServiceNow platform' \
  --candidate-name 'Acme Corp' \
  --memory '[{"date":"2025-10-20","note":"Discussed java role in Chicago"}]'
```

- Option B: Use a memory file (recommended for complex memory blocks)

Create `memory.json`:

```json
[
  {"date": "2025-10-20", "note": "Discussed Java role in Chicago"},
  {"pref": "onsite", "years_experience": 5}
]
```

Then run:

```bash
python create.py \
  --role-name 'ServiceNow Engineer' \
  --role-description 'Maintain and extend ServiceNow platform' \
  --candidate-name 'Acme Corp' \
  --memory-file memory.json
```

### Notes about memory handling
- `create.py` accepts two memory options:
  - `--memory` — a JSON string passed on the command line
  - `--memory-file` — path to a JSON file (this takes precedence over `--memory`)
- The script attempts to canonicalize JSON when reading `--memory-file`. If the file is not valid JSON, the raw text will be injected into the prompt as-is.
- Memory is substituted into the `SYSTEM_PROMPT_TEMPLATE` at the `{memory}` placeholder. Use structured JSON so the prompt can present useful context.

### Fetch calls and transcripts

```bash
python fetch_calls.py --agent-id YOUR_AGENT_ID
```

This fetches recent calls for the agent and prints transcripts to stdout.

## Tips & Troubleshooting
- If `python` or `python3` points to an unexpected interpreter, ensure your virtual environment is active (`source .venv/bin/activate`).
- If your API request fails, the scripts print the HTTP status and response text. Check that `BEY_API_KEY` is set in `.env` and valid.
- Use `--avatar-id` to pick a specific avatar; otherwise a default stock avatar is used.

## Further reading
- API docs: https://docs.bey.dev/integration/end-to-end
- API reference: https://docs.bey.dev/api-reference

## License
See the repository root for license information.
