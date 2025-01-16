from app.services.chat_service import handle_chat_response

def chat(user_input, session_id):
    return handle_chat_response(user_input, session_id)
