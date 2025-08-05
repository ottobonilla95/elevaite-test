"use client";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { pipelineSteps } from "./lib/pipelineData";
import { ElevaiteIcons } from "../../../packages/ui/src/components/icons/elevaite";
import { AdaptiveConfigGrid } from "./components/AdaptiveConfigGrid";
import { ConfigField } from "./components/ConfigField";
import { CustomInput } from "./components/CustomInput";
import "./page.scss";
import "./components/CustomNumberInput.scss";
import "./components/CustomDropdown.scss";
import "./components/UploadComponent.scss";

interface UploadingFile {
  id: string;
  name: string;
  size: string;
  progress: number;
  completed: boolean;
}

export default function Home(): JSX.Element {
  const [selectedStep, setSelectedStep] = useState<string | null>("loading");
  const [isWarningFlashing, setIsWarningFlashing] = useState(false);

  // Loading step state
  const [dataSource, setDataSource] = useState<string>("s3");
  const [fileFormat, setFileFormat] = useState<string>("pdf");
  const [enableFileUpload, setEnableFileUpload] = useState<boolean>(true);
  const [uploadEndpoint, setUploadEndpoint] = useState<string>(
    `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/files/upload` ||
      "http://localhost:8000/api/files/upload"
  );

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
    // Function to close all dropdowns on resize
    const closeAllDropdowns = () => {
      // Close the project dropdown
      const projectDropdown = document.getElementById("project-dropdown");
      if (projectDropdown) {
        projectDropdown.style.display = "none";
      }

      // Close any custom dropdowns by clicking outside them
      const clickEvent = new MouseEvent("mousedown", {
        bubbles: true,
        cancelable: true,
        view: window,
      });
      document.dispatchEvent(clickEvent);
    };

    // Add event listener for window resize
    window.addEventListener("resize", closeAllDropdowns);

    // Cleanup
    return () => {
      window.removeEventListener("resize", closeAllDropdowns);
    };
  }, []);

  // Helper function to check if any files are still uploading
  const hasUploadingFiles = () => {
    return uploadingFiles.some((file) => !file.completed);
  };

  const handleStepSelect = (stepId: string) => {
    // If the step is already selected, do nothing
    if (stepId === selectedStep) {
      return;
    }

    // If files are still uploading, prevent navigation to any other step
    if (hasUploadingFiles()) {
      // Trigger the warning flash effect
      setIsWarningFlashing(true);

      // Reset the flashing effect after 1.5 seconds
      setTimeout(() => {
        setIsWarningFlashing(false);
      }, 1500);

      return;
    }

    // Otherwise, set the selected step to the clicked step
    setSelectedStep(stepId);
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
      <div className="custom-number-input">
        <input
          ref={inputRef}
          type="number"
          value={value}
          onChange={handleChange}
          min={min}
          max={max}
          step={step}
        />
        <div className="number-input-arrows">
          <button
            onClick={increment}
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
  }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedValue, setSelectedValue] = useState(
      defaultValue || options[0]?.value || ""
    );
    const dropdownRef = React.useRef<HTMLDivElement>(null);

    // Find the label for the selected value
    const selectedLabel =
      options.find((option) => option.value === selectedValue)?.label || "";

    // Handle click outside to close dropdown and update position on scroll/resize
    useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
        if (
          dropdownRef.current &&
          !dropdownRef.current.contains(event.target as Node)
        ) {
          setIsOpen(false);
        }
      };

      // Force re-render when scrolling to update dropdown position
      const handleScroll = () => {
        if (isOpen) {
          // Force a re-render to update the dropdown position
          setIsOpen(false);
          setTimeout(() => setIsOpen(true), 0);
        }
      };

      // Close dropdown on window resize
      const handleResize = () => {
        if (isOpen) {
          setIsOpen(false);
        }
      };

      document.addEventListener("mousedown", handleClickOutside);
      window.addEventListener("scroll", handleScroll, true);
      window.addEventListener("resize", handleResize);

      return () => {
        document.removeEventListener("mousedown", handleClickOutside);
        window.removeEventListener("scroll", handleScroll, true);
        window.removeEventListener("resize", handleResize);
      };
    }, [isOpen]);

    const handleOptionClick = (value: string) => {
      setSelectedValue(value);
      setIsOpen(false);
      if (onChange) {
        onChange(value);
      }
    };

    return (
      <div ref={dropdownRef} className="custom-dropdown">
        {/* Dropdown Button */}
        <div
          className="dropdown-button"
          onClick={() => setIsOpen(!isOpen)}
          onMouseOver={(e) => {
            e.currentTarget.style.borderColor = "#5f5f61";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.borderColor = "#3f3f41";
          }}
        >
          <span>{selectedLabel || " "}</span>
          <svg
            className={`dropdown-arrow ${isOpen ? "open" : ""}`}
            fill="none"
            viewBox="0 0 16 16"
            width={16}
            height={16}
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="m4 6.5 4 4 4-4"
              stroke="white"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
            />
          </svg>
        </div>

        {/* Dropdown Options */}
        {isOpen && (
          <div
            className="dropdown-menu"
            style={{
              top:
                (dropdownRef.current?.getBoundingClientRect().bottom || 0) + 5,
              left: dropdownRef.current?.getBoundingClientRect().left || 0,
              width: dropdownRef.current?.offsetWidth || 0,
            }}
          >
            {options.map((option) => (
              <div
                key={option.value}
                className={`dropdown-option ${selectedValue === option.value ? "selected" : ""}`}
                onClick={() => handleOptionClick(option.value)}
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
    <div className="pipeline-page">
      {/* Border container for Document Processing Pipeline and steps */}
      <div className="border-container">
        {/* Document Processing Pipeline header */}
        <div className="pipeline-header-box">
          <div className="header-content">
            <h1>Document Processing Pipeline</h1>

            <div className="header-controls">
              <div className="project-selector">
                <span>Project:</span>
                <div style={{ width: "150px" }}>
                  {/* Custom dropdown with orange arrow */}
                  <div className="project-dropdown">
                    <div
                      className="project-dropdown-button"
                      onClick={() => {
                        // Toggle dropdown
                        const dropdown =
                          document.getElementById("project-dropdown");
                        if (dropdown) {
                          dropdown.style.display =
                            dropdown.style.display === "none"
                              ? "block"
                              : "none";
                        }
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.backgroundColor = "#4f4f51";
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.backgroundColor = "#3f3f41";
                      }}
                    >
                      <span>Default Project</span>
                      <svg
                        fill="none"
                        viewBox="0 0 16 16"
                        width={16}
                        height={16}
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path
                          d="m4 6.5 4 4 4-4"
                          stroke="#e75f33"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                        />
                      </svg>
                    </div>
                    <div
                      id="project-dropdown"
                      className="project-dropdown-menu"
                    >
                      <div
                        className="project-dropdown-option selected"
                        onClick={() => {
                          document.getElementById(
                            "project-dropdown"
                          )!.style.display = "none";
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor =
                            "rgba(231, 95, 51, 0.2)";
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor =
                            "rgba(231, 95, 51, 0.1)";
                        }}
                      >
                        Default Project
                      </div>
                      <div
                        className="project-dropdown-option"
                        onClick={() => {
                          document.getElementById(
                            "project-dropdown"
                          )!.style.display = "none";
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor =
                            "rgba(255, 255, 255, 0.05)";
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor = "transparent";
                        }}
                      >
                        Project 1
                      </div>
                      <div
                        className="project-dropdown-option"
                        onClick={() => {
                          document.getElementById(
                            "project-dropdown"
                          )!.style.display = "none";
                        }}
                        onMouseOver={(e) => {
                          e.currentTarget.style.backgroundColor =
                            "rgba(255, 255, 255, 0.05)";
                        }}
                        onMouseOut={(e) => {
                          e.currentTarget.style.backgroundColor = "transparent";
                        }}
                      >
                        Project 2
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="provider-display">
                <span>Provider:</span>
                <div className="provider-display">SageMaker</div>
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
      </div>

      {/* Configuration and Upload Files Boxes */}
      {selectedStep && (
        <div className="config-upload-container">
          {/* Configuration Box */}
          <div
            className={`config-box ${selectedStep === "loading" ? "with-upload" : ""}`}
          >
            {/* Inner border container - wraps header and config fields */}
            <div className="inner-border-container">
              {/* Header Section */}
              <div className="config-header">
                <div className="header-title">
                  <h1>
                    {pipelineSteps.find((s) => s.id === selectedStep)?.title}{" "}
                    Configuration
                  </h1>
                  <div
                    className="info-icon"
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
                <button className="monitor-button">
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
              <div className="config-content">
                {/* Configuration Options */}
                {selectedStep === "loading" && (
                  <div className="config-container">
                    <AdaptiveConfigGrid
                      containerClassName="config-grid-container"
                      options={[
                        {
                          id: "data_source",
                          children: (
                            <ConfigField label="Data Source">
                              <CustomDropdown
                                options={[
                                  { value: "s3", label: "Amazon S3" },
                                  { value: "local", label: "Local Storage" },
                                  { value: "url", label: "URL" },
                                  { value: "upload", label: "File Upload" },
                                ]}
                                defaultValue={dataSource}
                                onChange={(value) => {
                                  setDataSource(value);
                                  console.log("Selected data source:", value);
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "file_format",
                          children: (
                            <ConfigField label="File Format">
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
                            </ConfigField>
                          ),
                        },
                        ...(dataSource === "s3"
                          ? [
                              {
                                id: "s3_bucket_name",
                                children: (
                                  <ConfigField label="S3 Bucket Name">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter bucket name"
                                      defaultValue="kb-check-pdf"
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "aws_region",
                                children: (
                                  <ConfigField label="AWS Region">
                                    <CustomInput
                                      type="text"
                                      placeholder="e.g., us-east-1"
                                      defaultValue="us-east-2"
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                        ...(dataSource === "local"
                          ? [
                              {
                                id: "input_directory",
                                children: (
                                  <ConfigField label="Input Directory">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter input directory path"
                                      defaultValue="/elevaite_ingestion/INPUT"
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "output_directory",
                                children: (
                                  <ConfigField label="Output Directory">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter output directory path"
                                      defaultValue="/elevaite_ingestion/OUTPUT"
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                        ...(dataSource === "upload"
                          ? [
                              {
                                id: "upload_endpoint",
                                children: (
                                  <ConfigField label="Upload Endpoint URL">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter upload endpoint URL"
                                      defaultValue={uploadEndpoint}
                                      onChange={(value) => {
                                        setUploadEndpoint(value);
                                        console.log("Upload endpoint:", value);
                                      }}
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "enable_file_upload",
                                children: (
                                  <ConfigField label="Enable File Upload">
                                    <input
                                      type="checkbox"
                                      checked={enableFileUpload}
                                      onChange={(e) => {
                                        setEnableFileUpload(e.target.checked);
                                        console.log(
                                          "Enable file upload:",
                                          e.target.checked
                                        );
                                      }}
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                      ]}
                    />
                  </div>
                )}

                {selectedStep === "parsing" && (
                  <div className="config-container">
                    <AdaptiveConfigGrid
                      containerClassName="config-grid-container"
                      options={[
                        {
                          id: "parsing_mode",
                          children: (
                            <ConfigField label="Parsing Mode">
                              <CustomDropdown
                                options={[
                                  {
                                    value: "auto_parser",
                                    label: "Auto Parser",
                                  },
                                  {
                                    value: "custom_parser",
                                    label: "Custom Parser",
                                  },
                                ]}
                                defaultValue={parsingMode}
                                onChange={(value) => {
                                  setParsingMode(value);
                                  console.log("Selected parsing mode:", value);
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "parser_type",
                          children: (
                            <ConfigField label="Parser Type">
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
                            </ConfigField>
                          ),
                        },
                        ...(parsingMode === "custom_parser" && parserType
                          ? [
                              {
                                id: "parser_tool",
                                children: (
                                  <ConfigField label="Parser Tool">
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
                                                {
                                                  value: "docling",
                                                  label: "Docling",
                                                },
                                                {
                                                  value: "llamaparse",
                                                  label: "LlamaParse",
                                                },
                                              ]
                                            : [{ value: "none", label: "None" }]
                                      }
                                      defaultValue={
                                        parserTool ||
                                        (parserType === "pdf"
                                          ? "none"
                                          : "markitdown")
                                      }
                                      onChange={(value) => {
                                        setParserTool(value);
                                        console.log(
                                          "Selected parser tool:",
                                          value
                                        );
                                      }}
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                        ...(parsingMode === "custom_parser" && !parserType
                          ? [
                              {
                                id: "parser_tool_placeholder",
                                children: (
                                  <ConfigField label="Parser Tool">
                                    <div
                                      style={{
                                        color: "#808080",
                                        fontSize: "14px",
                                      }}
                                    >
                                      Select a parser type first
                                    </div>
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                        ...(parsingMode === "auto_parser"
                          ? [
                              {
                                id: "language",
                                children: (
                                  <ConfigField label="Language">
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
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                      ]}
                    />
                  </div>
                )}

                {selectedStep === "chunking" && (
                  <div className="config-container">
                    <AdaptiveConfigGrid
                      containerClassName="config-grid-container"
                      options={[
                        {
                          id: "chunking_strategy",
                          children: (
                            <ConfigField label="Chunking Strategy">
                              <CustomDropdown
                                options={[
                                  {
                                    value: "semantic_chunking",
                                    label: "Semantic Chunking",
                                  },
                                  {
                                    value: "mdstructure",
                                    label: "Markdown Structure",
                                  },
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
                                  console.log(
                                    "Selected chunking strategy:",
                                    value
                                  );
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "chunk_size",
                          children: (
                            <ConfigField label="Chunk Size">
                              <CustomNumberInput
                                min={100}
                                max={2000}
                                step={50}
                                defaultValue={chunkSize}
                                onChange={(value) => {
                                  setChunkSize(value);
                                  console.log("Selected chunk size:", value);
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "chunk_overlap",
                          children: (
                            <ConfigField label="Chunk Overlap">
                              <CustomNumberInput
                                min={0}
                                max={500}
                                step={10}
                                defaultValue={chunkOverlap}
                                onChange={(value) => {
                                  setChunkOverlap(value);
                                  console.log("Selected chunk overlap:", value);
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        ...(chunkingStrategy === "semantic_chunking"
                          ? [
                              {
                                id: "semantic_model",
                                children: (
                                  <ConfigField label="Semantic Model">
                                    <CustomDropdown
                                      options={[
                                        {
                                          value: "openai",
                                          label: "OpenAI",
                                        },
                                        {
                                          value: "cohere",
                                          label: "Cohere",
                                        },
                                        {
                                          value: "huggingface",
                                          label: "HuggingFace",
                                        },
                                      ]}
                                      defaultValue="openai"
                                      onChange={(value) =>
                                        console.log(
                                          "Selected semantic model:",
                                          value
                                        )
                                      }
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "threshold_type",
                                children: (
                                  <ConfigField label="Threshold Type">
                                    <CustomDropdown
                                      options={[
                                        {
                                          value: "percentile",
                                          label: "Percentile",
                                        },
                                        { value: "fixed", label: "Fixed" },
                                      ]}
                                      defaultValue={thresholdType}
                                      onChange={(value) => {
                                        setThresholdType(value);
                                        console.log(
                                          "Threshold type changed:",
                                          value
                                        );
                                      }}
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "threshold_amount",
                                children: (
                                  <ConfigField label="Threshold Amount">
                                    <CustomNumberInput
                                      defaultValue={thresholdAmount}
                                      min={1}
                                      max={100}
                                      step={1}
                                      onChange={(value) => {
                                        setThresholdAmount(value);
                                        console.log(
                                          "Threshold amount changed:",
                                          value
                                        );
                                      }}
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                        ...(chunkingStrategy === "sentence_chunking"
                          ? [
                              {
                                id: "max_chunk_size",
                                children: (
                                  <ConfigField label="Max Chunk Size">
                                    <CustomNumberInput
                                      defaultValue={maxChunkSize}
                                      min={100}
                                      max={5000}
                                      step={100}
                                      onChange={(value) => {
                                        setMaxChunkSize(value);
                                        console.log(
                                          "Max chunk size changed:",
                                          value
                                        );
                                      }}
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                      ]}
                    />
                  </div>
                )}

                {selectedStep === "embedding" && (
                  <div className="config-container">
                    <AdaptiveConfigGrid
                      containerClassName="config-grid-container"
                      options={[
                        {
                          id: "embedding_provider",
                          children: (
                            <ConfigField label="Embedding Provider">
                              <CustomDropdown
                                options={[
                                  { value: "openai", label: "OpenAI" },
                                  { value: "cohere", label: "Cohere" },
                                  {
                                    value: "local",
                                    label: "Local (Sentence Transformers)",
                                  },
                                  {
                                    value: "amazon_bedrock",
                                    label: "Amazon Bedrock",
                                  },
                                ]}
                                defaultValue={embeddingProvider}
                                onChange={(value) => {
                                  setEmbeddingProvider(value);
                                  console.log(
                                    "Selected embedding provider:",
                                    value
                                  );
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "embedding_model",
                          children: (
                            <ConfigField label="Embedding Model">
                              <CustomDropdown
                                options={
                                  embeddingProvider === "openai"
                                    ? [
                                        {
                                          value: "text-embedding-ada-002",
                                          label:
                                            "text-embedding-ada-002 (1536 dim)",
                                        },
                                        {
                                          value: "text-embedding-3-small",
                                          label:
                                            "text-embedding-3-small (1536 dim)",
                                        },
                                        {
                                          value: "text-embedding-3-large",
                                          label:
                                            "text-embedding-3-large (3072 dim)",
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
                                            label:
                                              "embed-english-v3.0 (1024 dim)",
                                          },
                                          {
                                            value: "embed-multilingual-v3.0",
                                            label:
                                              "embed-multilingual-v3.0 (1024 dim)",
                                          },
                                        ]
                                      : embeddingProvider === "local"
                                        ? [
                                            {
                                              value: "all-MiniLM-L6-v2",
                                              label:
                                                "all-MiniLM-L6-v2 (384 dim)",
                                            },
                                            {
                                              value: "all-mpnet-base-v2",
                                              label:
                                                "all-mpnet-base-v2 (768 dim)",
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
                                  console.log(
                                    "Selected embedding model:",
                                    value
                                  );
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        ...(embeddingProvider === "openai" ||
                        embeddingProvider === "cohere"
                          ? [
                              {
                                id: "api_key",
                                children: (
                                  <ConfigField label="API Key">
                                    <CustomInput
                                      type="password"
                                      placeholder="Enter API key"
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                        ...(embeddingProvider === "amazon_bedrock"
                          ? [
                              {
                                id: "aws_region",
                                children: (
                                  <ConfigField label="AWS Region">
                                    <CustomInput
                                      type="text"
                                      placeholder="e.g., us-east-1"
                                      defaultValue="us-east-2"
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                      ]}
                    />
                  </div>
                )}

                {selectedStep === "vectorstore" && (
                  <div className="config-container">
                    <AdaptiveConfigGrid
                      containerClassName="config-grid-container"
                      options={[
                        {
                          id: "vector_database",
                          children: (
                            <ConfigField label="Vector Database">
                              <CustomDropdown
                                options={[
                                  { value: "pinecone", label: "Pinecone" },
                                  { value: "qdrant", label: "Qdrant" },
                                  { value: "chroma", label: "Chroma" },
                                ]}
                                defaultValue={vectorDb}
                                onChange={(value) => {
                                  setVectorDb(value);
                                  console.log(
                                    "Selected vector database:",
                                    value
                                  );
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        ...(vectorDb === "pinecone"
                          ? [
                              {
                                id: "pinecone_api_key",
                                children: (
                                  <ConfigField label="API Key">
                                    <CustomInput
                                      type="password"
                                      placeholder="Enter Pinecone API key"
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "pinecone_cloud",
                                children: (
                                  <ConfigField label="Cloud">
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
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "pinecone_region",
                                children: (
                                  <ConfigField label="Region">
                                    <CustomInput
                                      type="text"
                                      placeholder="e.g., us-east-1"
                                      defaultValue="us-east-1"
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "pinecone_index",
                                children: (
                                  <ConfigField label="Index Name">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter index name"
                                      defaultValue="kb-final10"
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "pinecone_dimension",
                                children: (
                                  <ConfigField label="Dimension">
                                    <CustomNumberInput
                                      defaultValue={1536}
                                      min={1}
                                      max={4096}
                                      step={1}
                                      onChange={(value) =>
                                        console.log("Dimension changed:", value)
                                      }
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                        ...(vectorDb === "qdrant"
                          ? [
                              {
                                id: "qdrant_host",
                                children: (
                                  <ConfigField label="Host">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter host URL"
                                      defaultValue="http://localhost"
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "qdrant_port",
                                children: (
                                  <ConfigField label="Port">
                                    <CustomNumberInput
                                      defaultValue={5333}
                                      min={1}
                                      max={65535}
                                      step={1}
                                      onChange={(value) =>
                                        console.log("Port changed:", value)
                                      }
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "qdrant_collection",
                                children: (
                                  <ConfigField label="Collection Name">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter collection name"
                                      defaultValue="toshiba_pdf_7"
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                        ...(vectorDb === "chroma"
                          ? [
                              {
                                id: "chroma_db_path",
                                children: (
                                  <ConfigField label="Database Path">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter database path"
                                      defaultValue="data/chroma_db"
                                    />
                                  </ConfigField>
                                ),
                              },
                              {
                                id: "chroma_collection",
                                children: (
                                  <ConfigField label="Collection Name">
                                    <CustomInput
                                      type="text"
                                      placeholder="Enter collection name"
                                      defaultValue="kb-chroma"
                                    />
                                  </ConfigField>
                                ),
                              },
                            ]
                          : []),
                      ]}
                    />
                  </div>
                )}
              </div>
            </div>

            {/* Action Buttons Section */}
            <div className="config-actions">
              <button className="run-button">
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
              <button className="save-button">
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
            <div className="upload-component">
              {/* Header */}
              <div className="upload-header">
                <h1>Upload Files</h1>
              </div>

              {/* Upload Area */}
              <div className="upload-area">
                {/* Dropzone */}
                <div
                  className="upload-dropzone"
                  onClick={handleFileSelect}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = "#5f5f61";
                    e.currentTarget.style.backgroundColor =
                      "rgba(255, 255, 255, 0.03)";
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = "#3f3f41";
                    e.currentTarget.style.backgroundColor = "transparent";
                  }}
                >
                  <svg
                    className="upload-icon"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z" />
                  </svg>
                  <h3>Drag & Drop Files Here</h3>
                  <p>or click to browse your files</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    className="hidden-input"
                    onChange={handleFileChange}
                  />
                </div>

                {/* File List */}
                <div className="file-list">
                  {/* Status message if files are still uploading */}
                  {hasUploadingFiles() && (
                    <div
                      className={`warning-message ${isWarningFlashing ? "warning-flash" : ""}`}
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        width="18"
                        height="18"
                        viewBox="0 0 24 24"
                        fill="currentColor"
                      >
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
                      </svg>
                      <strong>Files are still uploading.</strong> Please wait
                      before proceeding to the next step.
                    </div>
                  )}

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
                      <div key={file.id} className="file-item">
                        <div className="file-info">
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
                          <span className="file-name">{file.name}</span>
                          <span className="file-size">{file.size}</span>
                        </div>
                        <div className="file-actions">
                          {!file.completed ? (
                            <>
                              <div className="progress-container">
                                <div
                                  className="progress-bar"
                                  style={{ width: `${file.progress}%` }}
                                />
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
                            </>
                          ) : (
                            <div style={{ flex: 1 }}></div>
                          )}
                          <button
                            className="delete-button"
                            onClick={() => handleDeleteFile(file.id)}
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
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
