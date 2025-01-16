
import os
import openai
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import fitz  # PyMuPDF
from langchain.text_splitter import TokenTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, OpenAI
from config.settings import OPENAI_API_KEY
import logging
import uuid

# Set OpenAI API Key
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
def split_into_chunks(documents, chunk_size=1000, chunk_overlap=100):
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

# Create FAISS Vector Store
def create_faiss_vector_store(documents):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store

# Set Up LangChain Retrieval-Augmented Generation (RAG)
def create_qa_chain(vector_store):
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=OpenAI(api_key=OPENAI_API_KEY),
        retriever=vector_store.as_retriever()
    )
    return qa_chain

# Handle Chatbot Responses
sessions = {}
qa_chains = {}

# Initialize default vector store and QA chain for default session
default_documents = load_pdf("The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf")
default_chunks = split_into_chunks(default_documents)
default_document_objects = create_document_objects(default_chunks)
default_vector_store = create_faiss_vector_store(default_document_objects)
default_qa_chain = create_qa_chain(default_vector_store)

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
        vector_store = create_faiss_vector_store(document_objects)
        qa_chain = create_qa_chain(vector_store)
        
        # Suggest a name for the chatbot based on the filename
        suggested_name = f"{os.path.splitext(filename)[0]}Bot"

        # Save the QA chain for the session
        session_id = str(uuid.uuid4())
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
        qa_chain = qa_chains.get(session_id, default_qa_chain)  # Use the uploaded PDF's chain if available
        response = qa_chain({"question": user_input, "chat_history": conversation_history})
        bot_reply = response['answer']

        if not bot_reply or "I am an AI" in bot_reply:
            bot_reply = "I'm here to help! Could you please provide more details or ask another question?"

        conversation_history.append(("assistant", bot_reply))
        sessions[session_id] = conversation_history
        return jsonify({"reply": bot_reply, "history": conversation_history})
    except Exception as e:
        logging.error(f"Error in chatbot_response: {e}")
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=False)
