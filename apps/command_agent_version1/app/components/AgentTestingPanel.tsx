import { ChatbotIcons } from "@repo/ui/components";
import { AlertCircle, Bot, User, Upload, Maximize2, Minimize2, FileText, X } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { executeWorkflowModern } from "../lib/actions";
import { useWorkflows } from "../ui/contexts/WorkflowsContext";
import "./AgentTestingPanel.scss";
import { AgentTestingParser } from "./AgentTestingParser";
import AgentWorkflowDetailsModal from "./AgentWorkflowDetailsModal";
import { type ChatMessage } from "./type";
import { ChatLoading } from "./ui/ChatLoading";
import UploadModal from "../components/agents/UploadModal";

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
  // ADD: Callback to update workflow ID
  onWorkflowUpdate?: (workflowId: string) => void;
}

function AgentTestingPanel({
  workflowId,
  sessionId,
  onWorkflowUpdate,
}: AgentTestingPanelProps): React.ReactElement {
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const { expandChat, setExpandChat } = useWorkflows();
  const [showAgentWorkflowModal, setShowAgentWorkflowModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState("Ready");
  
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>(() => [
    {
      id: Date.now(),
      text: workflowId
        ? `Workflow ready with ID: ${workflowId.substring(0, 8)}. You can now upload documents and ask questions!`
        : "No workflow detected. Please select a workflow from the left panel or save a new one.",
      sender: "bot",
    },
  ]);

  // UPDATE: React to workflowId changes
  useEffect(() => {
    if (workflowId) {
      setChatMessages([
        {
          id: Date.now(),
          text: ` Workflow ready with ID: ${workflowId.substring(0, 8)}. You can now upload documents and ask questions!`,
          sender: "bot",
        },
      ]);
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
  }, [workflowId]);

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

  function handleInputChange(event: React.ChangeEvent<HTMLInputElement>): void {
    setChatInput(event.target.value);
  }

  function handleKeyPress(e: React.KeyboardEvent): void {
    if (e.key === "Enter" && !isLoading && chatInput.trim()) {
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
          id: file.backendFileId || file.id,
          name: file.name
        }))
      };

      const result = await executeWorkflowModern(workflowId || "", executionRequest);

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
      text: `📎 Uploaded ${files.length} file(s): ${fileNames}. You can now ask questions about these documents!`,
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
            <div>
              <div
                className="flex items-center justify-between py-2 px-6 sticky top-0 z-10 bg-white"
                style={{ borderBottom: "1px solid #E2E8ED" }}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-[#FF681F] rounded-lg flex items-center justify-center">
                    <Bot size={16} className="text-white" />
                  </div>
                  <div>
                    <div className="font-bold text-sm">CoPilot</div>
                    <div className="text-xs text-gray-500">AI Assistant</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowUploadModal(true)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                    type="button"
                    title="Upload files"
                    disabled={!workflowId}
                  >
                    <Upload size={16} className={workflowId ? "text-gray-600" : "text-gray-300"} />
                  </button>
                  <button
                    onClick={() => setExpandChat(!expandChat)}
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
                    <div className="flex-1">
                      <div
                        className={`text-xs text-[#FF681F] mb-1 ${message.sender === "user" ? "user-time" : "bot-time"}`}
                      >
                        {formatTime(message.id)}
                      </div>
                      <div className="text-sm text-[#212124] opacity-75">
                        <AgentTestingParser message={message.text} />
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

        {workflowId && (
          <div
            className="bottom p-6 rounded-md bg-[#F8FAFC]"
            style={{ border: "1px solid #E2E8ED" }}
          >
            <div className="relative">
              <input
                type="text"
                className="h-[48px] w-full rounded-lg px-4 pr-12"
                value={chatInput}
                placeholder={
                  isLoading ? "Working, please wait..." : "Type message here"
                }
                onChange={handleInputChange}
                onKeyDown={handleKeyPress}
                disabled={isLoading}
              />
              <div className="actions flex items-center gap-2 absolute right-3 top-1/2 -translate-y-1/2">
                <button
                  className={`send-button p-2 rounded-lg ${
                    isLoading || !chatInput.trim()
                      ? "bg-gray-200 cursor-not-allowed"
                      : "bg-[#FF681F] hover:bg-orange-600"
                  } transition-colors`}
                  onClick={handleSendMessage}
                  disabled={isLoading || !chatInput.trim()}
                  type="button"
                >
                  {isLoading ? (
                    <ChatbotIcons.SVGSpinner />
                  ) : (
                    <ChatbotIcons.SVGSend />
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload Modal - Only show if we have a workflow */}
      {workflowId && (
        <UploadModal
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          onFilesUploaded={handleFilesUploaded}
        />
      )}

      {/* Workflow Details Modal */}
      {showAgentWorkflowModal && (
        <AgentWorkflowDetailsModal
          onClose={() => setShowAgentWorkflowModal(false)}
        />
      )}
    </>
  );
}

export default AgentTestingPanel; 