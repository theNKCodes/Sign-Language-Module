import React, { useState } from 'react';
import axios from 'axios';
import SignLanguageDisplay from './SignLanguageDisplay';
import './App.css';

function App() {
  const [isListening, setIsListening] = useState(false);
  const [audioContext, setAudioContext] = useState(null);
  const [mediaStream, setMediaStream] = useState(null);
  const [transcript, setTranscript] = useState('');
  const [nlpResults, setNlpResults] = useState(null);

  const startListening = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      
      setMediaStream(stream);
      setAudioContext(audioCtx);
      
      // Speech recognition setup
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcriptChunk = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            setTranscript(prevTranscript => prevTranscript + transcriptChunk);
          } else {
            interimTranscript += transcriptChunk;
          }
        }
        console.log('Interim transcript:', interimTranscript);
      };

      recognition.start();

      setIsListening(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const stopListening = () => {
    if (audioContext && mediaStream) {
      mediaStream.getTracks().forEach(track => track.stop());
      audioContext.close();

      setIsListening(false);
      setAudioContext(null);
      setMediaStream(null);
    }
  };

  const handleButtonClick = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  const handleSubmit = async () => {
    console.log('Text submitted:', transcript);
    await processText(transcript);
    // Clear the transcript to prepare for new input
    setTranscript('');
    if (isListening) {
      stopListening();}
  };

  const processText = async (text) => {
    try {
      console.log('Sending text to backend:', text); // Log the text being sent
      const response = await axios.post('http://localhost:5000/process', { text });
      console.log('Received response from backend:', response.data); // Log the response
      setNlpResults(response.data);
    } catch (error) {
      console.error('Error processing text', error);
    }
  };

  return (
    <div className="App">
      <h2>Enter input audio</h2>
      <button onClick={handleButtonClick}>
        <img src={"mic.png"} alt="mic" height='60px' width='60px'/>
        <br /><br />
        {isListening ? 'Stop Listening' : 'Start Listening'}
      </button>
      <br /><br />     
    <textarea
        value={transcript}
        readOnly
        placeholder="Transcribed text will appear here..."
        rows="3"
        cols="50"
      />
      <br /><br />
      <button className="btn" onClick={handleSubmit}>Submit</button>
      {/* {nlpResults && (
        
        <div>
          <br></br>
          <h2>NLP Results</h2>
          <h3>Message:</h3>
          {nlpResults.message}
          <h3>Input Text:</h3>
          {nlpResults.input_text}
          <h3>Tokens:</h3>
          {nlpResults.tokens.join(', ')}
          <h3>Filtered Tokens:</h3>
          <p>{nlpResults.filtered_tokens.join(', ')}</p>
          <h3>POS Tags:</h3>
          <p>{nlpResults.pos_tags.map(tag => `${tag[0]} (${tag[1]})`).join(', ')}</p>
          <h3>Entities:</h3>
          <p>{nlpResults.entities.map(ent => `${ent[0]} (${ent[1]})`).join(', ')}</p>
          <h3>Lemmas:</h3>
          <p>{nlpResults.lemmas.join(', ')}</p>
        </div>
      )} */}
      <h2><p className='video'>Sign Language Video Output</p></h2>
      <div className="video-container">
        <SignLanguageDisplay text={transcript} />
      </div>
    </div>
  );
}

export default App;
