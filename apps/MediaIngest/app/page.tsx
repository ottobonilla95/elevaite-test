"use client";
import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { mediaIngestSteps } from "./lib/mediaIngestData";
import { ElevaiteIcons } from "../../../packages/ui/src/components/icons/elevaite";
import { AdaptiveConfigGrid } from "./components/AdaptiveConfigGrid";
import { ConfigField } from "./components/ConfigField";
import { CustomInput } from "./components/CustomInput";
import { CustomSlider } from "./components/CustomSlider";
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
  const [campaignFormat, setCampaignFormat] = useState<string>("mixed");
  const [campaignLocation, setCampaignLocation] = useState<string>("us-east");
  const [sourceS3Bucket, setSourceS3Bucket] = useState<string>(
    "creative-assets-source"
  );
  const [destinationS3Bucket, setDestinationS3Bucket] = useState<string>(
    "processed-creative-insights"
  );

  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
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
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z" />
            </svg>
          </div>
        );
      case "datainput":
        return (
          <div className="step-icon datainput">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path d="M9 16h6v-6h4l-7-7-7 7h4v6zm-4 2h14v2H5v-2z" />
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
    <div className="pipeline-page">
      {/* Border container for Media Ingestion Process and steps */}
      <div className="border-container">
        {/* Media Ingestion Process header */}
        <div className="pipeline-header-box">
          <div className="header-content">
            <h1>Media Ingestion Process</h1>

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

        {/* Process visualization */}
        <div className="pipeline-visualization">
          <div className="pipeline-steps-container">
            {mediaIngestSteps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div
                  className={`pipeline-step-box ${selectedStep === step.id ? "selected" : ""} ${mediaIngestSteps.findIndex((s) => s.id === selectedStep) >= mediaIngestSteps.findIndex((s) => s.id === step.id) ? "highlighted" : ""}`}
                  onClick={() => handleStepSelect(step.id)}
                >
                  <div className="icon-circle">{getStepIcon(step.id)}</div>
                  <div className="step-title">{step.title}</div>
                </div>
                {index < mediaIngestSteps.length - 1 && (
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
                    {mediaIngestSteps.find((s) => s.id === selectedStep)?.title}{" "}
                    Configuration
                  </h1>
                  <div className="info-icon">
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
                          id: "source_s3_bucket",
                          children: (
                            <ConfigField label="Campaign S3 Bucket">
                              <CustomInput
                                type="text"
                                placeholder="e.g., creative-assets-source"
                                defaultValue={sourceS3Bucket}
                                onChange={(value) => {
                                  setSourceS3Bucket(value);
                                  console.log("Campaign S3 bucket:", value);
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "destination_s3_bucket",
                          children: (
                            <ConfigField label="Creative S3 Bucket">
                              <CustomInput
                                type="text"
                                placeholder="e.g., processed-creative-insights"
                                defaultValue={destinationS3Bucket}
                                onChange={(value) => {
                                  setDestinationS3Bucket(value);
                                  console.log(
                                    "Creative Insights S3 bucket:",
                                    value
                                  );
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "location",
                          children: (
                            <ConfigField label="S3 Location">
                              <CustomDropdown
                                options={[
                                  { value: "us-east", label: "US East Coast" },
                                  { value: "us-west", label: "US West Coast" },
                                  { value: "us-central", label: "US Central" },
                                  { value: "europe", label: "Europe" },
                                  {
                                    value: "asia-pacific",
                                    label: "Asia Pacific",
                                  },
                                  { value: "global", label: "Global Campaign" },
                                ]}
                                defaultValue={campaignLocation}
                                onChange={(value) => {
                                  setCampaignLocation(value);
                                  console.log(
                                    "Selected campaign location:",
                                    value
                                  );
                                }}
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "checkpoint_file_folder",
                          children: (
                            <ConfigField label="Checkpoint File Folder">
                              <CustomInput
                                type="text"
                                placeholder="/data/checkpoints"
                                defaultValue="/data/checkpoints"
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "checkpoint_frequency",
                          children: (
                            <ConfigField label="Checkpoint Frequency">
                              <CustomDropdown
                                options={[
                                  { value: "5%", label: "5% of campaigns" },
                                  { value: "10%", label: "10% of campaigns" },
                                  { value: "15%", label: "15% of campaigns" },
                                  { value: "20%", label: "20% of campaigns" },
                                  { value: "25%", label: "25% of campaigns" },
                                ]}
                                defaultValue="10%"
                                onChange={(value) =>
                                  console.log("Checkpoint frequency:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                      ]}
                    />
                  </div>
                )}

                {selectedStep === "datainput" && (
                  <div className="config-container">
                    <AdaptiveConfigGrid
                      containerClassName="config-grid-container"
                      options={[
                        {
                          id: "campaign_data_folder",
                          children: (
                            <ConfigField label="Campaign Data Folder File Path">
                              <CustomInput
                                type="text"
                                placeholder="/data/campaigns"
                                defaultValue="/data/campaigns"
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "creative_data_folders",
                          children: (
                            <ConfigField label="Creative Data Folders">
                              <CustomInput
                                type="text"
                                placeholder="/data/creatives"
                                defaultValue="/data/creatives"
                              />
                            </ConfigField>
                          ),
                        },
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
                          id: "md5_hash_generation",
                          children: (
                            <ConfigField label="MD5 Hash Generation">
                              <CustomDropdown
                                options={[
                                  { value: "true", label: "True" },
                                  { value: "false", label: "False" },
                                ]}
                                defaultValue="true"
                                onChange={(value) =>
                                  console.log("MD5 Hash:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "file_size_calculation",
                          children: (
                            <ConfigField label="File Size Calculation">
                              <CustomDropdown
                                options={[
                                  { value: "true", label: "True" },
                                  { value: "false", label: "False" },
                                ]}
                                defaultValue="true"
                                onChange={(value) =>
                                  console.log("File Size:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "file_type_detection",
                          children: (
                            <ConfigField label="File Type Detection">
                              <CustomDropdown
                                options={[
                                  { value: "true", label: "True" },
                                  { value: "false", label: "False" },
                                ]}
                                defaultValue="true"
                                onChange={(value) =>
                                  console.log("File Type Detection:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
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
                          id: "video_quadrants",
                          children: (
                            <ConfigField label="Video Processing - Quadrants">
                              <CustomDropdown
                                options={[
                                  { value: "true", label: "True" },
                                  { value: "false", label: "False" },
                                ]}
                                defaultValue="true"
                                onChange={(value) =>
                                  console.log("Video Quadrants:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "frame_skip_intervals",
                          children: (
                            <ConfigField label="Frame Skip Intervals">
                              <CustomInput
                                type="text"
                                placeholder="Auto or enter number (e.g., 5, 10)"
                                defaultValue="Auto"
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "video_scale_percent",
                          children: (
                            <ConfigField label="Video Scale Percent for Resizing">
                              <CustomNumberInput
                                defaultValue={50}
                                min={10}
                                max={100}
                                step={5}
                                onChange={(value) =>
                                  console.log("Video Scale:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "histogram_similarity_threshold",
                          children: (
                            <ConfigField label="Histogram Similarity Threshold">
                              <CustomNumberInput
                                defaultValue={0.8}
                                min={0.0}
                                max={1.0}
                                step={0.1}
                                onChange={(value) =>
                                  console.log("Histogram Threshold:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "image_scale_percent",
                          children: (
                            <ConfigField label="Image Scale Percent for Resizing %">
                              <CustomNumberInput
                                defaultValue={75}
                                min={10}
                                max={100}
                                step={5}
                                onChange={(value) =>
                                  console.log("Image Scale:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "image_format_conversion",
                          children: (
                            <ConfigField label="Image Format Conversion Settings">
                              <CustomDropdown
                                options={[
                                  { value: "jpg", label: "JPG" },
                                  { value: "png", label: "PNG" },
                                  { value: "webp", label: "WebP" },
                                ]}
                                defaultValue="jpg"
                                onChange={(value) =>
                                  console.log("Image Format:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
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
                          id: "video_model_selection",
                          children: (
                            <ConfigField label="Models">
                              <CustomDropdown
                                options={[
                                  {
                                    value: "gpt-4o-mini",
                                    label: "GPT-4o Mini",
                                  },
                                  { value: "gpt-4o", label: "GPT-4o" },
                                  {
                                    value: "gpt-4-turbo",
                                    label: "GPT-4 Turbo",
                                  },
                                ]}
                                defaultValue="gpt-4o-mini"
                                onChange={(value) =>
                                  console.log("Video Model:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "video_max_tokens",
                          children: (
                            <ConfigField label="Max Output Tokens">
                              <CustomNumberInput
                                defaultValue={600}
                                min={100}
                                max={4000}
                                step={50}
                                onChange={(value) =>
                                  console.log("Video Max Tokens:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "video_output_structure",
                          children: (
                            <ConfigField label="Response Type">
                              <CustomDropdown
                                options={[
                                  { value: "json", label: "JSON" },
                                  { value: "txt", label: "Text" },
                                  { value: "xml", label: "XML" },
                                  { value: "yaml", label: "YAML" },
                                ]}
                                defaultValue="json"
                                onChange={(value) =>
                                  console.log("Video Output Format:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "video_temperature",
                          children: (
                            <ConfigField
                              label="Temperature"
                              tooltip="0 is least creative, 1 is most creative"
                            >
                              <CustomSlider
                                defaultValue={0.3}
                                min={0.0}
                                max={1.0}
                                step={0.1}
                                onChange={(value) =>
                                  console.log("Video Temperature:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "video_prompt_1",
                          children: (
                            <ConfigField label="Video Prompt 1 (Initial Analysis)">
                              <textarea
                                className="custom-textarea"
                                rows={5}
                                defaultValue={`Given the provided image(s), extract and fill in the following information using <tags>:
<Start_Date>: Extract Start Date from Folder Name: {campaign_folder}. Example 1: SVT_ChurchillDowns_US_Twinspires_01-26-24-01-27-24_JourneyAd extract 01-26-2024 Example 2:Evidens De Beaute_10/04 extract 10-04-2024
<End_Date>: Extract End Date from Folder Name: {campaign_folder}. Example 1: SVT_ChurchillDowns_US_Twinspires_01-26-24-01-27-24_JourneyAd extract 01-27-24 Example 2:Evidens De Beaute_10/04 extract NULL
<industry>: Identify the industry (e.g., Animation, Food & Beverage).
<Brand_Logo_Present>: yes or no.
<Brand_Logo_Size>: small, medium, or large.
<Brand_Logo_Location>: upper-left, middle, bottom-right, etc.
<Does_Brand_Name_Appear>: yes or no.
<Does_Product_Name_Appear>: yes or no.
<Is_Product_Description_In_Text>: yes or no.
<Colors_Background>: List colors with percentages (e.g., [brown: 50%, beige: 30%]).
<Text_Locations>: Where text appears (e.g., bottom, middle).
<Text_Details>: Extract text with color and size (e.g., <text> "Be bold, Sam." <text_color> "white" <text_size> "medium").

Use the <tags> to structure your answers. If any data is unavailable, mark it as NULL or leave it blank.`}
                                placeholder="Enter initial analysis prompt template..."
                                onChange={(e) =>
                                  console.log("Video Prompt 1:", e.target.value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "video_prompt_2",
                          children: (
                            <ConfigField label="Video Prompt 2 (Quadrant Results Merging)">
                              <textarea
                                className="custom-textarea"
                                rows={5}
                                defaultValue={`Based on the results from the four quadrants, summarize the following using <tags>:
<industry>:[Industry of brand/product]
<Brand_Logo_Present>: "yes" if present in any quadrant, otherwise "no".
<Brand_Logo_Location>: Specify where the brand logo appeared.
<Brand_Logo_When>: Specify the quadrant(s) that the brand logo appeared.
<Brand_Logo_Size>: The size of the brand logo (choose one size if it varies).
<Does_Brand_Name_Appear> "yes" if the brand name appears in any quadrant, otherwise "no".
<Does_Product_Name_Appear>: "yes" if the product name appears in any quadrant, otherwise "no".
<Is_Product_Description_In_Text>: "yes" if product description appears in any quadrant, otherwise "no".
<Colors_Background>: Mention the background colors which were used as a string (comma separated). eg.light blue(30%), black(50%).
<Text_Extracted>: Include the text from the four quadrants.
<Text_Locations>: Include the most used text locations as a string (comma separated)
<Text_JSON>: JSON object of all the text with respective colors and sizes. eg. [{"text": "Be bold,","text_color": "red","text_size": "large"},{"text": "Hello","text_color": "green","text_size": "large"}]`}
                                placeholder="Enter quadrant merging prompt template..."
                                onChange={(e) =>
                                  console.log("Video Prompt 2:", e.target.value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "image_model_selection",
                          children: (
                            <ConfigField label="Image Model Selection">
                              <CustomDropdown
                                options={[
                                  {
                                    value: "gpt-4o-mini",
                                    label: "GPT-4o Mini",
                                  },
                                  { value: "gpt-4o", label: "GPT-4o" },
                                  {
                                    value: "gpt-4-turbo",
                                    label: "GPT-4 Turbo",
                                  },
                                ]}
                                defaultValue="gpt-4o-mini"
                                onChange={(value) =>
                                  console.log("Image Model:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "image_max_tokens",
                          children: (
                            <ConfigField label="Image Max Output Tokens Setting">
                              <CustomNumberInput
                                defaultValue={600}
                                min={100}
                                max={4000}
                                step={50}
                                onChange={(value) =>
                                  console.log("Image Max Tokens:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "image_prompt_1",
                          children: (
                            <ConfigField label="Image Prompt 1 (Analysis)">
                              <textarea
                                className="custom-textarea"
                                rows={5}
                                defaultValue={`Given the provided image(s), extract and fill in the following information using <tags>:
<Start_Date>: Extract Start Date from Folder Name: {campaign_folder}. Example 1: SVT_ChurchillDowns_US_Twinspires_01-26-24-01-27-24_JourneyAd extract 01-26-2024 Example 2:Evidens De Beaute_10/04 extract 10-04-2024
<End_Date>: Extract End Date from Folder Name: {campaign_folder}. Example 1: SVT_ChurchillDowns_US_Twinspires_01-26-24-01-27-24_JourneyAd extract 01-27-24 Example 2:Evidens De Beaute_10/04 extract NULL
<industry>: Identify the industry (e.g., Animation, Food & Beverage).
<Brand_Logo_Present>: yes or no.
<Brand_Logo_Size>: small, medium, or large.
<Brand_Logo_Location>: upper-left, middle, bottom-right, etc.
<Does_Brand_Name_Appear>: yes or no.
<Does_Product_Name_Appear>: yes or no.
<Is_Product_Description_In_Text>: yes or no.
<Colors_Background>: List colors with percentages (e.g., [brown: 50%, beige: 30%]).
<Text_Locations>: Where text appears (e.g., bottom, middle).
<Text_Details>: Extract text with color and size (e.g., <text> "Be bold, Sam." <text_color> "white" <text_size> "medium").

Use the <tags> to structure your answers. If any data is unavailable, mark it as NULL or leave it blank.`}
                                placeholder="Enter image analysis prompt template..."
                                onChange={(e) =>
                                  console.log("Image Prompt 1:", e.target.value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "image_output_structure",
                          children: (
                            <ConfigField label="Image Output Structure">
                              <CustomDropdown
                                options={[
                                  { value: "json", label: "JSON" },
                                  { value: "txt", label: "Text" },
                                  { value: "xml", label: "XML" },
                                  { value: "yaml", label: "YAML" },
                                ]}
                                defaultValue="json"
                                onChange={(value) =>
                                  console.log("Image Output Format:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
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
                          id: "database_meta_data",
                          children: (
                            <ConfigField label="Database for Meta Data">
                              <CustomDropdown
                                options={[
                                  { value: "postgres", label: "Postgres" },
                                  { value: "mysql", label: "MySQL" },
                                  { value: "mongodb", label: "MongoDB" },
                                  { value: "sqlite", label: "SQLite" },
                                ]}
                                defaultValue="postgres"
                                onChange={(value) =>
                                  console.log("Meta Database:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "embedding_model",
                          children: (
                            <ConfigField label="Embedding Model">
                              <CustomDropdown
                                options={[
                                  { value: "text-ada", label: "Text Ada" },
                                  {
                                    value: "text-embedding-3-small",
                                    label: "text-embedding-3-small",
                                  },
                                  {
                                    value: "text-embedding-3-large",
                                    label: "text-embedding-3-large",
                                  },
                                  {
                                    value: "all-MiniLM-L6-v2",
                                    label: "all-MiniLM-L6-v2",
                                  },
                                ]}
                                defaultValue="text-ada"
                                onChange={(value) =>
                                  console.log("Embedding Model:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "vector_db",
                          children: (
                            <ConfigField label="Vector DB">
                              <CustomDropdown
                                options={[
                                  { value: "qdrant", label: "Qdrant" },
                                  { value: "pinecone", label: "Pinecone" },
                                  { value: "weaviate", label: "Weaviate" },
                                  { value: "milvus", label: "Milvus" },
                                  { value: "chroma", label: "Chroma" },
                                ]}
                                defaultValue="qdrant"
                                onChange={(value) =>
                                  console.log("Vector DB:", value)
                                }
                              />
                            </ConfigField>
                          ),
                        },
                        {
                          id: "collection_name",
                          children: (
                            <ConfigField label="Collection Name">
                              <CustomInput
                                type="text"
                                placeholder="creative-insights-collection"
                                defaultValue="creative-insights-collection"
                              />
                            </ConfigField>
                          ),
                        },
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
                Run {mediaIngestSteps.find((s) => s.id === selectedStep)?.title}
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
