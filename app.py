from flask import Flask, request
import requests
import json
import time
import random

app = Flask(__name__)

# === AI Configuration ===
# Using Hugging Face Inference API (completely free)
HF_API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
HF_HEADERS = {
    "Authorization": "Bearer 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"  # Get free token from huggingface.co
}

# Alternative: Use local Ollama (if you want to run locally)
OLLAMA_URL = "http://localhost:11434/api/generate"

# Backup: Use a simple rule-based responses for common questions
SIMPLE_RESPONSES = {
    "hello": "Hello! 👋 How can I help you with your studies today?",
    "hi": "Hi there! 😊 What would you like to know?",
    "help": "I'm here to assist you! Ask me anything about studying, learning, or general questions! 🤖",
    "how are you": "I'm doing great and ready to help! How are your studies going? 📚",
    "what is your name": "I'm Sunnie AI, your study companion! 🤖✨",
    "bye": "Goodbye! Keep up the great work with your studies! 👋📚",
    "thanks": "You're welcome! Happy to help anytime! 😊",
    "study tips": "Here are quick study tips: 1) Take breaks every 25-30 mins 2) Stay hydrated 3) Remove distractions 4) Practice active recall! 💡",
    "motivation": "You've got this! 💪 Every small step counts. Keep pushing forward and believe in yourself! 🌟"
}

def get_simple_response(question):
    """Check if question matches simple responses"""
    question_lower = question.lower().strip()
    for key, response in SIMPLE_RESPONSES.items():
        if key in question_lower:
            return response
    return None

def query_huggingface(question):
    """Query Hugging Face API - completely free"""
    try:
        payload = {
            "inputs": question,
            "parameters": {
                "max_length": 100,
                "temperature": 0.7,
                "do_sample": True
            }
        }
        
        response = requests.post(HF_API_URL, headers=HF_HEADERS, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').strip()
        elif response.status_code == 503:
            return "🤖 AI model is loading, please try again in a moment!"
        
    except Exception as e:
        print(f"HuggingFace API error: {e}")
    
    return None

def query_ollama(question):
    """Query local Ollama installation - completely free"""
    try:
        payload = {
            "model": "llama2",  # or "mistral", "codellama" etc.
            "prompt": question,
            "stream": False
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
            
    except Exception as e:
        print(f"Ollama error: {e}")
    
    return None

def get_ai_response(question, username=""):
    """Get AI response with fallback options"""
    
    # First check for simple/common responses
    simple_resp = get_simple_response(question)
    if simple_resp:
        return simple_resp
    
    # Try Hugging Face API first
    hf_response = query_huggingface(question)
    if hf_response and len(hf_response) > 10:  # Valid response
        return hf_response
    
    # Try Ollama if available
    ollama_response = query_ollama(question)
    if ollama_response and len(ollama_response) > 10:
        return ollama_response
    
    # Fallback responses for different question types
    question_lower = question.lower()
    
    if any(word in question_lower for word in ['study', 'learn', 'exam', 'test']):
        return "📚 For effective studying: break topics into chunks, use active recall, teach concepts to others, and take regular breaks. What specific subject are you working on?"
    
    elif any(word in question_lower for word in ['math', 'mathematics', 'calculate']):
        return "🔢 Math tip: Practice problems step by step, understand the 'why' behind formulas, and don't rush. Would you like help with a specific math concept?"
    
    elif any(word in question_lower for word in ['science', 'physics', 'chemistry', 'biology']):
        return "🔬 Science learning: Connect concepts to real-world examples, use diagrams/visuals, and practice explaining phenomena. What science topic interests you?"
    
    elif any(word in question_lower for word in ['time', 'schedule', 'plan']):
        return "⏰ Time management: Use the Pomodoro technique (25min study + 5min break), prioritize important tasks, and set realistic daily goals!"
    
    elif any(word in question_lower for word in ['motivation', 'tired', 'stress']):
        return "💪 Stay motivated: Remember your goals, celebrate small wins, take care of your health, and don't be too hard on yourself. You're doing great!"
    
    else:
        return f"🤖 That's an interesting question! While I'd love to give you a detailed answer, I'm still learning. Try asking about study tips, subjects, or motivation - I'm great with those! 😊"

# === ROUTES ===

@app.route("/ai")
def ai_chat():
    username = request.args.get('user', 'Student')
    userid = request.args.get('id', '')
    question = request.args.get('msg', '').strip()
    
    if not question:
        return f"🤖 {username}, ask me anything! Example: !ai How do I study better?"
    
    # Remove common command prefixes if present
    if question.lower().startswith('!ai'):
        question = question[3:].strip()
    
    # Get AI response
    response = get_ai_response(question, username)
    
    # Ensure response isn't too long for chat (usually 500 char limit)
    if len(response) > 450:
        response = response[:447] + "..."
    
    return f"🤖 {username}: {response}"

@app.route("/ping")
def ping():
    return "🟢 AI Server is alive! 🤖"

@app.route("/test")
def test_ai():
    """Test endpoint to check AI functionality"""
    test_questions = [
        "Hello",
        "How do I study better?",
        "What is motivation?",
        "Help me with math"
    ]
    
    results = []
    for q in test_questions:
        resp = get_ai_response(q)
        results.append(f"Q: {q}\nA: {resp}\n---")
    
    return "<br><br>".join(results)

# === Run Server ===
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)  # Different port from your main app
