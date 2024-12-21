"use client";
import {ChatbotIcons, CommonButton, SimpleInput} from "@repo/ui/components";
import { ChatbotInput } from "./ChatbotInput";
import { WelcomeChatbotInput } from "./WelcomeChatbotInput";
import "./WelcomeScreen.scss";
import {ChatContext} from "../ui/contexts/ChatContext.tsx";
import { useContext, useState, useEffect } from "react";


export function WelcomeScreen(): JSX.Element {
    const chatContext = useContext(ChatContext);
    const [isPasteChatOpen, setIsPasteChatOpen] = useState(false);
    const [isAskQuestionOpen, setIsAskQuestionOpen] = useState(true);
    const [isTranscriptId, setIsTranscriptId] = useState(false);
    const [caseId, setCaseId] = useState("");

     useEffect(() => {
         if (chatContext.selectedSession?.welcomeFlow === "pasteChat") {
             setIsPasteChatOpen(true);
             setIsAskQuestionOpen(false);
         }
            else if (chatContext.selectedSession?.welcomeFlow === "chat") {
                setIsAskQuestionOpen(true);
                setIsPasteChatOpen(false);

            }
            else {
                setIsAskQuestionOpen(true);
                setIsPasteChatOpen(false);
            }
     });

    function handlePasteChat(): void {
        chatContext.setWelcomeFlow("pasteChat");

    }

    function handleAskQuestion(): void {
        setCaseId("");
        chatContext.setWelcomeFlow("chat");
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleCaseIdChange();
    }

    function handleSend(): void {
        if (chatContext.isChatLoading) return;
        handleCaseIdChange();
    }

    function handleCaseIdChange(): void {
        const value = caseId;
        if (chatContext.isChatLoading) return;
        chatContext.setCaseID(value);
        setIsTranscriptId(true);
    }

  return (
      <div>
                  <div className="welcome-screen">
                      { isAskQuestionOpen ?
                          <div className="welcome-text">
                          <p>How can I help you today?</p>
                            </div>
                           :null}
                      { isPasteChatOpen && !isTranscriptId ?
                          <div className="welcome-text">
                          <p>Please enter Transcript ID</p>
                            </div>
                           :null}
                      { isTranscriptId ?
                          <div className="welcome-text">
                          <p>Please paste the transcript</p>
                            </div>
                           :null}
                      { isPasteChatOpen && !isTranscriptId ?
                          <div className="chatbot-input-welcome-container">
                          <SimpleInput
                              // useCommonStyling={true}
                              wrapperClassName={"chatbot-input-welcome-field"}
                              value={caseId ?? "0000"}
                              // autoFocus={true}
                              placeholder="Enter Transcript ID and press ENTER"
                              onChange={(string) => {
                                    setCaseId(string);
                                }}
                              onKeyDown={handleKeyDown}
                              rightIcon={
                                <CommonButton
                                    onClick={handleSend}
                                    disabled={chatContext.isChatLoading}
                                >
                                    {chatContext.isChatLoading ?
                                        <ChatbotIcons.SVGSpinner/> :
                                        <ChatbotIcons.SVGSend/>
                                    }
                                </CommonButton>
                                 }
                              // onKeyDown={(e) => {
                              //     if (e.key === "Enter") {
                              //         handleCaseIdChange((e.target as HTMLInputElement).value);
                              //         e.currentTarget.value = "";
                              //     }
                              // }}
                          /></div>
                          : null}
                      {isTranscriptId && !isAskQuestionOpen? <WelcomeChatbotInput/> : null }
                      {isAskQuestionOpen ? <ChatbotInput/> : null}
                      <div className="controls-container">
                          <div className="button">
                              <CommonButton
                                  className={isPasteChatOpen ? "active" : "inactive"}
                                  onClick={() => {
                                      handlePasteChat()
                                  }}
                              >
                                  Process Transcript
                              </CommonButton>
                          </div>
                          <div className="controls-container button">
                              <CommonButton
                                  className={isAskQuestionOpen ? "active" : "inactive"}
                                  onClick={() => {
                                      handleAskQuestion()
                                  }}
                              >
                                  Ask a Question
                              </CommonButton>
                          </div>
                      </div>
                  </div>
                  {/*:*/}
                  {/*null*/}

                  {/*[<ChatbotWindow key="chatbotWindow"/>, <ChatbotInput key="chatbotInput"/>]*/}
          {/*}*/}
      </div>

  )
      ;
}