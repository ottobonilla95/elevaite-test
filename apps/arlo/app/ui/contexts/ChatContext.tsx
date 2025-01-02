"use client";
import { useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useState, } from "react";
import {changeCaseID, fetchChatbotResponse, fetchSessionSummary, logOut} from "../../lib/actions";
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
  ContactDetailsStr, OpexData, defaultOpexData, SFResponseMessage, SFData,
} from "../../lib/interfaces";
import {
  CHATBOT_MESSAGE_ID_PREFIX,
  SESSION_ID_PREFIX,
  SESSION_LABEL_PREFIX,
  USER_MESSAGE_ID_PREFIX,
  defaultChatbotV,
  defaultGenAIBotOption,
  defaultSession,
    defaultContact,
} from "../../lib/interfaces";
import { getLoadingMessageFromAgentStatus , tableToCsv, downloadCsv } from "./ChatContextHelpers";
import { v4 as uuid } from 'uuid'


// STRUCTURE
const BACKEND_URL = process.env.NEXT_PUBLIC_ARLO_BACKEND_URL ?? "http://localhost:8000/";
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
  processSFChat: (message: string) => void;
  addNewUserMessageWithLastMessages: (message: string) => void;
  setIsFeedbackBoxOpen: (isOpen: boolean) => void;
  summarizeSession: (inputValue: string) => void;
  setFetchKnowledge: (fetchedKnowledge: string) => void;
  // enableWebSearch: boolean;
  // toggleWebSearch: () => void;
  regenerateMessage: (queryId: string) => void;
  recentSummaryVote: number | undefined;
  setRecentSummaryVote: (vote: number) => void;
  voteOnSummary(number: number): void;
  setCaseID: (caseID: string) => void;
  setChatFlow: (chatFlow: string) => void;
  setWelcomeFlow: (welcomeFlow: string) => void;
}


export const ChatContext = createContext<ChatContextStructure>({
  addNewSession: () => {
    /**/
  },
  addNewUserMessageToCurrentSession: () => {
    /**/
  },
  processSFChat: () => {
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
  recentSummaryVote: 0,
  setRecentSummaryVote: () => {
    /**/
  },
  // selectedSession: undefined,
  selectedSession: defaultSession,
  sessions: [],
  setCaseID: () => {
    /**/
  },
  setChatFlow: () => {
    /**/
  },
  setWelcomeFlow: () => {
    /**/
  },
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
  const [recentSummaryVote, setRecentSummaryVote] = useState<number>(0);

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

    const username = session.data?.user?.name ?? "Unknown";
    if (username==="Unknown")
    {logOut();}
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
        chatFlow: "welcome",
        welcomeFlow: "chat",
        opexData: [],
        userName: sessions[0].userName ?? "Unknown",
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

  function setCaseID(caseID: string): void {
    if (!selectedSession) return;
    const newSelectedSession = { ...selectedSession, caseID };
    void changeCaseID(selectedSession.id, caseID);
    setSelectedSession(newSelectedSession);
  }

  function setChatFlow(chatFlow: string): void {
    if (!selectedSession) return;
    console.log("Setting Flow");
    const newSelectedSession = { ...selectedSession, chatFlow };
    setSelectedSession(newSelectedSession);
  }



  function setWelcomeFlow(welcomeFlow: string): void {
    if (!selectedSession) return;
    const newSelectedSession = { ...selectedSession, welcomeFlow };
    setSelectedSession(newSelectedSession);
  }


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
      userName: selectedSession.userName ?? "Unknown",
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

  function updateSessionFlow(flow: string, passedSession: SessionObject): SessionObject {
    const newSelectedSession = { ...passedSession, chatFlow: flow };
    setSelectedSession(newSelectedSession);
    return newSelectedSession;
  }

  function updateSessionWithNewContactDetails(
    contactDetails: ContactDetailsStr,
    passedSession: SessionObject
  ): SessionObject {
    const newSelectedSession = { ...passedSession, contactDetails: contactDetails };
    // console.log("New Selected Session after Contact:",newSelectedSession);
    setSelectedSession(newSelectedSession);
    return newSelectedSession;
  }

  function updateSessionListWithNewOpexData(
    opexData: OpexData[],
    passedSession: SessionObject
  ): SessionObject {
    const newOpexData = [...(passedSession.opexData ?? []), ...opexData];
    const newSelectedSession = { ...passedSession, opexData: newOpexData };
    setSelectedSession(newSelectedSession);
    return newSelectedSession;
  }

  function updateSessionListWithNewMessages(
    messages: ChatMessageObject[],
    passedSession: SessionObject
  ): SessionObject {
    const newMessageList = [...passedSession.messages, ...messages];
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
    fetch(BACKEND_URL + 'voting', {
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

    fetch(BACKEND_URL + 'feedback', {
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
      CHATBOT_MESSAGE_ID_PREFIX + data.queryID.slice(0, 3) +
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
    // console.log("Newmessage:",newMessage);
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

const wrappedProcessSFChat = (message: string): void => {
  void processSFChat(message);
}

  async function regenerateMessage(queryId: string): Promise<void> {
    if (!selectedSession) return;

    // Get the current message
    const currentMessage = selectedSession.messages.find(
      (item) => item.queryID === queryId
    );
    if (!currentMessage) return;
    // console.log("Current message:",currentMessage);

    // Get the index of the current message
    const currentMessageIndex = selectedSession.messages.findIndex(
      (item) => item.queryID === queryId
    );
    if(currentMessageIndex === -1) return;

    setIsChatLoading(true);
    // console.log("Current message index:",currentMessageIndex);

    const MAX_PAYLOAD_HISTORY = 20;
    let conversationPayload: ChatBotPayload[] = [];
    for (let i = 0; i < currentMessageIndex+1; i++) {
        if (i > MAX_PAYLOAD_HISTORY) break;
        const message = selectedSession.messages[i];
        // console.log("Message:",message);
        conversationPayload.push(
            { "actor": message.isBot ? "assistant" : "user", "content": message.text }
        );
    }
    const fetchedKnowledge = selectedSession.prevFetchedKnowledge ?? "";
    // console.log("Fetch Knowledge:",fetchedKnowledge);
    const response = await fetch(BACKEND_URL + 'regenerate', {
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
    const userId = selectedSession.userName ?? "Unknown User";
    // console.log("User ID:",userId);
    setRecentSummary("Loading summary...");
    const response = await fetch(BACKEND_URL + 'summary', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({session_id: selectedSession.id,
        user_id: userId,
        text: textToSummarize,
        case_id: selectedSession.caseIdSF ?? ""}),
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
    const userId = selectedSession.userName ?? "Unknown User";
    setRecentSummaryVote(number);
    // console.log("User ID:",userId);
    // console.log("Selected session:",selectedSession);
    const response = await fetch(BACKEND_URL + 'vote-summary', {
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

  function messageToContact(message: string):ContactDetailsStr {
    const contact: ContactDetailsStr ={
        customerName: "",
        productName: "",
        issue: "",
        uxVersion: "",
    };
    const lines = message.split("\n").map(line => line.trim());
    // console.log("Lines:",lines);
    for (const line of lines) {
      const [key, value] = line.split(":");
      if (key === "Customer Name") {
        contact.customerName = value;
      } else if (key === "Product Name") {
        contact.productName = value;
      } else if (key === "Issue") {
        contact.issue = value;
      } else if (key === "UX Version") {
        contact.uxVersion = value;
      } else if (key === "Email") {
        contact.email = value;
      } else if (key === "Phone Number") {
        contact.phoneNumber = value;
      }
    }
    // console.log("Contact:");
    // console.log(JSON.parse(JSON.stringify(contact)));
    return contact;

  }


  async function processSFChat(caseID: string): Promise<void> {
    if (!selectedSession) return;
    if (!caseID || !selectedSession) return;
    setIsChatLoading(true);
    selectedSession.caseIdSF = caseID;

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
        userName: selectedSession.userName ?? "Unknown",
        text: "Processing Salesforce Case",
    };

    selectedSession.chatFlow = "pasteChat";

    const newSession = updateSessionListWithNewMessage(newMessage, selectedSession);

    const currSessionID = selectedSession.id;
    const response = await fetch(BACKEND_URL+"processSFChat", {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: currSessionID,
      user_id: newMessage.userName, case_id: caseID }),
  });


  const jsonResponse = await response.json() as SFResponseMessage;
  console.log("JSON Response:",jsonResponse);
  const botResponse = jsonResponse.response;
  const urlRefs = jsonResponse.urls_fetched;

  // Get the last message
  const lastMessage = newSession.messages[newSession.messages.length - 1];
  const queryID = jsonResponse.query_id;

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


    const newContactDetails = messageToContact(jsonResponse.extracted_information ?? "");
    const newSessionWithContact = updateSessionWithNewContactDetails(newContactDetails, newSession)

    const opexDataList: OpexData[] = jsonResponse.sf_data.map( (data:SFData):OpexData => ({
        caseId: caseID,
        product: data.Subject ?? "Not Available",
        subject: data.Symptoms__c ?? "Not Available",
        issue: data.Problem__c ?? "Not Available",
        symptom: data.Symptoms__c ?? "Not Available",
        root_cause: data.Root_Cause__c ?? "Not Available",

        }));

    const newSessionWithOpex = updateSessionListWithNewOpexData(opexDataList, newSessionWithContact);
    newSessionWithOpex.caseID = caseID;

    lastMessage.text = jsonResponse.extracted_information ?? "";
    const userName = lastMessage.userName;
    const welcomeMessage = botResponse.replace("Hubble", userName ?? "_____");
    updateSessionListWithNewMessages(
                    [formatMessageFromServerResponse({queryID: queryID, text: welcomeMessage, refs: urlRefs}),
                    formatMessageFromServerResponse({queryID: "101", text: jsonResponse.verification_message ?? "", refs: urlRefs}),
                        formatMessageFromServerResponse({queryID: "102", text: jsonResponse.issue_acknowledgement ?? "", refs: urlRefs}),
                    ],
                    newSessionWithOpex
                );

setIsChatLoading(false);

  }

  async function addNewUserMessageWithLastMessages(messageText: string): Promise<void> {
    const MAX_PAYLOAD_HISTORY = 20;
    if (!messageText || !selectedSession) return;

    if (selectedSession.messages.length<=1) {
      selectedSession.userName = session.data?.user?.name ?? "Unknown";
    }

    // console.log("Selected Session after pasted chat:");
    // console.log(JSON.parse(JSON.stringify(selectedSession)));
    // console.log("Selected Session end pasted chat:");
    const originalFlow = selectedSession.chatFlow;
    const originalWelcomeFlow = selectedSession.welcomeFlow;

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
        userName: selectedSession.userName ?? "Unknown",
        text: selectedSession.welcomeFlow ==="pasteChat" ? "Processing Pasted Chat": messageText
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
    const flowURL = selectedSession.welcomeFlow==="welcome" ? "chat" : selectedSession.welcomeFlow;
    const response = await fetch(BACKEND_URL+( flowURL ?? "chat"), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message: messageText, session_id: currSessionID,
      user_id: newMessage.userName, chat_history: conversationPayload,
      enable_web_search: false, fetched_knowledge: prevFetchedKnowledge }),
  });

    // console.log("New Session before change of flow:");
    // console.log(JSON.parse(JSON.stringify(newSession)));

    if (originalFlow === "welcome") {
      newSession.welcomeFlow = "chat";
      newSession.chatFlow = originalWelcomeFlow;

    }

  // console.log("New Session after change of flow:");
  // console.log(JSON.parse(JSON.stringify(newSessionAfterFlow)));

  const jsonResponse = await response.json() as ChatResponseMessage;
  const botResponse = jsonResponse.response;
  const urlRefs = jsonResponse.urls_fetched;

  // Get the last message
  const lastMessage = newSession.messages[newSession.messages.length - 1];
  const queryID = jsonResponse.query_id;

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


  if (originalFlow === "welcome" && originalWelcomeFlow==="chat" ) {
     updateSessionListWithNewMessage(
                    formatMessageFromServerResponse({queryID: queryID, text: botResponse, refs: urlRefs}),
                    newSession
                );

  }
  else if (originalFlow === "welcome") {
    const newContactDetails = messageToContact(jsonResponse.extracted_information ?? "");

    const newSessionWithContact = updateSessionWithNewContactDetails(newContactDetails, newSession)

    const opexDataList: OpexData[] = jsonResponse.opex_data.map((data: string[]) => ({
      caseId: data[0] ?? "Not Available",
      subject: data[1] ?? "Not Available",
      issue: data[2] ?? "Not Available",
      symptom: data[3] ?? "Not Available",
      problem: data[4] ?? "Not Available",
      root_cause: data[5] ?? "Not Available",
      product: data[6]?? "Not Available",
    }));
    // newSession.opexData = opexDataList;

    const newSessionWithOpex = updateSessionListWithNewOpexData(opexDataList, newSessionWithContact);
    // console.log("newSessionWithOpex Opex Data:");
    // console.log(JSON.parse(JSON.stringify(newSessionWithOpex)));

    // setSelectedSession(newSession);

    lastMessage.text = jsonResponse.extracted_information ?? "";
    const userName = lastMessage.userName;
    const welcomeMessage = botResponse.replace("Hubble", userName ?? "_____");
    updateSessionListWithNewMessages(
                    [formatMessageFromServerResponse({queryID: queryID, text: welcomeMessage, refs: urlRefs}),
                    formatMessageFromServerResponse({queryID: "101", text: jsonResponse.verification_message ?? "", refs: urlRefs}),
                        formatMessageFromServerResponse({queryID: "102", text: jsonResponse.issue_acknowledgement ?? "", refs: urlRefs}),
                    ],
                    newSessionWithOpex
                );


  }

   else{
    // console.log("In chat");
     const fetchedKnowledge = jsonResponse.fetched_knowledge;
    if (fetchedKnowledge !== "") {newSession.prevFetchedKnowledge = fetchedKnowledge;}
    updateSessionListWithNewMessage(
                    formatMessageFromServerResponse({queryID: queryID, text: botResponse, refs: urlRefs}),
                    newSession
                );
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
        recentSummaryVote,
        setRecentSummaryVote,
        regenerateMessage: wrappedRegenerateMessage,
        summarizeSession: wrappedSummarizeSession,
        recentSummary,
        setCaseID,
        setFetchKnowledge,
        setRecentSummary,
        voteOnSummary: wrappedVoteOnSummary,
        // TODO: Move functions to actions.tsx
        addNewUserMessageWithLastMessages: wrappedAddNewUserMessageWithLastMessages,
        processSFChat: wrappedProcessSFChat,
        setChatFlow,
        setWelcomeFlow,
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
