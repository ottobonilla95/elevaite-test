"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { pipelineSteps } from "./lib/pipelineData";
import "./page.scss";

export default function Home(): JSX.Element {
  const [selectedStep, setSelectedStep] = useState<string | null>("loading");
  const [isMobile, setIsMobile] = useState(false);
  const router = useRouter();
  // TODO: Receive this from a call
  const selectedProvider = "SageMaker";

  useEffect(() => {
    const checkIfMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };

    // Initial check
    checkIfMobile();

    // Add event listener for window resize
    window.addEventListener("resize", checkIfMobile);

    // Cleanup
    return () => {
      window.removeEventListener("resize", checkIfMobile);
    };
  }, []);

  const handleStepSelect = (stepId: string) => {
    setSelectedStep(stepId === selectedStep ? "loading" : stepId);
  };

  // Function to get the appropriate icon for each step
  const getStepIcon = (stepId: string) => {
    switch (stepId) {
      case "loading":
        return (
          <div className="step-icon hourglass">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M12 2C8.13 2 5 5.13 5 9c0 2.38 1.19 4.47 3 5.74V17c0 .55.45 1 1 1h6c.55 0 1-.45 1-1v-2.26c1.81-1.27 3-3.36 3-5.74 0-3.87-3.13-7-7-7zm3 14H9v-1h6v1zm-3-9c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z" />
            </svg>
          </div>
        );
      case "parsing":
        return (
          <div className="step-icon editing">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
            </svg>
          </div>
        );
      case "chunking":
        return (
          <div className="step-icon chunking">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M3 3h8v8H3V3zm0 10h8v8H3v-8zM13 3h8v8h-8V3zm0 10h8v8h-8v-8z" />
            </svg>
          </div>
        );
      case "embedding":
        return (
          <div className="step-icon embedding">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
            </svg>
          </div>
        );
      case "vectorstore":
        return (
          <div className="step-icon vectorstore">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z" />
            </svg>
          </div>
        );
      default:
        return <div className="step-icon"></div>;
    }
  };

  return (
    <div
      className="pipeline-page"
      style={{
        backgroundColor: "#000",
        background: "#000",
        height: "100vh",
        maxHeight: "100vh",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div className="pipeline-header-box">
        <div className="header-content">
          <h1>Document Processing Pipeline</h1>

          <div className="header-controls">
            <div className="project-selector">
              <span>Project:</span>
              <select>
                <option value="default">Default Project</option>
                {/* TODO: Add project options from backend */}
              </select>
            </div>

            <div className="provider-display">
              <span>Provider:</span>
              <span className="provider-name">SageMaker</span>
              {/* TODO: Receive provider from backend */}
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline visualization */}
      <div className="pipeline-visualization">
        <div className="pipeline-steps-container">
          {pipelineSteps.map((step, index) => (
            <React.Fragment key={step.id}>
              <div
                className={`pipeline-step-box ${selectedStep === step.id ? "selected" : ""}`}
                onClick={() => handleStepSelect(step.id)}
                title={step.description}
              >
                <div className="icon-circle">{getStepIcon(step.id)}</div>
                <div className="step-title">{step.title}</div>
              </div>
              {index < pipelineSteps.length - 1 && (
                <div className="pipeline-connector">
                  <div className="connector-line"></div>
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Original Step details panel
      {selectedStep && (
        <div className="step-details-panel">
          <h2>
            {pipelineSteps.find((s) => s.id === selectedStep)?.title}
            <span className="step-provider">{selectedProvider}</span>
          </h2>
          <p>{pipelineSteps.find((s) => s.id === selectedStep)?.details}</p>

          <div className="step-features">
            <h3>Key Features</h3>
            <ul>
              {pipelineSteps
                .find((s) => s.id === selectedStep)
                ?.features.map((feature, index) => (
                  <li key={index}>{feature}</li>
                ))}
            </ul>
          </div>

          <div className="step-actions">
            <button
              className="learn-more-btn"
              onClick={() => router.push(`/${selectedStep}`)}
            >
              Learn More
            </button>
            <button
              className="configure-btn"
              onClick={() => router.push(`/${selectedStep}/configure`)}
            >
              Configure
            </button>
          </div>
        </div>
      )}
      */}

      {/* Configuration Box */}
      {selectedStep && (
        <div
          style={{
            width: "99%",
            margin: "1rem auto 0",
            display: "flex",
            justifyContent: "center",
            flex: 1,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: "100%",
              backgroundColor: "#212124",
              border: "1px solid #2a2a2d",
              borderRadius: "12px",
              display: "flex",
              flexDirection: "column",
              height: "85%",
            }}
          >
            {/* Header Section */}
            <div
              style={{
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                justifyContent: "space-between",
                alignItems: isMobile ? "flex-start" : "center",
                gap: isMobile ? "1rem" : "0",
                padding: "1.5rem",
                borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
              }}
            >
              <div style={{ display: "flex", alignItems: "center" }}>
                <h1
                  style={{
                    fontSize: "1.5rem",
                    margin: 0,
                    color: "white",
                    fontWeight: "normal",
                  }}
                >
                  {pipelineSteps.find((s) => s.id === selectedStep)?.title}{" "}
                  Configuration
                </h1>
                <div
                  style={{
                    marginLeft: "10px",
                    width: "16px",
                    height: "16px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "#999",
                    cursor: "pointer",
                  }}
                  title={
                    pipelineSteps.find((s) => s.id === selectedStep)?.details
                  }
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
                  </svg>
                </div>
              </div>
              <button
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  backgroundColor: "#2a2a2d",
                  color: "white",
                  border: "none",
                  padding: "8px 16px",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "14px",
                }}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" />
                </svg>
                Monitor
              </button>
            </div>

            {/* Form Elements Section */}
            <div
              style={{
                flex: "1",
                padding: "1.5rem",
                overflowY: "auto",
                height: "100%",
              }}
            >
              {/* Configuration Options */}
              {selectedStep === "loading" && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: isMobile
                      ? "1fr"
                      : "repeat(auto-fill, minmax(350px, 1fr))",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Data Source
                    </label>
                    <select
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    >
                      <option value="s3">Amazon S3</option>
                      <option value="local">Local Storage</option>
                      <option value="database">Database</option>
                    </select>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      File Format
                    </label>
                    <select
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    >
                      <option value="pdf">PDF</option>
                      <option value="txt">Text</option>
                      <option value="docx">Word Document</option>
                    </select>
                  </div>
                </div>
              )}

              {selectedStep === "parsing" && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: isMobile
                      ? "1fr"
                      : "repeat(auto-fill, minmax(350px, 1fr))",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Parser Type
                    </label>
                    <select
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    >
                      <option value="default">Default Parser</option>
                      <option value="ocr">OCR Parser</option>
                      <option value="structured">Structured Data Parser</option>
                    </select>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Language
                    </label>
                    <select
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    >
                      <option value="en">English</option>
                      <option value="es">Spanish</option>
                      <option value="fr">French</option>
                    </select>
                  </div>
                </div>
              )}

              {selectedStep === "chunking" && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: isMobile
                      ? "1fr"
                      : "repeat(auto-fill, minmax(350px, 1fr))",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Chunk Size
                    </label>
                    <input
                      type="number"
                      defaultValue="1000"
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    />
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Overlap
                    </label>
                    <input
                      type="number"
                      defaultValue="200"
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    />
                  </div>
                </div>
              )}

              {selectedStep === "embedding" && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: isMobile
                      ? "1fr"
                      : "repeat(auto-fill, minmax(350px, 1fr))",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Embedding Model
                    </label>
                    <select
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    >
                      <option value="openai">OpenAI Embeddings</option>
                      <option value="huggingface">
                        HuggingFace Embeddings
                      </option>
                      <option value="custom">Custom Embeddings</option>
                    </select>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Dimensions
                    </label>
                    <select
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    >
                      <option value="768">768</option>
                      <option value="1024">1024</option>
                      <option value="1536">1536</option>
                    </select>
                  </div>
                </div>
              )}

              {selectedStep === "vectorstore" && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: isMobile
                      ? "1fr"
                      : "repeat(auto-fill, minmax(350px, 1fr))",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Vector Database
                    </label>
                    <select
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    >
                      <option value="pinecone">Pinecone</option>
                      <option value="qdrant">Qdrant</option>
                      <option value="faiss">FAISS</option>
                    </select>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Index Name
                    </label>
                    <input
                      type="text"
                      defaultValue="document-index"
                      style={{
                        backgroundColor: "#161616",
                        color: "white",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        padding: "10px",
                        borderRadius: "8px",
                        fontSize: "14px",
                        width: "100%",
                      }}
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons Section */}
            <div
              style={{
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                gap: "12px",
                padding: "1.5rem",
                borderTop: "1px solid rgba(255, 255, 255, 0.1)",
                marginTop: "auto",
              }}
            >
              <button
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: isMobile ? "center" : "flex-start",
                  gap: "8px",
                  backgroundColor: "#e75f33",
                  color: "white",
                  border: "none",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: 600,
                  width: isMobile ? "100%" : "auto",
                }}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M8 5v14l11-7z" />
                </svg>
                Run Pipeline
              </button>
              <button
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: isMobile ? "center" : "flex-start",
                  gap: "8px",
                  backgroundColor: "#444",
                  color: "white",
                  border: "none",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: 600,
                  width: isMobile ? "100%" : "auto",
                }}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path d="M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z" />
                </svg>
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Commented out original content for now
      <div className="pipeline-content">
        <div className="pipeline-steps">
          {pipelineSteps.map((step, index) => (
            <div
              key={step.id}
              className={`pipeline-step ${selectedStep === step.id ? "selected" : ""}`}
              onClick={() => handleStepSelect(step.id)}
            >
              <div className="step-number">{index + 1}</div>
              <div className="step-content">
                <h2>{step.title}</h2>
                <p>{step.description}</p>
                {selectedStep === step.id && (
                  <div className="step-details">
                    <p>{step.details}</p>

                    <div className="step-actions">
                      <button
                        className="learn-more-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/${step.id}`);
                        }}
                      >
                        Learn More
                      </button>

                      {executionMode === "configure" && (
                        <button
                          className="configure-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/${step.id}/configure`);
                          }}
                        >
                          Configure
                        </button>
                      )}

                      {executionMode === "execute" && (
                        <button
                          className="execute-btn"
                          onClick={(e) => {
                            e.stopPropagation();
                            // Execute the step
                            alert(
                              `Executing ${step.title} step with ${selectedProvider} provider`
                            );
                          }}
                        >
                          Execute
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="pipeline-right-panel">
          <div className="pipeline-flow">
            <h3>Pipeline Flow</h3>
            <div className="flow-diagram">
              {pipelineSteps.map((step, index) => (
                <React.Fragment key={step.id}>
                  <div className="flow-step">
                    <div
                      className={`flow-node ${selectedStep === step.id ? "selected" : ""}`}
                      onClick={() => handleStepSelect(step.id)}
                    >
                      {index + 1}
                    </div>
                    <div className="flow-title">{step.title}</div>
                  </div>
                  {index < pipelineSteps.length - 1 && (
                    <div className="flow-arrow">→</div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          <div className="execution-panel">
            <h3>
              {executionMode === "configure"
                ? "Configuration"
                : executionMode === "execute"
                  ? "Execution"
                  : "Monitoring"}
            </h3>
            {selectedStep ? (
              <div className="panel-content">
                <h4>
                  {pipelineSteps.find((s) => s.id === selectedStep)?.title}
                </h4>
                {executionMode === "configure" && (
                  <div className="configuration-options">
                    <p>
                      Configure options for{" "}
                      {pipelineSteps.find((s) => s.id === selectedStep)?.title}
                    </p>
                    <button
                      onClick={() => router.push(`/${selectedStep}/configure`)}
                      className="view-config-btn"
                    >
                      View Configuration Options
                    </button>
                  </div>
                )}

                {executionMode === "execute" && (
                  <div className="execution-options">
                    <p>
                      Execute{" "}
                      {pipelineSteps.find((s) => s.id === selectedStep)?.title}{" "}
                      with {selectedProvider}
                    </p>
                    <button
                      onClick={() =>
                        alert(
                          `Executing ${pipelineSteps.find((s) => s.id === selectedStep)?.title} step with ${selectedProvider} provider`
                        )
                      }
                      className="execute-step-btn"
                    >
                      Execute Step
                    </button>
                  </div>
                )}

                {executionMode === "monitor" && (
                  <div className="monitoring-options">
                    <p>
                      Monitor{" "}
                      {pipelineSteps.find((s) => s.id === selectedStep)?.title}{" "}
                      executions
                    </p>
                    <div className="execution-list">
                      <p>No recent executions found.</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="panel-content empty">
                <p>
                  Select a pipeline step to{" "}
                  {executionMode === "configure"
                    ? "configure"
                    : executionMode === "execute"
                      ? "execute"
                      : "monitor"}
                  .
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
      */}
    </div>
  );
}
