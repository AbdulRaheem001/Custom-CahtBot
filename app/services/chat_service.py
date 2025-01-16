from app.models.chat_model import sessions, qa_chains, default_qa_chain

def handle_chat_response(user_input, session_id):
    if session_id not in sessions:
        sessions[session_id] = []

    conversation_history = sessions[session_id]
    conversation_history.append(("user", user_input))

    try:
        qa_chain = qa_chains.get(session_id, default_qa_chain)
        response = qa_chain({"question": user_input, "chat_history": conversation_history})
        bot_reply = response['answer']

        if not bot_reply or "I am an AI" in bot_reply:
            bot_reply = "I'm here to help! Could you please provide more details or ask another question?"

        conversation_history.append(("assistant", bot_reply))
        sessions[session_id] = conversation_history
        return {"reply": bot_reply, "history": conversation_history}
    except Exception as e:
        return {"error": str(e)}
