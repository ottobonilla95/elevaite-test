"use client";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { pipelineSteps } from "./lib/pipelineData";
import { ElevaiteIcons } from "../../../packages/ui/src/components/icons/elevaite";
import "./page.scss";

interface UploadingFile {
  id: string;
  name: string;
  size: string;
  progress: number;
  completed: boolean;
}

export default function Home(): JSX.Element {
  const [selectedStep, setSelectedStep] = useState<string | null>("loading");
  const [isMobile, setIsMobile] = useState(false);

  // Loading step state
  const [dataSource, setDataSource] = useState<string>("s3");
  const [fileFormat, setFileFormat] = useState<string>("pdf");

  // Parsing step state
  const [parsingMode, setParsingMode] = useState<string>("auto_parser");
  const [parserType, setParserType] = useState<string>("");
  const [parserTool, setParserTool] = useState<string>("");

  // Chunking step state
  const [chunkingStrategy, setChunkingStrategy] =
    useState<string>("recursive_chunking");
  const [thresholdType, setThresholdType] = useState<string>("percentile");
  const [thresholdAmount, setThresholdAmount] = useState<number>(90);
  const [chunkSize, setChunkSize] = useState<number>(500);
  const [chunkOverlap, setChunkOverlap] = useState<number>(50);
  const [maxChunkSize, setMaxChunkSize] = useState<number>(500);

  // Embedding step state
  const [embeddingProvider, setEmbeddingProvider] = useState<string>("openai");
  const [embeddingModel, setEmbeddingModel] = useState<string>(
    "text-embedding-ada-002"
  );

  // Vectorstore step state
  const [vectorDb, setVectorDb] = useState<string>("qdrant"); // From vector_db_config.py

  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([
    {
      id: "1",
      name: "document1.pdf",
      size: "5 MB",
      progress: 60,
      completed: false,
    },
    {
      id: "2",
      name: "report.docx",
      size: "2.3 MB",
      progress: 100,
      completed: true,
    },
  ]);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  // Keeping router for future use
  const router = useRouter(); // eslint-disable-line no-unused-vars
  // TODO: Receive this from a call
  const selectedProvider = "SageMaker"; // eslint-disable-line no-unused-vars

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

  const handleFileSelect = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const newFiles: UploadingFile[] = Array.from(files).map((file, index) => {
        // Convert file size to readable format
        const sizeInMB = file.size / (1024 * 1024);
        const formattedSize =
          sizeInMB < 1
            ? `${Math.round(sizeInMB * 1024)} KB`
            : `${sizeInMB.toFixed(1)} MB`;

        return {
          id: `new-${Date.now()}-${index}`,
          name: file.name,
          size: formattedSize,
          progress: 0,
          completed: false,
        };
      });

      setUploadingFiles([...uploadingFiles, ...newFiles]);

      // Simulate upload progress
      newFiles.forEach((file) => {
        simulateFileUpload(file.id);
      });
    }

    // Reset the input value so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const simulateFileUpload = (fileId: string) => {
    const interval = setInterval(() => {
      setUploadingFiles((prevFiles) => {
        const updatedFiles = prevFiles.map((file) => {
          if (file.id === fileId && !file.completed) {
            const newProgress = Math.min(file.progress + 10, 100);
            const completed = newProgress === 100;

            if (completed) {
              clearInterval(interval);
            }

            return { ...file, progress: newProgress, completed };
          }
          return file;
        });
        return updatedFiles;
      });
    }, 500);
  };

  const handleDeleteFile = (fileId: string) => {
    setUploadingFiles((prevFiles) =>
      prevFiles.filter((file) => file.id !== fileId)
    );
  };

  // Custom Dropdown Component
  interface CustomDropdownProps {
    options: { value: string; label: string }[];
    defaultValue?: string;
    onChange?: (value: string) => void;
    textColor?: string;
    isHeaderDropdown?: boolean;
  }

  // Custom Number Input Component
  interface CustomNumberInputProps {
    defaultValue?: number;
    min?: number;
    max?: number;
    step?: number;
    onChange?: (value: number) => void;
  }

  const CustomNumberInput: React.FC<CustomNumberInputProps> = ({
    defaultValue = 0,
    min = 0,
    max = 10000,
    step = 1,
    onChange,
  }) => {
    const [value, setValue] = useState(defaultValue);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = parseInt(e.target.value, 10);
      if (!isNaN(newValue)) {
        updateValue(newValue);
      }
    };

    const updateValue = (newValue: number) => {
      // Ensure value is within min/max bounds
      const boundedValue = Math.min(Math.max(newValue, min), max);
      setValue(boundedValue);
      if (onChange) {
        onChange(boundedValue);
      }
    };

    const increment = () => {
      updateValue(value + step);
    };

    const decrement = () => {
      updateValue(value - step);
    };

    return (
      <div
        style={{
          position: "relative",
          width: "100%",
          display: "flex",
          alignItems: "center",
        }}
      >
        <input
          ref={inputRef}
          type="number"
          value={value}
          onChange={handleChange}
          min={min}
          max={max}
          step={step}
          style={{
            backgroundColor: "#161616",
            color: "white",
            border: "2px solid #3f3f41",
            padding: "10px",
            paddingRight: "60px", // Make room for the buttons
            borderRadius: "8px",
            fontSize: "14px",
            width: "100%",
            appearance: "textfield", // Remove default arrows
          }}
        />
        <div
          style={{
            position: "absolute",
            right: "10px",
            top: "50%",
            transform: "translateY(-50%)",
            display: "flex",
            flexDirection: "column",
            gap: "0px",
          }}
        >
          <button
            onClick={increment}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "transparent",
              border: "none",
              cursor: "pointer",
              padding: "2px",
              color: "white",
              transition: "color 0.2s ease",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.color = "#e75f33";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.color = "white";
            }}
          >
            <div style={{ transform: "rotate(180deg)" }}>
              <ElevaiteIcons.SVGChevron />
            </div>
          </button>
          <button
            onClick={decrement}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "transparent",
              border: "none",
              cursor: "pointer",
              padding: "2px",
              color: "white",
              transition: "color 0.2s ease",
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.color = "#e75f33";
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.color = "white";
            }}
          >
            <ElevaiteIcons.SVGChevron />
          </button>
        </div>
      </div>
    );
  };

  const CustomDropdown: React.FC<CustomDropdownProps> = ({
    options,
    defaultValue,
    onChange,
    textColor,
    isHeaderDropdown,
  }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedValue, setSelectedValue] = useState(
      defaultValue || options[0]?.value || ""
    );
    const dropdownRef = React.useRef<HTMLDivElement>(null);

    // Find the label for the selected value
    const selectedLabel =
      options.find((option) => option.value === selectedValue)?.label || "";

    // Handle click outside to close dropdown
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          dropdownRef.current &&
          !dropdownRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false);
        }
      };

      document.addEventListener("mousedown", handleClickOutside);
      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
      };
    }, []);

    const handleOptionClick = (value: string) => {
      setSelectedValue(value);
      setIsOpen(false);
      if (onChange) {
        onChange(value);
      }
    };

    return (
      <div
        ref={dropdownRef}
        style={{
          position: "relative",
          width: "100%",
        }}
      >
        <div
          onClick={() => setIsOpen(!isOpen)}
          style={{
            backgroundColor: isHeaderDropdown ? "#3f3f41" : "#212124",
            color: "white",
            border: isHeaderDropdown ? "none" : "2px solid #3f3f41",
            padding: isHeaderDropdown ? "6px 12px" : "10px",
            borderRadius: "8px",
            fontSize: "14px",
            width: "100%",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            cursor: "pointer",
            transition: isHeaderDropdown
              ? "background-color 0.2s ease"
              : "border-color 0.2s ease",
          }}
          onMouseOver={(e) => {
            if (isHeaderDropdown) {
              e.currentTarget.style.backgroundColor = "#4f4f51";
            } else {
              e.currentTarget.style.borderColor = "#5f5f61";
            }
          }}
          onMouseOut={(e) => {
            if (isHeaderDropdown) {
              e.currentTarget.style.backgroundColor = "#3f3f41";
            } else {
              e.currentTarget.style.borderColor = "#3f3f41";
            }
          }}
        >
          <span style={{ color: textColor || "white" }}>{selectedLabel}</span>
          <ElevaiteIcons.SVGChevron
            style={{
              transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
              transition: "transform 0.2s ease",
              color: isHeaderDropdown ? "#e75f33" : "white",
            }}
          />
        </div>
        {isOpen && (
          <div
            style={{
              position: "absolute",
              top: "calc(100% + 5px)",
              left: 0,
              width: "100%",
              backgroundColor: isHeaderDropdown ? "#3f3f41" : "#212124",
              border: isHeaderDropdown ? "none" : "2px solid #3f3f41",
              borderRadius: "8px",
              zIndex: 10,
              boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
              maxHeight: "200px",
              overflowY: "auto",
            }}
          >
            {options.map((option) => (
              <div
                key={option.value}
                onClick={() => handleOptionClick(option.value)}
                style={{
                  padding: isHeaderDropdown ? "6px 12px" : "10px",
                  cursor: "pointer",
                  backgroundColor:
                    selectedValue === option.value
                      ? "rgba(231, 95, 51, 0.1)"
                      : "transparent",
                  color: selectedValue === option.value ? "#e75f33" : "white",
                  transition: "background-color 0.2s ease, color 0.2s ease",
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor =
                    selectedValue === option.value
                      ? "rgba(231, 95, 51, 0.2)"
                      : "rgba(255, 255, 255, 0.05)";
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor =
                    selectedValue === option.value
                      ? "rgba(231, 95, 51, 0.1)"
                      : "transparent";
                }}
              >
                {option.label}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Function to get the appropriate icon for each step
  const getStepIcon = (stepId: string) => {
    switch (stepId) {
      case "loading":
        return (
          <div className="step-icon">
            <ElevaiteIcons.SVGSpinner size={26} />
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
              <div style={{ width: "180px" }}>
                <CustomDropdown
                  options={[
                    { value: "default", label: "Default Project" },
                    { value: "project1", label: "Project 1" },
                    { value: "project2", label: "Project 2" },
                  ]}
                  defaultValue="default"
                  onChange={(value) => console.log("Selected project:", value)}
                  textColor="#e75f33"
                  isHeaderDropdown={true}
                />
              </div>
            </div>

            <div className="provider-display">
              <span>Provider:</span>
              <div
                style={{
                  backgroundColor: "#3f3f41",
                  padding: "6px 12px",
                  borderRadius: "8px",
                  fontSize: "14px",
                  color: "#ccc",
                  fontWeight: "normal",
                  border: "none",
                }}
              >
                SageMaker
              </div>
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
                className={`pipeline-step-box ${selectedStep === step.id ? "selected" : ""} ${pipelineSteps.findIndex((s) => s.id === selectedStep) >= pipelineSteps.findIndex((s) => s.id === step.id) ? "highlighted" : ""}`}
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

      {/* Configuration and Upload Files Boxes */}
      {selectedStep && (
        <div
          style={{
            width: "99%",
            margin: "0.5rem auto 0",
            display: "flex",
            justifyContent: "space-between",
            flex: 1,
            overflow: "hidden",
            gap: "16px",
          }}
        >
          {/* Configuration Box */}
          <div
            style={{
              width: selectedStep === "loading" ? "calc(50% - 8px)" : "100%",
              backgroundColor: "#212124",
              border: "2px solid #3f3f41",
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
                padding: "0 1.5rem 1.5rem",
                overflowY: "auto",
                height: "100%",
              }}
            >
              {/* Configuration Options */}
              {selectedStep === "loading" && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  {/* Data Source Selection */}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "2px solid #3f3f41",
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
                    <CustomDropdown
                      options={[
                        { value: "s3", label: "Amazon S3" },
                        { value: "local", label: "Local Storage" },
                      ]}
                      defaultValue={dataSource}
                      onChange={(value) => {
                        setDataSource(value);
                        console.log("Selected data source:", value);
                      }}
                    />
                  </div>

                  {/* File Format Selection */}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "2px solid #3f3f41",
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
                    <CustomDropdown
                      options={[
                        { value: "pdf", label: "PDF" },
                        { value: "docx", label: "Word Document" },
                        { value: "xlsx", label: "Excel Spreadsheet" },
                        { value: "html", label: "HTML" },
                      ]}
                      defaultValue={fileFormat}
                      onChange={(value) => {
                        setFileFormat(value);
                        console.log("Selected file format:", value);
                      }}
                    />
                  </div>

                  {/* S3 Specific Configuration */}
                  {dataSource === "s3" && (
                    <>
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          S3 Bucket Name
                        </label>
                        <input
                          type="text"
                          placeholder="Enter bucket name"
                          defaultValue="kb-check-pdf"
                          style={{
                            width: "100%",
                            padding: "10px",
                            backgroundColor: "#161616",
                            border: "2px solid #3f3f41",
                            borderRadius: "8px",
                            color: "white",
                            fontSize: "14px",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          AWS Region
                        </label>
                        <input
                          type="text"
                          placeholder="e.g., us-east-1"
                          defaultValue="us-east-2"
                          style={{
                            width: "100%",
                            padding: "10px",
                            backgroundColor: "#161616",
                            border: "2px solid #3f3f41",
                            borderRadius: "8px",
                            color: "white",
                            fontSize: "14px",
                          }}
                        />
                      </div>
                    </>
                  )}

                  {/* Local Storage Specific Configuration */}
                  {dataSource === "local" && (
                    <>
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Input Directory
                        </label>
                        <input
                          type="text"
                          placeholder="Enter input directory path"
                          defaultValue="/elevaite_ingestion/INPUT"
                          style={{
                            width: "100%",
                            padding: "10px",
                            backgroundColor: "#161616",
                            border: "2px solid #3f3f41",
                            borderRadius: "8px",
                            color: "white",
                            fontSize: "14px",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Output Directory
                        </label>
                        <input
                          type="text"
                          placeholder="Enter output directory path"
                          defaultValue="/elevaite_ingestion/OUTPUT"
                          style={{
                            width: "100%",
                            padding: "10px",
                            backgroundColor: "#161616",
                            border: "2px solid #3f3f41",
                            borderRadius: "8px",
                            color: "white",
                            fontSize: "14px",
                          }}
                        />
                      </div>
                    </>
                  )}
                </div>
              )}

              {selectedStep === "parsing" && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  {/* Parsing Mode Selection */}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "2px solid #3f3f41",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Parsing Mode
                    </label>
                    <CustomDropdown
                      options={[
                        { value: "auto_parser", label: "Auto Parser" },
                        { value: "custom_parser", label: "Custom Parser" },
                      ]}
                      defaultValue={parsingMode}
                      onChange={(value) => {
                        setParsingMode(value);
                        console.log("Selected parsing mode:", value);
                      }}
                    />
                  </div>

                  {/* Parser Configuration Options */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: isMobile
                        ? "1fr"
                        : "calc(50% - 12px) calc(50% - 12px)",
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
                        border: "2px solid #3f3f41",
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
                      <CustomDropdown
                        options={[
                          { value: "pdf", label: "PDF Parser" },
                          { value: "docx", label: "DOCX Parser" },
                          { value: "xlsx", label: "XLSX Parser" },
                          { value: "html", label: "HTML Parser" },
                        ]}
                        defaultValue={parserType || "pdf"}
                        onChange={(value) => {
                          setParserType(value);
                          console.log("Selected parser type:", value);
                        }}
                      />
                    </div>

                    {parsingMode === "custom_parser" && parserType && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Parser Tool
                        </label>
                        <CustomDropdown
                          options={
                            parserType === "pdf"
                              ? [{ value: "none", label: "None" }]
                              : parserType === "docx" ||
                                  parserType === "xlsx" ||
                                  parserType === "html"
                                ? [
                                    {
                                      value: "markitdown",
                                      label: "Markitdown",
                                    },
                                    { value: "docling", label: "Docling" },
                                    {
                                      value: "llamaparse",
                                      label: "LlamaParse",
                                    },
                                  ]
                                : [{ value: "none", label: "None" }]
                          }
                          defaultValue={
                            parserTool ||
                            (parserType === "pdf" ? "none" : "markitdown")
                          }
                          onChange={(value) => {
                            setParserTool(value);
                            console.log("Selected parser tool:", value);
                          }}
                        />
                      </div>
                    )}

                    {parsingMode === "custom_parser" && !parserType && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Parser Tool
                        </label>
                        <div style={{ color: "#808080", fontSize: "14px" }}>
                          Select a parser type first
                        </div>
                      </div>
                    )}

                    {parsingMode === "auto_parser" && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
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
                        <CustomDropdown
                          options={[
                            { value: "en", label: "English" },
                            { value: "es", label: "Spanish" },
                            { value: "fr", label: "French" },
                          ]}
                          defaultValue="en"
                          onChange={(value) =>
                            console.log("Selected language:", value)
                          }
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedStep === "chunking" && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  {/* Chunking Strategy Selection */}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "2px solid #3f3f41",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Chunking Strategy
                    </label>
                    <CustomDropdown
                      options={[
                        {
                          value: "semantic_chunking",
                          label: "Semantic Chunking",
                        },
                        { value: "mdstructure", label: "Markdown Structure" },
                        {
                          value: "recursive_chunking",
                          label: "Recursive Chunking",
                        },
                        {
                          value: "sentence_chunking",
                          label: "Sentence Chunking",
                        },
                      ]}
                      defaultValue={chunkingStrategy}
                      onChange={(value) => {
                        setChunkingStrategy(value);
                        console.log("Selected chunking strategy:", value);
                      }}
                    />
                  </div>

                  {/* Chunking Configuration Options */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: isMobile
                        ? "1fr"
                        : "calc(50% - 12px) calc(50% - 12px)",
                      gap: "24px",
                      width: "100%",
                    }}
                  >
                    {/* Semantic Chunking Options */}
                    {chunkingStrategy === "semantic_chunking" && (
                      <>
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "10px",
                            padding: "16px",
                            backgroundColor: "rgba(0, 0, 0, 0.2)",
                            borderRadius: "8px",
                            border: "2px solid #3f3f41",
                          }}
                        >
                          <label
                            style={{
                              fontSize: "14px",
                              color: "#808080",
                              fontWeight: 600,
                            }}
                          >
                            Threshold Type
                          </label>
                          <CustomDropdown
                            options={[
                              { value: "percentile", label: "Percentile" },
                              { value: "fixed", label: "Fixed" },
                            ]}
                            defaultValue={thresholdType}
                            onChange={(value) => {
                              setThresholdType(value);
                              console.log("Threshold type changed:", value);
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
                            border: "2px solid #3f3f41",
                          }}
                        >
                          <label
                            style={{
                              fontSize: "14px",
                              color: "#808080",
                              fontWeight: 600,
                            }}
                          >
                            Threshold Amount
                          </label>
                          <CustomNumberInput
                            defaultValue={thresholdAmount}
                            min={1}
                            max={100}
                            step={1}
                            onChange={(value) => {
                              setThresholdAmount(value);
                              console.log("Threshold amount changed:", value);
                            }}
                          />
                        </div>
                      </>
                    )}

                    {/* Markdown Structure Options */}
                    {chunkingStrategy === "mdstructure" && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
                          gridColumn: "1 / -1",
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
                        <CustomNumberInput
                          defaultValue={chunkSize}
                          min={100}
                          max={5000}
                          step={100}
                          onChange={(value) => {
                            setChunkSize(value);
                            console.log("Chunk size changed:", value);
                          }}
                        />
                      </div>
                    )}

                    {/* Recursive Chunking Options */}
                    {chunkingStrategy === "recursive_chunking" && (
                      <>
                        <div
                          style={{
                            display: "flex",
                            flexDirection: "column",
                            gap: "10px",
                            padding: "16px",
                            backgroundColor: "rgba(0, 0, 0, 0.2)",
                            borderRadius: "8px",
                            border: "2px solid #3f3f41",
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
                          <CustomNumberInput
                            defaultValue={chunkSize}
                            min={100}
                            max={5000}
                            step={100}
                            onChange={(value) => {
                              setChunkSize(value);
                              console.log("Chunk size changed:", value);
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
                            border: "2px solid #3f3f41",
                          }}
                        >
                          <label
                            style={{
                              fontSize: "14px",
                              color: "#808080",
                              fontWeight: 600,
                            }}
                          >
                            Chunk Overlap
                          </label>
                          <CustomNumberInput
                            defaultValue={chunkOverlap}
                            min={0}
                            max={1000}
                            step={50}
                            onChange={(value) => {
                              setChunkOverlap(value);
                              console.log("Chunk overlap changed:", value);
                            }}
                          />
                        </div>
                      </>
                    )}

                    {/* Sentence Chunking Options */}
                    {chunkingStrategy === "sentence_chunking" && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
                          gridColumn: "1 / -1",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Max Chunk Size
                        </label>
                        <CustomNumberInput
                          defaultValue={maxChunkSize}
                          min={100}
                          max={5000}
                          step={100}
                          onChange={(value) => {
                            setMaxChunkSize(value);
                            console.log("Max chunk size changed:", value);
                          }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedStep === "embedding" && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  {/* Embedding Provider Selection */}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "2px solid #3f3f41",
                    }}
                  >
                    <label
                      style={{
                        fontSize: "14px",
                        color: "#808080",
                        fontWeight: 600,
                      }}
                    >
                      Embedding Provider
                    </label>
                    <CustomDropdown
                      options={[
                        { value: "openai", label: "OpenAI" },
                        { value: "cohere", label: "Cohere" },
                        {
                          value: "local",
                          label: "Local (Sentence Transformers)",
                        },
                        { value: "amazon_bedrock", label: "Amazon Bedrock" },
                      ]}
                      defaultValue={embeddingProvider}
                      onChange={(value) => {
                        setEmbeddingProvider(value);
                        console.log("Selected embedding provider:", value);
                      }}
                    />
                  </div>

                  {/* Embedding Model Selection */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: isMobile
                        ? "1fr"
                        : "calc(50% - 12px) calc(50% - 12px)",
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
                        border: "2px solid #3f3f41",
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
                      <CustomDropdown
                        options={
                          embeddingProvider === "openai"
                            ? [
                                {
                                  value: "text-embedding-ada-002",
                                  label: "text-embedding-ada-002 (1536 dim)",
                                },
                                {
                                  value: "text-embedding-3-small",
                                  label: "text-embedding-3-small (1536 dim)",
                                },
                                {
                                  value: "text-embedding-3-large",
                                  label: "text-embedding-3-large (3072 dim)",
                                },
                              ]
                            : embeddingProvider === "cohere"
                              ? [
                                  {
                                    value: "embed-english-light-v3.0",
                                    label:
                                      "embed-english-light-v3.0 (1024 dim)",
                                  },
                                  {
                                    value: "embed-english-v3.0",
                                    label: "embed-english-v3.0 (1024 dim)",
                                  },
                                  {
                                    value: "embed-multilingual-v3.0",
                                    label: "embed-multilingual-v3.0 (1024 dim)",
                                  },
                                ]
                              : embeddingProvider === "local"
                                ? [
                                    {
                                      value: "all-MiniLM-L6-v2",
                                      label: "all-MiniLM-L6-v2 (384 dim)",
                                    },
                                    {
                                      value: "all-mpnet-base-v2",
                                      label: "all-mpnet-base-v2 (768 dim)",
                                    },
                                  ]
                                : embeddingProvider === "amazon_bedrock"
                                  ? [
                                      {
                                        value: "titan-embed-text-v1",
                                        label: "Titan Embed Text v1",
                                      },
                                    ]
                                  : [{ value: "none", label: "None" }]
                        }
                        defaultValue={embeddingModel}
                        onChange={(value) => {
                          setEmbeddingModel(value);
                          console.log("Selected embedding model:", value);
                        }}
                      />
                    </div>

                    {/* API Key Input for providers that need it */}
                    {(embeddingProvider === "openai" ||
                      embeddingProvider === "cohere") && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          API Key
                        </label>
                        <input
                          type="password"
                          placeholder="Enter API key"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
                            padding: "10px",
                            borderRadius: "8px",
                            fontSize: "14px",
                            width: "100%",
                          }}
                        />
                      </div>
                    )}

                    {/* AWS Region for Amazon Bedrock */}
                    {embeddingProvider === "amazon_bedrock" && (
                      <div
                        style={{
                          display: "flex",
                          flexDirection: "column",
                          gap: "10px",
                          padding: "16px",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          AWS Region
                        </label>
                        <input
                          type="text"
                          placeholder="e.g., us-east-1"
                          defaultValue="us-east-2"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
                            padding: "10px",
                            borderRadius: "8px",
                            fontSize: "14px",
                            width: "100%",
                          }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedStep === "vectorstore" && (
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "24px",
                    width: "100%",
                  }}
                >
                  {/* Vector Database Selection */}
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                      padding: "16px",
                      backgroundColor: "rgba(0, 0, 0, 0.2)",
                      borderRadius: "8px",
                      border: "2px solid #3f3f41",
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
                    <CustomDropdown
                      options={[
                        { value: "pinecone", label: "Pinecone" },
                        { value: "qdrant", label: "Qdrant" },
                        { value: "chroma", label: "Chroma" },
                      ]}
                      defaultValue={vectorDb}
                      onChange={(value) => {
                        setVectorDb(value);
                        console.log("Selected vector database:", value);
                      }}
                    />
                  </div>

                  {/* Database-specific Configuration */}
                  {vectorDb === "pinecone" && (
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: isMobile
                          ? "1fr"
                          : "calc(50% - 12px) calc(50% - 12px)",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          API Key
                        </label>
                        <input
                          type="password"
                          placeholder="Enter Pinecone API key"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Cloud
                        </label>
                        <CustomDropdown
                          options={[
                            { value: "aws", label: "AWS" },
                            { value: "gcp", label: "GCP" },
                            { value: "azure", label: "Azure" },
                          ]}
                          defaultValue="aws"
                          onChange={(value) =>
                            console.log("Selected cloud:", value)
                          }
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Region
                        </label>
                        <input
                          type="text"
                          placeholder="e.g., us-east-1"
                          defaultValue="us-east-1"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
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
                          border: "2px solid #3f3f41",
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
                          placeholder="Enter index name"
                          defaultValue="kb-final10"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Dimension
                        </label>
                        <CustomNumberInput
                          defaultValue={1536}
                          min={1}
                          max={4096}
                          step={1}
                          onChange={(value) =>
                            console.log("Dimension changed:", value)
                          }
                        />
                      </div>
                    </div>
                  )}

                  {vectorDb === "qdrant" && (
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: isMobile
                          ? "1fr"
                          : "calc(50% - 12px) calc(50% - 12px)",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Host
                        </label>
                        <input
                          type="text"
                          placeholder="Enter host URL"
                          defaultValue="http://localhost"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Port
                        </label>
                        <CustomNumberInput
                          defaultValue={5333}
                          min={1}
                          max={65535}
                          step={1}
                          onChange={(value) =>
                            console.log("Port changed:", value)
                          }
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
                          border: "2px solid #3f3f41",
                          gridColumn: "1 / -1",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Collection Name
                        </label>
                        <input
                          type="text"
                          placeholder="Enter collection name"
                          defaultValue="toshiba_pdf_7"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
                            padding: "10px",
                            borderRadius: "8px",
                            fontSize: "14px",
                            width: "100%",
                          }}
                        />
                      </div>
                    </div>
                  )}

                  {vectorDb === "chroma" && (
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: isMobile
                          ? "1fr"
                          : "calc(50% - 12px) calc(50% - 12px)",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Database Path
                        </label>
                        <input
                          type="text"
                          placeholder="Enter database path"
                          defaultValue="data/chroma_db"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
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
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <label
                          style={{
                            fontSize: "14px",
                            color: "#808080",
                            fontWeight: 600,
                          }}
                        >
                          Collection Name
                        </label>
                        <input
                          type="text"
                          placeholder="Enter collection name"
                          defaultValue="kb-chroma"
                          style={{
                            backgroundColor: "#161616",
                            color: "white",
                            border: "2px solid #3f3f41",
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
              )}
            </div>

            {/* Action Buttons Section */}
            <div
              style={{
                display: "flex",
                flexDirection: isMobile ? "column" : "row",
                gap: "12px",
                padding: "1.5rem",
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

          {/* Upload Files Box - Only shown for Loading step */}
          {selectedStep === "loading" && (
            <div
              style={{
                width: "calc(50% - 8px)",
                backgroundColor: "#212124",
                border: "2px solid #3f3f41",
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
                    Upload Files
                  </h1>
                </div>
              </div>

              {/* Upload Area */}
              <div
                style={{
                  flex: "1",
                  padding: "0 1.5rem 1.5rem",
                  overflowY: "auto",
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                {/* Top Section with Upload Box */}
                <div
                  style={{ flex: 1, display: "flex", flexDirection: "column" }}
                >
                  {/* Dashed Border Upload Box */}
                  <div
                    style={{
                      border: "2px dashed rgba(255, 255, 255, 0.2)",
                      borderRadius: "8px",
                      padding: "2rem",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                      marginBottom: "1.5rem",
                      cursor: "pointer",
                      flex: 1,
                    }}
                    onClick={handleFileSelect}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="48"
                      height="48"
                      viewBox="0 0 24 24"
                      fill="rgba(255, 255, 255, 0.5)"
                      style={{ marginBottom: "1rem" }}
                    >
                      <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z" />
                    </svg>
                    <p style={{ color: "white", marginBottom: "0.5rem" }}>
                      Drag and drop your files here
                    </p>
                    <p
                      style={{
                        color: "rgba(255, 255, 255, 0.5)",
                        fontSize: "0.9rem",
                      }}
                    >
                      or click to browse
                    </p>
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      style={{ display: "none" }}
                      onChange={handleFileChange}
                    />
                    <button
                      onClick={handleFileSelect}
                      style={{
                        backgroundColor: "#444",
                        color: "white",
                        border: "none",
                        padding: "8px 16px",
                        borderRadius: "4px",
                        marginTop: "1rem",
                        cursor: "pointer",
                        fontSize: "14px",
                      }}
                    >
                      Select Files
                    </button>
                  </div>
                </div>

                {/* Uploaded Files List - Now at the bottom */}
                <div style={{ marginTop: "1rem" }}>
                  {/* Render file items from state */}
                  {uploadingFiles.length === 0 ? (
                    <div
                      style={{
                        color: "#999",
                        textAlign: "center",
                        padding: "1rem",
                      }}
                    >
                      No files uploaded yet
                    </div>
                  ) : (
                    uploadingFiles.map((file) => (
                      <div
                        key={file.id}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          padding: "0.75rem",
                          backgroundColor: "rgba(0, 0, 0, 0.2)",
                          borderRadius: "8px",
                          marginBottom: "0.75rem",
                          border: "2px solid #3f3f41",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            marginRight: "12px",
                          }}
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="24"
                            height="24"
                            viewBox="0 0 24 24"
                            fill="white"
                            style={{ marginRight: "0.75rem" }}
                          >
                            <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
                          </svg>
                          <div
                            style={{ display: "flex", alignItems: "center" }}
                          >
                            <span
                              style={{ color: "white", fontSize: "0.9rem" }}
                            >
                              {file.name}
                            </span>
                            <span
                              style={{
                                color: "rgba(255, 255, 255, 0.5)",
                                fontSize: "0.8rem",
                                margin: "0 4px",
                              }}
                            >
                              •
                            </span>
                            <span
                              style={{
                                color: "rgba(255, 255, 255, 0.5)",
                                fontSize: "0.8rem",
                              }}
                            >
                              {file.size}
                            </span>
                          </div>
                        </div>

                        {/* Progress bar - only shown for files that aren't completed */}
                        {!file.completed && (
                          <div
                            style={{
                              flex: 1,
                              display: "flex",
                              alignItems: "center",
                            }}
                          >
                            <div
                              style={{
                                flex: 1,
                                height: "6px",
                                backgroundColor: "#eef1f3",
                                borderRadius: "5px",
                                position: "relative",
                                overflow: "hidden",
                                margin: "0 12px",
                              }}
                            >
                              <div
                                style={{
                                  position: "absolute",
                                  left: 0,
                                  top: 0,
                                  height: "100%",
                                  width: `${file.progress}%`,
                                  backgroundColor: "#30c292",
                                  borderRadius: "2px",
                                }}
                              ></div>
                            </div>
                            <div
                              style={{
                                minWidth: "45px",
                                textAlign: "right",
                                fontSize: "14px",
                                fontWeight: "500",
                                color:
                                  file.progress === 100 ? "#30c292" : "#ccc",
                              }}
                            >
                              {Math.round(file.progress)}%
                            </div>
                          </div>
                        )}

                        {/* If completed, add a spacer instead of progress bar */}
                        {file.completed && <div style={{ flex: 1 }}></div>}

                        <button
                          onClick={() => handleDeleteFile(file.id)}
                          style={{
                            backgroundColor: "transparent",
                            border: "none",
                            color: "#e74c3c",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            padding: "4px",
                          }}
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="currentColor"
                          >
                            <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
                          </svg>
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Removed Action Buttons Section */}
            </div>
          )}
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
