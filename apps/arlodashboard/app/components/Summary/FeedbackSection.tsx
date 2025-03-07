import React from 'react';
import { FeedbackItem } from './types';

interface FeedbackSectionProps {
    title: string;
    feedbackItems: FeedbackItem[];
    type: 'upvote' | 'downvote';
    onFeedbackClick: (feedbackItem: FeedbackItem, type: 'upvote' | 'downvote') => void;
    bgColor: string;
}

export const FeedbackSection: React.FC<FeedbackSectionProps> = ({
    title,
    feedbackItems,
    type,
    onFeedbackClick,
    bgColor
}) => {
    const handleItemClick = (feedbackItem: FeedbackItem) => {
        // Call the parent component's click handler
        onFeedbackClick(feedbackItem, type);
    };

    return (
        <div className={`${bgColor} rounded shadow border border-gray-200`}>
            <div className="p-2 border-b border-gray-200">
                <h2 className="font-semibold">{title}</h2>
            </div>
            <div className="overflow-y-auto">
                <ul className="divide-y divide-gray-200">
                    {feedbackItems.map((feedbackItem, index) => (
                        <li key={index} className="py-3 px-3 hover:bg-gray-50">
                            <div
                                onClick={() => handleItemClick(feedbackItem)}
                                className="flex items-start w-full text-left cursor-pointer"
                            >
                                {type === 'upvote' ? (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-green-600 mr-2 mt-1 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                                    </svg>
                                ) : (
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-red-600 mr-2 mt-1 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M18 9.5a1.5 1.5 0 11-3 0v-6a1.5 1.5 0 013 0v6zM14 9.667v-5.43a2 2 0 00-1.105-1.79l-.05-.025A4 4 0 0011.055 2H5.64a2 2 0 00-1.962 1.608l-1.2 6A2 2 0 004.44 12H8v4a2 2 0 002 2 1 1 0 001-1v-.667a4 4 0 01.8-2.4l1.4-1.866a4 4 0 00.8-2.4z" />
                                    </svg>
                                )}
                                <div>
                                    <p className="text-md font-medium">
                                        {feedbackItem.item} ({feedbackItem.count})
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        {feedbackItem.category || "Symptom"}
                                    </p>
                                </div>
                            </div>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
};