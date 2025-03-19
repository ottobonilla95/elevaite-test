// components/ChatMessage.tsx
import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Button } from "./ui/button";
import { formatDate } from "../lib/utils"; // You'll need to implement this
import MarkdownMessage from './MarkdownMessage';

interface Message {
  id: string;
  text: string;
  isBot: boolean;
  date: string;
  vote?: -1 | 0 | 1;
}

interface ChatMessageProps {
  message: Message;
  onVote: (vote: -1 | 0 | 1) => void;
}

export function ChatMessage({ message, onVote }: ChatMessageProps) {
  return (
    <div className={`flex gap-3 ${message.isBot ? "bg-muted/30" : ""} p-3 rounded-lg`}>
 <div className="h-8 w-8 flex-shrink-0 bg-foreground/80 text-background flex items-center justify-center text-xs rounded-full font-bold">
        {message.isBot ? "AI" : "You"}
      </div>
      
      <div className="flex-1 space-y-1">
        <div className="flex justify-between items-center">
          <span className="font-medium text-sm">
            {message.isBot ? "Assistant" : "You"}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatDate ? formatDate(message.date) : new Date(message.date).toLocaleString()}
          </span>
        </div>
        
        <div className="prose prose-sm max-w-none">
          <MarkdownMessage text={message.text} />
          {/* <p>{message.text}</p> */}
        </div>
        
        {message.isBot && (
          <div className="flex items-center space-x-2 pt-2">
            <Button 
              variant={message.vote === 1 ? "default" : "ghost"} 
              size="sm" 
              onClick={() => {onVote(1)}}
              className="h-7 px-2"
            >
              <ThumbsUp className="w-3 h-3 mr-1" />
              <span className="text-xs">Helpful</span>
            </Button>
            
            <Button 
              variant={message.vote === -1 ? "default" : "ghost"} 
              size="sm" 
              onClick={() => {onVote(-1)}}
              className="h-7 px-2"
            >
              <ThumbsDown className="w-3 h-3 mr-1" />
              <span className="text-xs">Not helpful</span>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
