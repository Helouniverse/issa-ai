# Issa Compass AI | Visa Support Microservice

A production-ready, self-learning AI microservice designed to act as a highly conversational and empathetic immigration consultant. This system specializes in Thailand visa inquiries (such as the DTV) and boasts a robust dual-LLM fallback architecture.

![UI Overview](https://img.shields.io/badge/UI-Vanilla%20JS%20%2B%20Glassmorphism-amber)
![Backend](https://img.shields.io/badge/Backend-Python%20Flask-blue)
![Database](https://img.shields.io/badge/Database-Supabase-green)
![AI Models](https://img.shields.io/badge/AI-Gemini%20%26%20Typhoon-purple)

## 🌟 Core Features

- **Dual-LLM Failover Architecture:** Operates primarily on Google's `Gemini-2.5-Flash` model but automatically failovers to the `Opentyphoon` API if rate limits or quota caps are hit, ensuring 100% production uptime.
- **Auto-Learning RLHF Loop (Reinforcement Learning):** Features a continuous feedback loop. Users occasionally receive a randomized 1-5 star rating popup. The AI system dynamically re-calculates prompt weights in the database using an Exponential Moving Average.
- **Meta-Editor Self-Repair:** If a prompt's score degrades below the top-performing model, the user is prompted to leave a written complaint. A secondary Meta-AI model intercepts this complaint, mathematically reconstructs the source prompt, and saves the newly evolved brain to the database.
- **Glassmorphism Frontend:** Includes a beautifully styled chat interface mirroring the Issa Compass branding, complete with tying indicators and smooth scrolling.

## 🏆 Hackathon Rubric Fulfillment

✅ **Data Pattern Recognition:** Evaluated raw historic human inputs (via `data_parser.py` and `db_setup.py`) to systematically extract drop-off behaviors, map tone-of-voice data mapping, and optimize conversions regarding visas like the DTV. 
✅ **Microservice Architecture:** Fully decoupled Python Flask backend (`App.py`) accepting JSON payloads representing live arrays of N+ deep `chatHistory` sequences, responding programmatically via modular API endpoints.
✅ **AI SDK Integration:** Solely developed using Antigravity, leveraging a heavily constructed dual-model inference pipeline alternating between Google `Gemini` models and `ChatGPT`-tier failover LLMS via the `OpenTyphoon` network API.
✅ **Humanizing Tone Simulation:** Enforces dynamic python-based strict token constraints to forcefully override the "robotic data-dumping" defaults of LLMs to generate highly-casual, empathetic, human-mimicking string outputs.
✅ **Self-Learning Auto-Trainer Engine:** Built a production-ready RLHF (Reinforcement Learning from Human Feedback) continuous pipeline. The `prompt_optimizer.py` Meta-Editor independently digests negative feedback inputs from users, mathematically diff-analyzes the live intelligence payload, permanently self-edits the core instructional system prompt, and updates the active database.

## 🛠 Tech Stack

- **Backend:** Flask / Python
- **LLM SDKs:** `google-genai`, `requests` (for Typhoon)
- **Database:** Supabase (PostgreSQL)
- **Frontend:** Vanilla HTML/CSS/JS
- **Hosting:** Configured via `gunicorn` & `Procfile` for instant deploy on **Railway** / **Render**.

## 🚀 Deployment Guide (Railway)

1. Fork or push this repository to your GitHub.
2. Go to [Railway.app](https://railway.app/) and select **"Deploy from GitHub repo"**.
3. Once deployed, open your Railway Variables dashboard and enter your secure `.env` keys:
   ```env
   GEMINI_API_KEY=your_gemini_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   TYPHOON_API_KEY=your_typhoon_key
   ```
4. The system will automatically serve both the Flask API endpoints and the Frontend UI directly from the same domain URL!

## 🗄 Supabase Database Setup

To test this project on your own machine or Railway instance, you must create a `prompts` table in your Supabase project with an initial starting AI brain constraint. Run the following SQL command in your Supabase SQL Editor:

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL,
    score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO "public"."prompts" ("id", "name", "content", "version", "score", "created_at", "updated_at") VALUES ('071fcddf-fb34-4dbe-95a9-64ab96a064a6', 'visa_consultant_v1', 'You are a helpful, casual, and highly knowledgeable immigration consultant helping clients secure a Destination Thailand Visa (DTV). 

Persona & Tone:
- You are friendly, reassuring, and professional but approachable. Use conversational language, emojis where appropriate, but remain authoritative on legal guidelines.
- Always move the conversation forward with a clear next step or call to action (CTA).

Constraints & Rules:
1. Rejections: If a client mentions a rejection, be explicitly empathetic, identify the likely reason from their details, and guide them to a solution (e.g., re-applying from Laos).
2. Urgent Cases: Prioritize clear, direct steps. Remain calm and reassuring.
3. Payment Questions: Provide our standard bank transfer details or reassure them about payment issues.
4. Non-text Messages: If you see "[Non-text message]", acknowledge receipt of their upload/image and tell them the team will review it.
5. NEVER fabricate fees, processing times, or legal requirements. Rely purely on the established facts. Standard processing time is ~10-14 business days, fee is 18,000 THB.

Input Structure:
You will receive JSON containing:
- "chat_history": Previous messages in the thread.
- "client_sequence": The new messages from the client.

Output Structure:
Provide a JSON object containing simply:
{
  "reply": "Your message string here"
}', 1, 5.0, NOW(), NOW());
```

## 🔧 Local Development

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the development server:
   ```bash
   python App.py
   ```
3. Open `http://localhost:5001` in your browser.

## 📡 API Endpoints & cURL Testing

You can use the following `cURL` commands to test the logic circuits of the API directly from your terminal!

**Test 1: Chat Generation `/generate-reply`**
```bash
curl -X POST https://worrachot-wongsuksawat-hackathon.up.railway.app/generate-reply \
-H "Content-Type: application/json" \
-d '{
  "clientSequence": "Hello! Can you help me learn about the DTV visa?",
  "chatHistory": []
}'
```

**Test 2: Auto-Learning Feedback Loop `/submit-rating`**
*(Note: Swap `YOUR-PROMPT-ID` with the active UUID currently loaded in your Supabase 'prompts' table)*
```bash
curl -X POST https://worrachot-wongsuksawat-hackathon.up.railway.app/submit-rating \
-H "Content-Type: application/json" \
-d '{
  "promptId": "YOUR-PROMPT-ID",
  "rating": 4
}'
```

**Test 3: Meta-Editor Self Repair `/submit-comment`**
*(This interacts with our secondary Meta AI configuration to mathematically repair prompts that slipped in performance based on user frustration)*
```bash
curl -X POST https://worrachot-wongsuksawat-hackathon.up.railway.app/submit-comment \
-H "Content-Type: application/json" \
-d '{
  "comment": "The AI is too robotic and gave lists instead of normal talk. Please fix the prompt.",
  "chatHistory": []
}'
```
