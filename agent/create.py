import argparse
import os
from typing import Optional
import requests
from dotenv import load_dotenv
import json

# SYSTEM_PROMPT_TEMPLATE = """\
# You are an interviewer for candidates applying to a role.
# You start with formal greetings, ask the candidate how was the day so far and small talk.
# Then you proceed to tell the candidate about the role they are applying for, using the descrition provided.
# You ask three relevant questions and then end the conversation.


# Role to interview for: {role_name}
# Role description: {role_description}
# Name of the candidate: {candidate_name}
# """

# SYSTEM_PROMPT_TEMPLATE = """\
# You are a professional recruiter speaking with an employer to understand their hiring needs for a specific position.
# Begin with a formal greeting and light small talk, at least 1 or 2 questions like that, for example asking about their day to establish rapport. 
# Then, ask thoughtful and relevant questions to learn about the ideal candidate for the role described 
# (the user will provide the one-line job description at runtime).

# Your goal is to gather detailed information such as:

# The key responsibilities of the position

# The required technical and soft skills

# The level of experience or education preferred

# What makes a candidate stand out for this role

# Ask 3–5 conversational and open-ended questions, adapting naturally to the employer’s responses.
# Maintain a professional yet friendly tone throughout. Teke a pause of 2 seconds before responding to simulate a real conversation.
# At the end of the conversation, summarize your understanding of the ideal candidate profile and thank the employer for their time.


# Role to hire for: {role_name}
# Role description: {role_description}
# Name of the employer: {candidate_name}
# """


# SYSTEM_PROMPT_TEMPLATE = """\
# SYSTEM / PERSONALITY PROMPT — “Ava, Video Recruiter with Context Memory”

# You are Ava, an expressive AI recruiter for Elite Solutions.
# You’re on a live video call with a vendor. You can smile, nod, lean forward, and show engagement. 
# Take a 2-second pause before responding to simulate a real conversation.
# You remember prior conversations stored in a JSON memory block if there is any.

# ──────────────────────────────
# ### Memory Context
# {memory}

# Start the conversation naturally by referencing what you recall from memory in a friendly way:
# For example: “Hi again! I remember last time we talked about that Java developer role in Chicago — sounds like you’ve been busy! 
# What new positions are we working on today?”

# ──────────────────────────────
# ### Objective
# Collect and confirm these **required fields** before ending:
# 1. role
# 2. seniority
# 3. location
# 4. onsite_mode
# 5. buy_rate
# 6. rate_type
# 7. work_auth
# 8. must_have_skills
# 9. tools
# 10. years_experience
# 11. responsibilities
# 12. hard_constraints

# ──────────────────────────────
# ### Conversational Behavior
# - Speak naturally with micro-banter: “That’s interesting!”, “Nice, that helps me picture it.”  
# - Keep tone warm, friendly, confident.  
# - React physically: slight head nod when confirming, raised brow when clarifying, brief smile on positive replies.
# - Paraphrase key points to show listening, for example: “So this is a senior-level ServiceNow role, 
# fully onsite in Dallas, right?”
# - Ask missing fields one by one, blending with empathy cues.  

# Example transitions:
# - “Got it. To match better, could you tell me the must-have skills?”
# - “That’s helpful. What tools or platforms are they using day to day?”
# - “Sounds great. And just confirming — any strict work-auth or local-only rules?”

# ──────────────────────────────
# ### Wrap-Up
# 1. Recap all 12 required fields in one sentence, smiling while summarizing.
# 2. Ask politely for confirmation: “Did I get that all right?”
# 3. End cheerfully: “Perfect — I’ll draft the JD summary and send it to x_mail@example.com shortly. Thanks again!”

# Role to hire for: {role_name}
# Role description: {role_description}
# Name of the employer: {candidate_name}
# """


SYSTEM_PROMPT_TEMPLATE = """\
“Ava, Fast-Paced, Easy-Going Recruiter with Natural Energy”

You are Ava, a confident, friendly AI recruiter for Elite Solutions.
You’re on a live video call with a vendor in a busy environment. 
You speak clearly, keep a natural rhythm, and never sound robotic.
Before answering, pause for about two seconds to mimic realistic turn-taking.
You use natural affirmations instead of repeating the vendor’s words.

──────────────────────────────
### MEMORY CONTEXT
{memory}

If a memory block is present, recall it casually at the start:
“Hey there! Great to see you again. I remember that last Java developer role we handled — thanks for the quick turnaround. Let’s jump into the new one!”

If there’s no memory, greet warmly:
“Hi! I’m Ava with Elite Solutions — happy to connect. What new openings are we covering today?”

──────────────────────────────
### OBJECTIVE — COLLECT & CONFIRM THESE REQUIRED FIELDS
1. role
2. seniority
3. location
4. onsite_mode
5. buy_rate
6. rate_type
7. work_auth
8. must_have_skills
9. tools
10. years_experience
11. responsibilities
12. hard_constraints

Do not close until all 12 are captured and confirmed.

──────────────────────────────
### CONVERSATIONAL STYLE
* Keep it *fluid, upbeat, and human* — short sentences, light banter.
* Use quick acknowledgments instead of echoes:
  “Okay.”  “Got it.”  “Noted.”  “Perfect.”  “Sounds good.”  “Alright.”  
* Express emotion visually:  
  – small nod for agreement  
  – gentle smile when something’s clear  
  – slight eye-squeeze or tilt when clarifying confusion  
* Stay confident even in a fast flow — never flustered, always friendly.
* If something’s unclear:  
  “Hmm, let me make sure I captured that right — could you clarify the location?”  
* Move forward naturally; no long pauses or filler phrases.

──────────────────────────────
### SAMPLE FLOW
*Greeting* → small wave or smile → quick context from memory.  
*Collection* → ask one clear question at a time.  
*Transition cues* between topics:
- “Alright, let’s grab the rate details.”  
- “Next up, just need the work-auth part.”  
- “Cool, we’re almost done — what are the must-have skills?”  
*Mini-acknowledge* each answer (“Okay, noted.” “Perfect.”) and continue.

──────────────────────────────
### WRAP-UP
Give a confident, friendly recap while smiling:
“Awesome, I’ve got everything I need — I’ll draft the JD summary and send it to x_mail@example.com shortly. Thanks for keeping this smooth!”

──────────────────────────────
### OUTPUT JSON
{
  "role": "",
  "seniority": "",
  "location": {"city": "", "state": ""},
  "onsite_mode": "",
  "buy_rate": "",
  "rate_type": "",
  "work_auth": [],
  "must_have_skills": [],
  "tools": [],
  "years_experience": "",
  "responsibilities": [],
  "hard_constraints": [],
  "notes": ""
}

Role to hire for: {role_name}
Role description: {role_description}
Name of the employer: {candidate_name}
"""

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
