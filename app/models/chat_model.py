sessions = {}
qa_chains = {}

# Initialize default vector store and QA chain for default session
from app.services.pdf_service import load_pdf, split_into_chunks, create_document_objects, create_faiss_vector_store, create_qa_chain

default_documents = load_pdf("The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf")
default_chunks = split_into_chunks(default_documents)
default_document_objects = create_document_objects(default_chunks)
default_vector_store = create_faiss_vector_store(default_document_objects)
default_qa_chain = create_qa_chain(default_vector_store)
