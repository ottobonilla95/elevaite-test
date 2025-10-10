"use client";
import { useEffect, useRef, useState } from "react";

interface VideoPlayerProps {
  videoUrl: string;
  startTime?: string; // Format: "h:m:s" or "hh:mm:ss"
  className?: string;
}

export function VideoPlayer({ videoUrl, startTime, className = "" }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Convert timestamp string to seconds
  const parseTimestamp = (timestamp: string): number => {
    const parts = timestamp.split(':').map(Number);
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2]; // h:m:s
    }
    return 0;
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleLoadedData = () => {
      setIsLoading(false);
      if (startTime) {
        const startSeconds = parseTimestamp(startTime);
        video.currentTime = startSeconds;
      }
    };

    const handleError = () => {
      setError("Failed to load video");
      setIsLoading(false);
    };

    video.addEventListener('loadeddata', handleLoadedData);
    video.addEventListener('error', handleError);

    return () => {
      video.removeEventListener('loadeddata', handleLoadedData);
      video.removeEventListener('error', handleError);
    };
  }, [startTime]);

  if (error) {
    return (
      <div className={`flex items-center justify-center p-4 bg-gray-100 rounded-lg ${className}`}>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100 rounded-lg">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      )}
      <video
        ref={videoRef}
        controls
        className="w-full max-w-md rounded-lg shadow-lg"
        preload="metadata"
      >
        <source src={videoUrl} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>
  );
}

// Utility function to parse video content from response text
export function parseVideoContent(text: string): { url: string; timestamp: string } | null {
  const videoRegex = /<VIDEO>(.*?)<TIMESTAMP>(.*?)<\/TIMESTAMP><\/VIDEO>/;
  const match = text.match(videoRegex);
  
  if (match) {
    return {
      url: match[1],
      timestamp: match[2]
    };
  }
  
  return null;
}