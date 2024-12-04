
// Enums, Interfaces, Types, and initializer objects
////////////////////////////////////////////////////
import { v4 as uuid } from 'uuid'

export const SESSION_ID_PREFIX = "sessionId_";
export const USER_MESSAGE_ID_PREFIX = "userMessageId_";
export const CHATBOT_MESSAGE_ID_PREFIX = "chatbotMessageId_";
export const SESSION_LABEL_PREFIX = "Session ";

export enum ChatbotV {
    InWarranty = "in-warranty",
    OutOfWarranty = "out-of-warranty",
    AgentAssist = "agent-assist",
    Upsell = "upsell",
}
export const defaultChatbotV = ChatbotV.InWarranty;

export enum ChatBotGenAI {
    Pan = "pan",
    Cisco = "cisco",
    CiscoClo = "cisco_clo",
    ServiceNow = "servicenow",
    BGPInsights = "bgpinsights",
    Creative = "Creative"
}
export const defaultGenAIBotOption = ChatBotGenAI.CiscoClo;

export interface ChatBotPayload {
    actor: string;
    content: string;
}

export interface SessionObject {
    id: string;
    label: string;
    messages: ChatMessageObject[];
    creationDate: string;
    summary?: SessionSummaryObject;
    prevFetchedKnowledge?: string;
}

export interface SessionSummaryObject {
    title: string;
    summaryID:string;
    problem: string;
    solution: string;
    sessionMessageLengthOnLastUpdate?: number;
    isExpectingDisplay?: boolean;
}

export const defaultSession: SessionObject = {
    id: uuid(),
    label: "Session 1",
    messages: [],
    creationDate: new Date().toISOString(),
}

export interface ChatMessageResponse {
    text: string;
    queryID: string;
    refs: string[];
}

export interface ChatMessageObject {
    id: string;
    userName: string;
    isBot: boolean;
    date: string;
    text: string;
    queryID: string;
    vote?: 0 | 1 | -1;
    feedback?: string;
    feedbackfiles?: ChatMessageFileObject[];
    files?: ChatMessageFileObject[];
}

export interface ChatMessageFileObject {
    id: string;
    filename: string;
    fileType?: ChatMessageFileTypes;
    isDownloadable?: boolean;
    isViewable?: boolean;
}

export enum ChatMessageFileTypes {
    DOC = "document",
}

export interface MarkdownMessageProps {
    text: string;
  }

export interface RegeneratedResponse {
    response: string;
}

export interface SummaryResponse {
    summaryID: string;
    summary: string;
}

export interface ChatResponseMessage {
    response: string;
    query_id: string;
    urls_fetched: string[];
    fetched_knowledge: string;
}

