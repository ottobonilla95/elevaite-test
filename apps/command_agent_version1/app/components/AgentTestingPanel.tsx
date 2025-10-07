import { ChatbotIcons, CommonButton } from "@repo/ui/components";
import { useAutoSizeTextArea } from "@repo/ui/hooks";
import {
  AlertCircle,
  Bot,
  FileText,
  Maximize2,
  Minimize2,
  Upload,
  User,
  X,
} from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { BACKEND_URL } from "../lib/constants";
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

function AgentTestingPanel({
  workflowId,
  sessionId,
  description,
}: AgentTestingPanelProps): React.ReactElement {
  const streamAbortRef = useRef<AbortController | null>(null);
  const runIdRef = useRef(0);
  const chatEndRef = useRef<HTMLDivElement | null>(null);
  const inFlightRef = useRef(false);
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
        ? // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- No! Not the same! description can be an empty string.
          description ||
          `Workflow ready with ID: ${workflowId.substring(0, 8)}. You can now upload documents and ask questions!`
        : "No workflow detected. Please select a workflow from the left panel or save a new one.",
      sender: "bot",
    },
  ]);

  // UPDATE: React to workflowId changes
  useEffect(() => {
    if (workflowId) {
      runIdRef.current++;

      try {
        streamAbortRef.current?.abort();
      } catch {
        /* noop */
      }
      inFlightRef.current = false;

      const intro = {
        id: Date.now(),
        // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- description can be an empty string
        text:
          description ||
          `Workflow ready with ID: ${workflowId.substring(0, 8)}. You can now upload documents and ask questions!`,
        sender: "bot" as const,
      };
      setChatMessages([intro]);
    } else {
      setChatMessages([
        {
          id: Date.now(),
          text: "No workflow detected. Please select a workflow from the left panel or save a new one.",
          sender: "bot",
        },
      ]);
    }

    setUploadedFiles([]);
    setIsLoading(false);
    setAgentStatus("Ready");
    setShowUploadModal(false);
  }, [workflowId, description]);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
    // console.log("Chat messages:", chatMessages);
  }, [chatMessages]);

  useEffect(() => {
    if (!sessionId || !process.env.NEXT_PUBLIC_BACKEND_URL) return;

    const userId = "superuser@iopex.com";
    const eventSource = new EventSource(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}currentStatus?uid=${userId}&sid=${sessionId}`
    );

    eventSource.onmessage = (event) => {
      if (typeof event.data === "string" && !inFlightRef.current) {
        setAgentStatus(event.data);
      }
    };

    return () => {
      eventSource.close();
    };
  }, [sessionId]);

  function handleInputChange(
    event: React.ChangeEvent<HTMLTextAreaElement>
  ): void {
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
    if (!chatInput.trim() || !workflowId) return;

    const controller = new AbortController();
    streamAbortRef.current = controller;
    const myRunId = ++runIdRef.current;

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

    // Prepare a placeholder bot message that we'll update as streaming content arrives
    const placeholderBotMessage: ChatMessage = {
      id: Date.now() + 1,
      text: "",
      sender: "bot",
    };
    setChatMessages((prev) => [...prev, placeholderBotMessage]);

    inFlightRef.current = true;
    try {
      const chatHistory = [...chatMessages, userMessage].map((message) => ({
        actor: message.sender,
        content: message.text,
      }));

      const executionRequest = {
        query,
        chat_history: chatHistory,
        runtime_overrides: {},
      };

      const response = await fetch(
        `${BACKEND_URL ?? ""}api/workflows/${workflowId}/stream`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(executionRequest),
          signal: controller.signal,
        }
      );
      // console.log("📥 Raw response:", response);
      if (!response.ok) throw new Error(`HTTP ${response.status.toString()}`);
      if (!response.body) throw new Error("No stream body returned");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let accumulatedText = "";

      let doneReading = false;
      while (!doneReading) {
        if (myRunId !== runIdRef.current) break;
        const { done, value } = await reader.read();
        if (done) {
          doneReading = true;
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        // console.log("📦 Chunk received:", buffer);
        const lines = buffer.split("\n");
        // Keep the last partial line in buffer
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;
          const payload = trimmed.slice(6);
          // console.log("🔍 Payload:", payload);
          if (!payload) continue;

          try {
            const parsed = JSON.parse(payload) as unknown;
            // status messages
            if (
              typeof parsed === "object" &&
              parsed !== null &&
              "status" in parsed
            ) {
              const status = (parsed as { status?: string }).status;
              if (status === "started") setAgentStatus("Started");
              if (status === "completed") setAgentStatus("Completed");
              if (status === "error") {
                const errorMessage =
                  (parsed as { error?: string }).error ?? "Unknown error";
                setAgentStatus("Error");
                setChatMessages((prev) => {
                  const placeholderHasText = prev.some(
                    (m) =>
                      m.id === placeholderBotMessage.id &&
                      m.text &&
                      m.text.trim().length > 0
                  );
                  const withoutEmptyPlaceholder = placeholderHasText
                    ? prev
                    : prev.filter((m) => m.id !== placeholderBotMessage.id);

                  return [
                    ...withoutEmptyPlaceholder,
                    {
                      id: Date.now(),
                      text: errorMessage,
                      sender: "bot",
                      error: true,
                    },
                  ];
                });

                // Stop streaming
                try {
                  void reader.cancel();
                } catch {
                  /*noop*/
                }
                doneReading = true;
                break;
              }
              continue;
            }

            // typed content/events
            if (
              typeof parsed === "object" &&
              parsed !== null &&
              "type" in parsed
            ) {
              const evt = parsed as { type: string; data?: unknown };
              if (evt.type === "content") {
                const data = typeof evt.data === "string" ? evt.data : "";
                const nextText = accumulatedText + data;
                accumulatedText = nextText;
                // Live update the placeholder message
                setChatMessages((prev) =>
                  prev.map((m) =>
                    m.id === placeholderBotMessage.id
                      ? { ...m, text: nextText }
                      : m
                  )
                );
              } else if (evt.type === "info") {
                const raw = typeof evt.data === "string" ? evt.data : "";
                const statusMessage = raw.trim();
                if (statusMessage) setAgentStatus(statusMessage);
              } else if (evt.type === "tool_response") {
                // Tool responses are logged to console for debugging
                console.log("🔧 Tool Response:", evt.data);
              } else if (evt.type === "error") {
                const raw = typeof evt.data === "string" ? evt.data : "";
                setAgentStatus("Error");
                setChatMessages((prev) => [
                  ...prev,
                  { id: Date.now(), text: raw, sender: "bot", error: true },
                ]);
                try {
                  void reader.cancel();
                } catch {
                  /* noop */
                }
                doneReading = true;
                break;
              } else if (evt.type === "agent_response") {
                handleAgentResponse(evt.data);
              } else if (evt.type === "tool_call_started") {
                const d = (evt.data ?? {}) as { tool_name?: string };
                setAgentStatus(
                  d.tool_name ? `Using: ${d.tool_name}` : "Using tool..."
                );
              } else if (evt.type === "tool_call_completed") {
                const d = (evt.data ?? {}) as {
                  tool_name?: string;
                  success?: boolean;
                };
                setAgentStatus(
                  d.tool_name
                    ? `Finished: ${d.tool_name}${d.success === false ? " (failed)" : ""}`
                    : "Tool done"
                );
              }
            }
          } catch (e) {
            // Avoid dumping structured events as content
            const looksStructured =
              payload.startsWith("{") && /"status"|"type"/.test(payload);
            if (looksStructured) continue;
            // Some back-compat chunks can be plain strings (e.g., "Agent Responded")
            const nextText = accumulatedText + payload;
            accumulatedText = nextText;
            setChatMessages((prev) =>
              prev.map((m) =>
                m.id === placeholderBotMessage.id ? { ...m, text: nextText } : m
              )
            );
          }
        }
      }

      // Finalize placeholder message
      setChatMessages((prev) =>
        prev.map((m) =>
          m.id === placeholderBotMessage.id
            ? { ...m, text: accumulatedText || m.text }
            : m
        )
      );
    } catch (error) {
      if (myRunId !== runIdRef.current) return;
      setChatMessages((prevMessages) => [
        ...prevMessages,
        {
          id: Date.now() + 2,
          text: `Error: ${(error as Error).message || "Failed to process message"}`,
          sender: "bot",
          error: true,
        },
      ]);
    } finally {
      if (myRunId === runIdRef.current) {
        setIsLoading(false);
        setAgentStatus("Ready");
        inFlightRef.current = false;
      }
    }
  }

  function handleAgentResponse(data: unknown): void {
    let responseMessage = "";

    if (typeof data === "string") {
      const raw = data.trim();
      try {
        const parsedResponse = JSON.parse(raw) as unknown;
        if (parsedResponse && typeof parsedResponse === "object") {
          const item = parsedResponse as Record<string, unknown>;
          if (typeof item.message === "string" && item.message.trim()) {
            responseMessage = item.message.trim();
          } else if (typeof item.success === "boolean") {
            responseMessage = item.success ? "Success" : "Failed";
          } else {
            const fields = Object.keys(item)
              .filter((key) => isObjOrArray(item[key]))
              .map(beautifyName);

            if (fields.length > 0) {
              responseMessage = `Evaluating: ${fields.join(", ")}.`;
            } else {
              responseMessage = raw;
            }
          }
        } else {
          responseMessage = raw;
        }
      } catch {
        responseMessage = raw;
      }
    }

    if (responseMessage) {
      setAgentStatus(
        responseMessage.length > 140
          ? `${responseMessage.slice(0, 137)}…`
          : responseMessage
      );
    }
  }

  function beautifyName(word: string): string {
    const spaced = word.replace(/_/g, " ");
    return spaced.length
      ? spaced[0].toUpperCase() + spaced.slice(1).toLowerCase()
      : spaced;
  }

  function isObjOrArray(item: unknown): boolean {
    return typeof item === "object" && item !== null;
  }

  function handleFilesUploaded(files: UploadedFile[]): void {
    setUploadedFiles((prev) => [...prev, ...files]);

    const fileNames = files.map((f) => f.name).join(", ");
    const systemMessage: ChatMessage = {
      id: Date.now(),
      text: `📎 Uploaded ${files.length.toString()} file(s): ${fileNames}. You can now ask questions about these documents!`,
      sender: "bot",
    };

    setChatMessages((prevMessages) => [...prevMessages, systemMessage]);
  }

  function renderUserAvatar(): React.ReactElement {
    return (
      <div className="message-avatar rounded-full shrink-0 bg-[#FF681F]">
        <User size={16} />
      </div>
    );
  }

  function renderBotAvatar(isError = false): React.ReactElement {
    return (
      <div className="message-avatar rounded-full shrink-0 bg-[#FF681F]">
        {isError ? <AlertCircle size={16} /> : <Bot size={16} />}
      </div>
    );
  }

  function formatTime(timestamp: number): string {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  }

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
                    onClick={() => {
                      setExpandChat(!expandChat);
                    }}
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
                        <AgentTestingParser
                          message={message.text}
                          isUser={message.sender === "user"}
                          isError={message.error}
                        />
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Show uploaded files if any */}
              {uploadedFiles.length > 0 && (
                <div className="uploaded-files px-6 mb-4">
                  <div className="text-xs font-medium text-gray-500 mb-2">
                    Uploaded Files:
                  </div>
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
                            setUploadedFiles((prev) =>
                              prev.filter((f) => f.id !== file.id)
                            );
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
          </div>
          <ChatLoading isLoading={isLoading} loadingMessage={agentStatus} />
        </div>

        {!workflowId ? undefined : (
          <div
            className={[
              "chatbot-input-container",
              isLoading ? "is-loading" : undefined,
            ]
              .filter(Boolean)
              .join(" ")}
          >
            <div className="chatbot-input-contents">
              <textarea
                ref={textAreaRef}
                className="chatbot-input-field chatbot-input-textarea"
                value={chatInput}
                placeholder={
                  isLoading ? "Working, please wait..." : "Type message here"
                }
                onChange={handleInputChange}
                onKeyDown={handleKeyPress}
                disabled={isLoading}
                rows={1}
              />

              <div className="chatbot-input-actions">
                <CommonButton
                  className="chatbot-input-upload-button"
                  onClick={() => {
                    setShowUploadModal(true);
                  }}
                  title="Upload files"
                  disabled={!workflowId}
                  noBackground
                >
                  <Upload size={16} />
                </CommonButton>

                <CommonButton
                  className={[
                    "chatbot-input-send-button",
                    isLoading || !chatInput.trim() ? "is-disabled" : undefined,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={handleSendMessage}
                  disabled={isLoading || !chatInput.trim()}
                  title="Send"
                >
                  {isLoading ? (
                    <ChatbotIcons.SVGSpinner />
                  ) : (
                    <ChatbotIcons.SVGSend />
                  )}
                </CommonButton>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Upload Modal - Only show if we have a workflow */}
      {!workflowId ? undefined : (
        <UploadModal
          isOpen={showUploadModal}
          onClose={() => {
            setShowUploadModal(false);
          }}
          onFilesUploaded={handleFilesUploaded}
        />
      )}

      {/* Workflow Details Modal */}
      {!showAgentWorkflowModal ? undefined : (
        <AgentWorkflowDetailsModal
          onClose={() => {
            setShowAgentWorkflowModal(false);
          }}
        />
      )}
    </>
  );
}

export default AgentTestingPanel;
