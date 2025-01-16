from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
from app.controllers.pdf_controller import process_uploaded_pdf

pdf_upload_bp = Blueprint('pdf_upload', __name__)

@pdf_upload_bp.route('/upload_pdf', methods=['POST'])
def upload_pdf_route():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        file.save(filepath)

        # Process the uploaded PDF
        session_id = str(uuid.uuid4())
        process_uploaded_pdf(filepath, session_id)

        # Suggest a name for the chatbot based on the filename
        suggested_name = f"{os.path.splitext(filename)[0]}Bot"
        return jsonify({"message": "File uploaded and processed successfully", "session_id": session_id, "suggested_name": suggested_name})
