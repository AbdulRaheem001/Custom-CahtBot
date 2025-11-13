
import os
import openai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from langchain_text_splitters import TokenTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAI
from config.settings import OPENAI_API_KEY
import logging
import uuid

# Set OpenAI API Key from config
openai.api_key = OPENAI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load PDF and Extract Text (Ignore Images)
def load_pdf(file_path):
    documents = []
    with fitz.open(file_path) as doc:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()  # Extract only text, ignore images
            documents.append(text)
    return documents

# Split Text into Chunks
def split_into_chunks(documents, chunk_size=800, chunk_overlap=100):
    text_splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = []
    for doc in documents:
        chunks.extend(text_splitter.split_text(doc))
    return chunks

# Convert Chunks to Document Objects for FAISS
class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}
        self.id = str(uuid.uuid4())  # Generate a unique ID for each document

def create_document_objects(chunks):
    return [Document(page_content=chunk, metadata={"chunk_index": idx}) for idx, chunk in enumerate(chunks)]

# Create ChromaDB Vector Store with free local embeddings
def create_chroma_vector_store(documents, collection_name="default"):
    # Use sentence-transformers for free local embeddings (no API costs)
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",  # Fast and efficient model
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory="./chroma_db"
    )
    return vector_store

# Set Up LangChain Retrieval-Augmented Generation (RAG)
def create_qa_chain(vector_store):
    # Configure retriever to fetch relevant documents
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}  # Retrieve top 3 most relevant chunks to save tokens
    )
    
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=OpenAI(
            api_key=OPENAI_API_KEY,
            temperature=0.7,
            max_tokens=500  # Reduced to avoid token limit errors
        ),
        retriever=retriever,
        return_source_documents=False,
        verbose=False
    )
    return qa_chain

# Handle Chatbot Responses
sessions = {}
qa_chains = {}

# Initialize default QA chain as None (will be created on first use or after PDF upload)
default_qa_chain = None

@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Process the uploaded PDF
        documents = load_pdf(filepath)
        chunks = split_into_chunks(documents)
        document_objects = create_document_objects(chunks)
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create ChromaDB vector store with unique collection name
        vector_store = create_chroma_vector_store(document_objects, collection_name=session_id)
        qa_chain = create_qa_chain(vector_store)
        
        # Suggest a name for the chatbot based on the filename
        suggested_name = f"{os.path.splitext(filename)[0]}Bot"

        # Save the QA chain for the session
        qa_chains[session_id] = qa_chain
        return jsonify({"message": "File uploaded and processed successfully", "session_id": session_id, "suggested_name": suggested_name})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_input = data.get("message")
    session_id = data.get("session_id", "default")
    
    if session_id not in sessions:
        sessions[session_id] = []

    conversation_history = sessions[session_id]
    conversation_history.append(("user", user_input))

    try:
        qa_chain = qa_chains.get(session_id, default_qa_chain)
        
        if qa_chain is None:
            return jsonify({"error": "Please upload a PDF first to start chatting."})
        
        # First, try to get answer from the document with detailed instructions
        # IMPORTANT: Don't pass conversation history to document search to avoid contamination
        document_prompt = f"""Question: {user_input}

Provide a detailed answer using the document content. Include all relevant facts, dosages, effects, and precautions. Write directly (not "the document says"). If no relevant info found, respond: NO_DOCUMENT_INFO

Answer:"""
        
        # Use empty chat history for document search to get clean results
        response = qa_chain({"question": document_prompt, "chat_history": []})
        bot_reply = response['answer'].strip()

        # Check if answer was found in document - more accurate detection
        # Log the response for debugging
        logging.info(f"Document response length: {len(bot_reply)}")
        logging.info(f"Document response preview: {bot_reply[:200]}")
        
        # Check for explicit "no info" signals
        has_no_info = (
            "NO_DOCUMENT_INFO" in bot_reply or
            len(bot_reply) < 30 or
            (("does not contain" in bot_reply.lower() or 
              "document does not" in bot_reply.lower() or
              "not found in the document" in bot_reply.lower() or
              "i don't have information" in bot_reply.lower() or
              "cannot answer" in bot_reply.lower()) and len(bot_reply) < 150)
        )
        
        if has_no_info:
            # No relevant info in document, use ChatGPT general knowledge
            logging.info(f"No document info found, using ChatGPT for: {user_input}")
            bot_reply = get_chatgpt_answer(user_input, conversation_history)
            bot_reply = f"📝 *Based on general knowledge (not from the document):*\n\n{bot_reply}"
        else:
            # Answer found in document - make it more conversational
            bot_reply = f"📚 *\n\n{bot_reply}"

        # Add conversational follow-up questions
        if "?" not in bot_reply[-200:]:
            follow_up = generate_follow_up_questions(user_input, bot_reply)
            bot_reply = f"{bot_reply}{follow_up}"

        conversation_history.append(("assistant", bot_reply))
        sessions[session_id] = conversation_history
        return jsonify({"reply": bot_reply, "history": conversation_history})
    except Exception as e:
        logging.error(f"Error in chatbot_response: {e}")
        return jsonify({"error": str(e)})

def get_chatgpt_answer(user_question, conversation_history):
    """Get answer from ChatGPT when document doesn't have the information"""
    try:
        # Build conversation context
        messages = [
            {"role": "system", "content": "You are a friendly, knowledgeable AI assistant. Provide helpful, conversational answers in a warm tone. Break down complex topics into easy-to-understand explanations."}
        ]
        
        # Add recent conversation history for context (last 2 exchanges to save tokens)
        for role, content in conversation_history[-4:]:
            messages.append({
                "role": "user" if role == "user" else "assistant",
                "content": content
            })
        
        # Add current question
        messages.append({"role": "user", "content": user_question})
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logging.error(f"Error getting ChatGPT answer: {e}")
        return "I'd be happy to help! However, I'm having trouble accessing that information right now. Could you try rephrasing your question or ask something else?"

def generate_follow_up_questions(user_question, bot_answer):
    """Generate relevant follow-up questions based on the conversation"""
    try:
        # Use OpenAI to generate contextual follow-up questions
        prompt = f"""Based on this conversation, suggest 3 brief, engaging follow-up questions:

User asked: {user_question}
Bot answered: {bot_answer[:500]}...

Generate 3 short, specific follow-up questions that would naturally continue this conversation. 
Each question should be on a new line, starting with an emoji and "Would you like to know..." or similar conversational phrase.
Keep them concise and directly related to the topic."""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        
        follow_up_text = response.choices[0].message.content.strip()
        return f"\n\n{follow_up_text}"
    
    except Exception as e:
        logging.error(f"Error generating follow-ups: {e}")
        # Fallback to generic questions
        follow_ups = [
            "💡 Would you like me to explain any part in more detail?",
            "🔍 Is there a specific aspect you'd like to explore further?",
            "📚 Would you like to know about related topics from the document?"
        ]
        return "\n\n" + "\n".join(follow_ups)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "Chatbot API is running"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
