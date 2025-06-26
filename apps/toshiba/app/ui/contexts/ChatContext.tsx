"use client";
import { createContext, useContext, useEffect, useState } from "react";
import {
  batchEvaluation,
  fetchPastSessions,
  fetchSessionSummary,
  getImageUrl,
} from "../../lib/actions";
import { extractSourcesFromText } from "../../lib/sourceUtils";
import { isSessionObject } from "../../lib/discriminators";
import {
  CHATBOT_MESSAGE_ID_PREFIX,
  ChatBotGenAI,
  ChatbotV,
  ChatMessageObject,
  ChatMessageResponse,
  defaultChatbotV,
  defaultGenAIBotOption,
  defaultSession,
  SESSION_ID_PREFIX,
  SessionObject,
  SessionSummaryObject,
  USER_MESSAGE_ID_PREFIX,
  WindowGrid,
} from "../../lib/interfaces";
import { getLoadingMessageFromAgentStatus } from "./ChatContextHelpers";
import { v4 as uuidv4 } from "uuid";
import { Session } from "next-auth";

// STRUCTURE

export interface ChatContextStructure {
  sessions: SessionObject[];
  addNewSession: () => void;
  deleteSessionById: (sessionId: string) => void;
  clearAllSessions: () => void;
  selectedSession: SessionObject | undefined;
  setSelectedSession: (sessionId: string) => void;
  setSelectedGenAIBot: (value: ChatBotGenAI) => void;
  isChatLoading: boolean;
  userEmail: string;
  chatLoadingMessage: string;
  addNewUserMessageToCurrentSession: (message: string) => void;
  updateMessageVote: (messageId: string, passedVote: -1 | 0 | 1) => void;
  updateMessageFeedback: (messageId: string, passedFeedback: string) => void;
  getSessionSummary: () => void;
  removeExpectedDisplayFromSelectedSessionSummary: () => void;
  activeWindowGrid: WindowGrid | undefined;
  setActiveWindowGrid: (grid?: WindowGrid) => void;
  agentStatus: string;
  recentChatsMessage: string;
  setRecentChatsMessage: (message: string) => void;
  processExcelFile: (file: File) => Promise<void>;
  isBatchEvaluationUser: boolean;
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
  activeWindowGrid: undefined,
  setActiveWindowGrid: () => {
    /**/
  },
  agentStatus: "Initializing...",
  recentChatsMessage: "Loading recent chats...",
  setRecentChatsMessage: () => {
    /**/
  },
  processExcelFile: (file: File) => Promise.resolve(),
  userEmail: "",
  isBatchEvaluationUser: false,
});

// PROVIDER

interface ChatContextProviderProps {
  children: React.ReactNode;
  session: Session | null;
}

export function ChatContextProvider(
  props: ChatContextProviderProps
): JSX.Element {
  const session = props.session;
  const [sessions, setSessions] = useState<SessionObject[]>([]);
  const [selectedSession, setSelectedSession] = useState<SessionObject>();
  const [selectedGenAIBot, setSelectedGenAIBot] = useState<ChatBotGenAI>(
    defaultGenAIBotOption
  );
  // eslint-disable-next-line @typescript-eslint/no-unused-vars -- No provisions to change this for now. Leaving it because we will, eventually.
  const [selectedChatbotV, setSelectedChatbotV] =
    useState<ChatbotV>(defaultChatbotV);
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);
  const [chatLoadingMessage, setChatLoadingMessage] = useState<string>("");
  const [activeWindowGrid, setActiveWindowGrid] = useState<
    WindowGrid | undefined
  >();
  const [agentStatus, setAgentStatus] = useState("Starting...");
  const [recentChatsMessage, setRecentChatsMessage] = useState(
    "Loading recent chats..."
  );
  const [userEmail, setUserEmail] = useState<string>(
    session?.user?.email ?? ""
  );
  const [isBatchEvaluationUser, setIsBatchEvaluationUser] = useState(false);

  // Initializations
  // useEffect(() => {
  //     console.log("Sessions changed", sessions);
  // }, [sessions]);

  useEffect(() => {
    if (session) {
      // const allowedEmails = process.env.NEXT_PUBLIC_BATCH_EVALUATION_USERS ?? "";

      const allowedEmails = [
        "somansh.budhwar@iopex.com",
        "nikhitha.kandula@iopex.com",
        "binu.ramachandran@iopex.com",
        "Walker.Franklin@toshibagcs.com",
        "thomas.conway@toshibagcs.com",
        "dheeraj.kumar@iopex.com",
        "somansh@gmail.com",
      ];
      console.log("Allowed Emails:", allowedEmails);
      console.log("Session Email:", session?.user?.email);
      console.log("----Chat Context----");
      console.log("Is Batch Evaluation User:", isBatchEvaluationUser);
      if (allowedEmails.includes(session?.user?.email ?? "")) {
        console.log("Allowed");
        setIsBatchEvaluationUser(true);
      }
      console.log("Is Batch Evaluation User:", isBatchEvaluationUser);
      console.log("---- End Chat Context----");
    }
  }, [session]);

  useEffect(() => {
    if (!selectedSession) return;
    const newSessions = sessions.map((item) =>
      item.id === selectedSession.id ? selectedSession : item
    );
    setSessions(newSessions);
  }, [selectedSession]);

  useEffect(() => {
    if (sessions.length === 0) {
      setRecentChatsMessage("Loading recent chats...");
      (async () => {
        const newSessions = await fetchPastSessions(
          session?.user?.email ?? "Unknown User"
        );
        if (newSessions.length === 0) {
          setRecentChatsMessage("No Chats");
        }
        // Map all the sessions and change the user name to the current user name
        for (const item of newSessions) {
          console.log("Session:", item);
          for (const message of item.messages) {
            message.userName = session?.user?.name ?? "Unknown User";
          }
        }
        setSessions([...newSessions, defaultSession]);
        setSelectedSession(defaultSession);
      })();
    } else {
      setSelectedSession(sessions[sessions.length - 1]);
    }
  }, [sessions.length, session]);

  //   useEffect(() => {
  //   if (session) {
  //     setUserEmail(session?.user?.email);
  //   }
  // }, [session]);

  //   useEffect(() => {
  //   // Whenever we add a session or delete all sessions, select the latest one.
  //   if (sessions.length === 0) {
  //     (async () => {
  //       const newSessions = await fetchPastSessions(session?.user?.email ?? "Unknown User");
  //       //  Mao all the sessions and change the user name to the current user name
  //       newSessions.forEach((item) => {
  //         item.messages.forEach((message) => {
  //           message.userName = session?.user?.name ?? "Unknown User";
  //           if (message.isBot) {
  //             message.sources = await processSources(extractSourcesFromText(message.text ?? "") ?? []);
  //           }
  //         });
  //       });
  //       setSessions([...newSessions, defaultSession]);
  //       setSelectedSession(defaultSession);
  //     })();
  //   } else {
  //     setSelectedSession(sessions[sessions.length - 1]);
  //   }
  // }, [sessions.length]);

  // useEffect(() => {
  //   // Whenever we add a session or delete all sessions, select the latest one.
  //   if (sessions.length === 0) {
  //     // const newSessions = [defaultSession];
  //     const newSessions = await fetchPastSessions(session?.user?.id ?? "Somansh Bud");
  //
  //     console.log("Past Sessions:", newSessions);
  //
  //     setSessions(newSessions);
  //     setSelectedSession(newSessions[0]);
  //   }
  //   setSelectedSession(sessions[sessions.length - 1]);
  // }, [sessions.length]);

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
      // id: newId,
      // label: `Session ${(newIdNumber + 1).toString()}`,
      id: uuidv4().toString(),
      label: `Session`,
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

  async function processExcelFile(file: File): Promise<void> {
    try {
      // Create FormData inside the server action
      console.log("Processing file in ChatContext:", file);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", session?.user?.email ?? "Unknown User");
      console.log("Form Data:", formData);
      setActiveWindowGrid(WindowGrid.active);
      // addNewUserMessageToCurrentSession("Processing file...");
      setIsChatLoading(true);

      const result = await batchEvaluation(formData);
      deleteSessionById(selectedSession?.id ?? "");
      console.log("Batch evaluation result:", result);
      if (isSessionObject(result)) {
        const newSession: SessionObject = {
          id: result.id,
          label: result.label,
          messages: result.messages,
          creationDate: result.creationDate,
        };
        setSessions((currentSessions) => [...currentSessions, newSession]);
        setSelectedSession(newSession);
        setIsChatLoading(false);
      }
    } catch (error) {
      console.error("Error uploading file:", error);
    }
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
      id: uuidv4().toString(),
      date: new Date().toISOString(),
      isBot: false,
      userName: session?.user?.name ?? "Unknown User",
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

    // Update the UI state
    const newMessageList = [...selectedSession.messages].map((item) =>
      item.id === messageId ? { ...item, vote: passedVote } : item
    );
    const newSelectedSession = { ...selectedSession, messages: newMessageList };
    setSelectedSession(newSelectedSession);

    // Get the current message
    const currentMessage = selectedSession.messages.find(
      (item) => item.id === messageId
    );

    if (!currentMessage) return;

    // Send the vote to the backend
    const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";

    // Get the user ID (using the first message's userName as a fallback)
    const userId =
      session?.user?.id ??
      session?.user?.name ??
      currentMessage.userName ??
      "Unknown User";

    // Ensure we have valid UUIDs
    let messageUuid = currentMessage.id;
    let sessionUuid = selectedSession.id;

    // Check if the IDs are already valid UUIDs
    const uuidPattern =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    // If not a valid UUID, generate a new one
    if (!uuidPattern.test(messageUuid)) {
      messageUuid = uuidv4().toString();
      console.log(`Generated new UUID for message: ${messageUuid}`);
    }

    if (!uuidPattern.test(sessionUuid)) {
      sessionUuid = uuidv4().toString();
      console.log(`Generated new UUID for session: ${sessionUuid}`);
    }

    fetch(`${BACKEND_URL}vote`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message_id: messageUuid,
        user_id: userId,
        vote: passedVote,
        session_id: sessionUuid,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        console.log("Vote update success:", data);
      })
      .catch((error: unknown) => {
        console.error("Error updating vote:", error);
      });
  }

  function updateMessageFeedback(
    messageId: string,
    passedFeedback: string
  ): void {
    if (!selectedSession) return;

    // Get the current message to check if feedback has changed
    const currentMessage = selectedSession.messages.find(
      (item) => item.id === messageId
    );

    if (!currentMessage) return;

    // Only send to backend if feedback has changed
    if (currentMessage.feedback !== passedFeedback) {
      // Update the UI state
      const newMessageList = [...selectedSession.messages].map((item) =>
        item.id === messageId ? { ...item, feedback: passedFeedback } : item
      );
      const newSelectedSession = {
        ...selectedSession,
        messages: newMessageList,
      };
      setSelectedSession(newSelectedSession);

      // Send the feedback to the backend
      const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";

      // Get the user ID (using the first message's userName as a fallback)
      const userId =
        session?.user?.id ??
        session?.user?.name ??
        currentMessage.userName ??
        "Unknown User";

      // Ensure we have valid UUIDs
      let messageUuid = currentMessage.id;
      let sessionUuid = selectedSession.id;

      // Check if the IDs are already valid UUIDs
      const uuidPattern =
        /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

      // If not a valid UUID, generate a new one
      if (!uuidPattern.test(messageUuid)) {
        messageUuid = uuidv4().toString();
        console.log(`Generated new UUID for message: ${messageUuid}`);
      }

      if (!uuidPattern.test(sessionUuid)) {
        sessionUuid = uuidv4().toString();
        console.log(`Generated new UUID for session: ${sessionUuid}`);
      }

      fetch(`${BACKEND_URL}feedback`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message_id: messageUuid,
          user_id: userId,
          feedback: passedFeedback,
          session_id: sessionUuid,
        }),
      })
        .then((response) => response.json())
        .then((data) => {
          console.log("Feedback update success:", data);
        })
        .catch((error: unknown) => {
          console.error("Error updating feedback:", error);
        });
    }
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

  // async function getServerChatbotResponse(
  //   messageText: string,
  //   passedSession: SessionObject
  // ): Promise<void> {
  //
  //   // const userId = session?.user?.id;
  //   // For testing purposes, we are using a hardcoded userId
  //   const userId = "testUserId"; // Replace with actual user ID logic
  //   if (!userId) return;
  //   await handleServerChatbotResponse(userId, messageText, passedSession);
  // }
  //
  // function handleAgentStatusChange(event: MessageEvent): void {
  //   if (event.data && typeof event.data === "string") {
  //     setChatLoadingMessage(getLoadingMessageFromAgentStatus(event.data));
  //   }
  // }
  //
  // async function handleServerChatbotResponse(
  //   userId: string,
  //   messageText: string,
  //   passedSession: SessionObject
  // ): Promise<void> {
  //   setIsChatLoading(true);
  //   console.log("Starting to fetch chatbot response");
  //   const agentEvent = new EventSource(
  //     `${process.env.NEXT_PUBLIC_BACKEND_URL ?? ""}currentStatus?uid=${userId}&sid=${passedSession.id}`
  //   );
  //
  //   try {
  //     agentEvent.onmessage = handleAgentStatusChange;
  //     const data = await fetchChatbotResponse(
  //       userId,
  //       messageText,
  //       passedSession.id,
  //       passedSession.messages,
  //       selectedChatbotV,
  //       selectedGenAIBot
  //     );
  //     updateSessionListWithNewMessage(
  //       formatMessageFromServerResponse(data),
  //       passedSession
  //     );
  //   } catch (error) {
  //     // eslint-disable-next-line no-console -- Current handling (consider a different error handling)
  //     console.error("Error in chatbot response:", error);
  //   } finally {
  //     setIsChatLoading(false);
  //     agentEvent.close();
  //   }
  // }

  async function getServerChatbotResponse(
    messageText: string,
    passedSession: SessionObject
  ): Promise<void> {
    const userId =
      session?.user?.email ??
      session?.user?.name ??
      session?.user?.id ??
      "Unknown User";
    // For testing purposes, we are using a hardcoded userId
    // const userId = "testUserId"; // Replace with actual user ID logic
    if (!userId) return;
    await handleServerChatbotResponse(userId, messageText, passedSession);
  }

  function handleAgentStatusChange(event: MessageEvent): void {
    if (event.data && typeof event.data === "string") {
      setChatLoadingMessage(getLoadingMessageFromAgentStatus(event.data));
    }
  }

  //   async function processSources(extractedSources: any[]): Promise<any[]> {
  //   let sources = extractedSources;
  //
  //   // If no sources were extracted, use the default source
  //   if (!sources || sources.length === 0) {
  //     sources = [];
  //   } else {
  //     // For extracted sources that don't have URLs, try to get them
  //     for (const source of sources) {
  //       if (!source.url) {
  //         // If we have an awsLink, use that to generate the URL
  //         if (source.awsLink) {
  //           try {
  //             console.log("Using awsLink to generate URL:", source.awsLink);
  //             const imageFilename = `${source.awsLink}.png`;
  //             console.log("Image filename:", imageFilename);
  //             const imageUrl = await getImageUrl(imageFilename);
  //             console.log("Generated image URL:", imageUrl);
  //             if (imageUrl) {
  //               source.url = imageUrl;
  //             }
  //           } catch (error) {
  //             console.error("Error getting image URL from awsLink:", error);
  //           }
  //         } else {
  //           // Fallback to the old method if no awsLink is available
  //           const pageNum = source.pages.split(",")[0].split("-")[0].trim();
  //           const imageFilename = `${source.filename.replace(".pdf", "")}_page_${pageNum}.png`;
  //           try {
  //             const imageUrl = await getImageUrl(imageFilename);
  //             if (imageUrl) {
  //               source.url = imageUrl;
  //             }
  //           } catch (error) {
  //             console.error("Error getting image URL:", error);
  //           }
  //         }
  //       }
  //     }
  //   }
  //
  //   return sources;
  // }
  async function processSources(extractedSources: any[]): Promise<any[]> {
    if (!extractedSources?.length) return [];

    return Promise.all(
      extractedSources.map(async (source) => {
        if (source.url) return source;

        try {
          let imageFilename;
          if (source.awsLink) {
            imageFilename = `${source.awsLink}.png`;
          } else {
            const pageNum = source.pages
              ?.split(",")?.[0]
              ?.split("-")?.[0]
              ?.trim();
            imageFilename = `${source.filename?.replace(".pdf", "")}_page_${pageNum}.png`;
          }

          const imageUrl = await getImageUrl(imageFilename);
          if (imageUrl) source.url = imageUrl;
        } catch (error) {
          console.error("Error getting image URL:", error);
        }

        return source;
      })
    );
  }
  async function handleServerChatbotResponse(
    userId: string,
    messageText: string,
    passedSession: SessionObject
  ): Promise<void> {
    if (!selectedSession) return;
    setIsChatLoading(true);
    console.log("Starting to fetch chatbot response");

    // 1. Create a placeholder for the bot message that will be updated as chunks arrive
    const placeholderBotMessage: ChatMessageObject = {
      id: uuidv4().toString(),
      isBot: true,
      date: new Date().toISOString(),
      text: "",
      userName: "ElevAIte",
      isStreaming: true,
      // Add any other required fields for your ChatMessageObject type
    };

    updateSessionListWithNewMessage(placeholderBotMessage, passedSession);

    // 2. Add the placeholder message to the session
    const sessionWithPlaceholder = {
      ...passedSession,
      messages: [...passedSession.messages, placeholderBotMessage],
    };
    setSelectedSession(sessionWithPlaceholder); // Assuming you have a state setter for current session

    // 3. Set up status event source as before
    const agentEvent = new EventSource(
      `${process.env.NEXT_PUBLIC_BACKEND_URL ?? ""}currentStatus?uid=${userId}&sid=${passedSession.id}`
    );
    // agentEvent.onmessage = handleAgentStatusChange;
    agentEvent.onmessage = (event) => {
      if (event.data && typeof event.data === "string") {
        const newStatus = event.data;
        setAgentStatus(newStatus);
        // const updatedSession = {
        //   ...sessionWithPlaceholder,
        //   messages: sessionWithPlaceholder.messages.map(msg =>
        //     msg.id === placeholderBotMessage.id
        //       ? { ...msg, text: newStatus }
        //       : msg
        //   ),
        // };
        // setSelectedSession(updatedSession);
      }
    };

    try {
      // 4. Fetch using streaming approach
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_URL ?? ""}run`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            query: messageText,
            qid: placeholderBotMessage.id,
            uid: userId,
            sid: passedSession.id,
            messages: passedSession.messages.slice(-12), // Keeping your context window
            collection: selectedGenAIBot,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      // 5. Process the streaming response
      if (response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedText = "";

        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          // Decode the chunk
          const chunk = decoder.decode(value, { stream: true });

          // Parse SSE format - looking for "data:" prefix
          const lines = chunk;
          for (const line of lines) {
            // if (line.startsWith('data: ')) {
            const eventData = line;
            if (eventData) {
              // Update accumulated text
              accumulatedText += eventData;

              // Update the bot message in the session
              const updatedSession = {
                ...sessionWithPlaceholder,
                messages: sessionWithPlaceholder.messages.map((msg) =>
                  msg.id === placeholderBotMessage.id
                    ? { ...msg, text: accumulatedText }
                    : msg
                ),
              };

              setSelectedSession(updatedSession);

              // Also update session list if you maintain separate state for that
              // updateSessionInList(updatedSession);
            }
          }
          // }
        }

        console.log("accumulatedText:", accumulatedText);

        // Extract source information from the accumulated text
        const extractedSources = extractSourcesFromText(accumulatedText);
        console.log("extractedSources:", extractedSources);

        // If we have sources from the text, use them
        // Otherwise, use the default source (for backward compatibility)
        // let sources = extractedSources;
        //
        // // If no sources were extracted, use the default source
        // if (!sources || sources.length === 0) {
        //   // const imageFilename = "6800 Hardware Service Guide (2)_page_41.png";
        //   // const imageUrl = await getImageUrl(imageFilename);
        //   // console.log("imageUrl:", imageUrl);
        //
        //   sources = [];
        // } else {
        //   // For extracted sources that don't have URLs, try to get them
        //   for (const source of sources) {
        //     if (!source.url) {
        //       // If we have an awsLink, use that to generate the URL
        //       if (source.awsLink) {
        //         try {
        //           // The awsLink is already in the format we need for getImageUrl
        //           console.log("Using awsLink to generate URL:", source.awsLink);
        //           const imageFilename = `${source.awsLink}.png`;
        //           console.log("Image filename:", imageFilename);
        //           const imageUrl = await getImageUrl(imageFilename);
        //           console.log("Generated image URL:", imageUrl);
        //           if (imageUrl) {
        //             source.url = imageUrl;
        //           }
        //         } catch (error) {
        //           console.error("Error getting image URL from awsLink:", error);
        //         }
        //       } else {
        //         // Fallback to the old method if no awsLink is available
        //         const pageNum = source.pages.split(",")[0].split("-")[0].trim();
        //         const imageFilename = `${source.filename.replace(".pdf", "")}_page_${pageNum}.png`;
        //         try {
        //           const imageUrl = await getImageUrl(imageFilename);
        //           if (imageUrl) {
        //             source.url = imageUrl;
        //           }
        //         } catch (error) {
        //           console.error("Error getting image URL:", error);
        //         }
        //       }
        //     }
        //   }
        // }
        const sources = await processSources(extractedSources ?? []);

        const final_text = accumulatedText;
        console.log("final_text:", final_text);

        // 6. After streaming is complete, finalize the message
        const finalMessage: ChatMessageObject = {
          ...placeholderBotMessage,
          text: final_text,
          isStreaming: false, // Mark as no longer streaming
        };

        // Update the session with the complete message
        const finalSession = {
          ...sessionWithPlaceholder,
          messages: sessionWithPlaceholder.messages.map((msg) =>
            msg.id === placeholderBotMessage.id ? finalMessage : msg
          ),
        };

        updateSessionListWithNewMessage(finalMessage, passedSession);
        setSelectedSession(finalSession);
        // updateSessionInList(finalSession);
      }
    } catch (error) {
      console.error("Error in chatbot response:", error);

      // Remove the placeholder message on error or show an error state
      const sessionWithoutPlaceholder = {
        ...passedSession,
        messages: passedSession.messages.filter(
          (msg) => msg.id !== placeholderBotMessage.id
        ),
      };
      setSelectedSession(sessionWithoutPlaceholder);

      // Optionally add an error message
      const errorMessage: ChatMessageObject = {
        id: `error-${Date.now()}`,
        isBot: true,
        text: "Sorry, there was an error processing your request.",
        userName: "ElevAIte",
        date: new Date().toISOString(),
      };
      updateSessionListWithNewMessage(errorMessage, passedSession);
    } finally {
      setIsChatLoading(false);
      agentEvent.close();
    }
  }

  // Helper function to update a session in your session list
  // Implement this based on your state management approach
  // function updateSessionInList(updatedSession: SessionObject): void {
  //   // Example implementation:
  //   setSessions(prevSessions =>
  //     prevSessions.map(session =>
  //       session.id === updatedSession.id ? updatedSession : session
  //     )
  //   );
  // }

  function getSessionSummary(): void {
    const userId = session?.user?.id;
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
      media: data.media?.map((item) => {
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
        activeWindowGrid,
        setActiveWindowGrid,
        agentStatus,
        recentChatsMessage,
        setRecentChatsMessage,
        processExcelFile,
        userEmail,
        isBatchEvaluationUser,
      }}
    >
      {props.children}
    </ChatContext.Provider>
  );
}

export function useChat(): ChatContextStructure {
  return useContext(ChatContext);
}
