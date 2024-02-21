
// Enums, Interfaces, Types, and initializer objects
////////////////////////////////////////////////////


export enum ChatbotV {
    IN_WARRANTY = "in-warranty",
    OUT_OF_WARRANTY = "out-of-warranty",
    AGENT_ASSIST = "agent-assist",
    UPSELL = "upsell",
}
export const defaultChatbotV = ChatbotV.IN_WARRANTY;

export enum ChatBotGenAI {
    NETGEAR = "netgear",
    NETSKOPE = "netskope",
    PAN = "pan",
    CISCO = "cisco",
    CISCO_CLO = "cisco_clo",
    ARLO = "arlo",
    JUNIPER = "juniper_vsrx",
}
export const defaultGenAIBotOption = ChatBotGenAI.CISCO_CLO;


export interface SessionObject {
    id: string;
    label: string;
    messages: ChatMessageObject[];
    creationDate: string;
}

export const defaultSession: SessionObject = {
    id: "id_0",
    label: "Session 1",
    messages: [],
    creationDate: new Date().toISOString(),
}


export interface ChatMessageObject {
    id: string;
    userName: string;
    isBot: boolean;
    date: string;
    text: string;
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








