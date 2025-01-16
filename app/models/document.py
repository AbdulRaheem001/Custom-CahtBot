# document.py
import uuid

class Document:
    def __init__(self, page_content, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}
        self.id = str(uuid.uuid4())
