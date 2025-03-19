import React, { useRef, useEffect } from 'react';
import { Message } from './type';
import MessageBubble from './MessageBubble';
import { ChevronRight, MessageSquare } from 'lucide-react';

interface ChatPanelProps {
    showFlow: boolean;
    messages: Message[];
    userQuery: string;
    setUserQuery: React.Dispatch<React.SetStateAction<string>>;
    handleQuerySubmit: () => void;
    handleExampleClick: (example: string) => void;
    isProcessing: boolean;
    messagesEndRef: React.RefObject<HTMLDivElement>;
}

const ChatPanel: React.FC<ChatPanelProps> = ({
    showFlow,
    messages,
    userQuery,
    setUserQuery,
    handleQuerySubmit,
    handleExampleClick,
    isProcessing,
    messagesEndRef
}) => {
    // Sample example queries
    const exampleQueries = [
        "How many iPhone models were released after 2020?",
        "Calculate the average sales from our quarterly data",
        "Write a function to convert temperatures between Celsius and Fahrenheit"
    ];

    return (
        <div
            className={`bg-white border-l border-gray-200/50 flex flex-col ${showFlow ? 'hidden md:flex md:w-[350px]' : 'w-full'
                }`}
        >
            <div className="flex-1 p-4 overflow-y-auto">
                {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-6">
                        <div className="mb-6 text-gray-400">
                            <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-30" />
                            <h3 className="text-lg font-medium text-gray-500">No messages yet</h3>
                            <p className="text-sm text-gray-400 mt-1">Send a query to get started</p>
                        </div>

                        <div className="w-full space-y-3 mt-4">
                            <p className="text-sm font-medium text-gray-600">Try one of these examples:</p>
                            {exampleQueries.map((query, index) => (
                                <button
                                    key={index}
                                    className="w-full text-left px-4 py-3 rounded-lg text-sm bg-gray-50 hover:bg-gray-100 transition-colors border border-gray-200/70"
                                    onClick={() => handleExampleClick(query)}
                                >
                                    {query}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {messages.map((message) => (
                            <MessageBubble key={message.id} message={message} />
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            <div className="p-4 border-t border-gray-200/50">
                <div className="flex items-center">
                    <input
                        type="text"
                        className="flex-1 border border-gray-300 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary"
                        placeholder="Ask a question..."
                        value={userQuery}
                        onChange={(e) => setUserQuery(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleQuerySubmit();
                            }
                        }}
                        disabled={isProcessing}
                    />
                    <button
                        className={`bg-primary text-white px-4 py-2 rounded-r-lg hover:bg-primary/90 transition-colors ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''
                            }`}
                        onClick={handleQuerySubmit}
                        disabled={isProcessing}
                    >
                        <ChevronRight className="w-5 h-5" />
                    </button>
                </div>
                {isProcessing && (
                    <div className="mt-2 text-xs text-gray-500 flex items-center">
                        <div className="w-3 h-3 bg-primary/60 rounded-full animate-pulse mr-2"></div>
                        Processing query...
                    </div>
                )}
            </div>
        </div>
    );
};

export default ChatPanel;