import os
import json
import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from data_parser import load_and_group_conversations
from supabase import create_client, Client

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_system_prompt():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in environment.")
        return "You are a helpful immigration consultant."
        
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        response = supabase.table('prompts').select('content').eq('name', 'visa_consultant_v1').order('version', desc=True).limit(1).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]['content']
    except Exception as e:
        print(f"Error loading prompt from Supabase: {e}")
    
    return "You are a helpful immigration consultant."

def generate_typhoon_reply(history, client_sequence, system_instruction):
    typhoon_key = os.getenv("TYPHOON_API_KEY")
    if not typhoon_key:
        return json.dumps({"reply": "ERROR: Gemini rate limit exceeded, and TYPHOON_API_KEY not set for fallback."})
        
    url = "https://api.opentyphoon.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {typhoon_key}",
        "Content-Type": "application/json"
    }
    
    messages = [{"role": "system", "content": system_instruction}]
    for msg in history:
        role = "assistant" if msg.get("role") == "consultant" else "user"
        messages.append({"role": role, "content": msg.get("content", "")})
        
    messages.append({
        "role": "user", 
        "content": f"New client message structure:\n{json.dumps(client_sequence)}"
    })
    
    payload = {
        "model": "typhoon-v2.5-30b-a3b-instruct",
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 8192,
        "response_format": {"type": "json_object"}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            return json.dumps({"reply": f"Typhoon API Error: {response.status_code} - {response.text}"})
    except Exception as e:
        return json.dumps({"reply": f"Error connecting to Typhoon fallback: {str(e)}"})

def generate_ai_reply(history, client_sequence):
    if not API_KEY:
        return '{"reply": "ERROR: GEMINI_API_KEY not found in environment or .env file."}'
        
    client = genai.Client(api_key=API_KEY)
    
    user_message = {
        "chat_history": history,
        "client_sequence": client_sequence
    }
    
    base_instruction = get_system_prompt()
    system_instruction = base_instruction + "\n\nCRITICAL ENFORCED RULE: You must keep your responses extremely conversational, highly empathetic, and concise (maximum 2 to 3 sentences). Always operate under the unquestionable fact that the Destination Thailand Visa (DTV) is a real, officially recognized, and highly sought-after Thai visa for digital nomads and freelancers. NEVER claim it is not recognized or not standard. ONLY answer the specific question asked by the user. NEVER output long lists of all visa categories."
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=json.dumps(user_message),
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
            )
        )
        return response.text
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
            print("⚠️ Gemini Free-Tier limit hit! Falling back to Typhoon...")
            return generate_typhoon_reply(history, client_sequence, system_instruction)
        return json.dumps({"reply": f"Error connecting to LLM: {error_str}"})

if __name__ == "__main__":
    if not API_KEY:
        print("⚠️  Error: GEMINI_API_KEY not set. Please set it in your .env file or export it in your environment.")
    else:
        print("✅ Environment loaded. Preparing test samples using Gemini...\n")
        examples = load_and_group_conversations('conversations.json')
        
        # Pick 3 specific examples showcasing different behaviors
        # examples[0]  -> Standard entry
        # examples[24] -> Rejected application intro (SYNTH_003)
        # examples[30] -> Payment receipt with image (SYNTH_008)
        
        test_samples = [examples[0], examples[24], examples[62]]
        
        for i, sample in enumerate(test_samples):
            print(f"========== TEST SAMPLE {i+1} ==========")
            print("--- CHAT HISTORY ---")
            if not sample['chat_history']:
                print("(No prior history)")
            else:
                for h in sample['chat_history']:
                    print(f"({h['role'].upper()}) {h['content']}")
            
            print("\n--- CLIENT ---")
            print(sample['client_sequence'])
            
            print("\n--- EXPECTED (Original Data) ---")
            print(sample['consultant_reply'])
            
            print("\n--- AI REPLY (Generated) ---")
            ai_reply_json = generate_ai_reply(sample['chat_history'], sample['client_sequence'])
            try:
                parsed = json.loads(ai_reply_json)
                print(parsed.get('reply', ai_reply_json))
            except:
                print(ai_reply_json)
            print("=========================================\n")
