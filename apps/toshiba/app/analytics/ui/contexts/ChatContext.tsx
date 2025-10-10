"use client";
import { useSession } from "next-auth/react";
import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { fetchChatbotResponse, fetchSessionSummary } from "../../lib/actions";
import type {
  ChatBotGenAI,
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
import { getLoadingMessageFromAgentStatus } from "./ChatContextHelpers";
import { WindowGrid } from "../../../lib/interfaces";

// STRUCTURE

export interface ChatContextStructure {
  userEmail: string;
  isBatchEvaluationUser: boolean;
  processExcelFile(file: File): Promise<void>;
  recentChatsMessage: ReactNode;
  activeWindowGrid: WindowGrid | undefined;
  setActiveWindowGrid(windowGrid?: WindowGrid): void;
  sessions: SessionObject[];
  addNewSession: () => void;
  deleteSessionById: (sessionId: string) => void;
  clearAllSessions: () => void;
  selectedSession: SessionObject | undefined;
  setSelectedSession: (sessionId: string) => void;
  setSelectedGenAIBot: (value: ChatBotGenAI) => void;
  isChatLoading: boolean;
  chatLoadingMessage: string;
  addNewUserMessageToCurrentSession: (message: string) => void;
  updateMessageVote: (messageId: string, passedVote: -1 | 0 | 1) => void;
  updateMessageFeedback: (messageId: string, passedFeedback: string) => void;
  getSessionSummary: () => void;
  removeExpectedDisplayFromSelectedSessionSummary: () => void;
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
  recentChatsMessage: undefined,
  activeWindowGrid: undefined,
  setActiveWindowGrid: () => {
    /**/
  },
  userEmail: "",
  isBatchEvaluationUser: false,
  processExcelFile: async () => { },
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
  const [selectedChatbotV, setSelectedChatbotV] =
    useState<ChatbotV>(defaultChatbotV);
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);
  const [chatLoadingMessage, setChatLoadingMessage] = useState<string>("");
  const [activeWindowGrid, setActiveWindowGrid] = useState<WindowGrid | undefined>();
  const [userEmail, setUserEmail] = useState<string>("");
  const [isBatchEvaluationUser, setIsBatchEvaluationUser] = useState<boolean>(false);

  async function processExcelFile(file: File): Promise<void> {
    // Implementation needed
    console.log("Processing Excel file:", file.name);
  }

  function setInternalActiveWindowGrid(windowGrid?: WindowGrid): void {
    setActiveWindowGrid(windowGrid);
  }

  // Initializations
  // useEffect(() => {
  //     console.log("Sessions changed", sessions);
  // }, [sessions]);

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
      userName: session.data?.user?.name ?? "Unknown User",
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
      userName: "ElevAIte",
      files: data.refs.map((item) => {
        return {
          id: item + new Date().toISOString(),
          filename: item,
        };
      }),
    };
    return newMessage;
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
        setSelectedGenAIBot,
        isChatLoading,
        chatLoadingMessage,
        addNewUserMessageToCurrentSession,
        updateMessageVote,
        updateMessageFeedback,
        getSessionSummary,
        removeExpectedDisplayFromSelectedSessionSummary,
        recentChatsMessage: undefined,
        activeWindowGrid,
        setActiveWindowGrid: setInternalActiveWindowGrid,
        userEmail,
        isBatchEvaluationUser,
        processExcelFile,
      }}
    >
      {props.children}
    </ChatContext.Provider>
  );
}

export function useChat(): ChatContextStructure {
  return useContext(ChatContext);
}






