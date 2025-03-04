import React, { useState, useEffect } from 'react';
import dictionary from './isl_dictionary.json'; 

function SignLanguageDisplay({ text }) {
  const [videoUrls, setVideoUrls] = useState([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getBaseUrl = () => {
    return '';
  };

  const generateSignLanguage = (text) => {
    try {
      setLoading(true);
      setError(null);
      
      if (!text || text.trim() === '') {
        setVideoUrls([]);
        setLoading(false);
        return;
      }

      console.log('Generating sign language for text:', text);
      const words = text.trim().split(/\s+/);
      const urls = [];

      console.log(`Found ${words.length} words to translate:`, words);

      let i = 0;
      while (i < words.length) {
        let foundPhrase = false;
        for (let j = Math.min(4, words.length - i); j > 0; j--) {
          const phrase = words.slice(i, i + j).join(' ').toLowerCase();
          console.log(`Checking phrase: "${phrase}"`);
          
          if (dictionary[phrase]) {
            const videoPath = `${getBaseUrl()}/${dictionary[phrase]}`;
            console.log(`Found match for phrase "${phrase}": ${videoPath}`);
            urls.push(videoPath);
            i += j;
            foundPhrase = true;
            break;
          }
        }
        
        if (!foundPhrase) {
          const word = words[i].toLowerCase();
          console.log(`Checking single word: "${word}"`);
          
          if (dictionary[word]) {
            const videoPath = `${getBaseUrl()}/${dictionary[word]}`;
            console.log(`Found match for word "${word}": ${videoPath}`);
            urls.push(videoPath);
          } else {
            console.log(`No video found for word: "${word}"`);
            urls.push(null);
          }
          i++;
        }
      }

      console.log(`Generated ${urls.length} video URLs:`, urls);
      setVideoUrls(urls.filter(url => url !== null));
      setCurrentVideoIndex(0); 
      setLoading(false);
    } catch (err) {
      console.error('Error generating sign language videos:', err);
      setError('Failed to generate sign language videos: ' + err.message);
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('SignLanguageDisplay received text:', text);
    generateSignLanguage(text);
  }, [text]);

  const handleVideoEnded = () => {
    console.log(`Video ${currentVideoIndex} ended, moving to next`);
    setCurrentVideoIndex(prevIndex => {
      const nextIndex = prevIndex + 1;
      console.log(`Moving to video index ${nextIndex} of ${videoUrls.length - 1}`);
      return nextIndex;
    });
  };

  const handleVideoError = (e) => {
    console.error(`Error loading video at index ${currentVideoIndex}:`, e);
    setError(`Unable to load video file: ${videoUrls[currentVideoIndex]}`);
    // Move to next video after a short delay
    setTimeout(() => handleVideoEnded(), 1000);
  };

  return (
    <div className="video-container">
      {loading && <p>Loading videos...</p>}
      
      {error && <p className="error-message">{error}</p>}
      
      {!loading && videoUrls.length === 0 && (
        <p>No sign language videos available for the provided text.</p>
      )}
      
      <div className="video-player">
        {videoUrls.length > 0 && currentVideoIndex < videoUrls.length ? (
          <>
            <p>Playing video {currentVideoIndex + 1} of {videoUrls.length}</p>
            <video
              key={currentVideoIndex}
              src={videoUrls[currentVideoIndex]}
              controls
              autoPlay
              onEnded={handleVideoEnded}
              onError={handleVideoError}
              muted
              style={{ maxHeight: '500px', maxWidth: '800px', width: '100%' }}
            />
          </>
        ) : videoUrls.length > 0 && currentVideoIndex >= videoUrls.length ? (
          <p>All videos have been played.</p>
        ) : null}
      </div>
      
      {videoUrls.length > 0 && (
        <div className="video-controls">
          <button 
            onClick={() => setCurrentVideoIndex(0)} 
            disabled={currentVideoIndex === 0 && videoUrls.length > 0}
            className="control-btn"
          >
            Restart
          </button>
        </div>
      )}
    </div>
  );
}

export default SignLanguageDisplay;