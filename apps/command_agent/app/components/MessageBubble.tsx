import React from 'react';
import { Message } from './type';

interface MessageBubbleProps {
    message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
    // Format time for display
    const formatTime = (date: Date): string => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // Determine styling based on message type
    let classes = '';
    let badge = null;

    switch (message.type) {
        case 'user':
            classes = 'bg-primary/10 text-gray-800 ml-auto border-primary/20';
            break;
        case 'agent':
            classes = 'bg-indigo-50 border-indigo-100';
            badge = <span className="text-xs font-semibold text-indigo-700 mb-1 block">{message.agent} Agent</span>;
            break;
        case 'component':
            classes = 'bg-emerald-50 border-emerald-100';
            badge = <span className="text-xs font-semibold text-emerald-700 mb-1 block">{message.agent} Component</span>;
            break;
        case 'tool':
            classes = 'bg-amber-50 border-amber-100';
            badge = <span className="text-xs font-semibold text-amber-700 mb-1 block">{message.agent} Tool</span>;
            break;
        case 'final':
            classes = 'bg-blue-50 border-blue-100';
            badge = <span className="text-xs font-semibold text-blue-700 mb-1 block">Final Response</span>;
            break;
        default:
            classes = 'bg-gray-50 border-gray-100';
    }

    return (
        <div
            className={`p-3 rounded-lg max-w-[90%] border ${classes} ${message.type === 'user' ? 'ml-auto' : 'mr-auto'}`}
        >
            {badge}
            <p className="text-sm whitespace-pre-wrap">{message.text}</p>
            <div className="text-right mt-1">
                <span className="text-xs text-gray-400">
                    {formatTime(message.timestamp)}
                </span>
            </div>
        </div>
    );
};

export default MessageBubble;