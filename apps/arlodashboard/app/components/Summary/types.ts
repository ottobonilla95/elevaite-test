// types.ts
export interface DateRange {
    fromDate: string;
    toDate: string;
}

export interface RootCause {
    name: string;
    sessions: number;
    percentage: number;
}

export interface FeedbackItem {
    item: string;
    category: string;
    count: number;
    transcript_ids: string[];
}

export interface FeedbackDetails {
    chat_transcript_id: string;
    root_cause: string;
    symptoms: string;
    problem: string;
    product: string;
    upvotes: number;
    downvotes: number;
    status: string;
    total_votes: number;
}

export interface SummaryData {
    totalSessions: number;
    aht: string;
    resolutionRate: number;
    upvotes: number;
    downvotes: number;
    rootCauses: RootCause[];
    feedback: {
        mostUpvoted: FeedbackItem[];
        mostDownvoted: FeedbackItem[];
    };
}

export interface SelectedFeedback extends FeedbackItem {
    type: 'upvote' | 'downvote';
}