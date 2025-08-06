"use client";

import React, { useState, useEffect } from "react";
import { Upload, X } from "lucide-react";
import {
  type VectorizationStepType,
  type VectorizationStepData,
} from "../VectorizerBottomDrawer";
import { ConfigField } from "./ConfigField";
import { CustomDropdown } from "./CustomDropdown";
import UploadModal from "../UploadModal";
import "./VectorizerStepConfig.scss";

// Dropdown option interface matching pipelines app
interface DropdownOption {
  value: string;
  label: string;
  disabled?: boolean;
}

// Configuration field interface
interface ConfigFieldData {
  id: string;
  label: string;
  type: "select" | "text" | "number" | "checkbox";
  options?: DropdownOption[];
  default?: string | number | boolean;
  description?: string;
  dependsOn?: string;
  showWhen?: string | string[];
}

type StepConfigData = Record<string, string | number | boolean>;

interface UploadedFile {
  id: string;
  name: string;
  size: string;
  completed: boolean;
}

interface VectorizerStepConfigProps {
  stepData: VectorizationStepData | null;
  onConfigChange?: (stepId: string, config: StepConfigData) => void;
  existingConfig?: Record<string, unknown>;
}

// Configuration options for each step type based on actual pipelines app
const getStepConfigOptions = (
  stepType: VectorizationStepType
): ConfigFieldData[] => {
  switch (stepType) {
    case "load":
      return [
        {
          id: "provider",
          label: "Provider",
          type: "select",
          options: [
            { value: "s3", label: "Amazon S3" },
            { value: "gcs", label: "Google Cloud Storage" },
            { value: "azure", label: "Azure Blob Storage" },
            { value: "local", label: "Local File System" },
            { value: "url", label: "URL/Web" },
          ],
          default: "s3",
          description: "Select the data source provider",
        },
        {
          id: "bucket_name",
          label: "Bucket Name",
          type: "text",
          default: "",
          description: "Name of the storage bucket",
          dependsOn: "provider",
          showWhen: ["s3", "gcs", "azure"],
        },
        {
          id: "file_path",
          label: "File Path",
          type: "text",
          default: "",
          description: "Path to the files or directory",
        },
        {
          id: "file_pattern",
          label: "File Pattern",
          type: "text",
          default: "*.pdf",
          description: "Pattern to match files (e.g., *.pdf, *.txt)",
        },
        {
          id: "recursive",
          label: "Recursive",
          type: "checkbox",
          default: false,
          description: "Include files from subdirectories",
        },
      ];
    case "parse":
      return [
        {
          id: "provider",
          label: "Provider",
          type: "select",
          options: [
            { value: "unstructured", label: "Unstructured.io" },
            { value: "llamaparse", label: "LlamaParse" },
            {
              value: "azure_document_intelligence",
              label: "Azure Document Intelligence",
            },
            { value: "simple", label: "Simple Text Parser" },
          ],
          default: "unstructured",
          description: "Select the parsing provider",
        },
        {
          id: "api_key",
          label: "API Key",
          type: "text",
          default: "",
          description: "API key for the parsing service",
          dependsOn: "provider",
          showWhen: [
            "unstructured",
            "llamaparse",
            "azure_document_intelligence",
          ],
        },
        {
          id: "strategy",
          label: "Strategy",
          type: "select",
          options: [
            { value: "auto", label: "Auto" },
            { value: "fast", label: "Fast" },
            { value: "ocr_only", label: "OCR Only" },
            { value: "hi_res", label: "High Resolution" },
          ],
          default: "auto",
          description: "Parsing strategy to use",
          dependsOn: "provider",
          showWhen: ["unstructured"],
        },
        {
          id: "extract_images",
          label: "Extract Images",
          type: "checkbox",
          default: false,
          description: "Extract and process images from documents",
        },
      ];
    case "chunk":
      return [
        {
          id: "strategy",
          label: "Strategy",
          type: "select",
          options: [
            { value: "recursive", label: "Recursive Character Text Splitter" },
            { value: "semantic", label: "Semantic Chunking" },
            { value: "fixed", label: "Fixed Size" },
            { value: "markdown", label: "Markdown Splitter" },
          ],
          default: "recursive",
          description: "Method for splitting text into chunks",
        },
        {
          id: "chunk_size",
          label: "Chunk Size",
          type: "number",
          default: 1000,
          description: "Maximum number of characters per chunk",
        },
        {
          id: "chunk_overlap",
          label: "Chunk Overlap",
          type: "number",
          default: 200,
          description: "Number of overlapping characters between chunks",
        },
        {
          id: "separators",
          label: "Separators",
          type: "text",
          default: "\\n\\n,\\n, ,",
          description: "Comma-separated list of separators",
          dependsOn: "strategy",
          showWhen: ["recursive"],
        },
        {
          id: "similarity_threshold",
          label: "Similarity Threshold",
          type: "number",
          default: 0.5,
          description: "Threshold for semantic similarity",
          dependsOn: "strategy",
          showWhen: ["semantic"],
        },
      ];
    case "embed":
      return [
        {
          id: "provider",
          label: "Provider",
          type: "select",
          options: [
            { value: "openai", label: "OpenAI" },
            { value: "azure_openai", label: "Azure OpenAI" },
            { value: "huggingface", label: "Hugging Face" },
            { value: "cohere", label: "Cohere" },
            { value: "voyage", label: "Voyage AI" },
          ],
          default: "openai",
          description: "Select the embedding provider",
        },
        {
          id: "model",
          label: "Model",
          type: "select",
          options: [
            {
              value: "text-embedding-3-small",
              label: "text-embedding-3-small",
            },
            {
              value: "text-embedding-3-large",
              label: "text-embedding-3-large",
            },
            {
              value: "text-embedding-ada-002",
              label: "text-embedding-ada-002",
            },
          ],
          default: "text-embedding-3-small",
          description: "Embedding model to use",
          dependsOn: "provider",
          showWhen: ["openai", "azure_openai"],
        },
        {
          id: "api_key",
          label: "API Key",
          type: "text",
          default: "",
          description: "API key for the embedding service",
        },
        {
          id: "batch_size",
          label: "Batch Size",
          type: "number",
          default: 100,
          description: "Number of texts to embed in each batch",
        },
      ];
    case "store":
      return [
        {
          id: "provider",
          label: "Provider",
          type: "select",
          options: [
            { value: "pinecone", label: "Pinecone" },
            { value: "weaviate", label: "Weaviate" },
            { value: "qdrant", label: "Qdrant" },
            { value: "chroma", label: "Chroma" },
            { value: "elasticsearch", label: "Elasticsearch" },
          ],
          default: "pinecone",
          description: "Vector database provider",
        },
        {
          id: "api_key",
          label: "API Key",
          type: "text",
          default: "",
          description: "API key for the vector database",
          dependsOn: "provider",
          showWhen: ["pinecone", "weaviate", "qdrant"],
        },
        {
          id: "index_name",
          label: "Index Name",
          type: "text",
          default: "vectorizer-index",
          description: "Name of the vector index",
        },
        {
          id: "namespace",
          label: "Namespace",
          type: "text",
          default: "",
          description: "Namespace for organizing vectors",
          dependsOn: "provider",
          showWhen: ["pinecone"],
        },
        {
          id: "collection_name",
          label: "Collection Name",
          type: "text",
          default: "documents",
          description: "Name of the collection",
          dependsOn: "provider",
          showWhen: ["weaviate", "qdrant", "chroma"],
        },
      ];
    case "query":
      return [
        {
          id: "retrieval_strategy",
          label: "Retrieval Strategy",
          type: "select",
          options: [
            { value: "similarity", label: "Similarity Search" },
            { value: "mmr", label: "Maximal Marginal Relevance" },
            { value: "hybrid", label: "Hybrid Search" },
          ],
          default: "similarity",
          description: "Strategy for retrieving relevant documents",
        },
        {
          id: "top_k",
          label: "Top K Results",
          type: "number",
          default: 5,
          description: "Number of most relevant documents to return",
        },
        {
          id: "score_threshold",
          label: "Score Threshold",
          type: "number",
          default: 0.0,
          description: "Minimum similarity score for results",
        },
        {
          id: "lambda_mult",
          label: "Lambda Multiplier",
          type: "number",
          default: 0.5,
          description: "Diversity parameter for MMR",
          dependsOn: "retrieval_strategy",
          showWhen: ["mmr"],
        },
        {
          id: "include_metadata",
          label: "Include Metadata",
          type: "checkbox",
          default: true,
          description: "Include document metadata in results",
        },
      ];
    default:
      return [];
  }
};

const getStepIcon = (stepType: VectorizationStepType): string => {
  switch (stepType) {
    case "load":
      return "📁";
    case "parse":
      return "📄";
    case "chunk":
      return "✂️";
    case "embed":
      return "🔢";
    case "store":
      return "💾";
    case "query":
      return "🔍";
    default:
      return "⚙️";
  }
};

export default function VectorizerStepConfig({
  stepData,
  onConfigChange,
  existingConfig,
}: VectorizerStepConfigProps): JSX.Element {
  const [config, setConfig] = useState<StepConfigData>({});

  // Upload functionality state - keyed by step ID
  const [stepFiles, setStepFiles] = useState<Record<string, UploadedFile[]>>(
    {}
  );
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  // Get current step's files
  const currentStepId = stepData?.id || "default";
  const currentFiles = stepFiles[currentStepId] || [];

  // Initialize config with default values when stepData changes
  useEffect(() => {
    if (stepData) {
      const configOptions = getStepConfigOptions(stepData.type);
      const defaultConfig: StepConfigData = {};

      configOptions.forEach((option) => {
        defaultConfig[option.id] = option.default ?? "";
      });

      // Merge with existing config from props, stepData, or use defaults
      const mergedConfig = {
        ...defaultConfig,
        ...(stepData.config ?? {}),
        ...(existingConfig ?? {}),
      };
      setConfig(mergedConfig as StepConfigData);
    }
  }, [stepData, existingConfig]);

  const handleConfigChange = (
    optionId: string,
    value: string | number | boolean
  ): void => {
    const newConfig = {
      ...config,
      [optionId]: value,
    };
    setConfig(newConfig);

    if (stepData && onConfigChange) {
      onConfigChange(stepData.id, newConfig);
    }
  };

  // Upload handlers
  const handleUploadClick = (): void => {
    setIsUploadModalOpen(true);
  };

  const handleFilesUploaded = (uploadedFiles: any[]): void => {
    // Convert UploadingFile to UploadedFile format
    const convertedFiles: UploadedFile[] = uploadedFiles.map((file) => ({
      id: file.id,
      name: file.name,
      size: file.size,
      completed: file.completed,
    }));

    // Add new files to existing files for this step
    setStepFiles((prev) => ({
      ...prev,
      [currentStepId]: [...currentFiles, ...convertedFiles],
    }));
  };

  const handleRemoveFile = (fileId: string): void => {
    setStepFiles((prev) => ({
      ...prev,
      [currentStepId]: currentFiles.filter((file) => file.id !== fileId),
    }));
  };

  // Check if a field should be shown based on dependencies
  const shouldShowField = (field: ConfigFieldData): boolean => {
    if (!field.dependsOn || !field.showWhen) {
      return true;
    }

    const dependentValue = config[field.dependsOn];
    if (Array.isArray(field.showWhen)) {
      return field.showWhen.includes(dependentValue as string);
    }
    return dependentValue === field.showWhen;
  };

  if (!stepData) {
    return (
      <div className="vectorizer-step-config empty-state">
        <div className="empty-state-content">
          <div className="empty-state-icon">⚙️</div>
          <h3 className="empty-state-title">Select a step to configure</h3>
          <p className="empty-state-description">
            Click on any step in the vectorizer canvas to view and edit its
            configuration options.
          </p>
        </div>
      </div>
    );
  }

  const configOptions = getStepConfigOptions(stepData.type);
  const visibleOptions = configOptions.filter(shouldShowField);

  return (
    <div className="vectorizer-step-config">
      {/* Step Header */}
      <div className="step-config-header">
        <div className="step-info">
          <span className="step-icon">{getStepIcon(stepData.type)}</span>
          <div className="step-details">
            <h3 className="step-name">{stepData.name}</h3>
            <p className="step-description">{stepData.description}</p>
          </div>
        </div>
      </div>

      {/* Configuration Options */}
      <div className="config-options">
        <h4 className="config-section-title">Configuration</h4>
        <div className="config-fields">
          {visibleOptions.map((option) => (
            <ConfigField
              key={option.id}
              label={option.label}
              description={option.description}
            >
              {option.type === "select" && option.options ? (
                <CustomDropdown
                  options={option.options}
                  value={config[option.id] as string}
                  defaultValue={option.default as string}
                  onChange={(value) => {
                    handleConfigChange(option.id, value);
                  }}
                />
              ) : null}

              {option.type === "text" && (
                <input
                  type="text"
                  value={(config[option.id] as string) || ""}
                  onChange={(e) => {
                    handleConfigChange(option.id, e.target.value);
                  }}
                  placeholder={`Enter ${option.label.toLowerCase()}`}
                />
              )}

              {option.type === "number" && (
                <input
                  type="number"
                  value={
                    (config[option.id] as number) ||
                    (typeof option.default === "number" ? option.default : 0)
                  }
                  onChange={(e) => {
                    handleConfigChange(
                      option.id,
                      parseFloat(e.target.value) || 0
                    );
                  }}
                  step="any"
                />
              )}

              {option.type === "checkbox" && (
                <div className="checkbox-wrapper">
                  <input
                    type="checkbox"
                    id={`checkbox-${option.id}`}
                    checked={(config[option.id] as boolean) || false}
                    onChange={(e) => {
                      handleConfigChange(option.id, e.target.checked);
                    }}
                  />
                  <label htmlFor={`checkbox-${option.id}`}>
                    {option.description ?? option.label}
                  </label>
                </div>
              )}
            </ConfigField>
          ))}
        </div>
      </div>

      {/* Upload Section - Only for load steps */}
      {stepData.type === "load" && (
        <div className="config-options">
          <h4 className="config-section-title">File Upload</h4>
          <div className="config-fields">
            <ConfigField
              label="Upload Files"
              description="Upload files to be processed by this loading step"
            >
              <div className="flex flex-col gap-3">
                <button
                  type="button"
                  onClick={handleUploadClick}
                  className="px-3 py-2 bg-white hover:bg-gray-50 text-brand-primary text-sm font-medium rounded border border-brand-primary transition-colors flex items-center justify-center gap-2 w-full max-w-md"
                >
                  <Upload size={16} />
                  Upload Files
                </button>

                {/* Display uploaded files */}
                {currentFiles.length > 0 && (
                  <div className="uploaded-files-list">
                    <span className="text-xs font-medium text-gray-600 mb-2 block">
                      Uploaded Files:
                    </span>
                    <div className="flex flex-col gap-2">
                      {currentFiles.map((file) => (
                        <div
                          key={file.id}
                          className="flex items-center justify-between bg-gray-50 rounded px-3 py-2 text-sm"
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-gray-700">{file.name}</span>
                            <span className="text-gray-500">({file.size})</span>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveFile(file.id)}
                            className="text-gray-400 hover:text-red-500 transition-colors"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </ConfigField>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onFilesUploaded={handleFilesUploaded}
      />
    </div>
  );
}
