#!/usr/bin/env python3
"""
Simple webhook receiver for Beyond Presence call events.
Saves the final JSON block emitted by the agent into `agent/call_outputs/`.

Usage (dev):
  pip install flask requests python-dotenv
  python agent/webhook.py

Expose with ngrok for testing and register the public URL + /webhook with Bey.
"""
import os
import re
import json
import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

load_dotenv()
API_URL = "https://api.bey.dev/v1"
BEY_API_KEY = os.getenv("BEY_API_KEY")
SAVE_DIR = Path(__file__).resolve().parent / "call_outputs"
SAVE_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Patterns to find a JSON block. First pattern is preferred when you control the prompt markers.
JSON_PATTERNS = [
    r"OUTPUT_JSON_START\s*(\{.*?\})\s*OUTPUT_JSON_END",
    r"```json\s*(\{.*?\})\s*```",
    r"(\{\s*\"role\".*?\})",
]


def extract_json_from_text(text: str) -> Optional[dict]:
    for pat in JSON_PATTERNS:
        m = re.search(pat, text, flags=re.DOTALL)
        if not m:
            continue
        candidate = m.group(1).strip()
        # Trim surrounding backticks if present
        candidate = candidate.strip('`')
        try:
            return json.loads(candidate)
        except Exception:
            # try to fix common issues: remove trailing commas
            cleaned = re.sub(r",\s*}\s*$", "}", candidate)
            cleaned = re.sub(r",\s*\]\s*$", "]", cleaned)
            try:
                return json.loads(cleaned)
            except Exception:
                continue
    return None


@app.route("/webhook", methods=["POST"])  # receiver endpoint
def webhook():
    payload = request.get_json(silent=True) or {}
    logging.info("Received webhook payload: %s", payload)

    # Attempt to find a call id in common locations
    call_id = (
        payload.get("call_id")
        or (payload.get("data") or {}).get("id")
        or (payload.get("call") or {}).get("id")
        or (payload.get("event") or {}).get("call_id")
    )

    if not call_id:
        return jsonify({"ok": False, "reason": "no call id found in payload"}), 400

    # If the webhook already contains a transcript or messages, use them; otherwise fetch from Bey
    messages = []
    if "messages" in payload:
        messages = payload["messages"]
    else:
        if not BEY_API_KEY:
            return jsonify({"ok": False, "reason": "missing BEY_API_KEY on server"}), 500
        resp = requests.get(f"{API_URL}/calls/{call_id}/messages", headers={"x-api-key": BEY_API_KEY})
        if resp.status_code != 200:
            logging.error("Failed fetching messages for call %s: %s %s", call_id, resp.status_code, resp.text)
            return jsonify({"ok": False, "reason": "failed fetching messages", "status": resp.status_code}), 502
        messages = resp.json()

    # Join messages into a single text blob for extraction
    full_text = "\n\n".join(m.get("message", "") for m in messages)

    result = extract_json_from_text(full_text)
    if not result:
        logging.info("No JSON block found for call %s", call_id)
        return jsonify({"ok": False, "reason": "no JSON block found in messages"}), 200

    out_path = SAVE_DIR / f"call_{call_id}_output.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    logging.info("Saved output JSON for call %s to %s", call_id, out_path)
    return jsonify({"ok": True, "saved": str(out_path)}), 200


if __name__ == "__main__":
    # Dev server
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
