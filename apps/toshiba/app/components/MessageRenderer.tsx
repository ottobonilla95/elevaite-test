import { VideoPlayer, parseVideoContent } from "./VideoPlayer";

interface MessageRendererProps {
  content: string;
  className?: string;
}

export function MessageRenderer({ content, className = "" }: MessageRendererProps) {
  // Split content by video tags to handle mixed text and video content
  const parts = content.split(/(<VIDEO>.*?<\/VIDEO>)/);
  
  return (
    <div className={className}>
      {parts.map((part, index) => {
        const videoContent = parseVideoContent(part);
        
        if (videoContent) {
          return (
            <VideoPlayer
              key={index}
              videoUrl={videoContent.url}
              startTime={videoContent.timestamp}
              className="my-4"
            />
          );
        }
        
        // Render text content (skip empty strings)
        if (part.trim()) {
          return (
            <div key={index} className="whitespace-pre-wrap">
              {part}
            </div>
          );
        }
        
        return null;
      })}
    </div>
  );
}