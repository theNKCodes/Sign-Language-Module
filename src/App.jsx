import React, { useState } from 'react';
import axios from 'axios';
import SignLanguageDisplay from './SignLanguageDisplay';
import './App.css';

function App() {
  const [inputText, setInputText] = useState('');
  const [submittedText, setSubmittedText] = useState('');
  const [nlpResults, setNlpResults] = useState(null);
  const [isTranslating, setIsTranslating] = useState(false);

  const handleSubmit = async () => {
    if (inputText.trim()) {
      setIsTranslating(true);
      console.log('Text submitted:', inputText);
      setSubmittedText(inputText);
      await processText(inputText);
      // Keep the current text in the input field
      // If you want to clear it after submission, uncomment the next line:
      // setInputText('');
    } else {
      console.log('No text to submit');
    }
  };

  const processText = async (text) => {
    try {
      console.log('Sending text to backend:', text); 
      const response = await axios.post('http://localhost:5000/process', { text }, {
        headers: { 'Content-Type': 'application/json' }
      });
      console.log('Received response from backend:', response.data); 
      setNlpResults(response.data);
    } catch (error) {
      console.error('Error processing text:', error.response ? error.response.data : error.message);
    }
  };

  // Reset the process to start over
  const handleReset = () => {
    setInputText('');
    setSubmittedText('');
    setNlpResults(null);
    setIsTranslating(false);
  };

  return (
    <div className="App">
      <h2>Sign Language Translation</h2>
      
      {!isTranslating ? (
        <>
          <div className="input-section">
            <h3>Enter your text:</h3>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Type your text here..."
              rows="4"
              cols="50"
              className="text-input"
            />
            
            {inputText.trim() && (
              <div className="submit-container">
                <button className="btn submit-btn" onClick={handleSubmit}>
                  Translate to Sign Language
                </button>
              </div>
            )}
          </div>
        </>
      ) : (
        <>
          <div className="translation-section">
            <h3>Translating:</h3>
            <div className="submitted-text">"{submittedText}"</div>
            
            <h3><p className='video'>Sign Language Video</p></h3>
            <div className="video-container">
              <SignLanguageDisplay text={submittedText} />
            </div>
            
            <button className="btn reset-btn" onClick={handleReset}>
              Translate New Text
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default App;