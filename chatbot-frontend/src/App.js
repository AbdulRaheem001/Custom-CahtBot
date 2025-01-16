// import React, { useState } from 'react';
// import './App.css';

// function App() {
//   const [input, setInput] = useState('');
//   const [messages, setMessages] = useState([]);
//   const [session_id, setSessionId] = useState('default');
//   const [pdf, setPdf] = useState(null);
//   const [showChat, setShowChat] = useState(false);
//   const [disableButton, setDisableButton] = useState(false)
//   const [chatbotName, setChatbotName] = useState('Medical Chatbot');

//   const uploadPdf = async () => {
//     if (!pdf) return;
//     const formData = new FormData();
//     formData.append('file', pdf);

//     try {
//       const response = await fetch('http://localhost:5000/upload_pdf', {
//         method: 'POST',
//         body: formData,
//       });

//       const data = await response.json();
//       if (data.session_id) {
//         setSessionId(data.session_id);
//         setChatbotName(data.suggested_name || 'Custom Chatbot');
//         setShowChat(true);
//       } else {
//         console.error('Error uploading PDF:', data.error);
//       }
//     } catch (error) {
//       console.error('Error:', error);
//     }
//   };

//   const sendMessage = async () => {
//     if (input.trim()) {
      
//       const userMessage = { role: 'user', content: input.trim() };
//       setMessages([...messages, userMessage]);
//       setInput('');
//       try {
//         const response = await fetch('http://localhost:5000/chat', {
//           method: 'POST',
//           headers: {
//             'Content-Type': 'application/json',
//           },
//           body: JSON.stringify({ message: input.trim(), session_id }),
//         });

//         const data = await response.json();
//         const botMessage = { role: 'assistant', content: data.reply };
//         setMessages((prevMessages) => [...prevMessages, botMessage]);
//       } catch (error) {
//         console.error('Error:', error);
//       }
      
      
//     }
//   };

//   const handleKeyPress = (e) => {
//     if (e.key === 'Enter') {
//       setDisableButton(true)
//       sendMessage();
//       setDisableButton(false);
//     }
//   };

//   return (
//     <div className="App">
//       {!showChat ? (
//         <div className="upload-container">
//           <h2>Welcome to the Medical Chatbot</h2>
//           <p>Upload a PDF to train the chatbot or continue with the default medical information.</p>
//           <input type="file" onChange={(e) => setPdf(e.target.files[0])} />
//           <button onClick={uploadPdf}>Upload PDF</button>
//           <button onClick={() => setShowChat(true)}>Continue with Default</button>
//         </div>
//       ) : (
//         <div className="chat-container">
//           <div className="chat-header">{chatbotName}</div>
//           <div className="chat-box">
//             {messages.map((msg, idx) => (
//               <div
//                 key={idx}
//                 className={`message ${msg.role === 'user' ? 'user' : 'assistant'}`}
//               >
//                 <span>{msg.content}</span>
//               </div>
//             ))}
//           </div>
//           <div className="input-container">
//             <input
//               type="text"
//               value={input}
//               onChange={(e) => setInput(e.target.value)}
//               onKeyPress={handleKeyPress}
//               placeholder="Type your message..."
//             />
//             <button onClick={sendMessage}
//             disabled={disableButton}>
//               <i className="send-icon">&#9658;</i> {/* Send icon */}
//             </button>
//           </div>
//         </div>
//       )}
//     </div>
//   );
// }

// export default App;


import React, { useState } from 'react';
import './App.css';
import PdfUpload from './components/PdfUpload';  // Import the new component

function App() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [session_id, setSessionId] = useState('default');
  const [showChat, setShowChat] = useState(false);
  const [chatbotName, setChatbotName] = useState('Medical Chatbot');

  const onUploadSuccess = (sessionId, suggestedName) => {
    setSessionId(sessionId);
    setChatbotName(suggestedName);
    setShowChat(true);
  };

  const onContinueWithDefault = () => {
    setShowChat(true);
  };

  const sendMessage = async () => {
    if (input.trim()) {
      const userMessage = { role: 'user', content: input.trim() };

      try {
        const response = await fetch('http://localhost:5000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: input.trim(), session_id }),
        });

        const data = await response.json();
        const botMessage = { role: 'assistant', content: data.reply };
        setMessages((prevMessages) => [...prevMessages, userMessage, botMessage]);
      } catch (error) {
        console.error('Error:', error);
      }

      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  return (
    <div className="App">
      {!showChat ? (
        <PdfUpload
          onUploadSuccess={onUploadSuccess}
          onContinueWithDefault={onContinueWithDefault}
        />
      ) : (
        <div className="chat-container">
          <div className="chat-header">{chatbotName}</div>
          <div className="chat-box">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`message ${msg.role === 'user' ? 'user' : 'assistant'}`}
              >
                <span>{msg.content}</span>
              </div>
            ))}
          </div>
          <div className="input-container">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
            />
            <button onClick={sendMessage}>
              <i className="send-icon">&#9658;</i> {/* Send icon */}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
