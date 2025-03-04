"use client";

import { useState, useEffect, useCallback } from "react";
import dictionary from "@/lib/isl_dictionary.json"; // Ensure TypeScript knows the type of this JSON
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Loader2, RefreshCcw } from "lucide-react";

// Define props interface
interface SignLanguageDisplayProps {
  text: string;
}

export function SignLanguageDisplay({ text }: SignLanguageDisplayProps) {
  const [videoUrls, setVideoUrls] = useState<string[]>([]);
  const [currentVideoIndex, setCurrentVideoIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);

  // Helper function to get base URL
  const getBaseUrl = (): string => {
    return "";
  };

  // Type for dictionary
  const dictionaryTyped = dictionary as Record<string, string>;

  // Generate sign language videos
  const generateSignLanguage = useCallback((text: string) => {
    try {
      setLoading(true);
      setError(null);

      if (!text || text.trim() === "") {
        setVideoUrls([]);
        setLoading(false);
        return;
      }

      console.log("Generating sign language for text:", text);
      const words = text.trim().split(/\s+/);
      const urls: string[] = [];

      console.log(`Found ${words.length} words to translate:`, words);

      let i = 0;
      while (i < words.length) {
        let foundPhrase = false;
        for (let j = Math.min(4, words.length - i); j > 0; j--) {
          const phrase = words.slice(i, i + j).join(" ").toLowerCase();
          console.log(`Checking phrase: "${phrase}"`);

          if (dictionaryTyped[phrase]) {
            const videoPath = `${getBaseUrl()}/${dictionaryTyped[phrase]}`;
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

          if (dictionaryTyped[word]) {
            const videoPath = `${getBaseUrl()}/${dictionaryTyped[word]}`;
            console.log(`Found match for word "${word}": ${videoPath}`);
            urls.push(videoPath);
          } else {
            console.log(`No video found for word: "${word}"`);
          }
          i++;
        }
      }

      console.log(`Generated ${urls.length} video URLs:`, urls);
      setVideoUrls(urls);
      setCurrentVideoIndex(0);
      setLoading(false);
    } catch (err) {
      console.error("Error generating sign language videos:", err);
      setError("Failed to generate sign language videos.");
      setLoading(false);
    }
  }, []);

  // Effect to regenerate sign language videos when text changes
  useEffect(() => {
    console.log("SignLanguageDisplay received text:", text);
    generateSignLanguage(text);
  }, [text, generateSignLanguage]);

  // Update progress bar
  useEffect(() => {
    if (videoUrls.length > 0) {
      setProgress((currentVideoIndex / videoUrls.length) * 100);
    }
  }, [currentVideoIndex, videoUrls.length]);

  // Handle video end event
  const handleVideoEnded = () => {
    console.log(`Video ${currentVideoIndex} ended, moving to next`);
    setCurrentVideoIndex((prevIndex) => prevIndex + 1);
  };

  // Handle video error event
  const handleVideoError = () => {
    console.error(`Error loading video at index ${currentVideoIndex}`);
    setError(`Unable to load video file: ${videoUrls[currentVideoIndex]}`);
    setTimeout(() => handleVideoEnded(), 1000);
  };

  return (
    <div className="space-y-4">
      {loading && (
        <div className="flex flex-col items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
          <p className="text-center text-muted-foreground">Loading videos...</p>
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-5 w-5" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!loading && videoUrls.length === 0 && <p>No sign language videos available.</p>}

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
              className="max-h-[500px] max-w-[800px] w-full"
            />
          </>
        ) : videoUrls.length > 0 && currentVideoIndex >= videoUrls.length ? (
          <p>All videos have been played.</p>
        ) : null}
      </div>

      {videoUrls.length > 0 && (
        <div className="video-controls flex gap-2">
          <Button onClick={() => setCurrentVideoIndex(0)} disabled={currentVideoIndex === 0}>
            <RefreshCcw className="mr-2 h-4 w-4" /> Restart
          </Button>
          <Progress value={progress} />
        </div>
      )}
    </div>
  );
}
