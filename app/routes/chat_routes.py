from flask import Blueprint, request, jsonify
from app.controllers.chatbot_controller import chat

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat_route():
    data = request.json
    user_input = data.get("message")
    session_id = data.get("session_id", "default")
    response = chat(user_input, session_id)
    return jsonify(response)
