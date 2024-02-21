"use client";
import { useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useState } from "react";
import { fetchChatbotResponse } from "../../lib/actions";
import type { ChatBotGenAI, ChatMessageObject, ChatMessageResponse, ChatbotV, SessionObject } from "../../lib/interfaces";
import { CHATBOT_MESSAGE_ID_PREFIX, SESSION_ID_PREFIX, USER_MESSAGE_ID_PREFIX, defaultChatbotV, defaultGenAIBotOption, defaultSession } from "../../lib/interfaces";
import { getLoadingMessageFromAgentStatus } from "./ChatContextHelpers";



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

    
    // Initializations
    // useEffect(() => {
    //     console.log("Sessions changed", sessions);
    // }, [sessions]);

    useEffect(() => {
        if (!selectedSession) return;        
        const newSessions = sessions.map(item => item.id === selectedSession.id ? selectedSession : item);
        setSessions(newSessions);
    }, [selectedSession]);



    useEffect(() => {
        // Whenever we add a session or delete all sessions, select the latest one.
        setSelectedSession(sessions[sessions.length-1]);
    }, [sessions.length]);





    function addNewSession(): void {
        // Find highest id
        const sessionIdNumbersList = sessions.map(item => Number(item.id.slice(SESSION_ID_PREFIX.length)));
        // New id will be highest +1
        const newId = SESSION_ID_PREFIX + (sessionIdNumbersList.length > 0 ? (Math.max(...sessionIdNumbersList) + 1) : 0);
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
        const newSession = updateSessionListWithNewMessage(newMessage, selectedSession);
        void getServerResponse(messageText, newSession);
    }


    function updateSessionListWithNewMessage(message: ChatMessageObject, passedSession: SessionObject): SessionObject {
        const newMessageList = [...passedSession.messages, message];
        const newSelectedSession = {...passedSession, messages: newMessageList};
        setSelectedSession(newSelectedSession);
        return newSelectedSession;
    }



    async function getServerResponse(messageText: string, passedSession: SessionObject): Promise<void> {
        const userId = session.data?.user?.id;
        if (!userId) return;
        await handleResponse(userId, messageText, passedSession);
    }

    function handleAgentStatusChange(event: MessageEvent): void {
        if (event.data && typeof event.data === "string") {
            setChatLoadingMessage(getLoadingMessageFromAgentStatus(event.data));
        }
    }

    // THIS IS NOT BEING USED (check the one below)
    // async function handleStreamingResponse(userId: string, messageText: string): Promise<void> {
    //     if (!selectedSession) return;
    //     setIsChatLoading(true);
    //     try {
    //         console.log("UserId:", userId, "sessionId", selectedSession.id, "chatbotV", selectedChatbotV, "chatbotAI", selectedGenAIBot);
    //         const agentEvent = await getAgentEventSource(userId, selectedSession.id);
    //         agentEvent.onmessage = handleAgentStatusChange;
    //         const data = await getStreamingResponse(userId, messageText, selectedSession.id, selectedChatbotV, selectedGenAIBot);
    //         updateSessionListWithNewMessage(formatMessageFromServerResponse(data))
    //         agentEvent.close();
    //     } catch (error) {
    //         // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
    //         console.error("Error in streaming response:", error);
    //     } finally {
    //         setIsChatLoading(false);
    //     }
    // }

    async function handleResponse(userId: string, messageText: string, passedSession: SessionObject): Promise<void> {
        setIsChatLoading(true);        
        const agentEvent = new EventSource(`${process.env.NEXT_PUBLIC_BACKEND_URL}currentStatus?uid=${userId}&sid=${passedSession.id}`);
        try {
            agentEvent.onmessage = handleAgentStatusChange;
            const data = await fetchChatbotResponse(userId, messageText, passedSession.id, selectedChatbotV, selectedGenAIBot);
            updateSessionListWithNewMessage(formatMessageFromServerResponse(data), passedSession);
        } catch (error) {
            // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
            console.error("Error in non-streaming response:", error);
        } finally {
            setIsChatLoading(false);
            agentEvent.close();
        }
    }


    function formatMessageFromServerResponse(data: ChatMessageResponse): ChatMessageObject {
        const usedSession = selectedSession ?? sessions[0];
        // Find highest id of non-bot messages
        const botIdNumbersList = usedSession.messages.filter(item => item.isBot).map(botItem => Number(botItem.id.slice(CHATBOT_MESSAGE_ID_PREFIX.length)));
        const newId = CHATBOT_MESSAGE_ID_PREFIX + (botIdNumbersList.length > 0 ? (Math.max(...botIdNumbersList) + 1) : 0);
        const newMessage: ChatMessageObject = {
            id: newId,
            date: new Date().toISOString(),
            isBot: true,
            text: data.text,
            userName: "ElevAIte",
            files: data.refs.map(item => { return {
                id: item + new Date().toISOString(),
                filename: item,
            }})
        }
        return newMessage;
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