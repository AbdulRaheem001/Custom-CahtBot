# utils/helpers.py

def format_conversation(conversation_history):
    """
    Format conversation history for displaying or logging.
    """
    formatted = ""
    for msg in conversation_history:
        role = "User" if msg['role'] == "user" else "Bot"
        formatted += f"{role}: {msg['content']}\n"
    return formatted
