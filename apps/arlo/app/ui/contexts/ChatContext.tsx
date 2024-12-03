"use client";
import { useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useState, } from "react";
import { fetchChatbotResponse, fetchSessionSummary } from "../../lib/actions";
import type {
  ChatBotGenAI,
  ChatBotPayload,
  ChatMessageObject,
  ChatMessageResponse,
  ChatbotV,
  SessionObject,
  SessionSummaryObject,
  RegeneratedResponse,
    ChatResponseMessage,
    SummaryResponse,
} from "../../lib/interfaces";
import {
  CHATBOT_MESSAGE_ID_PREFIX,
  SESSION_ID_PREFIX,
  SESSION_LABEL_PREFIX,
  USER_MESSAGE_ID_PREFIX,
  defaultChatbotV,
  defaultGenAIBotOption,
  defaultSession,
} from "../../lib/interfaces";
import { getLoadingMessageFromAgentStatus , tableToCsv, downloadCsv } from "./ChatContextHelpers";
import {list} from "postcss";
import {name} from "next/dist/telemetry/ci-info";
import { v4 as uuid } from 'uuid'

// STRUCTURE
const BACKEND_URL = process.env.ARLO_BACKEND_URL ?? "http://localhost:8000";
// const BACKEND_URL = "http://localhost:8000";

export interface ChatContextStructure {
  sessions: SessionObject[];
  addNewSession: () => void;
  deleteSessionById: (sessionId: string) => void;
  clearAllSessions: () => void;
  selectedSession: SessionObject | undefined;
  setSelectedSession: (sessionId: string) => void;
  setSelectedGenAIBot: (value: ChatBotGenAI) => void;
  isChatLoading: boolean;
  recentSummary: string | undefined;
  isFeedbackBoxOpen: boolean;
  chatLoadingMessage: string;
  addNewUserMessageToCurrentSession: (message: string) => void;
  updateMessageVote: (messageId: string, passedVote: -1 | 0 | 1) => void;
  updateMessageFeedback: (messageId: string, passedFeedback: string) => void;
  getSessionSummary: () => void;
  setRecentSummary: (summary: string | undefined) => void;
  removeExpectedDisplayFromSelectedSessionSummary: () => void;
  addNewUserMessageWithLastMessages: (message: string) => void;
  setIsFeedbackBoxOpen: (isOpen: boolean) => void;
  summarizeSession: (inputValue: string) => void;
  setFetchKnowledge: (fetchedKnowledge: string) => void;
  // enableWebSearch: boolean;
  // toggleWebSearch: () => void;
  regenerateMessage: (queryId: string) => void;

  voteOnSummary(number: number): void;
}


export const ChatContext = createContext<ChatContextStructure>({
  addNewSession: () => {
    /**/
  },
  addNewUserMessageToCurrentSession: () => {
    /**/
  },
  addNewUserMessageWithLastMessages: () => {
    /**/
  },
  chatLoadingMessage: "",
  clearAllSessions: () => {
    /**/
  },
  deleteSessionById: () => {
    /**/
  },
  getSessionSummary: () => {
    /**/
  },
  isChatLoading: false,
  isFeedbackBoxOpen: false,
  recentSummary: undefined,
  regenerateMessage: (queryId: string) => {
    /**/
  },
  removeExpectedDisplayFromSelectedSessionSummary: () => {
    /**/
  },
  // selectedSession: undefined,
    selectedSession: defaultSession,
  sessions: [],
  setRecentSummary: () => {
    /**/
  },
  setIsFeedbackBoxOpen: () => {
    /**/
  },
  setFetchKnowledge: () => {
    /**/
  },
  setSelectedGenAIBot: () => {
    /**/
  },
  setSelectedSession: () => {
    /**/
  },
  summarizeSession: () => {
    /**/
  },
  updateMessageFeedback: () => {
    /**/
  },
  updateMessageVote: () => {
    /**/
  },
  voteOnSummary() {
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
  const [isFeedbackBoxOpen, setIsFeedbackBoxOpen] = useState(false);
  const [recentSummary, setRecentSummary] = useState<string | undefined>(undefined);
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
      Number(item.label.slice(SESSION_LABEL_PREFIX.length))
    );
      // setIsChatLoading(false);
    // console.log("SESSION ID NUMBERS LIST:",sessionIdNumbersList);
    // New id will be highest +1
    const newIdNumber = sessionIdNumbersList.length > 0
        ? Math.max(...sessionIdNumbersList) + 1
        : 0;
    const newId = uuid();
    // New Session
    const newSession: SessionObject = {
      id: newId,
      label: `Session ${(newIdNumber).toString()}`,
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

  // function toggleWebSearch(): void {
  //   setEnableWebSearch(prevState => !prevState);
  // }

  function setInternallySelectedSession(sessionId: string): void {
    if (!sessionId || sessionId === selectedSession?.id) return;
    const foundSession = sessions.find((item) => item.id === sessionId);
    if (!foundSession) return;
    setSelectedSession(foundSession);
  }

  function addNewUserMessageToCurrentSession(messageText: string ): void {
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
      queryID: "",
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
    // console.log("MESSAGE ID:",messageId);
    // console.log("SELECTED SESSION:",selectedSession);
    // Get current message
    const currentMessage = selectedSession.messages.find(
      (item) => item.id === messageId
    );

    // Get first message from selected session
    const firstMessage = selectedSession.messages[0];

    if (!currentMessage) return;

  if (passedVote === 1) {
    fetch(BACKEND_URL + '/voting', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query_id: currentMessage.queryID, user_id: firstMessage.userName, vote: passedVote }),
    })
    .then(response => response.json())
    .then(data => {
      console.log('Success:', data);
    })
    .catch((error:unknown) => {
      console.error('Error:', error);
    });
  }
  else {
    currentMessage.vote = passedVote;
  }

    // Send the vote to the server with queryID and vote value
    // const userId = session.data?.user?.id;
    // if (!userId) return;
    // void fetchChatbotResponse(userId, messageText, passedSession.id);
    // console.log("VOTE:",passedVote);
    // console.log("MESSAGE ID:",messageId);
    // console.log("SELECTED SESSION:",selectedSession);


    const newSelectedSession = { ...selectedSession, messages: newMessageList };
    setSelectedSession(newSelectedSession);
  }

  function updateMessageFeedback(
    messageId: string,
    passedFeedback: string
  ): void {
    // setIsChatLoading(true);
    if (!selectedSession) return;
    const newMessageList = [...selectedSession.messages].map((item) =>
      item.id === messageId ? { ...item, feedback: passedFeedback } : item
    );
    // Get current message
    const currentMessage = selectedSession.messages.find(
      (item) => item.id === messageId
    );
    if (!currentMessage) return;
    const queryID = currentMessage.queryID;
    // if (currentMessage.vote !== 1) {
    //   console.log("Vote for current message is", currentMessage.vote);
    //  setIsChatLoading(true);
    // }
    if (passedFeedback !== "") {
      const firstMessage = selectedSession.messages[0];

    fetch(BACKEND_URL + '/feedback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query_id: currentMessage.queryID, user_id: firstMessage.userName, feedback: passedFeedback, vote: currentMessage.vote }),
    })
    .then(response => response.json())
    .then(data => {
      console.log('Success:', data);
      setIsChatLoading(false);
    })
    .catch((error: unknown) => {
      console.error('Error:', error);
      setIsChatLoading(false);
    });
  }
    else {
    setIsChatLoading(false); // Turn off loading if no feedback is provided
  }


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
    // if (passedSession.id === selectedSession?.id) setIsChatLoading(true);
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
      queryID: data.queryID,
      userName: "elevaite",
      // fetched_knowledge: data.fetched_knowledge,
      files: data.refs.map((item) => {
        return {
          id: item + new Date().toISOString(),
          filename: item,
        };
      }),
    };
    console.log("Newmessage:",newMessage);
    return newMessage;
  }

  const wrappedRegenerateMessage = (queryId: string): void => {
  void regenerateMessage(queryId);
};

  const wrappedSummarizeSession = (inputValue: string): void => {
  void summarizeSession(inputValue);
};

const wrappedVoteOnSummary = (number: number): void => {
  void voteOnSummary(number);
};

const wrappedAddNewUserMessageWithLastMessages = (message: string): void => {
  void addNewUserMessageWithLastMessages(message);
};

  async function regenerateMessage(queryId: string): Promise<void> {
    if (!selectedSession) return;

    // Get the current message
    const currentMessage = selectedSession.messages.find(
      (item) => item.queryID === queryId
    );
    if (!currentMessage) return;
    console.log("Current message:",currentMessage);

    // Get the index of the current message
    const currentMessageIndex = selectedSession.messages.findIndex(
      (item) => item.queryID === queryId
    );
    if(currentMessageIndex === -1) return;

    setIsChatLoading(true);
    console.log("Current message index:",currentMessageIndex);

    const MAX_PAYLOAD_HISTORY = 20;
    let conversationPayload: ChatBotPayload[] = [];
    for (let i = 0; i < currentMessageIndex+1; i++) {
        if (i > MAX_PAYLOAD_HISTORY) break;
        const message = selectedSession.messages[i];
        console.log("Message:",message);
        conversationPayload.push(
            { "actor": message.isBot ? "assistant" : "user", "content": message.text }
        );
    }
    const fetchedKnowledge = selectedSession.prevFetchedKnowledge ?? "";
    console.log("Fetch Knowledge:",fetchedKnowledge);
    const response = await fetch(BACKEND_URL + '/regenerate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query_id: queryId,
            session_id: selectedSession.id,
            user_id: currentMessage.userName,
            chat_history: conversationPayload,
            fetched_knowledge: fetchedKnowledge? fetchedKnowledge : "",
            message: currentMessage.text }),

    });
    // Readable stream from response body
    const jsonResponse = await response.json() as RegeneratedResponse;

    const regeneratedMessage = jsonResponse.response;

    // Add the regenerated message to the list
    const newMessage = {
      id: currentMessage.id,
      date: currentMessage.date,
      isBot: true,
      text: regeneratedMessage,
      queryID: currentMessage.queryID,
      userName: currentMessage.userName,
      files: currentMessage.files,
    };

    // Replace the current message with the regenerated message
    const newMessageList = selectedSession.messages.map((item) =>
        item.queryID === queryId ? newMessage : item
    );


    const newSelectedSession = { ...selectedSession, messages: newMessageList };
    setSelectedSession(newSelectedSession);
    setIsChatLoading(false);

  }

  function setFetchKnowledge(fetchedKnowledge: string): void {
    if (!selectedSession) return;
    const newSelectedSession = { ...selectedSession, prevFetchedKnowledge: fetchedKnowledge };
    setSelectedSession(newSelectedSession);
    // return newSelectedSession;

    // return newSelectedSession
    // console.log("Selected Session:",selectedSession);
  }

  async function summarizeSession(inputValue: string): Promise<void> {
    if (!selectedSession) return;
    const textToSummarize = inputValue?.trim();
    if (!textToSummarize) return;
    const userId = session.data?.user?.name ?? "Unknown User";
    // console.log("User ID:",userId);
    setRecentSummary("Loading summary...");
    const response = await fetch(BACKEND_URL + '/summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({session_id: selectedSession.id, user_id: userId ,text: textToSummarize}),
    });

    const jsonResponse = await response.json() as SummaryResponse;
    const summary:string = jsonResponse.summary;
    // console.log("Summary:", summary);
    updateCurrentSessionWithSummary({title: "Summary", summaryID: jsonResponse.summaryID, problem: textToSummarize, solution: summary});
    setRecentSummary(summary);
  }

  async function voteOnSummary(number: number): Promise<void> {
    if (!selectedSession) return;
    if (!selectedSession.summary) return;
    if (number !== 1 && number !== -1) return;
    const userId = session.data?.user?.name ?? "Unknown User";
    // console.log("User ID:",userId);
    // console.log("Selected session:",selectedSession);
    const response = await fetch(BACKEND_URL + '/vote-summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        summary_id: selectedSession.summary?.summaryID ,
        session_id: selectedSession.id,
        user_id: userId ,
        vote: number}),
    });

    // const jsonResponse = await response.json();
    // const summary:string = jsonResponse.summary;
    // console.log("Summary:", summary);
    // setRecentSummary(summary);
  }

  async function addNewUserMessageWithLastMessages(messageText: string): Promise<void> {
    const MAX_PAYLOAD_HISTORY = 20;
    if (!messageText || !selectedSession) return;
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
        queryID: "",
        userName: session.data?.user?.name ?? "You",
        text: messageText,
    };

    // Update session with new user message
    const newSession = updateSessionListWithNewMessage(newMessage, selectedSession);

    let conversationPayload: ChatBotPayload[] = [];
    for (let i = 0; i < selectedSession.messages.length; i++) {
        if (i > MAX_PAYLOAD_HISTORY) break;
        const message = selectedSession.messages[selectedSession.messages.length - i - 1];
        conversationPayload.push(
            { "actor": message.isBot ? "assistant" : "user", "content": message.text }
        );
    }

    setIsChatLoading(true);
    conversationPayload = conversationPayload.reverse();

    const currSessionID = selectedSession.id;
    const prevFetchedKnowledge = selectedSession.prevFetchedKnowledge ?? "";
    const response = await fetch(BACKEND_URL+'/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: messageText, session_id: currSessionID,
      user_id: newMessage.userName, chat_history: conversationPayload,
      enable_web_search: false, fetched_knowledge: prevFetchedKnowledge }),
  });

  // console.log("RESPONSE:",response);
    // Readable stream from response body
  const jsonResponse = await response.json() as ChatResponseMessage;
  // console.log("JSON RESPONSE:",jsonResponse);
  // console.log("Chat history:",jsonResponse.chat_history);
  const botResponse = jsonResponse.response;
  const urlRefs = jsonResponse.urls_fetched;
  const fetchedKnowledge = jsonResponse.fetched_knowledge;
  // console.log("Fetched Knowledge:",fetchedKnowledge);
  // if (fetchedKnowledge!== "") setFetchKnowledge(fetchedKnowledge);
  if (fetchedKnowledge !== "") {newSession.prevFetchedKnowledge = fetchedKnowledge;}

  // console.log("URL REFS:",url_refs);
  const queryID = jsonResponse.query_id;

  // console.log("Session Fetched Knowledge:",selectedSession.prevFetchedKnowledge);

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

  updateSessionListWithNewMessage(
                    formatMessageFromServerResponse({queryID: queryID, text: botResponse, refs: urlRefs}),
                    newSession
                );
  // const reader = response.body.getReader();
  // const decoder = new TextDecoder("utf-8");
  // let buffer = '';
  // let fullResponse = '';
  // let mediaPlanContent = '';

//   while (true) {
//     var { done, value} = await reader.read();
//
//
//     buffer += decoder.decode(value, { stream: true });
//     console.log(buffer)
//     const lines = buffer.split('\n\n');
//     buffer = lines.pop() || '';
//     console.log("LINES:",lines);
//
//     for (const line of lines) {
//         if (line.startsWith('data: ')) {
//             try {
//                 const jsonStr = line.slice(6); // Remove 'data: ' prefix
//                 const json = JSON.parse(jsonStr);
//                 console.log("JSON:", json);
//                 console.log("Parsed JSON:", json.response);
//                 const responseText = json.response;
//                 fullResponse += responseText; // Append to fullResponse
//                 // Update state with the new combined response
//                 // setLatestResponse(fullResponse);
//                 // Update session with new message
//                 const markdownContent = `<div className="message"><MarkdownMessage text="${responseText}" /></div>`;
//                 updateSessionListWithNewMessage(
//                     formatMessageFromServerResponse({ text: fullResponse, refs: [] }),
//                     newSession
//                 );
//             } catch (e) {
//                 console.error("Error parsing JSON:", e);
//             }
//         }
//     }
//     if (done) break;
//
// }
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
        setSelectedGenAIBot,
        isChatLoading,
        isFeedbackBoxOpen,
        setIsFeedbackBoxOpen,
        chatLoadingMessage,
        addNewUserMessageToCurrentSession,
        updateMessageVote,
        updateMessageFeedback,
        getSessionSummary,
        removeExpectedDisplayFromSelectedSessionSummary,
        regenerateMessage: wrappedRegenerateMessage,
        summarizeSession: wrappedSummarizeSession,
        recentSummary,
        setFetchKnowledge,
        setRecentSummary,
        voteOnSummary: wrappedVoteOnSummary,
        // TODO: Move functions to actions.tsx
        addNewUserMessageWithLastMessages: wrappedAddNewUserMessageWithLastMessages,
      }}
    >
      {props.children}
    </ChatContext.Provider>
  );
}

// export function useChat(): ChatContextStructure {
//   return useContext(ChatContext);
// }

export const useChatContext = () => {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error("useChatContext must be used within a ChatProvider");
    }
    return context;
};

export function useChat(): ChatContextStructure {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
