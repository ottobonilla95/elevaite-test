// components/ChatComponent.tsx
"use client";
import { useState, useRef, useEffect } from "react";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";
import { X, Send, ThumbsUp, ThumbsDown } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import type {ResponseData} from "../lib/interfaces";

export default function ChatComponent({ onClose }: { onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [message, setMessage] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const messageListRef = useRef<HTMLDivElement>(null);

  const API_URL  = process.env.NEXT_PUBLIC_API_BASE_URL_SQLAGENT??"http://localhost:8000/api";

  interface Message {
    id: string;
    text: string;
    isBot: boolean;
    date: string;
    vote?: -1 | 0 | 1;
    // sqlQueries?: string[];
  }

  useEffect(() => {
    // Add welcome message when component mounts
    if (messages.length === 0) {
      const welcomeMessage: Message = {
        id: `bot-welcome-${Date.now()}`,
        text: "How can I help with your creative insights today?",
        isBot: true,
        date: new Date().toISOString(),
      };
      setMessages([welcomeMessage]);
    }
  }, []);

  useEffect(() => {
    scrollToLastMessage();
  }, [messages.length]);

  function scrollToLastMessage(): void {
    if (messageListRef.current) {
      messageListRef.current.scrollIntoView({ behavior: "smooth", block: "end", inline: "nearest" });
    }
  }

  async function handleSend(): Promise<void> {
    if (isChatLoading || !message.trim()) return;
    
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      text: message,
      isBot: false,
      date: new Date().toISOString(),
    };
    
    setMessage("");
    setMessages(prev => [...prev, userMessage]);
    
    // Simulate bot response
    await fetchBotResponse(message);
  }

  async function fetchBotResponse(userMessage: string): Promise<void> {
    setIsChatLoading(true);
    
    try {
      // Create conversation payload with last few messages for context
      const recentMessages = messages.slice(-3).map(msg => ({
        actor: msg.isBot ? "system" : "user",
        content: msg.text
      }));
      
      // Add the current message
      const conversationPayload = [
        ...recentMessages,
        { actor: "user", content: userMessage }
      ];
      let imageBase64: string | undefined;
      const response = await fetch(`${API_URL}/sqlagent`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          "conversation_payload":conversationPayload,
          "query": userMessage,
          "skip_llm_call": false,
          "creative": imageBase64,
          "user_id": "Unknown User",
          "session_id": "sessionId_0"
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${String(response.status)}`);
      }

      if (!response.body) {
        throw new Error("Response body is null.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = '';
      let fullResponse = '';
      // let sqlQueries: string[] = [];

      let isProcessing = true;
      while (isProcessing) {
        const { done, value } = await reader.read();
        if (done) {
          isProcessing = false;
          break;
        }
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() ?? '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const jsonStr = line.slice(6); // Remove 'data: ' prefix
              const json = JSON.parse(jsonStr) as ResponseData;
              
              if (json.response) {
                console.log(json.sql_queries);
                fullResponse += json.response;
                
                // if (json.sql_queries && Array.isArray(json.sql_queries)) {
                //   sqlQueries = json.sql_queries;
                // }

                // Update the UI with the current accumulated response
                const botMessage: Message = {
                  id: `bot-${Date.now()}`,
                  text: fullResponse,
                  isBot: true,
                  date: new Date().toISOString(),
                  // sqlQueries: sqlQueries
                };
                
                setMessages(prev => {
                  // Replace the last bot message if it exists, otherwise add a new one
                  const lastMsgIsBot = prev[prev.length - 1]?.isBot;
                  if (lastMsgIsBot) {
                    return [...prev.slice(0, -1), botMessage];
                  }
                  return [...prev, botMessage];
                });
              }
              
            } catch (e) {
              console.error("Error parsing JSON:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error fetching response:", error);
      
      // Add error message
      const errorMessage: Message = {
        id: `bot-error-${Date.now()}`,
        text: "Sorry, I encountered an error while processing your request. Please try again.",
        isBot: true,
        date: new Date().toISOString(),
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent): void {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  function updateMessageVote(messageId: string, vote: -1 | 0 | 1): void {
    setMessages(prev => 
      prev.map(msg => 
        msg.id === messageId 
          ? { ...msg, vote: msg.vote === vote ? 0 : vote } 
          : msg
      )
    );
  }

  return (
    <div className="sticky flex flex-col h-[80vh] border rounded-lg shadow-lg">
      <div className="flex justify-between items-center p-4 border-b">
        <h2 className="text-xl font-semibold">Campaign Assistant</h2>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="w-4" />
        </Button>
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-4">
          {messages.map(msg => (
            <ChatMessage 
              key={msg.id}
              message={msg}
              onVote={(vote) => {updateMessageVote(msg.id, vote)}}
            />
          ))}
          {/* {messages.map(msg => (<SqlQueriesDisplay queries={msg.sqlQueries} />))} */}
          
          {isChatLoading && (
            <div className="flex items-center space-x-2 p-3 bg-muted/30 rounded-lg animate-pulse">
              <div className="w-4 h-4 rounded-full bg-primary/60"></div>
              <p className="text-sm text-foreground">
                Generating response...
              </p>
            </div>
          )}
          
          <div ref={messageListRef} />
        </div>
      </div>

      <div className="p-4">
        <div className="flex items-end space-x-2">
          <Textarea
            value={message}
            onChange={(e) => {setMessage(e.target.value)}}
            onKeyDown={handleKeyDown}
            placeholder="Type your message here..."
            className="resize-none min-h-[80px]"
            disabled={isChatLoading}
          />
          <Button 
            onClick={handleSend}
            disabled={isChatLoading || !message.trim()}
            className="h-20"
          >
            <Send className="w-4 h-4" />
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
