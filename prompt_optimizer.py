import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from supabase import create_client, Client

from data_parser import load_and_group_conversations
from ai_generator import get_system_prompt, generate_ai_reply

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

EDITOR_SYSTEM_PROMPT = """You are an expert prompt engineer specialising in conversational AI for immigration consulting. Your sole job is to analyse the gap between how a real human consultant replied and how an AI chatbot replied to the same client message, diagnose the root cause in the AI's system prompt, and return a surgically improved version of that prompt.

You do not rewrite the prompt from scratch. You make the minimum precise changes needed to close the observed gap — preserving everything that already works.

---

## INPUT STRUCTURE

You will receive a JSON object with five fields:

```json
{
  "existing_prompt": "The full current system prompt given to the AI chatbot",
  "chat_history": [
    {"direction": "in",  "text": "..."},
    {"direction": "out", "text": "..."}
  ],
  "client_sequence": [
    {"direction": "in", "text": "..."}
  ],
  "real_reply": "The actual reply written by the human consultant",
  "predicted_reply": "The reply the AI chatbot produced"
}
```

---

## YOUR TASK — FOLLOW THESE STEPS IN ORDER

### Step 1: Diff the replies
Compare `real_reply` and `predicted_reply` across these dimensions:
- **Content**: What did the human include that the AI omitted, or vice versa? What was factually different?
- **Structure**: Did the human use prose where the AI used bullets, or use a different ordering?
- **Tone**: Was the human warmer, more direct, more empathetic, more casual?
- **CTA**: Did the human end with a different or more effective call to action?
- **Length**: Was the human significantly more concise or more thorough?

### Step 2: Diagnose the prompt
Look at `existing_prompt` and identify exactly which part — or missing part — caused each gap you found in Step 1. Be precise: name the rule, section, or absence responsible. Possible root causes include:
- A rule is missing entirely
- A rule exists but is ambiguous or underspecified
- A rule exists but is contradicted elsewhere in the prompt
- An example is misleading the model toward the wrong behaviour
- The tone guidance doesn't cover this scenario
- A factual constraint is wrong or missing

### Step 3: Edit with surgical precision
Make only the changes required to fix the diagnosed issues. You may:
- Add a new rule or sub-rule
- Reword an existing rule to be more specific
- Add, replace, or remove an example
- Add a new fact to the established facts block
- Adjust tone guidance for a specific scenario

Do NOT:
- Rewrite sections that are working correctly
- Change the prompt's structure or format unless it is itself the problem
- Add padding, commentary, or explanation inside the prompt
- Alter the output format instructions

### Step 4: Return the result
Return a single JSON object and nothing else:

```json
{"prompt": "The full updated system prompt, with your changes applied"}
```

The `prompt` value must be the complete updated system prompt — not a diff, not a summary, not a partial excerpt.

---

## REASONING SCRATCHPAD

Before producing your output, reason through Steps 1–3 explicitly inside `<thinking>` tags. This reasoning is for your own use and will not be returned to the caller. Your final output must contain only the JSON object.

---

## IMPORTANT CONSTRAINTS

- **Minimum intervention.** Every word you add to the prompt has a cost: complexity, possible conflicts, token usage. Add only what is necessary.
- **Evidence-based.** Every change must be traceable to a specific observed gap in Step 1. Do not make speculative improvements.
- **Preserve voice.** The prompt has a defined tone and persona. Do not sanitise or formalise it.
- **No fabrication.** Do not introduce new fees, timelines, or legal rules into the prompt unless the `real_reply` demonstrates they are correct.
"""

def get_current_version():
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table('prompts').select('version').eq('name', 'visa_consultant_v1').order('version', desc=True).limit(1).execute()
        if response.data and len(response.data) > 0:
            return int(response.data[0]['version'])
    except Exception as e:
        print(f"Error fetching version: {e}")
    return 1

def push_new_prompt_version(new_content, new_version):
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # We insert a brand new row instead of updating to keep a history of prompt versions
        supabase.table('prompts').insert({
            'name': 'visa_consultant_v1',
            'content': new_content,
            'version': new_version
        }).execute()
        print(f"✅ Success! Generated and inserted PROMPT VERSION {new_version}")
    except Exception as e:
        print(f"❌ Failed to push new prompt: {e}")

def call_editor_ai(editor_input, system_prompt):
    client = genai.Client(api_key=API_KEY)
    editor_output = None
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=json.dumps(editor_input),
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2, # Low temp for analytical task
            )
        )
        editor_output = response.text
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            print("⚠️ Gemini API limit hit! Meta Editor is falling back to Typhoon API...")
            import requests
            typhoon_key = os.getenv("TYPHOON_API_KEY")
            if not typhoon_key:
                print("❌ Cannot fallback: TYPHOON_API_KEY not set in environment.")
                return None
            
            payload = {
                "model": "typhoon-v2.5-30b-a3b-instruct",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(editor_input)}
                ],
                "max_tokens": 4096,
                "temperature": 0.2
            }
            try:
                res = requests.post(
                    "https://api.opentyphoon.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {typhoon_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=60
                )
                if res.status_code == 200:
                    editor_output = res.json()["choices"][0]["message"]["content"]
                else:
                    print(f"❌ Typhoon Fallback Error: {res.text}")
                    return None
            except Exception as ty_e:
                print(f"❌ Typhoon connection failed: {ty_e}")
                return None
        else:
            print(f"❌ Error communicating with Gemini: {e}")
            return None

    if not editor_output:
        return None

    # Parse the JSON blob
    json_match = re.search(r'```json\n?(.*?)\n?```', editor_output, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Fallback string matching
        json_str = editor_output[editor_output.rfind('{'):editor_output.rfind('}')+1]
        
    try:
        try:
            return json.loads(json_str)["prompt"]
        except json.JSONDecodeError:
            import ast
            return ast.literal_eval(json_str)["prompt"]
    except Exception as parse_e:
        print(f"Failed to parse LLM json: {parse_e}")
        return None

def optimize_prompt_gap(chat_history, client_sequence, real_reply):
    prompt_data = get_system_prompt()
    existing_prompt = prompt_data.get("content", "")
    current_version = get_current_version()
    
    predicted_reply_json_str = generate_ai_reply(chat_history, client_sequence)
    try:
        parsed = json.loads(predicted_reply_json_str)
        predicted_reply = parsed.get("reply", predicted_reply_json_str)
    except:
        predicted_reply = predicted_reply_json_str
        
    editor_input = {
        "existing_prompt": existing_prompt,
        "chat_history": chat_history,
        "client_sequence": [{"direction": "in", "text": client_sequence}],
        "real_reply": real_reply,
        "predicted_reply": predicted_reply
    }
    
    updated_prompt = call_editor_ai(editor_input, EDITOR_SYSTEM_PROMPT)
    if updated_prompt:
        push_new_prompt_version(updated_prompt, current_version + 1)
        return {
            "predictedReply": predicted_reply,
            "updatedPrompt": updated_prompt
        }
    return None

def optimize_prompt_manual(instructions):
    prompt_data = get_system_prompt()
    existing_prompt = prompt_data.get("content", "")
    current_version = get_current_version()
    
    MANUAL_SYSTEM_PROMPT = "You are an expert prompt engineer. Your job is to strictly apply the user's instructions to the provided system prompt. You must preserve the prompt's tone, structure, bullet points, and constraints, changing only what is necessary to fulfill the instructions. Return ONLY a single JSON object structured as: {\"prompt\": \"The full updated system prompt text\"}."
    
    editor_input = {
        "existing_prompt": existing_prompt,
        "user_instructions": instructions
    }
    
    updated_prompt = call_editor_ai(editor_input, MANUAL_SYSTEM_PROMPT)
    if updated_prompt:
        push_new_prompt_version(updated_prompt, current_version + 1)
        return {
            "updatedPrompt": updated_prompt
        }
    return None

def run_optimization(sample_index=24):
    print(f"🚀 --- STARTING PROMPT OPTIMIZATION (Sample #{sample_index}) ---")
    
    examples = load_and_group_conversations('conversations.json')
    sample = examples[sample_index]
    
    result = optimize_prompt_gap(sample['chat_history'], sample['client_sequence'], sample['consultant_reply'])
    if result:
        print("Success! Prompt optimized.")
        print(f"New Prompt Snippet: {result['updatedPrompt'][:200]}...")

if __name__ == "__main__":
    run_optimization(24)
