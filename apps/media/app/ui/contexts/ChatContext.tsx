"use client";
import { useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useState, useRef  } from "react";
import { fetchChatbotResponse, fetchSessionSummary } from "../../lib/actions";
import type {
  ChatBotGenAI,
  ChatBotPayload,
  ChatMessageObject,
  ChatMessageResponse,
  ChatbotV,
  SessionObject,
  SessionSummaryObject,
} from "../../lib/interfaces";
import {
  CHATBOT_MESSAGE_ID_PREFIX,
  SESSION_ID_PREFIX,
  USER_MESSAGE_ID_PREFIX,
  defaultChatbotV,
  defaultGenAIBotOption,
  defaultSession,
} from "../../lib/interfaces";
import { getLoadingMessageFromAgentStatus , tableToCsv, downloadCsv } from "./ChatContextHelpers";
// STRUCTURE

export interface ChatContextStructure {
  sessions: SessionObject[];
  addNewSession: () => void;
  deleteSessionById: (sessionId: string) => void;
  clearAllSessions: () => void;
  selectedSession: SessionObject | undefined;
  setSelectedSession: (sessionId: string) => void;
  selectedGenAIBot: string |undefined;
  setSelectedGenAIBot: (value: ChatBotGenAI) => void;
  isChatLoading: boolean;
  chatLoadingMessage: string;
  addNewUserMessageToCurrentSession: (message: string) => void;
  updateMessageVote: (messageId: string, passedVote: -1 | 0 | 1) => void;
  updateMessageFeedback: (messageId: string, passedFeedback: string) => void;
  getSessionSummary: () => void;
  removeExpectedDisplayFromSelectedSessionSummary: () => void;
  addNewUserMessageWithLastMessages: (message: string,file?: File) => void;
}

export const ChatContext = createContext<ChatContextStructure>({
  sessions: [],
  addNewSession: () => {
    /**/
  },
  deleteSessionById: () => {
    /**/
  },
  clearAllSessions: () => {
    /**/
  },
  selectedSession: undefined,
  setSelectedSession: () => {
    /**/
  },
  selectedGenAIBot:undefined,
  setSelectedGenAIBot: () => {
    /**/
  },
  isChatLoading: false,
  chatLoadingMessage: "",
  addNewUserMessageToCurrentSession: () => {
    /**/
  },
  updateMessageVote: () => {
    /**/
  },
  updateMessageFeedback: () => {
    /**/
  },
  getSessionSummary: () => {
    /**/
  },
  removeExpectedDisplayFromSelectedSessionSummary: () => {
    /**/
  },
  addNewUserMessageWithLastMessages: () => {
    /**/
  },
});

// PROVIDER

interface ChatContextProviderProps {
  children: React.ReactNode;
}

export function ChatContextProvider(
  props: ChatContextProviderProps
): JSX.Element {
  const session = useSession();
  const [sessions, setSessions] = useState<SessionObject[]>([defaultSession]);
  const [selectedSession, setSelectedSession] = useState<SessionObject>();
  const [selectedGenAIBot, setSelectedGenAIBot] = useState<ChatBotGenAI>(
    defaultGenAIBotOption
  );
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- No provisions to change this for now. Leaving it because we will, eventually.
  const [selectedChatbotV, setSelectedChatbotV] =
    useState<ChatbotV>(defaultChatbotV);
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);
  const [chatLoadingMessage, setChatLoadingMessage] = useState<string>("");
  // Initializations
  // useEffect(() => {
  //     console.log("Sessions changed", sessions);
  // }, [sessions]);

  // const scrollPosition = chatContainerRef.current?.scrollTop;

  // useEffect(() => {
  //   if (chatContainerRef.current && scrollPosition !== undefined) {
  //     chatContainerRef.current.scrollTop = scrollPosition;
  //   }
  // }, [selectedSession?.messages]);
  
  useEffect(() => {
    if (!selectedGenAIBot) return;
    setSelectedGenAIBot(selectedGenAIBot);
    // console.log("Setting Gen AI Bot:",selectedGenAIBot);
  }, [selectedGenAIBot]);

  useEffect(() => {
    if (!selectedSession) return;
    const newSessions = sessions.map((item) =>
      item.id === selectedSession.id ? selectedSession : item
    );
    setSessions(newSessions);
  }, [selectedSession]);

  useEffect(() => {
    // Whenever we add a session or delete all sessions, select the latest one.
    if (sessions.length === 0) {
      const newSessions = [defaultSession];
      setSessions(newSessions);
      setSelectedSession(newSessions[0]);
    }
    setSelectedSession(sessions[sessions.length - 1]);
  }, [sessions.length]);

  function addNewSession(): void {
    // Find highest id
    const sessionIdNumbersList = sessions.map((item) =>
      Number(item.id.slice(SESSION_ID_PREFIX.length))
    );
    // New id will be highest +1
    const newIdNumber =
      sessionIdNumbersList.length > 0
        ? Math.max(...sessionIdNumbersList) + 1
        : 0;
    const newId = SESSION_ID_PREFIX + newIdNumber.toString();
    // New Session
    const newSession: SessionObject = {
      id: newId,
      label: `Session ${(newIdNumber + 1).toString()}`,
      messages: [],
      creationDate: new Date().toISOString(),
    };
    // Add it to the list
    setSessions((currentSessions) => [...currentSessions, newSession]);
  }

  function deleteSessionById(sessionId: string): void {
    const foundSession = sessions.find((item) => item.id === sessionId);
    if (!foundSession) return;
    setSessions((current) =>
      current.filter((item) => {
        return item.id !== sessionId;
      })
    );
  }

  function clearAllSessions(): void {
    setSessions([]);
  }

  function setInternallySelectedSession(sessionId: string): void {
    if (!sessionId || sessionId === selectedSession?.id) return;
    const foundSession = sessions.find((item) => item.id === sessionId);
    if (!foundSession) return;
    setSelectedSession(foundSession);
  }

  function addNewUserMessageToCurrentSession(messageText: string): void {
    if (!messageText || !selectedSession) return;
    // Find highest id of non-bot messages
    const userIdNumbersList = selectedSession.messages
      .filter((item) => !item.isBot)
      .map((userItem) =>
        Number(userItem.id.slice(USER_MESSAGE_ID_PREFIX.length))
      );
    const newId =
      USER_MESSAGE_ID_PREFIX +
      (userIdNumbersList.length > 0
        ? Math.max(...userIdNumbersList) + 1
        : 0
      ).toString();
    const newMessage: ChatMessageObject = {
      id: newId,
      date: new Date().toISOString(),
      isBot: false,
      userName: session.data?.user?.name ?? "You",
      text: messageText,
    };
    const newSession = updateSessionListWithNewMessage(
      newMessage,
      selectedSession
    );
    void getServerChatbotResponse(messageText, newSession);
  }

  function updateSessionListWithNewMessage(
    message: ChatMessageObject,
    passedSession: SessionObject
  ): SessionObject {
    const newMessageList = [...passedSession.messages, message];
    const newSelectedSession = { ...passedSession, messages: newMessageList };
    setSelectedSession(newSelectedSession);
    return newSelectedSession;
  }

  function updateMessageVote(messageId: string, passedVote: -1 | 0 | 1): void {
    if (!selectedSession) return;
    const newMessageList = [...selectedSession.messages].map((item) =>
      item.id === messageId ? { ...item, vote: passedVote } : item
    );
    const newSelectedSession = { ...selectedSession, messages: newMessageList };
    setSelectedSession(newSelectedSession);
  }

  function updateMessageFeedback(
    messageId: string,
    passedFeedback: string
  ): void {
    if (!selectedSession) return;
    const newMessageList = [...selectedSession.messages].map((item) =>
      item.id === messageId ? { ...item, feedback: passedFeedback } : item
    );
    const newSelectedSession = { ...selectedSession, messages: newMessageList };
    setSelectedSession(newSelectedSession);
  }

  function updateCurrentSessionWithSummary(
    summary: SessionSummaryObject,
    messagesLength?: number
  ): void {
    if (!selectedSession) return;
    summary.isExpectingDisplay = true;
    if (messagesLength) {
      summary.sessionMessageLengthOnLastUpdate = messagesLength;
    }
    setSelectedSession({ ...selectedSession, summary });
  }

  function removeExpectedDisplayFromSelectedSessionSummary(): void {
    if (!selectedSession) return;
    const newSummary = selectedSession.summary;
    if (newSummary) newSummary.isExpectingDisplay = false;
    setSelectedSession({ ...selectedSession, summary: newSummary });
  }

  async function getServerChatbotResponse(
    messageText: string,
    passedSession: SessionObject
  ): Promise<void> {
    const userId = session.data?.user?.id;
    if (!userId) return;
    await handleServerChatbotResponse(userId, messageText, passedSession);
  }

  function handleAgentStatusChange(event: MessageEvent): void {
    if (event.data && typeof event.data === "string") {
      setChatLoadingMessage(getLoadingMessageFromAgentStatus(event.data));
    }
  }

  async function handleServerChatbotResponse(
    userId: string,
    messageText: string,
    passedSession: SessionObject
  ): Promise<void> {
    setIsChatLoading(true);
    const agentEvent = new EventSource(
      `${process.env.NEXT_PUBLIC_BACKEND_URL ?? ""}currentStatus?uid=${userId}&sid=${passedSession.id}`
    );
    try {
      agentEvent.onmessage = handleAgentStatusChange;
      const data = await fetchChatbotResponse(
        userId,
        messageText,
        passedSession.id,
        selectedChatbotV,
        selectedGenAIBot
      );
      updateSessionListWithNewMessage(
        formatMessageFromServerResponse(data),
        passedSession
      );
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in chatbot response:", error);
    } finally {
      setIsChatLoading(false);
      agentEvent.close();
    }
  }

  function getSessionSummary(): void {
    const userId = session.data?.user?.id;
    if (!userId || !selectedSession) return;
    // If we already have the summary and the length of the messages hasn't changed, serve it again.
    if (
      selectedSession.summary?.sessionMessageLengthOnLastUpdate &&
      selectedSession.summary.sessionMessageLengthOnLastUpdate ===
      selectedSession.messages.length
    ) {
      updateCurrentSessionWithSummary(
        selectedSession.summary,
        selectedSession.messages.length
      );
      return;
    }
    void requestSessionSummary(
      userId,
      selectedSession.id,
      selectedSession.messages.length
    );
  }

  async function requestSessionSummary(
    userId: string,
    sessionId: string,
    messagesLength?: number
  ): Promise<void> {
    setIsChatLoading(true);
    try {
      const data = await fetchSessionSummary(userId, sessionId);
      updateCurrentSessionWithSummary(data, messagesLength);
    } catch (error) {
      // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
      console.error("Error in fetching summary response:", error);
    } finally {
      setIsChatLoading(false);
    }
  }

  function formatMessageFromServerResponse(
    data: ChatMessageResponse
  ): ChatMessageObject {
    const usedSession = selectedSession ?? sessions[0];
    // Find highest id of non-bot messages
    const botIdNumbersList = usedSession.messages
      .filter((item) => item.isBot)
      .map((botItem) =>
        Number(botItem.id.slice(CHATBOT_MESSAGE_ID_PREFIX.length))
      );
    const newId =
      CHATBOT_MESSAGE_ID_PREFIX +
      (botIdNumbersList.length > 0
        ? Math.max(...botIdNumbersList) + 1
        : 0
      ).toString();
    const newMessage: ChatMessageObject = {
      id: newId,
      date: new Date().toISOString(),
      isBot: true,
      text: data.text,
      relatedQueries: data.relatedQueries,
      userName: "elevaite",
      files: data.refs.map((item) => {
        return {
          id: item + new Date().toISOString(),
          filename: item,
        };
      }),
    };
    // console.log("Newmessage:",newMessage);
    return newMessage;
  }

  async function addNewUserMessageWithLastMessages(messageText: string, file?: File): Promise<void> {
    const MAX_PAYLOAD_HISTORY = 3;
    if (!messageText || !selectedSession) return;

    function fileToBase64(file) {
      return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.readAsDataURL(file);
          reader.onload = () => resolve(reader.result);
          reader.onerror = error => reject(error);
      });
    }
    let imageBase64;
    if (file) {
      imageBase64 = await fileToBase64(file);
      // console.log(imageBase64);
    }

    const userIdNumbersList = selectedSession.messages
        .filter((item) => !item.isBot)
        .map((userItem) =>
            Number(userItem.id.slice(USER_MESSAGE_ID_PREFIX.length))
        );
    
    const newId = USER_MESSAGE_ID_PREFIX + (userIdNumbersList.length > 0
        ? Math.max(...userIdNumbersList) + 1
        : 0).toString();

    const newMessage: ChatMessageObject = {
        id: newId,
        date: new Date().toISOString(),
        isBot: false,
        creative:imageBase64,
        userName: session.data?.user?.name ?? "You",
        text: messageText,
    };

    // Update session with new user message
    const newSession = updateSessionListWithNewMessage(newMessage, selectedSession);

    let conversation_payload: ChatBotPayload[] = [];
    for (let i = 0; i < selectedSession.messages.length; i++) {
        if (i > MAX_PAYLOAD_HISTORY) break;
        const message = selectedSession.messages[selectedSession.messages.length - i - 1];
        conversation_payload.push(
            { "actor": message.isBot ? "system" : "user", "content": message.text }
        );
    }

    setIsChatLoading(true);
    conversation_payload = conversation_payload.reverse();
    // console.log("CONVERSATION_PAYLOAD:", conversation_payload);


    // Fetching with streaming
    const response = await fetch("http://127.0.0.1:8000/", {
      method: 'POST',
      headers: {
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
          "X-Token": "coneofsilence",
      },
      body: JSON.stringify({
          "conversation_payload": conversation_payload,
          "query": messageText,
          "skip_llm_call": false,
          "creative": imageBase64 
      })
  });
  if (!response.body) {
    console.error("Response body is null.");
    setIsChatLoading(false);
    return;
  }
  if (!response.ok) {
    console.error(`HTTP error! status: ${response.status}`);
    setIsChatLoading(false);
    return;
  }
  // console.log("RESPONSE:",response);
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = '';
  let fullResponse = '';

// Uncomment for Streaming
//   const TYPING_SPEED = 0.5; 
//   function simulateTyping(text) {
//     return new Promise<void>((resolve) => {
//         let index = 0;
//         let currentResponse = '';  
//         const typingInterval = setInterval(() => {
//             if (index < text.length) {
//                 currentResponse = text[index];
//                 fullResponse += currentResponse
//                 updateSessionListWithNewMessage(
//                     formatMessageFromServerResponse({ text: fullResponse, refs: [] }),
//                     newSession
//                 );
//                 index++;
//             } else {
//                 clearInterval(typingInterval);
//                 resolve(); // Resolve without arguments once typing is complete
//             }
//         }, TYPING_SPEED); // Adjust typing speed here
//     });
// }

//   while (true) {
//     const { done, value } = await reader.read();
//     if (done) break;

//     buffer += decoder.decode(value, { stream: true });
//     const lines = buffer.split('\n\n');
//     buffer = lines.pop() || '';

//     for (const line of lines) {
//         if (line.startsWith('data: ')) {
//             try {
//                 const jsonStr = line.slice(6); // Remove 'data: ' prefix
//                 const json = JSON.parse(jsonStr);
//                 console.log("Parsed JSON:", json.response);
//                 const responseText = json.response; 
//                 // Simulate typing for each new chunk of response
//                 await simulateTyping(responseText);

//             } catch (e) {
//                 console.error("Error parsing JSON:", e);
//             }
//         }
//     }
// }
// setIsChatLoading(false);
// }
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
        if (line.startsWith('data: ')) {
            try {
                console.log("LINE:",line);
                const jsonStr = line.slice(6); // Remove 'data: ' prefix
                const json = JSON.parse(jsonStr);
                let relatedQueries: string[] = [];
                console.log("Parsed JSON:", json.response);
                if(json.response){
                    const responseText = json.response; 
                    fullResponse += responseText; // Append to fullResponse
                }
                if(json.related_queries){
                    relatedQueries = json.related_queries;
                }
                // Update state with the new combined response
                // setLatestResponse(fullResponse);
                // Update session with new message
                updateSessionListWithNewMessage(
                    formatMessageFromServerResponse({ text: fullResponse, refs: [] ,relatedQueries: relatedQueries}),
                    newSession
                );
            } catch (e) {
                console.error("Error parsing JSON:", e);
            }
        }
    }
}
setIsChatLoading(false);
}

  return (
    <ChatContext.Provider
      value={{
        sessions,
        addNewSession,
        deleteSessionById,
        clearAllSessions,
        selectedSession,
        setSelectedSession: setInternallySelectedSession,
        selectedGenAIBot,
        setSelectedGenAIBot,
        isChatLoading,
        chatLoadingMessage,
        addNewUserMessageToCurrentSession,
        updateMessageVote,
        updateMessageFeedback,
        getSessionSummary,
        removeExpectedDisplayFromSelectedSessionSummary,
        addNewUserMessageWithLastMessages,
      }}
    >
      {props.children}
    </ChatContext.Provider>
  );
}

export function useChat(): ChatContextStructure {
  return useContext(ChatContext);
}
