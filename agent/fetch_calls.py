import argparse
import os
import re
import json
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

API_URL = "https://api.bey.dev/v1"
SAVE_DIR = Path(__file__).resolve().parent / "call_outputs"


# Patterns to find a JSON block. Prefer explicit markers (OUTPUT_JSON_START/END) or ```json fences.
JSON_PATTERNS = [
    r"OUTPUT_JSON_START\s*(\{.*?\})\s*OUTPUT_JSON_END",
    r"```json\s*(\{.*?\})\s*```",
    r"(\{\s*\"role\".*?\})",
]


def extract_json_from_text(text: str) -> Optional[dict]:
    # 1) try the explicit marker / fence patterns first
    for pat in JSON_PATTERNS:
        m = re.search(pat, text, flags=re.DOTALL)
        if not m:
            continue
        candidate = m.group(1).strip()
        candidate = candidate.strip('`')
        try:
            return json.loads(candidate)
        except Exception:
            # try to clean minor trailing commas
            cleaned = re.sub(r",\s*}\s*$", "}", candidate)
            cleaned = re.sub(r",\s*\]\s*$", "]", cleaned)
            try:
                return json.loads(cleaned)
            except Exception:
                continue

    # 2) fallback: scan for balanced JSON objects/arrays and try parsing each
    def try_extract_by_balanced_delims(s: str):
        opens = {'{': '}', '[': ']'}
        for open_ch, close_ch in opens.items():
            start_idx = 0
            while True:
                start = s.find(open_ch, start_idx)
                if start == -1:
                    break
                depth = 0
                for i in range(start, len(s)):
                    if s[i] == open_ch:
                        depth += 1
                    elif s[i] == close_ch:
                        depth -= 1
                        if depth == 0:
                            cand = s[start:i+1]
                            cand = cand.strip().strip('`')
                            # try direct parse
                            try:
                                return json.loads(cand)
                            except Exception:
                                # try cleaning trailing commas
                                tmp = re.sub(r",\s*}\s*$", "}", cand)
                                tmp = re.sub(r",\s*\]\s*$", "]", tmp)
                                try:
                                    return json.loads(tmp)
                                except Exception:
                                    break  # move to next start
                start_idx = start + 1
        return None

    fallback = try_extract_by_balanced_delims(text)
    return fallback


def main(api_key: str, agent_id: str) -> None:
    SAVE_DIR.mkdir(exist_ok=True)

    calls_response = requests.get(
        f"{API_URL}/calls",
        headers={"x-api-key": api_key},
    )

    if calls_response.status_code != 200:
        print(
            f"Error fetching calls: {calls_response.status_code} - {calls_response.text}"
        )
        exit(1)

    calls = calls_response.json().get("data", [])
    for call in calls:
        if call.get("agent_id") != agent_id:
            continue

        call_id = call.get("id")
        call_started_at = call.get("started_at")
        call_ended_at = call.get("ended_at")

        print(f"=== Call {call_id} ===")
        print(f"Started at: {call_started_at}")
        print(f"Ended at: {call_ended_at}")

        messages_response = requests.get(
            f"{API_URL}/calls/{call_id}/messages",
            headers={"x-api-key": api_key},
        )
        if messages_response.status_code != 200:
            print(
                f"Error fetching messages for call {call_id}: "
                f"{messages_response.status_code} - {messages_response.text}"
            )
            continue

        messages = messages_response.json()
        # Try extracting JSON from individual assistant messages (reverse chronological), then fallback to full transcript
        result = None
        found_in_message = None
        for msg in reversed(messages):
            text = msg.get("message", "")
            # prefer assistant messages but try all
            if msg.get("sender") and msg.get("sender").lower() in ("assistant", "ai", "bot"):
                candidate = extract_json_from_text(text)
                if candidate is not None:
                    result = candidate
                    found_in_message = msg
                    break

        if result is None:
            # fallback: search entire transcript
            full_text = "\n\n".join(m.get("message", "") for m in messages)
            result = extract_json_from_text(full_text)

        if result is None:
            print("No structured JSON found in this call. Messages follow:")
            for message in messages:
                print(f"[{message.get('sent_at')}] {message.get('sender')}: {message.get('message')}")
            continue

        # Save and print the JSON output
        out_path = SAVE_DIR / f"call_{call_id}_output.json"
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        if found_in_message:
            print(f"Saved structured JSON to: {out_path} (extracted from message at {found_in_message.get('sent_at')})")
        else:
            print(f"Saved structured JSON to: {out_path}")
        # Print only the JSON block as requested
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    load_dotenv()
    if (api_key := os.getenv("BEY_API_KEY")) is None:
        raise ValueError("Please set the BEY_API_KEY environment variable in .env")

    parser = argparse.ArgumentParser(
        description="Fetch calls for a specific agent from the Beyond Presence API and extract structured JSON outputs."
    )
    parser.add_argument(
        "--agent-id",
        type=str,
        help="Agent ID to fetch calls for.",
        required=True,
    )
    args = parser.parse_args()

    main(api_key=api_key, agent_id=args.agent_id)
