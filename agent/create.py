import argparse
import os
from typing import Optional
import requests
from dotenv import load_dotenv
import json

# Load the canonical system prompt from file so it can be shared with the web app
SYSTEM_PROMPT_TEMPLATE = None
PROMPT_FILE = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
if os.path.exists(PROMPT_FILE):
    with open(PROMPT_FILE, "r", encoding="utf-8") as pf:
        SYSTEM_PROMPT_TEMPLATE = pf.read()
else:
    # fallback to the embedded prompt if file missing
    SYSTEM_PROMPT_TEMPLATE = "Ava recruiter prompt missing; please create agent/system_prompt.txt"

EGE_STOCK_AVATAR_ID = "b9be11b8-89fb-4227-8f86-4a881393cbdb"
API_URL = "https://api.bey.dev/v1"


def main(
    api_key: str,
    role_name: str,
    role_description: str,
    candidate_name: str,
    avatar_id: Optional[str],
    memory: Optional[str],
) -> None:
    # Ensure memory is a JSON-like string for interpolation into the system prompt
    memory_block = memory if memory is not None else "[]"

    response = requests.post(
        f"{API_URL}/agent",
        headers={"x-api-key": api_key},
        json={
            "name": f"{role_name} Recruiter for {candidate_name}",
            "system_prompt": SYSTEM_PROMPT_TEMPLATE.format(
                memory=memory_block,
                role_name=role_name,
                role_description=role_description,
                candidate_name=candidate_name,
            ),
            "greeting": (
                f"Hello {candidate_name}, how are you doing? "
                "Are you ready to the discuss the candidate requirements?"
            ),
            "avatar_id": avatar_id if avatar_id is not None else EGE_STOCK_AVATAR_ID,
            # ---
            # Uncomment the following lines to customize the avatar further
            # "language": "es",  # use language codes, e.g., "en", "es", "fr"
            # "max_session_length_minutes": 10,
            # "capabilities": ["webcam_vision"],  # enable agent to see user's video
        },
    )

    if response.status_code != 201:
        print(f"Error creating agent: {response.status_code} - {response.text}")
        exit(1)

    agent_data = response.json()
    agent_name = agent_data["name"]
    agent_id = agent_data["id"]

    print(f"Created agent: {agent_name}")
    print(f"Agent ID: {agent_id}")
    print(f"Agent call link: https://bey.chat/{agent_id}")


if __name__ == "__main__":
    load_dotenv()
    if (api_key := os.getenv("BEY_API_KEY")) is None:
        raise ValueError("Please set the BEY_API_KEY environment variable in .env")

    parser = argparse.ArgumentParser(
        description="Create an end-to-end Bey avatar agent for interviews."
    )
    parser.add_argument(
        "--role-name",
        type=str,
        help="Name of the role to interview for.",
        required=True,
    )
    parser.add_argument(
        "--role-description",
        type=str,
        help="Description of the role to interview for.",
        required=True,
    )
    parser.add_argument(
        "--candidate-name",
        type=str,
        help="Name of the candidate to interview.",
        required=True,
    )
    parser.add_argument(
        "--avatar-id", type=str, help="Avatar ID to use.", default=EGE_STOCK_AVATAR_ID
    )
    parser.add_argument(
        "--memory",
        type=str,
        help="Optional memory JSON string to inject into the system prompt. Example: '[{\"note\":\"previous call: asked about java\"}]'",
        default=None,
    )
    parser.add_argument(
        "--memory-file",
        type=str,
        help="Path to a JSON file containing the memory block to include in the system prompt.",
        default=None,
    )
    args = parser.parse_args()

    # Resolve memory: --memory-file takes precedence over --memory
    memory_value = None
    if args.memory_file:
        with open(args.memory_file, "r", encoding="utf-8") as f:
            memory_value = f.read()
            # ensure it's valid JSON string; keep as string for template
            try:
                # canonicalize formatting
                memory_value = json.dumps(json.loads(memory_value))
            except Exception:
                # if not valid JSON, keep raw text
                pass
    elif args.memory:
        memory_value = args.memory

    main(
        api_key=api_key,
        role_name=args.role_name,
        role_description=args.role_description,
        candidate_name=args.candidate_name,
        avatar_id=args.avatar_id,
        memory=memory_value,
    )
