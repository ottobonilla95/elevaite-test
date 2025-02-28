// components/ChatComponent.tsx
"use client";
import { useState } from "react";
import { Textarea } from "../components/ui/textarea";
import { Button } from "../components/ui/button";
import { X, MessageCircle } from "lucide-react";
import { Send } from "lucide-react";

export default function ChatComponent({ onClose }: { onClose: () => void }){
  const [message, setMessage] = useState("");

  return (
    <div className="sticky flex flex-col h-[80vh]">
      <div className="flex justify-between items-center p-4 border-b">
        <h2 className="text-xl font-semibold">Campaign Assistant</h2>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className=" w-4" />
        </Button>
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        <div className="space-y-4">
          <div className="bg-muted/50 p-4 rounded-lg">
            <p>How can I help with your creative insights today?</p>
          </div>
        </div>
      </div>

      <div className="p-4 flex justify-between items-center ">
      <Textarea
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message here..."
        className="resize-none"
      />

      <Button className=" ml-1 w-full md:w-auto " variant="ghost" disabled={!message}>
        <Send className="w-4 h-4"/>
      </Button>
    </div>
    </div>
  );
}
