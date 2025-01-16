from .chat_routes import chat_bp
from .pdf_routes import pdf_upload_bp

def init_routes(app):
    app.register_blueprint(chat_bp)
    app.register_blueprint(pdf_upload_bp)
