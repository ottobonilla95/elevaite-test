"use client";
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
    DateRange,
    SummaryData,
    FeedbackItem,
    SelectedFeedback,
    FeedbackDetails
} from './types';
import { MetricCard } from './MetricCard';
import { FeedbackSection } from './FeedbackSection';
import { RootCausesChart } from './RootCausesChart';
import { FeedbackDetailsModal } from './FeedbackDetailsModal';

interface SummaryProps {
    dateRange: DateRange | null;
}

export const Summary: React.FC<SummaryProps> = ({ dateRange }) => {
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<SummaryData>({
        totalSessions: 0,
        aht: '00:00',
        resolutionRate: 0,
        upvotes: 0,
        downvotes: 0,
        rootCauses: [],
        feedback: {
            mostUpvoted: [],
            mostDownvoted: []
        }
    });

    // Dialog state
    const [dialogOpen, setDialogOpen] = useState<boolean>(false);
    const [selectedFeedback, setSelectedFeedback] = useState<SelectedFeedback | null>(null);
    const [feedbackDetails, setFeedbackDetails] = useState<FeedbackDetails[] | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            // Reset loading state
            setLoading(true);

            // Check if we have dateRange - if not or both dates are empty, fetch all data
            const shouldFetchAllData = !dateRange ||
                (dateRange.fromDate === '' && dateRange.toDate === '') ||
                !dateRange.fromDate || !dateRange.toDate;

            try {
                let summaryParams = {};
                let feedbackParams = {};

                // Only add date parameters if we're not fetching all data
                if (!shouldFetchAllData) {
                    summaryParams = {
                        from: dateRange.fromDate,
                        to: dateRange.toDate
                    };

                    feedbackParams = {
                        from: dateRange.fromDate,
                        to: dateRange.toDate
                    };
                }

                console.log("Fetching data with params:", shouldFetchAllData ? "All data" : summaryParams);

                const [summaryResponse, feedbackResponse] = await Promise.all([
                    axios.get(`http://localhost:5000/api/summary-data`, { params: summaryParams }),
                    axios.get(`http://localhost:5000/api/feedback`, { params: feedbackParams })
                ]);

                // Transform root causes data
                if (summaryResponse.data.rootCauses) {
                    summaryResponse.data.rootCauses = summaryResponse.data.rootCauses.map((item: any) => ({
                        name: item.name || '',
                        sessions: item.sessions || 0,
                        percentage: item.percentage || 0
                    }));
                }

                // Filter out the first item from both upvoted and downvoted arrays
                const filteredResponse = {
                    ...feedbackResponse.data,
                    mostUpvoted: feedbackResponse.data.mostUpvoted.slice(1, 4),
                    mostDownvoted: feedbackResponse.data.mostDownvoted.slice(1, 4)
                };

                setData({
                    ...summaryResponse.data,
                    feedback: filteredResponse
                });
            } catch (error) {
                console.error('Error fetching data:', error);
                setError(error instanceof Error ? error.message : 'An unknown error occurred');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [dateRange]);

    // Add this improved handleFeedbackClick function to your Summary.tsx

    const handleFeedbackClick = async (feedbackItem: FeedbackItem, type: 'upvote' | 'downvote') => {
        try {
            console.log('Handling feedback click:', feedbackItem.item);

            // Set the selected feedback immediately
            setSelectedFeedback({
                ...feedbackItem,
                type
            });

            // Open the modal right away
            setDialogOpen(true);

            // Check for transcript_ids and format them correctly if present
            let transcriptIds = '';
            if (feedbackItem.transcript_ids) {
                if (Array.isArray(feedbackItem.transcript_ids)) {
                    // For array of transcript IDs (from API)
                    transcriptIds = feedbackItem.transcript_ids.join(',');
                    console.log(`Found ${feedbackItem.transcript_ids.length} transcript IDs`);
                } else if (typeof feedbackItem.transcript_ids === 'string') {
                    // In case it's already a string
                    transcriptIds = feedbackItem.transcript_ids;
                    console.log('Using pre-formatted transcript IDs string');
                }
            } else {
                console.warn('No transcript IDs found for this feedback item');
            }

            // Always start with empty details array
            setFeedbackDetails([]);

            // Only attempt to fetch details if we have transcript IDs
            if (transcriptIds) {
                // Prepare parameters for feedback details request
                const params: any = {
                    item: feedbackItem.item,
                    type: type,
                    transcript_ids: transcriptIds
                };

                // Add date parameters if they exist
                if (dateRange && dateRange.fromDate && dateRange.toDate) {
                    params.from = dateRange.fromDate;
                    params.to = dateRange.toDate;
                }

                console.log('Fetching feedback details with params:', params);

                try {
                    const response = await axios.get('http://localhost:5000/api/feedback-details', {
                        params,
                        timeout: 8000 // Increase timeout to 8 seconds
                    });

                    console.log('Feedback details response:', response.data);

                    if (response.data && Array.isArray(response.data)) {
                        setFeedbackDetails(response.data);
                    } else {
                        console.warn('No valid data in response');
                    }
                } catch (apiError) {
                    console.error('Error fetching feedback details:', apiError);
                }
            }
        } catch (error) {
            console.error('Error in handleFeedbackClick:', error);
        }
    };
    const calculateSatisfaction = (upvotes: number, downvotes: number) => {
        const satisfaction = upvotes + downvotes === 0 ? 0 : (upvotes / (upvotes + downvotes) * 100);
        return satisfaction;
    };

    // Parse AHT from string to minutes for progress calculation
    const parseAhtToMinutes = (aht: string): number => {
        const [minutes, seconds] = aht.split(':').map(Number);
        return minutes + (seconds / 60);
    };

    if (loading) return (
        <div className="flex justify-center items-center h-screen">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
    );

    if (error) return (
        <div className="flex justify-center items-center h-screen">
            <p className="text-red-500">Error: {error}</p>
        </div>
    );

    return (
        <div className="w-full">
            <div className="p-10">
                {/* Metric Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <MetricCard
                        title="Total Sessions"
                        value={data.totalSessions}
                        maxValue={10000}
                        subtitle="Support Interactions"
                    />

                    <MetricCard
                        title="Average Handle Time"
                        value={data.aht}
                        maxValue={30}
                        subtitle="Minutes per session"
                    />

                    <MetricCard
                        title="ElevAIte Usage"
                        value={`${calculateSatisfaction(data.upvotes, data.downvotes).toFixed(1)}%`}
                        maxValue={100}
                        subtitle={`Based on ${data.upvotes + data.downvotes} ratings`}
                    />
                </div>

                {/* Feedback Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                    <FeedbackSection
                        title="Most Upvoted Feedback"
                        feedbackItems={data.feedback.mostUpvoted}
                        type="upvote"
                        onFeedbackClick={handleFeedbackClick}
                        bgColor="bg-green-50"
                    />

                    <FeedbackSection
                        title="Most Downvoted Feedback"
                        feedbackItems={data.feedback.mostDownvoted}
                        type="downvote"
                        onFeedbackClick={handleFeedbackClick}
                        bgColor="bg-red-50"
                    />
                </div>

                {/* Root Causes Chart */}
                <div className="mt-6">
                    <RootCausesChart rootCauses={data.rootCauses} />
                </div>

                {/* Test button - uncomment if needed for testing */}
                {/* <button 
                    className="mt-4 p-2 bg-blue-500 text-white rounded"
                    onClick={() => {
                        setSelectedFeedback({
                            item: "Test Feedback Item",
                            count: 42,
                            category: "Test Category",
                            type: "upvote"
                        });
                        setFeedbackDetails([{
                            chat_transcript_id: "TEST-123",
                            product: "Test Product",
                            problem: "Test Problem",
                            root_cause: "Test Root Cause",
                            symptoms: "Test Symptoms",
                            upvotes: 1
                        }]);
                        setDialogOpen(true);
                    }}
                >
                    Test Modal
                </button> */}
            </div>

            {/* Feedback Details Modal */}
            <FeedbackDetailsModal
                isOpen={dialogOpen}
                onClose={() => setDialogOpen(false)}
                selectedFeedback={selectedFeedback}
                feedbackDetails={feedbackDetails}
            />
        </div>
    );
};

export default Summary;