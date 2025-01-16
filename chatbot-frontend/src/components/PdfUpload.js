import React, { useState } from 'react';
import './PdfUpload.css'; // Import CSS for styling

function PdfUpload({ onUploadSuccess, onContinueWithDefault }) {
  const [pdf, setPdf] = useState(null);

  const uploadPdf = async () => {
    if (!pdf) return;
    const formData = new FormData();
    formData.append('file', pdf);

    try {
      const response = await fetch('http://localhost:5000/upload_pdf', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (data.session_id) {
        onUploadSuccess(data.session_id, data.suggested_name || 'Custom Chatbot');
      } else {
        console.error('Error uploading PDF:', data.error);
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-card">
        <h2 className="title">Welcome to the Medical Chatbot</h2>
        <p className="description">
          Upload a PDF to train the chatbot or continue with the default medical information.
        </p>
        <div className="file-upload">
          <label htmlFor="fileInput" className="file-label">
            Choose a PDF File
          </label>
          <input
            id="fileInput"
            type="file"
            accept=".pdf"
            onChange={(e) => setPdf(e.target.files[0])}
            className="file-input"
          />
          {pdf && <p className="file-name">Selected: {pdf.name}</p>}
        </div>
        <div className="button-group">
          <button onClick={uploadPdf} className="upload-button">
            Upload PDF
          </button>
          <button onClick={onContinueWithDefault} className="default-button">
            Continue with Default
          </button>
        </div>
      </div>
    </div>
  );
}

export default PdfUpload;
