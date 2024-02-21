"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { ChatBotGenAI, ChatMessageObject, ChatbotV, SessionObject, defaultChatbotV, defaultGenAIBotOption, defaultSession } from "../../lib/interfaces";
import { useSession } from "next-auth/react";
import { getAgentEventSource, getStreamingResponse } from "../../lib/actions";
import { getLoadingMessageFromAgentStatus } from "./ChatContextHelpers";
import { getTestMessagesList } from "../../lib/testData";


const SESSION_ID_PREFIX = "sessionId_";
const USER_MESSAGE_ID_PREFIX = "userMessageId_";


// STRUCTURE 


export interface ChatContextStructure {
    sessions: SessionObject[];
    addNewSession: () => void;
    clearAllSessions: () => void;
    selectedSession: SessionObject | undefined;
    setSelectedSession: (sessionId: string) => void;
    setSelectedGenAIBot: (value: ChatBotGenAI) => void;
    isChatLoading: boolean;
    chatLoadingMessage: string;
    addNewUserMessageToCurrentSession: (message: string) => void;
}

export const ChatContext = createContext<ChatContextStructure>({
    sessions: [],
    addNewSession: () => {},
    clearAllSessions: () => {},
    selectedSession: undefined,
    setSelectedSession: () => {},
    setSelectedGenAIBot: () => {},
    isChatLoading: false,
    chatLoadingMessage: "",
    addNewUserMessageToCurrentSession: () => {},
});








// PROVIDER

interface ChatContextProviderProps {
    children: React.ReactNode;
}


export function ChatContextProvider(props: ChatContextProviderProps): JSX.Element {
    const session = useSession();
    const [sessions, setSessions] = useState<SessionObject[]>([defaultSession]);
    const [selectedSession, setSelectedSession] = useState<SessionObject>();
    const [selectedGenAIBot, setSelectedGenAIBot] = useState<ChatBotGenAI>(defaultGenAIBotOption);
    const [selectedChatbotV, setSelectedChatbotV] = useState<ChatbotV>(defaultChatbotV);
    const [isChatLoading, setIsChatLoading] = useState<boolean>(false);
    const [chatLoadingMessage, setChatLoadingMessage] = useState<string>("");


    useEffect(() => {
        console.log("Session:", session);
    }, [session]);
    
    // Initializations
    // useEffect(() => {
    //     console.log("Sessions changed", sessions);
    // }, [sessions]);
    // useEffect(() => {
    //     console.log("selectedSession changed", selectedSession);
    // }, [selectedSession]);


    useEffect(() => {
        // Whenever we add a session or delete all sessions, select the latest one.
        setSelectedSession(sessions[sessions.length-1]);
    }, [sessions.length]);





    function addNewSession(): void {
        // Find highest id
        const idNumbersList = sessions.map(item => Number(item.id.slice(SESSION_ID_PREFIX.length)));
        // New id will be highest +1
        const newId = SESSION_ID_PREFIX + (Math.max(...idNumbersList) + 1);
        // New Session
        const newSession: SessionObject = {
            id: newId,
            label: "Session " + (sessions.length + 1),
            messages: [],
            creationDate: new Date().toISOString(),
        }
        // Add it to the list
        setSessions(currentSessions => [...currentSessions, newSession]);
    }

    function clearAllSessions(): void {
        setSessions([defaultSession]);
    }

    function setInternallySelectedSession(sessionId: string): void {
        if (!sessionId || sessionId === selectedSession?.id) return;
        const foundSession = sessions.find(item => item.id === sessionId);
        if (!foundSession) return;
        setSelectedSession(foundSession);
    }


    function addNewUserMessageToCurrentSession(messageText: string): void {
        if (!messageText || ! selectedSession) return;
        // Find highest id of non-bot messages
        const userIdNumbersList = selectedSession?.messages.filter(item => !item.isBot).map(userItem => Number(userItem.id.slice(USER_MESSAGE_ID_PREFIX.length)));
        const newId = USER_MESSAGE_ID_PREFIX + (userIdNumbersList.length > 0 ? (Math.max(...userIdNumbersList) + 1) : 0);
        const newMessage: ChatMessageObject = {
            id: newId,
            date: new Date().toISOString(),
            isBot: false,
            userName: session?.data?.user?.name ?? "Unknown User",
            text: messageText,
        }
        updateSessionListWithNewMessage(newMessage);
        getServerResponse(messageText);
    }


    function updateSessionListWithNewMessage(message: ChatMessageObject): void {
        if (!sessions || !selectedSession || !message) return;
        const newMessageList = [...selectedSession.messages, message];
        const newSelectedSession = {...selectedSession, messages: newMessageList};
        const newSessions = sessions.map(item => item.id === newSelectedSession.id ? newSelectedSession : item);
        setSessions(newSessions);
        setSelectedSession(newSessions.find(item => item.id === newSelectedSession.id));
    }



    function getServerResponse(messageText: string): void {
        const userId = session?.data?.user?.id;
        // console.log("Session:", session, "user id:", userId);
        if (!userId) return;
        if (selectedGenAIBot === ChatBotGenAI.CISCO_CLO) {
            handleNonStreamingResponse(userId, messageText);
        } else {
            handleStreamingResponse(userId, messageText);
        }
    }

    function handleAgentStatusChange(event: MessageEvent<any>) {
        if (event?.data && typeof event.data === "string") {
            setChatLoadingMessage(getLoadingMessageFromAgentStatus(event.data));
        }
    }

    async function handleStreamingResponse(userId: string, messageText: string): Promise<void> {
        if (!selectedSession) return;
        setIsChatLoading(true);
        const agentEvent = await getAgentEventSource(userId, selectedSession.id);
        agentEvent.onmessage = handleAgentStatusChange;
        try {
            const data = await getStreamingResponse(userId, messageText, selectedSession.id, selectedChatbotV, selectedGenAIBot);
            updateSessionListWithNewMessage(formatMessageFromServerResponse(data))
        } catch (error) {
            console.error("Error in streaming response:", error);
        } finally {
            setIsChatLoading(false);
            agentEvent.close();
        }
    }

    async function handleNonStreamingResponse(userId: string, messageText: string): Promise<void> {
        if (!selectedSession) return;
        setIsChatLoading(true);
        const agentEvent = await getAgentEventSource(userId, selectedSession.id);
        agentEvent.onmessage = handleAgentStatusChange;
        try {
        const data = await getStreamingResponse(userId, messageText, selectedSession.id, selectedChatbotV, selectedGenAIBot);
        updateSessionListWithNewMessage(formatMessageFromServerResponse(data))
        } catch (error) {
            console.error("Error in non-streaming response:", error);
        } finally {
            setIsChatLoading(false);
            agentEvent.close();
        }
    }


    function formatMessageFromServerResponse(data): ChatMessageObject {
        console.log("Data to format into message:", data);
        // TODO: finalize this.
        return getTestMessagesList(1)[0];
    }

   
  
    return (
        <ChatContext.Provider
            value={ {
                sessions,
                addNewSession,
                clearAllSessions,
                selectedSession,
                setSelectedSession: setInternallySelectedSession,
                setSelectedGenAIBot,
                isChatLoading,
                chatLoadingMessage,
                addNewUserMessageToCurrentSession,
            } }
        >
            {props.children}
        </ChatContext.Provider>
    );
}
  
export function useChat(): ChatContextStructure {
    return useContext(ChatContext);
}