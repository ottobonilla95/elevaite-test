import { ChatbotIcons, CommonButton } from "@repo/ui/components";
import { useAutoSizeTextArea } from "@repo/ui/hooks";
import { AlertCircle, Bot, FileText, Maximize2, Minimize2, Upload, User, X } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { executeWorkflowModern } from "../lib/actions";
import { useWorkflows } from "../ui/contexts/WorkflowsContext";
import UploadModal from "./agents/UploadModal";
import "./AgentTestingPanel.scss";
import { AgentTestingParser } from "./AgentTestingParser";
import AgentWorkflowDetailsModal from "./AgentWorkflowDetailsModal";
import { type ChatMessage } from "./type";
import { ChatLoading } from "./ui/ChatLoading";

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  completed: boolean;
  backendFileId?: string;
}

interface AgentTestingPanelProps {
  workflowId?: string;
  sessionId?: string;
  description?: string;
  // ADD: Callback to update workflow ID
  onWorkflowUpdate?: (workflowId: string) => void;
}

function AgentTestingPanel({ workflowId, sessionId, description, onWorkflowUpdate }: AgentTestingPanelProps): React.ReactElement {
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const { expandChat, setExpandChat } = useWorkflows();
  const [showAgentWorkflowModal, setShowAgentWorkflowModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState("Ready");
  const textAreaRef = useRef<HTMLTextAreaElement | null>(null);
  useAutoSizeTextArea(textAreaRef.current, chatInput, 15);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(() => [
    {
      id: Date.now(),
      text: workflowId
        // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- No! Not the same! description can be an empty string.
        ? (description || `Workflow ready with ID: ${workflowId.substring(0, 8)}. You can now upload documents and ask questions!`)
        : "No workflow detected. Please select a workflow from the left panel or save a new one.",
      sender: "bot",
    },
  ]);

  // UPDATE: React to workflowId changes
  useEffect(() => {
    if (workflowId) {
      setChatMessages(prev => {
        const intro = {
          id: Date.now(),
          // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- description can be an empty string
          text: description || `Workflow ready with ID: ${workflowId.substring(0, 8)}. You can now upload documents and ask questions!`,
          sender: "bot" as const,
        };

        if (prev.length === 0) return [intro];
        if (prev.length === 1 && prev[0].sender === "bot") return [intro];
        return prev;
      });
      // Clear any previous uploads when workflow changes
      setUploadedFiles([]);
    } else {
      setChatMessages([
        {
          id: Date.now(),
          text: "No workflow detected. Please select a workflow from the left panel or save a new one.",
          sender: "bot",
        },
      ]);
    }
  }, [workflowId, description]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages]);

  useEffect(() => {
    if (!sessionId || !process.env.NEXT_PUBLIC_BACKEND_URL) return;

    const userId = "superuser@iopex.com";
    const eventSource = new EventSource(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}currentStatus?uid=${userId}&sid=${sessionId}`
    );

    eventSource.onmessage = (event) => {
      if (typeof event.data === "string") {
        setAgentStatus(event.data);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId]);

  function handleInputChange(event: React.ChangeEvent<HTMLTextAreaElement>): void {
    setChatInput(event.target.value);
  }

  function handleKeyPress(event: React.KeyboardEvent): void {
    if (event.key !== "Enter" || isLoading) return;

    // Return without preventing the default: Newline
    if (event.shiftKey) return;

    event.preventDefault();

    if (chatInput.trim()) {
      void handleSendMessage();
    }
  }

  async function handleSendMessage(): Promise<void> {
    if (!chatInput.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
      text: chatInput,
      sender: "user",
    };

    setChatMessages((prevMessages) => [...prevMessages, userMessage]);

    const query = chatInput;
    setChatInput("");
    setIsLoading(true);
    setAgentStatus("Processing your request...");

    try {
      const chatHistory = chatMessages.map((message) => ({
        actor: message.sender,
        content: message.text,
      }));

      const executionRequest = {
        query,
        chat_history: chatHistory,
        runtime_overrides: {},
        files: uploadedFiles.map(file => ({
          id: file.backendFileId ?? file.id,
          name: file.name
        }))
      };

      const result = await executeWorkflowModern(workflowId ?? "", executionRequest);

      let responseText = "No response received";

      if (result.response) {
        try {
          const parsedResponse = JSON.parse(result.response) as unknown;
          responseText =
            typeof parsedResponse === "object" &&
            parsedResponse !== null &&
            "content" in parsedResponse &&
            parsedResponse.content &&
            typeof parsedResponse.content === "string"
              ? parsedResponse.content
              : "No content found";
        } catch (parseError) {
          console.error("Failed to parse response JSON:", parseError);
          responseText = result.response || "No response received";
        }
      }

      const botMessage: ChatMessage = {
        id: Date.now() + 1,
        text: responseText,
        sender: "bot",
      };

      setChatMessages((prevMessages) => [...prevMessages, botMessage]);
    } catch (error) {
      console.error("Error running workflow:", error);

      setChatMessages((prevMessages) => [
        ...prevMessages,
        {
          id: Date.now() + 1,
          text: `Error: ${(error as Error).message || "Failed to process message"}`,
          sender: "bot",
          error: true,
        },
      ]);
    } finally {
      setIsLoading(false);
      setAgentStatus("Ready");
    }
  }

  const handleFilesUploaded = (files: UploadedFile[]): void => {
    setUploadedFiles((prev) => [...prev, ...files]);
    
    const fileNames = files.map(f => f.name).join(', ');
    const systemMessage: ChatMessage = {
      id: Date.now(),
      text: `📎 Uploaded ${files.length.toString()} file(s): ${fileNames}. You can now ask questions about these documents!`,
      sender: "bot",
    };
    
    setChatMessages((prevMessages) => [...prevMessages, systemMessage]);
  };

  const renderUserAvatar = (): React.ReactElement => {
    return (
      <div className="message-avatar rounded-full shrink-0 bg-[#FF681F]">
        <User size={16} />
      </div>
    );
  };

  const renderBotAvatar = (isError = false): React.ReactElement => {
    return (
      <div className="message-avatar rounded-full shrink-0 bg-[#FF681F]">
        {isError ? <AlertCircle size={16} /> : <Bot size={16} />}
      </div>
    );
  };

  const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  };

  return (
    <>
      <div
        className={`agent-testing-panel absolute top-4 right-4 bg-white z-10 flex flex-col gap-3 rounded-xl p-2${expandChat ? " is-expanded" : ""}`}
      >
        <div
          className="top flex-1 rounded-lg flex flex-col justify-between overflow-hidden"
          style={{ border: "1px solid #E2E8ED" }}
        >
          <div className="chat-scroll flex-1 overflow-auto">
            <div className="chat-contents">
              <div
                className="flex items-center justify-between py-2 px-6 sticky top-0 z-10 bg-white"
                style={{ borderBottom: "1px solid #E2E8ED" }}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-[#FF681F] rounded-lg flex items-center justify-center">
                    <Bot size={16} className="text-white" />
                  </div>
                  <div>
                    <div className="font-bold text-sm">Elai</div>
                    <div className="text-xs text-gray-500">Your Co-Creator</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => { setExpandChat(!expandChat); }}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    type="button"
                    title={expandChat ? "Minimize chat" : "Expand chat"}
                  >
                    {expandChat ? (
                      <Minimize2 size={16} className="text-gray-600" />
                    ) : (
                      <Maximize2 size={16} className="text-gray-600" />
                    )}
                  </button>
                </div>
              </div>

              <div className="chat-bubbles my-4 px-6">
                {chatMessages.map((message) => (
                  <div
                    key={message.id}
                    className={`chat-bubble rounded-lg bg-[#F8FAFC] flex items-start gap-4 p-4 mb-4 ${message.sender === "user" ? "user-message" : "bot-message"} ${message.error ? "error-message" : ""}`}
                  >
                    {message.sender === "user"
                      ? renderUserAvatar()
                      : renderBotAvatar(message.error)}
                    <div className="chat-content">
                      <div
                        className={`text-xs text-[#FF681F] mb-1 ${message.sender === "user" ? "user-time" : "bot-time"}`}
                      >
                        {formatTime(message.id)}
                      </div>
                      <div className="text-sm text-[#212124] opacity-75">
                        <AgentTestingParser message={message.text} isUser={message.sender === "user"} />
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Show uploaded files if any */}
              {uploadedFiles.length > 0 && (
                <div className="uploaded-files px-6 mb-4">
                  <div className="text-xs font-medium text-gray-500 mb-2">Uploaded Files:</div>
                  <div className="flex flex-wrap gap-2">
                    {uploadedFiles.map((file) => (
                      <div
                        key={file.id}
                        className="flex items-center gap-2 bg-blue-50 text-blue-700 px-2 py-1 rounded-md text-xs"
                      >
                        <FileText size={12} />
                        <span>{file.name}</span>
                        <button
                          onClick={() => {
                            setUploadedFiles(prev => prev.filter(f => f.id !== file.id));
                          }}
                          className="text-blue-500 hover:text-blue-700"
                          type="button"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <ChatLoading isLoading={isLoading} loadingMessage={agentStatus} />
          </div>
        </div>

        {!workflowId ? undefined :
          <div className={["chatbot-input-container", isLoading ? "is-loading" : undefined].filter(Boolean).join(" ")}>
            <div className="chatbot-input-contents">

              <textarea
                ref={textAreaRef}
                className="chatbot-input-field chatbot-input-textarea"
                value={chatInput}
                placeholder={isLoading ? "Working, please wait..." : "Type message here"}
                onChange={handleInputChange}
                onKeyDown={handleKeyPress}
                disabled={isLoading}
                rows={1}
              />

              <div className="chatbot-input-actions">

                <CommonButton
                  className="chatbot-input-upload-button"
                  onClick={() => { setShowUploadModal(true); }}
                  title="Upload files"
                  disabled={!workflowId}
                  noBackground
                >
                  <Upload size={16} />
                </CommonButton>

                <CommonButton
                  className={[
                    "chatbot-input-send-button",
                    (isLoading || !chatInput.trim()) ? "is-disabled" : undefined
                  ].filter(Boolean).join(" ")}
                  onClick={handleSendMessage}
                  disabled={isLoading || !chatInput.trim()}
                  title="Send"
                >
                  {isLoading ? <ChatbotIcons.SVGSpinner /> : <ChatbotIcons.SVGSend />}
                </CommonButton>

              </div>

            </div>
          </div>
        }
      </div>

      {/* Upload Modal - Only show if we have a workflow */}
      {!workflowId ? undefined :
        <UploadModal
          isOpen={showUploadModal}
          onClose={() => { setShowUploadModal(false); }}
          onFilesUploaded={handleFilesUploaded}
        />
      }

      {/* Workflow Details Modal */}
      {!showAgentWorkflowModal ? undefined :
        <AgentWorkflowDetailsModal
          onClose={() => { setShowAgentWorkflowModal(false); }}
        />
      }
    </>
  );
}

export default AgentTestingPanel;
