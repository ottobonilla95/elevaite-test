
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

export interface ContactDetailsStr {
    customerName: string;
    productName?: string;
    issue?: string;
    uxVersion?: string;
    email?: string;
    phoneNumber?: string;
}


export const defaultContact: ContactDetailsStr = {
    customerName: "Unknown",
    productName: "Unknown",
    issue: "Unknown",
    uxVersion: "Unknown",
    email: "Unknown",
    phoneNumber: "Unknown",
}

export interface OpexData {
    caseId: string;
    subject?: string;
    issue?: string;
    symptom?: string;
    problem?: string;
    root_cause?: string;
    product?: string;
}

export interface SFData {
    AccountId: string;
    CaseNumber?: string;
    Description?: string;
    Id?: string;
    Status?: string;
    Subject?: string;
    UX_Version__c?: string;
    ContactPhone?: string;
    ContactEmail?: string;
    Problem__c?: string;
    Root_Cause__c?: string;
    Symptoms__c?: string;
}

export const defaultOpexData: OpexData = {
    caseId: "Unknown",
    subject: "Unknown",
    issue: "Unknown",
    symptom: "Unknown",
    problem: "Unknown",
    root_cause: "Unknown",
    product: "Unknown",
}


export interface SessionObject {
    id: string;
    label: string;
    messages: ChatMessageObject[];
    creationDate: string;
    summary?: SessionSummaryObject;
    caseID?: string;
    prevFetchedKnowledge?: string;
    chatFlow: string;
    welcomeFlow: string;
    contactDetails?: ContactDetailsStr;
    opexData?: OpexData[];
    sfData?: SFData[];
    caseIdSF?: string;
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
    caseID: "",
    welcomeFlow: "chat",
    chatFlow: "welcome",
    contactDetails: defaultContact,
    opexData: [],
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
    fetched_knowledge?: string;
    extracted_information?: string;
    verification_message?: string;
    issue_acknowledgement?: string;
    opex_data: string[][];
}

export interface SFResponseMessage {
    response: string;
    query_id: string;
    urls_fetched: string[];
    fetched_knowledge?: string;
    extracted_information?: string;
    verification_message?: string;
    issue_acknowledgement?: string;
    sf_data: SFData[];
}

