"use client";
import { useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useState } from "react";
import { getAgentEventSource, getStreamingResponse } from "../../lib/actions";
import type { ChatMessageObject, ChatbotV, SessionObject } from "../../lib/interfaces";
import { ChatBotGenAI, defaultChatbotV, defaultGenAIBotOption, defaultSession } from "../../lib/interfaces";
import { getTestMessagesList } from "../../lib/testData";
import { getLoadingMessageFromAgentStatus } from "./ChatContextHelpers";


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
    addNewSession: () => {/**/},
    clearAllSessions: () => {/**/},
    selectedSession: undefined,
    setSelectedSession: () => {/**/},
    setSelectedGenAIBot: () => {/**/},
    isChatLoading: false,
    chatLoadingMessage: "",
    addNewUserMessageToCurrentSession: () => {/**/},
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


    // useEffect(() => {
    //     console.log("Session:", session);
    // }, [session]);
    
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
        const sessionIdNumbersList = sessions.map(item => Number(item.id.slice(SESSION_ID_PREFIX.length)));
        // New id will be highest +1
        // const newId = SESSION_ID_PREFIX + (sessionIdNumbersList.length > 0 ? (Math.max(...sessionIdNumbersList) + 1) : 0);
        const newId = (sessionIdNumbersList.length > 0 ? (Math.max(...sessionIdNumbersList) + 1) : 0).toString();
        // New Session
        const newSession: SessionObject = {
            id: newId,
            label: `Session ${sessions.length + 1}`,
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
        const userIdNumbersList = selectedSession.messages.filter(item => !item.isBot).map(userItem => Number(userItem.id.slice(USER_MESSAGE_ID_PREFIX.length)));
        const newId = USER_MESSAGE_ID_PREFIX + (userIdNumbersList.length > 0 ? (Math.max(...userIdNumbersList) + 1) : 0);
        const newMessage: ChatMessageObject = {
            id: newId,
            date: new Date().toISOString(),
            isBot: false,
            userName: session.data?.user?.name ?? "Unknown User",
            text: messageText,
        }
        updateSessionListWithNewMessage(newMessage);
        void getServerResponse(messageText);
    }


    function updateSessionListWithNewMessage(message: ChatMessageObject): void {
        if (!selectedSession) return;
        const newMessageList = [...selectedSession.messages, message];
        const newSelectedSession = {...selectedSession, messages: newMessageList};
        const newSessions = sessions.map(item => item.id === newSelectedSession.id ? newSelectedSession : item);
        setSessions(newSessions);
        setSelectedSession(newSessions.find(item => item.id === newSelectedSession.id));
    }



    async function getServerResponse(messageText: string): Promise<void> {
        const userId = session.data?.user?.id;
        // console.log("Session:", session, "user id:", userId);
        if (!userId) return;
        if (selectedGenAIBot === ChatBotGenAI.CiscoClo) {
            await handleNonStreamingResponse(userId, messageText);
        } else {
            await handleStreamingResponse(userId, messageText);
        }
    }

    function handleAgentStatusChange(event: MessageEvent): void {
        if (event.data && typeof event.data === "string") {
            setChatLoadingMessage(getLoadingMessageFromAgentStatus(event.data));
        }
    }

    // THIS IS NOT BEING USED (check the one below)
    async function handleStreamingResponse(userId: string, messageText: string): Promise<void> {
        if (!selectedSession) return;
        setIsChatLoading(true);
        try {
            console.log("UserId:", userId, "sessionId", selectedSession.id, "chatbotV", selectedChatbotV, "chatbotAI", selectedGenAIBot);
            const agentEvent = await getAgentEventSource(userId, selectedSession.id);
            agentEvent.onmessage = handleAgentStatusChange;
            const data = await getStreamingResponse(userId, messageText, selectedSession.id, selectedChatbotV, selectedGenAIBot);
            updateSessionListWithNewMessage(formatMessageFromServerResponse(data))
            agentEvent.close();
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in streaming response:", error);
        } finally {
            setIsChatLoading(false);
        }
    }

    async function handleNonStreamingResponse(userId: string, messageText: string): Promise<void> {
        if (!selectedSession) return;
        setIsChatLoading(true);
        try {
            console.log("UserId:", userId, "sessionId", selectedSession.id, "chatbotV", selectedChatbotV, "chatbotAI", selectedGenAIBot);
            // const agentEvent = await getAgentEventSource(userId, selectedSession.id);
            const agentEvent = new EventSource(`${process.env.NEXT_PUBLIC_BACKEND_URL}currentStatus?uid=${userId}&sid=${selectedSession.id}`);
            agentEvent.onmessage = handleAgentStatusChange;
            const data = await getStreamingResponse(userId, messageText, selectedSession.id, selectedChatbotV, selectedGenAIBot);
            updateSessionListWithNewMessage(formatMessageFromServerResponse(data))
            agentEvent.close();
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in non-streaming response:", error);
        } finally {
            setIsChatLoading(false);
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