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

## 📡 API Endpoints

- `GET /` - Serves the main UI interface.
- `POST /generate-reply` - Generate an AI response strictly based on conversation history.
- `POST /submit-rating` - Adjust the Exponential Moving Average score of the active prompt.
- `POST /submit-comment` - Triggers the automated Meta-Editor prompt logic fix.
