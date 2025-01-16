from app.services.pdf_service import process_pdf, create_qa_chain
from app.models.chat_model import qa_chains

def process_uploaded_pdf(filepath, session_id):
    documents = process_pdf(filepath)
    qa_chain = create_qa_chain(documents)
    qa_chains[session_id] = qa_chain
