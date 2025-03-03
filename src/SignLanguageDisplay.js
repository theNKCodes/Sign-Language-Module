import React, { useState, useEffect } from 'react';
import dictionary from './isl_dictionary.json'; // Adjust the path according to your project structure

function SignLanguageDisplay({ text }) {
  const [videoUrls, setVideoUrls] = useState([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState(0);

  const generateSignLanguage = (text) => {
    const words = text.split(' ');
    const urls = [];

    let i = 0;
    while (i < words.length) {
      // Check for phrases in the dictionary
      let foundPhrase = false;
      for (let j = Math.min(4, words.length - i); j > 0; j--) { // Check up to 4-word phrases
        const phrase = words.slice(i, i + j).join(' ').toLowerCase();
        if (dictionary[phrase]) {
          urls.push(`${process.env.PUBLIC_URL}/${dictionary[phrase]}`);
          i += j; // Move index past the phrase
          foundPhrase = true;
          break;
        }
      }
      if (!foundPhrase) {
        const word = words[i].toLowerCase();
        if (dictionary[word]) {
          urls.push(`${process.env.PUBLIC_URL}/${dictionary[word]}`);
        } else {
          urls.push(null); // No video found for this word/phrase
        }
        i++;
      }
    }

    setVideoUrls(urls);
    setCurrentVideoIndex(0); // Reset the current video index
  };

  useEffect(() => {
    if (text) {
      generateSignLanguage(text);
    }
  }, [text]);

  const handleVideoEnded = () => {
    setCurrentVideoIndex(prevIndex => prevIndex + 1);
  };

  return (
    <div className="video-container">
      <div className="video-player">
        {videoUrls.length > 0 && currentVideoIndex < videoUrls.length && (
          <video
            key={currentVideoIndex}
            src={videoUrls[currentVideoIndex]}
            controls
            autoPlay
            onEnded={handleVideoEnded}
            muted
            style={{ height: '500px', width: '800px' }}
          />
        )}
      </div>
    </div>
  );
}

export default SignLanguageDisplay;