import fitz  # PyMuPDF
from langchain.text_splitter import TokenTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, OpenAI
from config.settings import OPENAI_API_KEY
import uuid

class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}
        self.id = str(uuid.uuid4())

def process_pdf(file_path):
    documents = load_pdf(file_path)
    chunks = split_into_chunks(documents)
    document_objects = create_document_objects(chunks)
    vector_store = create_faiss_vector_store(document_objects)
    return vector_store

def load_pdf(file_path):
    documents = []
    with fitz.open(file_path) as doc:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            documents.append(text)
    return documents

def split_into_chunks(documents, chunk_size=1000, chunk_overlap=100):
    text_splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = [chunk for doc in documents for chunk in text_splitter.split_text(doc)]
    return chunks

def create_document_objects(chunks):
    return [Document(page_content=chunk, metadata={"chunk_index": idx}) for idx, chunk in enumerate(chunks)]

def create_faiss_vector_store(documents):
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    vector_store = FAISS.from_documents(documents, embeddings)
    return vector_store

def create_qa_chain(vector_store):
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=OpenAI(api_key=OPENAI_API_KEY),
        retriever=vector_store.as_retriever()
    )
    return qa_chain
