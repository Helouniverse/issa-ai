import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from ai_generator import generate_ai_reply
from prompt_optimizer import optimize_prompt_gap, optimize_prompt_manual
import json

app = Flask(__name__, static_folder='frontend', static_url_path='')
# Enable CORS so frontend apps (React/Vue/etc) can communicate with this API
CORS(app)

@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route("/generate-reply", methods=["POST"])
def generate_reply():
    try:
        data = request.get_json()
        
        # Parse inputs based on requested camelCase schema
        chat_history = data.get("chatHistory", [])
        client_sequence = data.get("clientSequence", "")
        
        if not client_sequence:
            return jsonify({"error": "clientSequence is required"}), 400
            
        # Get response from AI Generator
        ai_reply_json_str, prompt_id = generate_ai_reply(history=chat_history, client_sequence=client_sequence)
        
        # ai_generator returns a JSON string, so we parse it to return a clean JSON payload
        try:
            parsed_reply = json.loads(ai_reply_json_str)
            ai_reply_text = parsed_reply.get("reply") or parsed_reply.get("response") or ai_reply_json_str
        except:
            ai_reply_text = ai_reply_json_str
            
        return jsonify({
            "aiReply": ai_reply_text,
            "promptId": prompt_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/improve-ai", methods=["POST"])
def improve_ai():
    try:
        data = request.get_json()
        
        chat_history = data.get("chatHistory", [])
        client_sequence = data.get("clientSequence", "")
        consultant_reply = data.get("consultantReply", "")
        
        if not client_sequence or not consultant_reply:
            return jsonify({"error": "clientSequence and consultantReply are required"}), 400
            
        result = optimize_prompt_gap(chat_history, client_sequence, consultant_reply)
        
        if result:
            return jsonify({
                "predictedReply": result["predictedReply"],
                "updatedPrompt": result["updatedPrompt"]
            })
        else:
            return jsonify({"error": "Failed to output an improved prompt. Model may have refused or hit limits."}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/improve-ai-manually", methods=["POST"])
def improve_ai_manually():
    try:
        data = request.get_json()
        instructions = data.get("instructions", "")
        
        if not instructions:
            return jsonify({"error": "instructions are required"}), 400
            
        result = optimize_prompt_manual(instructions)
        
        if result:
            return jsonify({"updatedPrompt": result["updatedPrompt"]})
        else:
            return jsonify({"error": "Failed to output an improved prompt."}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/submit-rating", methods=["POST"])
def submit_rating():
    try:
        data = request.get_json()
        prompt_id = data.get("promptId")
        rating = data.get("rating")
        
        if not prompt_id or rating is None:
            return jsonify({"error": "promptId and rating are required"}), 400
            
        from ai_generator import SUPABASE_URL, SUPABASE_KEY
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Fetch current score
        res = supabase.table("prompts").select("score").eq("id", prompt_id).execute()
        if not res.data:
            return jsonify({"error": "Prompt not found"}), 404
            
        current_score = res.data[0]["score"]
        # Exponential moving average calculation
        # New score = (Current Score * 0.7) + (Rating * 0.3)
        # If it's the first rating (score 0), just take the rating directly
        if current_score == 0:
            new_score = float(rating)
        else:
            new_score = (current_score * 0.7) + (float(rating) * 0.3)
            
        # Update database
        supabase.table("prompts").update({"score": new_score}).eq("id", prompt_id).execute()
        
        # Check if it is still the highest score
        high_res = supabase.table("prompts").select("score").eq("name", "visa_consultant_v1").order("score", desc=True).limit(1).execute()
        highest_score = high_res.data[0]["score"] if high_res.data else 0
        
        # If new_score is less than highest_score, we want to trigger a comment
        is_highest = new_score >= highest_score
        
        return jsonify({"success": True, "newScore": new_score, "isHighest": is_highest})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/submit-comment", methods=["POST"])
def submit_comment():
    try:
        data = request.get_json()
        comment = data.get("comment", "")
        chat_history = data.get("chatHistory", [])
        
        if not comment:
            return jsonify({"error": "comment is required"}), 400
            
        # Compile instruction using user feedback
        instructions = f"The user left this critical feedback about the AI's recent conversation performance: '{comment}'. Adjust the persona and rules to immediately fix this complaint."
        
        result = optimize_prompt_manual(instructions)
        
        if result:
            return jsonify({"success": True, "newPrompt": result["updatedPrompt"]})
        else:
            return jsonify({"error": "Failed to auto-generate prompt."}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
